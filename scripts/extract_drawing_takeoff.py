#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
import os
import re
import sys
from collections import OrderedDict
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

from scripts.lib.pdf_ingest import build_document_inventory, build_inventory_summary, normalize_whitespace

try:
    from openai import OpenAI
except ImportError:  # pragma: no cover - handled at runtime
    OpenAI = None  # type: ignore[assignment]


SCHEMA_PATH = BASE_DIR / "schemas" / "drawing_takeoff.schema.json"
EXPORT_COLUMNS = [
    "item_number",
    "section_name",
    "description",
    "manufacturer",
    "model_number",
    "spec_section",
    "quantity",
    "quantity_unit",
    "cut_sheet_path",
    "cert_nsf61_path",
    "cert_nsf372_path",
    "other_certs",
    "spec_pages_path",
    "notes",
    "confidence",
    "review_status",
    "source_pages",
]

SYSTEM_PROMPT = """
You are a senior construction submittal and takeoff analyst.
Extract material and equipment rows from the provided PDFs with a bias toward correctness over completeness.
Read schedules, legends, keyed notes, callouts, details, and specification references together.
Only emit an item when there is document evidence for it.
Never invent a manufacturer, model number, quantity, or spec section.
If the evidence is incomplete or conflicting, leave the uncertain field blank, set needs_review=true, and lower confidence.
Every item must include source_evidence entries with exact page references and short supporting quotes.
Merge duplicate mentions of the same real-world item when the evidence clearly matches.
""".strip()


def load_sources(sources_path: Path) -> dict[str, Any]:
    payload = json.loads(sources_path.read_text(encoding="utf-8"))
    if "documents" not in payload or not payload["documents"]:
        raise ValueError("sources file must contain a non-empty 'documents' list")
    return payload


def repo_path(raw_path: str) -> Path:
    path = Path(raw_path)
    return path if path.is_absolute() else (BASE_DIR / path)


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
        if not path.exists():
            raise FileNotFoundError(f"source document not found: {document['path']}")
        inventory["documents"].append(
            build_document_inventory(path, output_dir=output_dir, kind=document.get("kind", "drawings"), dpi=dpi)
        )

    return inventory


def load_schema() -> dict[str, Any]:
    return json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))


def extract_output_text(response: Any) -> str:
    output_text = getattr(response, "output_text", None)
    if output_text:
        return output_text

    parts: list[str] = []
    for output in getattr(response, "output", []) or []:
        for content in getattr(output, "content", []) or []:
            text = getattr(content, "text", None)
            if text:
                parts.append(text)
                continue
            if isinstance(content, dict) and content.get("text"):
                parts.append(str(content["text"]))
    if not parts:
        raise ValueError("OpenAI response did not contain output text")
    return "".join(parts)


