#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

from scripts.extract_drawing_takeoff import (
    extract_output_text,
    fallback_takeoff,
    load_schema,
    load_sources,
    normalize_takeoff,
    repo_path,
    validate_takeoff,
    write_json,
    write_manifest_csv,
    write_traceability_report,
)
from scripts.lib.note_extract import extract_notes_from_inventory, summarize_notes
from scripts.lib.pdf_ingest import build_inventory_summary, build_document_inventory
from scripts.lib.vendor_match import match_vendor_documents

try:
    from openai import OpenAI
except ImportError:  # pragma: no cover
    OpenAI = None  # type: ignore[assignment]


SYSTEM_PROMPT = """
You are a senior construction submittal and takeoff analyst.
Create a conservative, reviewer-friendly equipment/material takeoff from the supplied PDFs.
Use schedules, legends, keyed notes, callouts, and spec sections together.
Treat the page inventory and extracted note summary as navigation aids, but rely on the PDFs for final evidence.
Do not invent missing manufacturers, models, quantities, or spec sections.
If there is ambiguity, keep the row, mark needs_review=true, and lower confidence.
Every item must cite exact pages and short evidence quotes.
Also capture drawing_notes for keyed/general notes that materially affect takeoff or submittal grouping.
""".strip()


def inventory_documents_v2(sources: dict[str, Any], output_dir: Path, dpi: int) -> dict[str, Any]:
    inventory = {
        "project": {
            "code": sources.get("project_code", "UNKNOWN"),
            "name": sources.get("project_name", sources.get("project_code", "Unknown Project")),
        },
        "documents": [],
    }
    for document in sources["documents"]:
        path = repo_path(document["path"])
        if path.suffix.lower() != ".pdf":
            continue
        inventory["documents"].append(
            build_document_inventory(path, output_dir=output_dir, kind=document.get("kind", "drawings"), dpi=dpi)
        )
    return inventory


def extract_with_openai_v2(
    schema: dict[str, Any],
    inventory: dict[str, Any],
    notes: list[dict[str, Any]],
    sources: dict[str, Any],
    model: str,
) -> dict[str, Any]:
    if OpenAI is None:
        raise RuntimeError("openai package is not installed. Run: pip install -r requirements.txt")

    client = OpenAI()
    content: list[dict[str, Any]] = [
        {
            "type": "input_text",
            "text": (
                f"Project code: {inventory['project']['code']}\n"
                f"Project name: {inventory['project']['name']}\n\n"
                "Page inventory summary:\n"
                f"{build_inventory_summary(inventory)}\n\n"
                "Extracted keyed/general notes summary:\n"
                f"{summarize_notes(notes) or '- none found -'}\n\n"
                "Return one consolidated JSON object matching the schema exactly."
            ),
        }
    ]

    for document in sources["documents"]:
        path = repo_path(document["path"])
        if path.suffix.lower() != ".pdf":
            continue
        with path.open("rb") as handle:
            uploaded = client.files.create(file=handle, purpose="user_data")
        content.append({"type": "input_file", "file_id": uploaded.id})

    response = client.responses.create(
        model=model,
        input=[
            {"role": "system", "content": [{"type": "input_text", "text": SYSTEM_PROMPT}]},
            {"role": "user", "content": content},
        ],
        text={
            "format": {
                "type": "json_schema",
                "name": "drawing_takeoff",
                "strict": True,
                "schema": schema,
            }
        },
    )
    return json.loads(extract_output_text(response))


def enrich_with_vendor_candidates(normalized: dict[str, Any], base_dir: Path) -> list[dict[str, Any]]:
    return match_vendor_documents(normalized.get("items", []), base_dir=base_dir)


