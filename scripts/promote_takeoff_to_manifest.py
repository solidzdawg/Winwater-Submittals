#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Any


MANIFEST_COLUMNS = [
    "item_number",
    "section_name",
    "description",
    "manufacturer",
    "model_number",
    "spec_section",
    "cut_sheet_path",
    "cert_nsf61_path",
    "cert_nsf372_path",
    "other_certs",
    "spec_pages_path",
    "notes",
]


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def pick_best_vendor_path(item_number: int, vendor_matches: dict[str, Any], min_score: float) -> str:
    for item in vendor_matches.get("items", []):
        if int(item.get("item_number", -1)) != int(item_number):
            continue
        for candidate in item.get("candidates", []):
            if float(candidate.get("score", 0.0)) >= min_score:
                return str(candidate.get("path", ""))
    return ""


def source_pages(item: dict[str, Any], doc_filter: str | None = None) -> str:
    values: list[str] = []
    for evidence in item.get("source_evidence", []):
        document_path = str(evidence.get("document_path", ""))
        if doc_filter and doc_filter not in document_path.lower():
            continue
        values.append(f"{document_path}#page={evidence.get('page_number')}")
    deduped = list(dict.fromkeys(values))
    return "; ".join(deduped)


def should_promote(item: dict[str, Any], min_confidence: float, allow_review: bool) -> tuple[bool, list[str]]:
    reasons: list[str] = []
    confidence = float(item.get("confidence", 0.0))
    if confidence < min_confidence:
        reasons.append(f"confidence<{min_confidence}")
    if item.get("needs_review") and not allow_review:
        reasons.append("needs_review=true")
    if not item.get("manufacturer"):
        reasons.append("missing manufacturer")
    if not item.get("model_number"):
        reasons.append("missing model number")
    if not item.get("spec_section"):
        reasons.append("missing spec section")
    if not item.get("source_evidence"):
        reasons.append("missing source evidence")
    return len(reasons) == 0, reasons


def promote(
    takeoff: dict[str, Any],
    vendor_matches: dict[str, Any],
    output_csv: Path,
    skipped_json: Path,
    min_confidence: float,
    min_vendor_score: float,
    allow_review: bool,
) -> dict[str, Any]:
    promoted = 0
    skipped: list[dict[str, Any]] = []

    output_csv.parent.mkdir(parents=True, exist_ok=True)
    with output_csv.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=MANIFEST_COLUMNS)
        writer.writeheader()

        for item in takeoff.get("items", []):
            is_ok, reasons = should_promote(item, min_confidence=min_confidence, allow_review=allow_review)
            if not is_ok:
                skipped.append(
                    {
                        "item_number": item.get("item_number"),
                        "description": item.get("description"),
                        "reasons": reasons,
                    }
                )
                continue

            writer.writerow(
                {
                    "item_number": item.get("item_number"),
                    "section_name": item.get("submittal_group", ""),
                    "description": item.get("description", ""),
                    "manufacturer": item.get("manufacturer", ""),
                    "model_number": item.get("model_number", ""),
                    "spec_section": item.get("spec_section", ""),
                    "cut_sheet_path": pick_best_vendor_path(item.get("item_number"), vendor_matches, min_score=min_vendor_score),
                    "cert_nsf61_path": "",
                    "cert_nsf372_path": "",
                    "other_certs": "",
                    "spec_pages_path": source_pages(item, doc_filter="spec"),
                    "notes": item.get("notes", ""),
                }
            )
            promoted += 1

    skipped_json.parent.mkdir(parents=True, exist_ok=True)
    skipped_json.write_text(
        json.dumps(
            {
                "project": takeoff.get("project", {}),
                "promoted_count": promoted,
                "skipped_count": len(skipped),
                "skipped_items": skipped,
            },
            indent=2,
        ),
        encoding="utf-8",
    )

    return {
        "promoted_count": promoted,
        "skipped_count": len(skipped),
        "output_csv": output_csv.as_posix(),
        "skipped_json": skipped_json.as_posix(),
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Promote trusted takeoff rows into a Winwater-style manifest CSV."
    )
    parser.add_argument("--takeoff", required=True, help="Path to takeoff.normalized.json")
    parser.add_argument("--vendor-matches", required=True, help="Path to vendor-match-candidates.json")
    parser.add_argument("--output-csv", default="_output/promoted/manifest.promoted.csv", help="Path for promoted manifest CSV")
    parser.add_argument("--skipped-json", default="_output/promoted/skipped-items.json", help="Path for skipped item report")
    parser.add_argument("--min-confidence", type=float, default=0.85, help="Minimum confidence required for promotion")
    parser.add_argument("--min-vendor-score", type=float, default=4.0, help="Minimum vendor candidate score to auto-fill cut_sheet_path")
    parser.add_argument("--allow-review", action="store_true", help="Allow promotion of rows still marked needs_review")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    result = promote(
        takeoff=load_json(Path(args.takeoff)),
        vendor_matches=load_json(Path(args.vendor_matches)),
        output_csv=Path(args.output_csv),
        skipped_json=Path(args.skipped_json),
        min_confidence=args.min_confidence,
        min_vendor_score=args.min_vendor_score,
        allow_review=args.allow_review,
    )
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
