#!/usr/bin/env python3
"""
Separator Generator Agent
=========================
Reads manifest.csv and the separator-sheet template, then generates separator.md
files for any item folder that doesn't already have one.

Usage:
    python -m agents.separator_agent --project "Double-RR"
    python -m agents.separator_agent --project "Double-RR" --force   # overwrite existing
"""

import csv
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent.parent
SUBMITTALS_DIR = BASE_DIR / "submittals"
TEMPLATES_DIR = BASE_DIR / "templates"

# Section mapping: define which items belong to which section header
# This is driven by spec_section ranges — customize per project if needed
SECTION_MAP = {
    "22 05 23": {"A": "Pressure Regulation", "C": "Valves", "D": "Metering & Instrumentation",
                 "F": "Domestic Hot Water", "G": "Drainage & Specialties"},
    "22 05 29": {"B": "Backflow Prevention"},
    "22 05 19": {"D": "Metering & Instrumentation"},
    "22 07 19": {"H": "Safety & Insulation"},
    "22 11 19": {"E": "Pumps"},
    "22 11 23": {"E": "Pumps"},
    "22 34 00": {"F": "Domestic Hot Water"},
    "22 40 00": {"G": "Drainage & Specialties"},
    "22 42 00": {"H": "Safety & Insulation"},
}

# Direct item-to-section mapping (more reliable than spec-section guessing)
DEFAULT_SECTIONS = {
    1: ("A", "Pressure Regulation"),
    2: ("A", "Pressure Regulation"),
    3: ("B", "Backflow Prevention"),
    4: ("B", "Backflow Prevention"),
    5: ("C", "Valves"),
    6: ("C", "Valves"),
    7: ("C", "Valves"),
    8: ("C", "Valves"),
    9: ("D", "Metering & Instrumentation"),
    10: ("D", "Metering & Instrumentation"),
    11: ("E", "Pumps"),
    12: ("E", "Pumps"),
    13: ("F", "Domestic Hot Water"),
    14: ("F", "Domestic Hot Water"),
    15: ("F", "Domestic Hot Water"),
    16: ("F", "Domestic Hot Water"),
    17: ("G", "Drainage & Specialties"),
    18: ("G", "Drainage & Specialties"),
    19: ("H", "Safety & Insulation"),
    20: ("H", "Safety & Insulation"),
}


def load_manifest(project_dir: Path) -> list[dict]:
    manifest_path = project_dir / "manifest.csv"
    if not manifest_path.exists():
        print(f"  ❌ Manifest not found: {manifest_path}")
        return []
    with open(manifest_path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def determine_certs(row: dict) -> list[str]:
    """Determine which certification checkboxes should be checked."""
    certs = []
    if row.get("cut_sheet_path"):
        certs.append("Product Data / Cut Sheet")
    if row.get("cert_nsf61_path"):
        certs.append("NSF 61 Certification")
    if row.get("cert_nsf372_path"):
        certs.append("NSF 372 (Lead-Free) Certification")

    other = row.get("other_certs", "")
    if other:
        for cert_path in other.split(","):
            cert_path = cert_path.strip().upper()
            if "UL" in cert_path:
                certs.append("UL / cUL Listing")
            elif "ASSE" in cert_path:
                certs.append("ASSE Certification")
            elif "AHRI" in cert_path:
                certs.append("AHRI Certification")
    return certs


def generate_separator(row: dict, project_name: str, submittal_number: str = "WW-2024-001") -> str:
    """Generate separator sheet markdown content for an item."""
    item_num = int(row["item_number"])
    padded = str(item_num).zfill(2)
    section_letter, section_name = DEFAULT_SECTIONS.get(item_num, ("?", "General"))
    desc = row.get("description", "")
    mfr = row.get("manufacturer", "")
    model = row.get("model_number", "")
    spec = row.get("spec_section", "")
    notes = row.get("notes", "")

    certs = determine_certs(row)

    # Build checkbox list
    all_checkboxes = [
        ("Product Data / Cut Sheet", "Product Data / Cut Sheet"),
        ("NSF 61 Certification", "NSF 61 Certification"),
        ("NSF 372 (Lead-Free) Certification", "NSF 372 (Lead-Free) Certification"),
        ("UL / cUL Listing", "UL / cUL Listing"),
        ("ASSE Certification", "ASSE Certification"),
        ("AHRI Certification", "AHRI Certification"),
        ("Referenced Specification Pages", "Referenced Specification Pages"),
    ]

    checkbox_lines = []
    for label, match_key in all_checkboxes:
        checked = "☒" if match_key in certs else "☐"
        checkbox_lines.append(f"│   {checked} {label:<58}│")

    checkboxes = "\n".join(checkbox_lines)

    content = f"""# ITEM SEPARATOR SHEET
## Section {section_letter} — {section_name}

---

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                                                                             │
│                           WINWATER                                          │
│                        PROJECT SUBMITTAL                                    │
│                                                                             │
│                     ┌───────────────────────┐                              │
│                     │                       │                              │
│                     │    ITEM  {padded:<13}│                              │
│                     │                       │                              │
│                     └───────────────────────┘                              │
│                                                                             │
│   {desc:<68}│
│                                                                             │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│   Manufacturer:    {mfr:<52}│
│   Model / Part #:  {model:<52}│
│   Spec Section:    {spec:<52}│
│                                                                             │
│   Application:     {notes:<52}│
│                                                                             │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│   Included in this section:                                                 │
{checkboxes}
│   ☐ Other: _______________                                                  │
│                                                                             │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│   Project: {project_name:<20}  Submittal #: {submittal_number:<20}│
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```
"""
    return content


def run(project: str, force: bool = False) -> dict:
    """
    Generate separator sheets for all items in the manifest.

    Returns dict with keys: created (int), skipped (int), errors (list[str])
    """
    project_dir = SUBMITTALS_DIR / project
    items_dir = project_dir / "03-items"
    result = {"created": 0, "skipped": 0, "errors": []}

    rows = load_manifest(project_dir)
    if not rows:
        result["errors"].append("No items in manifest")
        return result

    for row in rows:
        item_num = row.get("item_number", "").zfill(2)
        item_folder = items_dir / f"Item-{item_num}"
        sep_path = item_folder / "separator.md"

        if sep_path.exists() and not force:
            result["skipped"] += 1
            continue

        item_folder.mkdir(parents=True, exist_ok=True)
        content = generate_separator(row, project)
        sep_path.write_text(content, encoding="utf-8")
        result["created"] += 1
        print(f"  ✅ Generated separator for Item-{item_num}")

    return result


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Generate separator sheets from manifest.")
    parser.add_argument("--project", required=True, help="Project folder name")
    parser.add_argument("--force", action="store_true", help="Overwrite existing separators")
    args = parser.parse_args()

    print(f"\n{'=' * 60}")
    print(f"  Separator Generator Agent")
    print(f"  Project: {args.project}")
    print(f"{'=' * 60}\n")

    result = run(args.project, args.force)
    print(f"\n  Created: {result['created']}  Skipped: {result['skipped']}")
    if result["errors"]:
        for e in result["errors"]:
            print(f"  ❌ {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
