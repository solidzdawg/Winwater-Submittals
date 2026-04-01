#!/usr/bin/env python3
"""
Vendor Fetch Agent
==================
Scans the manifest and checks whether each referenced vendor PDF exists in the
vendor-docs/ directory tree. Reports missing files and can optionally create
the expected folder structure.

Usage:
    python -m agents.vendor_fetch_agent --project "Double-RR"
    python -m agents.vendor_fetch_agent --project "Double-RR" --create-dirs
"""

import csv
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent.parent
SUBMITTALS_DIR = BASE_DIR / "submittals"
VENDOR_DOCS_DIR = BASE_DIR / "vendor-docs"


def load_manifest(project_dir: Path) -> list[dict]:
    manifest_path = project_dir / "manifest.csv"
    if not manifest_path.exists():
        return []
    with open(manifest_path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def check_vendor_files(project: str, create_dirs: bool = False) -> dict:
    """
    Check all vendor file references in the manifest.

    Returns dict:
        found (list), missing (list), manufacturers (set),
        dirs_created (int)
    """
    project_dir = SUBMITTALS_DIR / project
    result = {
        "found": [],
        "missing": [],
        "manufacturers": set(),
        "dirs_created": 0,
    }

    if not project_dir.resolve().is_relative_to(SUBMITTALS_DIR.resolve()):
        print(f"ERROR: Invalid project path: {project}")
        return result

    rows = load_manifest(project_dir)

    if not rows:
        return result

    file_fields = ["cut_sheet_path", "cert_nsf61_path", "cert_nsf372_path", "other_certs", "spec_pages_path"]

    for row in rows:
        item_num = row.get("item_number", "?").zfill(2)
        mfr = row.get("manufacturer", "Unknown")
        result["manufacturers"].add(mfr)

        for field in file_fields:
            paths_str = row.get(field, "")
            if not paths_str:
                continue
            for single_path in paths_str.split(","):
                single_path = single_path.strip()
                if not single_path:
                    continue
                full_path = BASE_DIR / single_path
                if full_path.exists():
                    result["found"].append((item_num, field, single_path))
                else:
                    result["missing"].append((item_num, field, single_path))
                    if create_dirs:
                        full_path.parent.mkdir(parents=True, exist_ok=True)
                        result["dirs_created"] += 1

    return result


def print_vendor_report(result: dict) -> None:
    print("\n" + "=" * 60)
    print("  VENDOR FILE AUDIT")
    print("=" * 60)

    print(f"\n  Manufacturers referenced: {', '.join(sorted(result['manufacturers']))}")
    print(f"  Files found:   {len(result['found'])}")
    print(f"  Files missing: {len(result['missing'])}")

    if result["missing"]:
        print(f"\n  MISSING FILES:")
        print(f"  {'Item':<6} {'Field':<20} Path")
        print(f"  {'─'*6} {'─'*20} {'─'*40}")
        for item, field, path in result["missing"]:
            short_field = field.replace("_path", "").replace("cert_", "")
            print(f"  {item:<6} {short_field:<20} {path}")

    if result["dirs_created"]:
        print(f"\n  📁 Created {result['dirs_created']} missing directories")

    if not result["missing"]:
        print("\n  ✅ All vendor files present!")
    else:
        print(f"\n  ⚠️  {len(result['missing'])} vendor files need to be placed.")
        print("  Copy from Z:\\Vendor Parts\\ into the paths listed above.")

    print("=" * 60 + "\n")


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Audit vendor files for a submittal project.")
    parser.add_argument("--project", required=True, help="Project folder name")
    parser.add_argument("--create-dirs", action="store_true",
                        help="Create missing vendor-docs directories")
    args = parser.parse_args()

    print(f"\n{'=' * 60}")
    print(f"  Vendor Fetch Agent")
    print(f"  Project: {args.project}")
    print(f"{'=' * 60}")

    result = check_vendor_files(args.project, args.create_dirs)
    print_vendor_report(result)


if __name__ == "__main__":
    main()
