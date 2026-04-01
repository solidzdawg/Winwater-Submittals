#!/usr/bin/env python3
"""
Validate Agent
==============
Validates the entire submittal project structure against the manifest.
Reports missing files, empty folders, and readiness status for each item.

Usage:
    python -m agents.validate_agent --project "Double-RR"
"""

import csv
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent.parent
SUBMITTALS_DIR = BASE_DIR / "submittals"


def load_manifest(manifest_path: Path) -> list[dict]:
    """Load and return rows from manifest.csv."""
    if not manifest_path.exists():
        print(f"  ❌ Manifest not found: {manifest_path}")
        return []
    with open(manifest_path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def validate_project(project: str) -> dict:
    """
    Run full validation on a submittal project.

    Returns a report dict with keys:
        ready (bool), errors (list[str]), warnings (list[str]), items (list[dict])
    """
    project_dir = (SUBMITTALS_DIR / project).resolve()
    report = {"ready": True, "errors": [], "warnings": [], "items": []}

    if not project_dir.is_relative_to(SUBMITTALS_DIR.resolve()):
        report["errors"].append(f"Invalid project path: {project}")
        report["ready"] = False
        return report

    if not project_dir.exists():
        report["errors"].append(f"Project directory not found: {project_dir}")
        report["ready"] = False
        return report

    # --- Structural checks ---
    required_dirs = {
        "01-cover": "Cover Sheet",
        "02-index": "Item Index",
        "03-items": "Item Sections",
        "04-attachments": "Attachments",
    }

    for dirname, label in required_dirs.items():
        dir_path = project_dir / dirname
        if not dir_path.exists():
            report["errors"].append(f"Missing required directory: {dirname}/ ({label})")
            report["ready"] = False
        elif dirname != "03-items":
            pdfs = list(dir_path.glob("*.pdf"))
            md_files = list(dir_path.glob("*.md"))
            if not pdfs and not md_files:
                report["warnings"].append(f"{dirname}/ exists but has no PDF or MD files")

    # --- Manifest-driven item validation ---
    manifest_path = project_dir / "manifest.csv"
    items = load_manifest(manifest_path)
    if not items:
        report["errors"].append("Manifest is empty or missing")
        report["ready"] = False
        return report

    items_dir = project_dir / "03-items"

    for row in items:
        item_num = row.get("item_number", "?").zfill(2)
        item_folder = items_dir / f"Item-{item_num}"
        item_report = {
            "item": item_num,
            "description": row.get("description", ""),
            "manufacturer": row.get("manufacturer", ""),
            "model": row.get("model_number", ""),
            "separator": False,
            "cut_sheet": False,
            "certs": [],
            "missing_certs": [],
        }

        if not item_folder.exists():
            report["errors"].append(f"Item-{item_num} folder missing")
            report["ready"] = False
            item_report["separator"] = False
        else:
            # Check separator
            sep_files = list(item_folder.glob("separator.*"))
            item_report["separator"] = len(sep_files) > 0
            if not sep_files:
                report["warnings"].append(f"Item-{item_num}: No separator sheet")

            # Check cut sheet
            cut_sheet_path = row.get("cut_sheet_path", "")
            if cut_sheet_path:
                full_path = BASE_DIR / cut_sheet_path
                item_report["cut_sheet"] = full_path.exists()
                if not full_path.exists():
                    report["warnings"].append(
                        f"Item-{item_num}: Cut sheet not found — {cut_sheet_path}"
                    )
            else:
                # Check for any PDF in folder that isn't a separator
                pdfs = [p for p in item_folder.glob("*.pdf") if "separator" not in p.stem.lower()]
                item_report["cut_sheet"] = len(pdfs) > 0

            # Check certifications
            cert_fields = [
                ("cert_nsf61_path", "NSF 61"),
                ("cert_nsf372_path", "NSF 372"),
                ("other_certs", "Other"),
            ]
            for field, label in cert_fields:
                cert_path = row.get(field, "")
                if cert_path:
                    for single_path in cert_path.split(","):
                        single_path = single_path.strip()
                        if single_path:
                            full = BASE_DIR / single_path
                            if full.exists():
                                item_report["certs"].append(label)
                            else:
                                item_report["missing_certs"].append(f"{label}: {single_path}")
                                report["warnings"].append(
                                    f"Item-{item_num}: Cert not found — {single_path}"
                                )

        report["items"].append(item_report)

    return report


def print_report(report: dict) -> None:
    """Pretty-print the validation report."""
    print("\n" + "=" * 60)
    print("  VALIDATION REPORT")
    print("=" * 60)

    if report["errors"]:
        print(f"\n❌ ERRORS ({len(report['errors'])}):")
        for err in report["errors"]:
            print(f"   • {err}")

    if report["warnings"]:
        print(f"\n⚠️  WARNINGS ({len(report['warnings'])}):")
        for warn in report["warnings"]:
            print(f"   • {warn}")

    print(f"\n📋 ITEM STATUS ({len(report['items'])} items):")
    print(f"   {'Item':<6} {'Sep':>3} {'Cut':>3} {'Certs':>6}  Description")
    print(f"   {'─'*6} {'─'*3} {'─'*3} {'─'*6}  {'─'*30}")
    for item in report["items"]:
        sep = "✅" if item["separator"] else "❌"
        cut = "✅" if item["cut_sheet"] else "❌"
        cert_count = len(item["certs"])
        miss_count = len(item["missing_certs"])
        cert_str = f"{cert_count}/{cert_count + miss_count}" if (cert_count + miss_count) > 0 else "—"
        desc = item["description"][:35]
        print(f"   {item['item']:<6} {sep:>3} {cut:>3} {cert_str:>6}  {desc}")

    status = "✅ READY" if report["ready"] else "❌ NOT READY"
    print(f"\n{'=' * 60}")
    print(f"  STATUS: {status}")
    print(f"{'=' * 60}\n")


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Validate submittal project structure.")
    parser.add_argument("--project", required=True, help="Project folder name")
    args = parser.parse_args()

    report = validate_project(args.project)
    print_report(report)
    sys.exit(0 if report["ready"] else 1)


if __name__ == "__main__":
    main()
