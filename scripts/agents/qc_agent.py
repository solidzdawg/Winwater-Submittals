#!/usr/bin/env python3
"""
QC Agent
========
Quality-checks a submittal project before or after PDF assembly.
Verifies completeness, naming conventions, file ordering, and catch common
mistakes an estimator would get dinged for by the EOR.

Usage:
    python -m agents.qc_agent --project "Double-RR"
"""

import csv
import re
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent.parent
SUBMITTALS_DIR = BASE_DIR / "submittals"


def load_manifest(project_dir: Path) -> list[dict]:
    manifest_path = project_dir / "manifest.csv"
    if not manifest_path.exists():
        return []
    with open(manifest_path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def qc_check(project: str) -> dict:
    """
    Run quality-control checks on the submittal project.

    Returns dict with:
        passed (list[str]), failed (list[str]), warnings (list[str]),
        score (int out of 100)
    """
    project_dir = SUBMITTALS_DIR / project
    report = {"passed": [], "failed": [], "warnings": [], "score": 0}

    if not project_dir.resolve().is_relative_to(SUBMITTALS_DIR.resolve()):
        report["failed"].append(f"Invalid project path: {project}")
        return report

    if not project_dir.exists():
        report["failed"].append("Project directory does not exist")
        return report

    # --- Check 1: Required directories ---
    for d in ["01-cover", "02-index", "03-items", "04-attachments"]:
        if (project_dir / d).exists():
            report["passed"].append(f"Directory exists: {d}/")
        else:
            report["failed"].append(f"Missing directory: {d}/")

    # --- Check 2: Manifest exists and is well-formed ---
    manifest = project_dir / "manifest.csv"
    if manifest.exists():
        rows = load_manifest(project_dir)
        if rows:
            report["passed"].append(f"Manifest loaded: {len(rows)} items")
            # Check required fields
            required_fields = ["item_number", "description", "manufacturer", "model_number", "spec_section"]
            first_row = rows[0]
            for field in required_fields:
                if field in first_row and first_row[field]:
                    report["passed"].append(f"Manifest field present: {field}")
                else:
                    report["failed"].append(f"Manifest missing field: {field}")
        else:
            report["failed"].append("Manifest is empty")
    else:
        report["failed"].append("Manifest file missing")

    # --- Check 3: Cover sheet populated ---
    cover_md = project_dir / "01-cover" / "cover-sheet.md"
    if cover_md.exists():
        content = cover_md.read_text(encoding="utf-8")
        placeholders = re.findall(r"⚠️|{{ .+? }}", content)
        if placeholders:
            report["warnings"].append(
                f"Cover sheet has {len(placeholders)} unfilled placeholders"
            )
        else:
            report["passed"].append("Cover sheet has no ⚠️ placeholders")

        # Check spec sections populated
        if "22" in content:
            report["passed"].append("Cover sheet has spec section references")
        else:
            report["warnings"].append("Cover sheet may be missing spec sections")
    else:
        report["warnings"].append("No cover-sheet.md found (may be PDF only)")

    # --- Check 4: Item index populated ---
    index_md = project_dir / "02-index" / "item-index.md"
    if index_md.exists():
        content = index_md.read_text(encoding="utf-8")
        # Count table rows (lines starting with |)
        rows_found = [l for l in content.split("\n") if l.strip().startswith("|") and "Item" not in l and "---" not in l]
        if len(rows_found) >= len(load_manifest(project_dir)):
            report["passed"].append(f"Item index has {len(rows_found)} rows (matches manifest)")
        else:
            report["warnings"].append(
                f"Item index has {len(rows_found)} rows but manifest has {len(load_manifest(project_dir))} items"
            )
    else:
        report["warnings"].append("No item-index.md found (may be PDF only)")

    # --- Check 5: Sequential item numbering ---
    items_dir = project_dir / "03-items"
    if items_dir.exists():
        item_dirs = sorted([d.name for d in items_dir.iterdir() if d.is_dir()])
        expected = [f"Item-{str(i).zfill(2)}" for i in range(1, len(item_dirs) + 1)]
        if item_dirs == expected:
            report["passed"].append(f"Item folders sequentially numbered: {len(item_dirs)} items")
        else:
            missing = set(expected) - set(item_dirs)
            if missing:
                report["failed"].append(f"Missing item folders: {', '.join(sorted(missing))}")
            extra = set(item_dirs) - set(expected)
            if extra:
                report["warnings"].append(f"Unexpected item folders: {', '.join(sorted(extra))}")

    # --- Check 6: Every item has a separator ---
    rows = load_manifest(project_dir)
    for row in rows:
        item_num = row.get("item_number", "").zfill(2)
        sep = items_dir / f"Item-{item_num}" / "separator.md"
        sep_pdf = items_dir / f"Item-{item_num}" / "separator.pdf"
        if sep.exists() or sep_pdf.exists():
            pass  # don't be verbose on per-item pass
        else:
            report["failed"].append(f"Item-{item_num}: No separator sheet")

    # --- Check 7: Disclaimer exists ---
    disclaimer = project_dir / "04-attachments" / "disclaimer.md"
    disclaimer_pdf = project_dir / "04-attachments" / "disclaimer.pdf"
    if disclaimer.exists() or disclaimer_pdf.exists():
        report["passed"].append("Disclaimer attachment present")
    else:
        report["warnings"].append("No disclaimer found in 04-attachments/")

    # --- Check 8: Spec section format ---
    for row in rows:
        spec = row.get("spec_section", "")
        if spec and not re.match(r"^\d{2}\s\d{2}\s\d{2}$", spec):
            report["warnings"].append(
                f"Item {row.get('item_number', '?')}: Spec section '{spec}' "
                f"doesn't match CSI format XX XX XX"
            )

    # --- Check 9: SUBMITTAL-PACKAGE.md status ---
    pkg_md = project_dir / "SUBMITTAL-PACKAGE.md"
    if pkg_md.exists():
        content = pkg_md.read_text(encoding="utf-8")
        stale_markers = content.count("⚠️")
        if stale_markers == 0:
            report["passed"].append("SUBMITTAL-PACKAGE.md is clean (no ⚠️ markers)")
        else:
            report["warnings"].append(
                f"SUBMITTAL-PACKAGE.md still has {stale_markers} ⚠️ markers"
            )

    # --- Score ---
    total_checks = len(report["passed"]) + len(report["failed"]) + len(report["warnings"])
    if total_checks > 0:
        report["score"] = int(
            (len(report["passed"]) / total_checks) * 100
        )

    return report


def print_qc_report(report: dict) -> None:
    print("\n" + "=" * 60)
    print("  QC REPORT")
    print("=" * 60)

    if report["passed"]:
        print(f"\n✅ PASSED ({len(report['passed'])}):")
        for p in report["passed"]:
            print(f"   • {p}")

    if report["warnings"]:
        print(f"\n⚠️  WARNINGS ({len(report['warnings'])}):")
        for w in report["warnings"]:
            print(f"   • {w}")

    if report["failed"]:
        print(f"\n❌ FAILED ({len(report['failed'])}):")
        for f in report["failed"]:
            print(f"   • {f}")

    grade = "A" if report["score"] >= 90 else "B" if report["score"] >= 75 else "C" if report["score"] >= 60 else "F"
    print(f"\n{'=' * 60}")
    print(f"  QUALITY SCORE: {report['score']}/100 ({grade})")
    print(f"{'=' * 60}\n")


def main():
    import argparse
    parser = argparse.ArgumentParser(description="QC check a submittal project.")
    parser.add_argument("--project", required=True, help="Project folder name")
    args = parser.parse_args()

    print(f"\n{'=' * 60}")
    print(f"  QC Agent")
    print(f"  Project: {args.project}")
    print(f"{'=' * 60}")

    report = qc_check(args.project)
    print_qc_report(report)
    sys.exit(0 if not report["failed"] else 1)


if __name__ == "__main__":
    main()