def extract_with_openai(
    schema: dict[str, Any],
    inventory: dict[str, Any],
    sources: dict[str, Any],
    model: str,
) -> dict[str, Any]:
    if OpenAI is None:
        raise RuntimeError("openai package is not installed. Run: pip install -r requirements.txt")
    if not os.environ.get("OPENAI_API_KEY"):
        raise RuntimeError("OPENAI_API_KEY is not set")

    client = OpenAI()

    input_content: list[dict[str, Any]] = [
        {
            "type": "input_text",
            "text": (
                "Project context:\n"
                f"- code: {inventory['project']['code']}\n"
                f"- name: {inventory['project']['name']}\n\n"
                "Use the uploaded PDFs as the primary source of truth.\n"
                "Use this page inventory as a locator index, not as a substitute for reading the documents:\n"
                f"{build_inventory_summary(inventory)}\n\n"
                "Return a single consolidated takeoff/submittal draft that follows the provided schema."
            ),
        }
    ]

    for document in sources["documents"]:
        path = repo_path(document["path"])
        if path.suffix.lower() != ".pdf":
            continue
        with path.open("rb") as handle:
            uploaded = client.files.create(file=handle, purpose="user_data")
        input_content.append({"type": "input_file", "file_id": uploaded.id})

    response = client.responses.create(
        model=model,
        input=[
            {"role": "system", "content": [{"type": "input_text", "text": SYSTEM_PROMPT}]},
            {"role": "user", "content": input_content},
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

    raw = extract_output_text(response)
    return json.loads(raw)


def fallback_takeoff(inventory: dict[str, Any], reason: str) -> dict[str, Any]:
    return {
        "project": inventory["project"],
        "items": [],
        "drawing_notes": [],
        "assumptions": [reason],
    }


def clamp_confidence(value: Any) -> float:
    try:
        numeric = float(value)
    except (TypeError, ValueError):
        numeric = 0.0
    return max(0.0, min(1.0, round(numeric, 2)))


def normalize_spec_section(value: str) -> str:
    digits = re.findall(r"\d+", value or "")
    if len(digits) >= 3:
        return f"{digits[0].zfill(2)} {digits[1].zfill(2)} {digits[2].zfill(2)}"
    return normalize_whitespace(value)


def normalize_document_path(value: str, known_paths: set[str]) -> str:
    cleaned = normalize_whitespace(value)
    if cleaned in known_paths:
        return cleaned
    basename = Path(cleaned).name
    for known in known_paths:
        if Path(known).name == basename:
            return known
    return basename


def merge_text(left: str, right: str) -> str:
    left = normalize_whitespace(left)
    right = normalize_whitespace(right)
    if not left:
        return right
    if not right or right in left:
        return left
    if left in right:
        return right
    return f"{left}; {right}"


def normalize_takeoff(raw_takeoff: dict[str, Any], inventory: dict[str, Any]) -> dict[str, Any]:
    known_paths = {document["document_path"] for document in inventory.get("documents", [])}
    grouped: OrderedDict[tuple[str, str, str, str, str], dict[str, Any]] = OrderedDict()

    for raw_item in raw_takeoff.get("items", []):
        description = normalize_whitespace(raw_item.get("description", ""))
        manufacturer = normalize_whitespace(raw_item.get("manufacturer", ""))
        model_number = normalize_whitespace(raw_item.get("model_number", ""))
        spec_section = normalize_spec_section(raw_item.get("spec_section", ""))
        quantity = raw_item.get("quantity")
        quantity_unit = normalize_whitespace(raw_item.get("quantity_unit", "ea")) or "ea"
        notes = normalize_whitespace(raw_item.get("notes", ""))
        submittal_group = normalize_whitespace(raw_item.get("submittal_group", ""))
        confidence = clamp_confidence(raw_item.get("confidence", 0.0))
        needs_review = bool(raw_item.get("needs_review", False))
        review_reasons: list[str] = []

        if quantity is not None:
            try:
                quantity = float(quantity)
            except (TypeError, ValueError):
                quantity = None

        evidence_rows: list[dict[str, Any]] = []
        for evidence in raw_item.get("source_evidence", []):
            document_path = normalize_document_path(evidence.get("document_path", ""), known_paths)
            quote = normalize_whitespace(evidence.get("evidence_quote", ""))[:300]
            reason = normalize_whitespace(evidence.get("reason", ""))[:200]
            try:
                page_number = int(evidence.get("page_number"))
            except (TypeError, ValueError):
                page_number = 0
            page_label = normalize_whitespace(str(evidence.get("page_label", page_number or "")))
            sheet_id = evidence.get("sheet_id") or None
            if page_number <= 0 or not quote:
                continue
            evidence_rows.append(
                {
                    "document_path": document_path,
                    "page_number": page_number,
                    "page_label": page_label,
                    "sheet_id": sheet_id,
                    "evidence_quote": quote,
                    "reason": reason,
                }
            )

        if not description:
            review_reasons.append("missing description")
        if not manufacturer:
            review_reasons.append("missing manufacturer")
        if not model_number:
            review_reasons.append("missing model number")
        if not re.match(r"^\d{2} \d{2} \d{2}$", spec_section):
            review_reasons.append("spec section is not in CSI format")
        if not evidence_rows:
            review_reasons.append("missing source evidence")
        if confidence < 0.75:
            review_reasons.append("confidence below 0.75")

        if review_reasons:
            needs_review = True

        key = (
            description.lower(),
            manufacturer.lower(),
            model_number.lower(),
            spec_section.lower(),
            quantity_unit.lower(),
        )

        normalized = {
            "description": description,
            "manufacturer": manufacturer,
            "model_number": model_number,
            "spec_section": spec_section,
            "quantity": quantity,
            "quantity_unit": quantity_unit,
            "notes": notes,
            "submittal_group": submittal_group,
            "confidence": confidence,
            "needs_review": needs_review,
            "review_reasons": review_reasons,
            "source_evidence": evidence_rows,
        }

        if key not in grouped:
            grouped[key] = normalized
            continue

        existing = grouped[key]
        if existing["quantity"] is not None and quantity is not None:
            existing["quantity"] = float(existing["quantity"]) + float(quantity)
        elif existing["quantity"] is None:
            existing["quantity"] = quantity
        existing["notes"] = merge_text(existing["notes"], notes)
        existing["submittal_group"] = existing["submittal_group"] or submittal_group
        existing["confidence"] = round(min(existing["confidence"], confidence), 2)
        existing["needs_review"] = existing["needs_review"] or needs_review
        existing["review_reasons"] = sorted(set(existing["review_reasons"] + review_reasons))
        existing["source_evidence"].extend(evidence_rows)

    items: list[dict[str, Any]] = []
    for index, item in enumerate(grouped.values(), start=1):
        item["item_number"] = index
        item["source_evidence"] = sorted(
            item["source_evidence"], key=lambda row: (row["document_path"], row["page_number"], row["evidence_quote"])
        )
        items.append(item)

    return {
        "project": raw_takeoff.get("project", inventory["project"]),
        "items": items,
        "drawing_notes": raw_takeoff.get("drawing_notes", []),
        "assumptions": raw_takeoff.get("assumptions", []),
    }


def validate_takeoff(schema: dict[str, Any], takeoff: dict[str, Any]) -> None:
    validator = Draft202012Validator(schema)
    errors = sorted(validator.iter_errors(takeoff), key=lambda error: list(error.absolute_path))
    if errors:
        message = "; ".join(f"{'/'.join(map(str, error.absolute_path))}: {error.message}" for error in errors[:10])
        raise ValueError(f"schema validation failed: {message}")


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def write_manifest_csv(path: Path, takeoff: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=EXPORT_COLUMNS)
        writer.writeheader()
        for item in takeoff.get("items", []):
            source_pages = "; ".join(
                f"{e['document_path']}#page={e['page_number']}" for e in item.get("source_evidence", [])
            )
            spec_pages = "; ".join(
                f"{e['document_path']}#page={e['page_number']}"
                for e in item.get("source_evidence", [])
                if "spec" in e["document_path"].lower()
            )
            writer.writerow(
                {
                    "item_number": item["item_number"],
                    "section_name": item.get("submittal_group", ""),
                    "description": item.get("description", ""),
                    "manufacturer": item.get("manufacturer", ""),
                    "model_number": item.get("model_number", ""),
                    "spec_section": item.get("spec_section", ""),
                    "quantity": item.get("quantity", ""),
                    "quantity_unit": item.get("quantity_unit", ""),
                    "cut_sheet_path": "",
                    "cert_nsf61_path": "",
                    "cert_nsf372_path": "",
                    "other_certs": "",
                    "spec_pages_path": spec_pages,
                    "notes": item.get("notes", ""),
                    "confidence": item.get("confidence", 0),
                    "review_status": "needs_review" if item.get("needs_review") else "ready",
                    "source_pages": source_pages,
                }
            )


def write_traceability_report(path: Path, inventory: dict[str, Any], takeoff: dict[str, Any]) -> None:
    lines = [
        f"# {inventory['project']['name']} Drawing Takeoff Traceability",
        "",
        f"Project code: `{inventory['project']['code']}`",
        "",
        "## Documents",
        "",
    ]
    for document in inventory.get("documents", []):
        lines.append(
            f"- `{document['document_path']}` ({document['document_kind']}, {document['page_count']} pages)"
        )
    lines.extend(["", "## Items", ""])

    for item in takeoff.get("items", []):
        review_state = "needs review" if item.get("needs_review") else "ready"
        lines.append(
            f"### Item {item['item_number']}: {item['description']}"
        )
        lines.append(
            f"- Manufacturer / model: `{item['manufacturer']}` / `{item['model_number']}`"
        )
        lines.append(
            f"- Spec / qty: `{item['spec_section']}` / `{item['quantity']}` `{item['quantity_unit']}`"
        )
        lines.append(
            f"- Confidence: `{item['confidence']}` ({review_state})"
        )
        if item.get("review_reasons"):
            lines.append(f"- Review reasons: {', '.join(item['review_reasons'])}")
        if item.get("notes"):
            lines.append(f"- Notes: {item['notes']}")
        lines.append("- Evidence:")
        for evidence in item.get("source_evidence", []):
            sheet = evidence.get("sheet_id") or "n/a"
            lines.append(
                "  - "
                f"{evidence['document_path']} page {evidence['page_number']} "
                f"(label `{evidence['page_label']}`, sheet `{sheet}`): "
                f"{evidence['reason']} -> \"{evidence['evidence_quote']}\""
            )
        lines.append("")

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")


def run_pipeline(args: argparse.Namespace) -> dict[str, Any]:
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    sources = load_sources(Path(args.sources))
    inventory = inventory_documents(sources, output_dir=output_dir, dpi=args.dpi)
    write_json(output_dir / "inventory.json", inventory)

    schema = load_schema()
    if args.inventory_only:
        takeoff = fallback_takeoff(inventory, "inventory-only run; model extraction skipped")
    else:
        try:
            takeoff = extract_with_openai(schema=schema, inventory=inventory, sources=sources, model=args.model)
            validate_takeoff(schema, takeoff)
        except Exception as exc:
            takeoff = fallback_takeoff(inventory, f"model extraction skipped: {exc}")

    normalized = normalize_takeoff(takeoff, inventory)
    write_json(output_dir / "takeoff.raw.json", takeoff)
    write_json(output_dir / "takeoff.normalized.json", normalized)
    write_manifest_csv(output_dir / "manifest.draft.csv", normalized)
    write_traceability_report(output_dir / "traceability.md", inventory, normalized)
    return normalized


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Extract evidence-backed takeoff/submittal drafts from drawing and spec PDFs."
    )
    parser.add_argument("--sources", required=True, help="Path to the sources JSON file")
    parser.add_argument("--output-dir", default="_output/drawing-takeoff", help="Directory for generated artifacts")
    parser.add_argument("--dpi", type=int, default=150, help="Rasterization DPI for page images")
    parser.add_argument("--model", default="gpt-5", help="OpenAI model name for multimodal extraction")
    parser.add_argument("--inventory-only", action="store_true", help="Skip model extraction and only build page inventory")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    result = run_pipeline(args)
    print(json.dumps(
        {
            "project": result["project"],
            "item_count": len(result.get("items", [])),
            "assumptions": result.get("assumptions", []),
        },
        indent=2,
    ))


if __name__ == "__main__":
    main()
