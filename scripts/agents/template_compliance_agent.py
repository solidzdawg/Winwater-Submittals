#!/usr/bin/env python3
"""
Template Compliance Agent
=========================
Checks whether a project is positioned to produce polished submittals from the
required Office templates (cover, item index, separator) and flags common
"looks bad" failure modes before PDF build.

Usage:
    python -m agents.template_compliance_agent --project "Double-RR"
"""

from __future__ import annotations

import csv
import json
import re
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent.parent
SUBMITTALS_DIR = BASE_DIR / "submittals"
TEMPLATES_DIR = BASE_DIR / "templates"

REQUIRED_TEMPLATE_CANDIDATES = {
    "cover": ["submittal cover.xlsx"],
    "index": ["Item Index Template.docx"],
    "separator": ["Seperator Sheet Template.docx", "Separator Sheet Template.docx"],
}


def _template_exists(candidates: list[str]) -> Path | None:
    for name in candidates:
        path = TEMPLATES_DIR / name
        if path.exists():
            return path
    return None


def _load_manifest(project_dir: Path) -> list[dict]:
    manifest_path = project_dir / "manifest.csv"
    if not manifest_path.exists():
        return []
    with open(manifest_path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def _load_project_json(project_dir: Path) -> dict:
    config_path = project_dir / "project.json"
    if not config_path.exists():
        return {}
    return json.loads(config_path.read_text(encoding="utf-8"))


def compliance_check(project: str) -> dict:
    report = {
        "passed": [],
        "failed": [],
        "warnings": [],
        "score": 0,
    }

    project_dir = SUBMITTALS_DIR / project
    if not project_dir.exists():
        report["failed"].append("Project directory does not exist")
        return report

    # 1) Required Office templates available
    for template_type, names in REQUIRED_TEMPLATE_CANDIDATES.items():
        found = _template_exists(names)
        if found:
            report["passed"].append(f"Template present ({template_type}): {found.name}")
        else:
            report["failed"].append(
                f"Missing required {template_type} template in templates/: {', '.join(names)}"
            )

    # 2) project.json has essentials used by template fill
    config = _load_project_json(project_dir)
    required_project_fields = [
        "project_name",
        "project_number",
        "submittal_prefix",
        "revision",
        "date",
        "submitted_by",
        "submittal_sets",
    ]
    for field in required_project_fields:
        if config.get(field):
            report["passed"].append(f"project.json field present: {field}")
        else:
            report["failed"].append(f"project.json missing required field: {field}")

    # 3) Manifest hygiene for visual output quality
    rows = _load_manifest(project_dir)
    if not rows:
        report["failed"].append("manifest.csv missing or empty")
    else:
        report["passed"].append(f"Manifest loaded: {len(rows)} rows")

    max_desc = 56
    max_mfr = 26
    max_model = 26
    for row in rows:
        item = row.get("item_number", "?")
        desc = (row.get("description") or "").strip()
        mfr = (row.get("manufacturer") or "").strip()
        model = (row.get("model_number") or "").strip()
        spec = (row.get("spec_section") or "").strip()

        if len(desc) > max_desc:
            report["warnings"].append(
                f"Item {item}: description likely wraps badly on separator/index ({len(desc)}>{max_desc})"
            )
        if len(mfr) > max_mfr:
            report["warnings"].append(
                f"Item {item}: manufacturer likely wraps badly ({len(mfr)}>{max_mfr})"
            )
        if len(model) > max_model:
            report["warnings"].append(
                f"Item {item}: model likely wraps badly ({len(model)}>{max_model})"
            )
        if spec and not re.match(r"^\d{2}\s\d{2}\s\d{2}$", spec):
            report["warnings"].append(
                f"Item {item}: spec_section '{spec}' not in CSI format XX XX XX"
            )

        cut = (row.get("cut_sheet_path") or "").strip()
        if cut:
            full = BASE_DIR / cut
            if full.exists() and full.suffix.lower() == ".pdf":
                report["passed"].append(f"Item {item}: cut sheet PDF found")
            else:
                report["failed"].append(f"Item {item}: missing cut_sheet_path PDF: {cut}")
        else:
            report["failed"].append(f"Item {item}: cut_sheet_path is blank")

    # 4) Check markdown placeholders in working docs (if those files are used)
    markdown_checks = [
        project_dir / "01-cover" / "cover-sheet.md",
        project_dir / "02-index" / "item-index.md",
    ]
    for file in markdown_checks:
        if not file.exists():
            report["warnings"].append(f"Optional source not found: {file.relative_to(project_dir)}")
            continue
        content = file.read_text(encoding="utf-8")
        placeholders = re.findall(r"\{\{\s*[^}]+\s*\}\}", content)
        if placeholders:
            report["warnings"].append(
                f"{file.relative_to(project_dir)} has {len(placeholders)} unresolved placeholders"
            )
        else:
            report["passed"].append(f"{file.relative_to(project_dir)} has no unresolved placeholders")

    total = len(report["passed"]) + len(report["failed"]) + len(report["warnings"])
    if total:
        report["score"] = int((len(report["passed"]) / total) * 100)

    return report


def print_compliance_report(report: dict) -> None:
    print("\n" + "=" * 60)
    print("  TEMPLATE COMPLIANCE REPORT")
    print("=" * 60)

    if report["passed"]:
        print(f"\n✅ PASSED ({len(report['passed'])}):")
        for line in report["passed"]:
            print(f"   • {line}")

    if report["warnings"]:
        print(f"\n⚠️  WARNINGS ({len(report['warnings'])}):")
        for line in report["warnings"]:
            print(f"   • {line}")

    if report["failed"]:
        print(f"\n❌ FAILED ({len(report['failed'])}):")
        for line in report["failed"]:
            print(f"   • {line}")

    grade = "A" if report["score"] >= 90 else "B" if report["score"] >= 75 else "C" if report["score"] >= 60 else "F"
    print("\n" + "=" * 60)
    print(f"  COMPLIANCE SCORE: {report['score']}/100 ({grade})")
    print("=" * 60 + "\n")


def main() -> None:
    import argparse
    import sys

    parser = argparse.ArgumentParser(
        description="Check template compliance and visual quality readiness for a submittal project."
    )
    parser.add_argument("--project", required=True, help="Project folder name")
    args = parser.parse_args()

    report = compliance_check(args.project)
    print_compliance_report(report)
    sys.exit(0 if not report["failed"] else 1)


if __name__ == "__main__":
    main()
