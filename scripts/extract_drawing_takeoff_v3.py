#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
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
from scripts.extract_drawing_takeoff_v2 import enrich_with_vendor_candidates, write_review_queue
from scripts.lib.note_extract import extract_notes_from_inventory, summarize_notes
from scripts.lib.page_select import select_priority_pages
from scripts.lib.pdf_ingest import build_document_inventory, build_inventory_summary

try:
    from openai import OpenAI
except ImportError:  # pragma: no cover
    OpenAI = None  # type: ignore[assignment]


SYSTEM_PROMPT = """
You are a senior construction submittal and takeoff analyst.
Build a conservative, evidence-backed takeoff from the supplied drawings and specifications.
Use the uploaded PDFs as the primary source of truth.
Use the uploaded page snapshots to read schedule tables, keyed notes, legends, and drawing annotations that may be weak in the PDF text layer.
Prefer omission over invention.
If evidence is partial or conflicting, keep the row but set needs_review=true and lower confidence.
Every extracted item must cite page-level evidence and a short supporting quote.
Also capture any drawing_notes that materially change product selection, quantity, submittal grouping, or required certifications.
""".strip()


def inventory_documents(sources: dict[str, Any], output_dir: Path, dpi: int) -> dict[str, Any]:
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


def upload_pdf_inputs(client: Any, sources: dict[str, Any]) -> list[dict[str, Any]]:
    inputs: list[dict[str, Any]] = []
    for document in sources["documents"]:
        path = repo_path(document["path"])
        if path.suffix.lower() != ".pdf":
            continue
        with path.open("rb") as handle:
            uploaded = client.files.create(file=handle, purpose="user_data")
        inputs.append({"type": "input_file", "file_id": uploaded.id})
    return inputs


def upload_priority_page_images(client: Any, priority_pages: list[dict[str, Any]]) -> list[dict[str, Any]]:
    content: list[dict[str, Any]] = []
    for index, page in enumerate(priority_pages, start=1):
        image_path = BASE_DIR / page["image_path"] if not Path(page["image_path"]).is_absolute() else Path(page["image_path"])
        with image_path.open("rb") as handle:
            uploaded = client.files.create(file=handle, purpose="vision")
        reason_text = ", ".join(page.get("reasons", []))
        content.append(
            {
                "type": "input_text",
                "text": (
                    f"Priority page snapshot {index}: {page['document_path']} page {page['page_number']} "
                    f"(label {page['page_label']}, sheet {page.get('sheet_id')}, score {page['score']}). "
                    f"Why it matters: {reason_text}."
                ),
            }
        )
        content.append(
            {
                "type": "input_image",
                "file_id": uploaded.id,
            }
        )
    return content


def extract_with_openai(
    schema: dict[str, Any],
    inventory: dict[str, Any],
    notes: list[dict[str, Any]],
    sources: dict[str, Any],
    priority_pages: list[dict[str, Any]],
    model: str,
) -> dict[str, Any]:
    if OpenAI is None:
        raise RuntimeError("openai package is not installed. Run: pip install -r requirements.txt")
    if not os.environ.get("OPENAI_API_KEY"):
        raise RuntimeError("OPENAI_API_KEY is not set")

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
                "Priority page snapshots were selected because they are likely to contain schedules, notes, legends, or spec references.\n"
                "Return one consolidated JSON object matching the schema exactly."
            ),
        }
    ]
    content.extend(upload_priority_page_images(client, priority_pages))
    content.extend(upload_pdf_inputs(client, sources))

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


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Page-image assisted drawing takeoff pipeline for high-accuracy PDF extraction."
    )
    parser.add_argument("--sources", required=True, help="Path to the sources JSON file")
    parser.add_argument("--output-dir", default="_output/drawing-takeoff-v3", help="Directory for generated artifacts")
    parser.add_argument("--dpi", type=int, default=180, help="Rasterization DPI for page images")
    parser.add_argument("--model", default="gpt-5", help="OpenAI model name")
    parser.add_argument("--inventory-only", action="store_true", help="Skip model extraction and only build inventory/note outputs")
    parser.add_argument("--max-page-images", type=int, default=12, help="Maximum number of priority page images to upload")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    sources = load_sources(Path(args.sources))
    inventory = inventory_documents(sources, output_dir=output_dir, dpi=args.dpi)
    notes = extract_notes_from_inventory(inventory)
    priority_pages = select_priority_pages(inventory, max_pages=args.max_page_images)

    write_json(output_dir / "inventory.json", inventory)
    write_json(output_dir / "drawing-notes.json", {"notes": notes})
    write_json(output_dir / "priority-pages.json", {"pages": priority_pages})

    schema = load_schema()
    if args.inventory_only:
        raw_takeoff = fallback_takeoff(inventory, "inventory-only run; model extraction skipped")
        raw_takeoff["drawing_notes"] = notes
    else:
        try:
            raw_takeoff = extract_with_openai(
                schema=schema,
                inventory=inventory,
                notes=notes,
                sources=sources,
                priority_pages=priority_pages,
                model=args.model,
            )
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
            "priority_page_count": len(priority_pages),
            "needs_review": sum(1 for item in normalized.get("items", []) if item.get("needs_review")),
        },
        indent=2,
    ))


if __name__ == "__main__":
    main()