def write_review_queue(path: Path, takeoff: dict[str, Any], vendor_matches: list[dict[str, Any]]) -> None:
    vendor_map = {row["item_number"]: row for row in vendor_matches}
    rows = sorted(
        takeoff.get("items", []),
        key=lambda item: (not item.get("needs_review", False), item.get("confidence", 1.0), item.get("item_number", 9999)),
    )

    lines = [
        f"# {takeoff['project']['name']} Review Queue",
        "",
        "Rows at the top need the most attention.",
        "",
    ]

    for item in rows:
        state = "needs review" if item.get("needs_review") else "ready"
        lines.append(f"## Item {item['item_number']} - {item['description']}")
        lines.append(f"- Status: `{state}`")
        lines.append(f"- Confidence: `{item.get('confidence', 0)}`")
        lines.append(f"- Manufacturer/model: `{item.get('manufacturer', '')}` / `{item.get('model_number', '')}`")
        lines.append(f"- Spec/qty: `{item.get('spec_section', '')}` / `{item.get('quantity', '')}` `{item.get('quantity_unit', '')}`")
        if item.get("review_reasons"):
            lines.append(f"- Review reasons: {', '.join(item['review_reasons'])}")
        if item.get("notes"):
            lines.append(f"- Notes: {item['notes']}")
        candidate_block = vendor_map.get(item["item_number"], {}).get("candidates", [])
        if candidate_block:
            lines.append("- Candidate vendor PDFs:")
            for candidate in candidate_block[:3]:
                lines.append(f"  - `{candidate['path']}` (score `{candidate['score']}`)")
        else:
            lines.append("- Candidate vendor PDFs: none")
        lines.append("- Evidence:")
        for evidence in item.get("source_evidence", [])[:5]:
            lines.append(
                f"  - `{evidence['document_path']}` page `{evidence['page_number']}` sheet `{evidence.get('sheet_id')}`: {evidence['reason']} -> \"{evidence['evidence_quote']}\""
            )
        lines.append("")

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Enhanced drawing takeoff pipeline with note extraction and vendor matching."
    )
    parser.add_argument("--sources", required=True, help="Path to the sources JSON file")
    parser.add_argument("--output-dir", default="_output/drawing-takeoff-v2", help="Directory for generated artifacts")
    parser.add_argument("--dpi", type=int, default=170, help="Rasterization DPI for page images")
    parser.add_argument("--model", default="gpt-5", help="OpenAI model name")
    parser.add_argument("--inventory-only", action="store_true", help="Skip model extraction and only build inventory/note outputs")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    sources = load_sources(Path(args.sources))
    inventory = inventory_documents_v2(sources, output_dir=output_dir, dpi=args.dpi)
    notes = extract_notes_from_inventory(inventory)

    write_json(output_dir / "inventory.json", inventory)
    write_json(output_dir / "drawing-notes.json", {"notes": notes})

    schema = load_schema()
    if args.inventory_only:
        raw_takeoff = fallback_takeoff(inventory, "inventory-only run; model extraction skipped")
        raw_takeoff["drawing_notes"] = notes
    else:
        try:
            raw_takeoff = extract_with_openai_v2(schema=schema, inventory=inventory, notes=notes, sources=sources, model=args.model)
            validate_takeoff(schema, raw_takeoff)
        except Exception as exc:
            raw_takeoff = fallback_takeoff(inventory, f"model extraction skipped: {exc}")
            raw_takeoff["drawing_notes"] = notes

    normalized = normalize_takeoff(raw_takeoff, inventory)
    if not normalized.get("drawing_notes"):
        normalized["drawing_notes"] = notes

    vendor_matches = enrich_with_vendor_candidates(normalized, base_dir=BASE_DIR)

    write_json(output_dir / "takeoff.raw.json", raw_takeoff)
    write_json(output_dir / "takeoff.normalized.json", normalized)
    write_json(output_dir / "vendor-match-candidates.json", {"items": vendor_matches})
    write_manifest_csv(output_dir / "manifest.draft.csv", normalized)
    write_traceability_report(output_dir / "traceability.md", inventory, normalized)
    write_review_queue(output_dir / "review-queue.md", normalized, vendor_matches)

    print(json.dumps(
        {
            "project": normalized["project"],
            "item_count": len(normalized.get("items", [])),
            "note_count": len(notes),
            "needs_review": sum(1 for item in normalized.get("items", []) if item.get("needs_review")),
        },
        indent=2,
    ))


if __name__ == "__main__":
    main()
