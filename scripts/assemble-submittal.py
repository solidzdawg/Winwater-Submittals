#!/usr/bin/env python3
"""
Winwater Submittal Assembly Script
===================================
Assembles a complete submittal package PDF from individual section PDFs.
Adds bookmarks per item for easy navigation in the final PDF.

Usage:
    python assemble-submittal.py --project "Double-RR"
    python assemble-submittal.py --project "Double-RR" --output "DoubleRR_SUB_001_Rev0.pdf"
    python assemble-submittal.py --project "Double-RR" --manifest manifest.csv

Requirements:
    pip install pypdf

Directory Structure Expected:
    submittals/<project>/
        manifest.csv           <- item manifest (drives assembly order)
        01-cover/              <- cover sheet PDF(s)
        02-index/              <- item index PDF(s)
        03-items/              <- subfolders per item (Item-01, Item-02, ...)
            Item-01/           <- separator + cut sheet + certs + spec pages
            Item-02/
            ...
        04-attachments/        <- disclaimer, LEED, etc.
"""

import argparse
import csv
import os
import sys
from pathlib import Path

try:
    from pypdf import PdfWriter, PdfReader
except ImportError:
    print("ERROR: pypdf is not installed. Run: pip install pypdf")
    sys.exit(1)


BASE_DIR = Path(__file__).resolve().parent.parent
SUBMITTALS_DIR = BASE_DIR / "submittals"


def find_pdfs_in_dir(directory: Path) -> list[Path]:
    """Return all PDF files in a directory, sorted by filename."""
    if not directory.exists():
        return []
    return sorted(directory.glob("*.pdf"))


def collect_item_dirs(items_dir: Path) -> list[Path]:
    """Return item subdirectories sorted by name (Item-01, Item-02, ...)."""
    if not items_dir.exists():
        return []
    return sorted(
        [d for d in items_dir.iterdir() if d.is_dir()],
        key=lambda d: d.name
    )


def load_manifest(project_dir: Path) -> list[dict]:
    """Load manifest.csv and return list of item dicts."""
    manifest_path = project_dir / "manifest.csv"
    if not manifest_path.exists():
        return []
    with open(manifest_path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def assemble_submittal(project: str, output_name: str | None = None) -> Path:
    """
    Assemble all PDFs in the correct submittal order into a single output PDF.
    Adds PDF bookmarks for each major section and each item for easy navigation.

    Order:
      1. 01-cover/   (cover sheet)
      2. 02-index/   (item index)
      3. 03-items/Item-XX/  (per-item: separator, cut sheet, certs, spec pages)
      4. 04-attachments/    (disclaimer, appendices)

    Returns:
        Path to the assembled output PDF.
    """
    project_dir = SUBMITTALS_DIR / project
    if not project_dir.exists():
        print(f"ERROR: Project directory not found: {project_dir}")
        sys.exit(1)

    # Load manifest for bookmark labels
    manifest_items = load_manifest(project_dir)
    item_labels = {}
    for row in manifest_items:
        num = row.get("item_number", "").zfill(2)
        desc = row.get("description", f"Item {num}")
        mfr = row.get("manufacturer", "")
        label = f"Item {num} — {desc}"
        if mfr:
            label += f" ({mfr})"
        item_labels[f"Item-{num}"] = label

    sections = [
        project_dir / "01-cover",
        project_dir / "02-index",
    ]

    writer = PdfWriter()
    total_pages = 0
    assembly_log = []

    # --- Cover and Index ---
    section_names = ["Cover Sheet", "Item Index"]
    for section_dir, section_name in zip(sections, section_names):
        pdfs = find_pdfs_in_dir(section_dir)
        if not pdfs:
            print(f"  ⚠️  No PDFs found in {section_dir.name}/ — section skipped")
            assembly_log.append(f"MISSING: {section_dir.name}/")
            continue
        for i, pdf_path in enumerate(pdfs):
            reader = PdfReader(str(pdf_path))
            page_count = len(reader.pages)

            # Only add the bookmark for the first PDF in the section
            outline = section_name if i == 0 else None
            writer.append(reader, outline_item=outline, import_outline=False)

            total_pages += page_count
            print(f"  ✅ Added {pdf_path.name} ({page_count} pages)")
            assembly_log.append(f"OK: {pdf_path.relative_to(project_dir)}")

    # --- Per-item sections ---
    items_dir = project_dir / "03-items"
    item_dirs = collect_item_dirs(items_dir)
    if not item_dirs:
        print(f"  ⚠️  No item folders found in 03-items/ — items section skipped")
        assembly_log.append("MISSING: 03-items/ (no item subfolders)")
    else:
        items_parent = writer.add_outline_item("Item Sections", total_pages)
        for item_dir in item_dirs:
            pdfs = find_pdfs_in_dir(item_dir)
            if not pdfs:
                print(f"  ⚠️  No PDFs in {item_dir.name}/ — item skipped")
                assembly_log.append(f"MISSING: 03-items/{item_dir.name}/")
                continue
            label = item_labels.get(item_dir.name, item_dir.name)
            for i, pdf_path in enumerate(pdfs):
                reader = PdfReader(str(pdf_path))
                page_count = len(reader.pages)

                # We need to manually add the outline item so it can be a child
                if i == 0:
                    bookmark_page = total_pages

                writer.append(reader, import_outline=False)
                total_pages += page_count
                print(f"  ✅ Added {item_dir.name}/{pdf_path.name} ({page_count} pages)")
                assembly_log.append(f"OK: {pdf_path.relative_to(project_dir)}")

            writer.add_outline_item(label, bookmark_page, parent=items_parent)

    # --- Attachments ---
    attachments_dir = project_dir / "04-attachments"
    attachment_pdfs = find_pdfs_in_dir(attachments_dir)
    if not attachment_pdfs:
        print(f"  ⚠️  No PDFs found in 04-attachments/ — attachments skipped")
        assembly_log.append("MISSING: 04-attachments/")
    else:
        for i, pdf_path in enumerate(attachment_pdfs):
            reader = PdfReader(str(pdf_path))
            page_count = len(reader.pages)

            outline = "Attachments" if i == 0 else None
            writer.append(reader, outline_item=outline, import_outline=False)

            total_pages += page_count
            print(f"  ✅ Added {pdf_path.name} ({page_count} pages)")
            assembly_log.append(f"OK: {pdf_path.relative_to(project_dir)}")

    # --- Write output ---
    if output_name is None:
        safe_project = project.replace(" ", "-")
        output_name = f"{safe_project}_SUB_001_Rev0_PlumbingEquipment.pdf"
    output_path = project_dir / output_name
    with open(output_path, "wb") as f:
        writer.write(f)

    print(f"\n✅ Assembly complete: {output_path}")
    print(f"   Total pages: {total_pages}")

    # Write assembly log
    log_path = project_dir / "assembly-log.txt"
    with open(log_path, "w") as f:
        f.write(f"Winwater Submittal Assembly Log\n")
        f.write(f"Project: {project}\n")
        f.write(f"Output:  {output_name}\n")
        f.write(f"Pages:   {total_pages}\n\n")
        for line in assembly_log:
            f.write(line + "\n")
    print(f"   Assembly log: {log_path}")

    return output_path


def validate_project_structure(project: str) -> bool:
    """
    Check that all expected directories exist and report missing items.
    Returns True if ready to assemble, False if there are blockers.
    """
    project_dir = SUBMITTALS_DIR / project
    required_dirs = [
        "01-cover",
        "02-index",
        "03-items",
        "04-attachments",
    ]
    all_ok = True
    print(f"\nValidating project structure for: {project}")
    print(f"  Location: {project_dir}\n")

    for d in required_dirs:
        dir_path = project_dir / d
        exists = dir_path.exists()
        pdf_count = len(find_pdfs_in_dir(dir_path)) if exists else 0
        if d == "03-items":
            item_dirs = collect_item_dirs(dir_path) if exists else []
            status = f"{'✅' if exists else '❌'} {d}/  ({len(item_dirs)} item folders)"
        else:
            status = f"{'✅' if exists and pdf_count > 0 else '⚠️'} {d}/  ({pdf_count} PDF files)"
        print(f"  {status}")
        if not exists or (d != "03-items" and pdf_count == 0):
            all_ok = False

    if all_ok:
        print("\n✅ Project structure looks good — ready to assemble.")
    else:
        print("\n⚠️  Some sections are missing PDFs. "
              "Populate from the submittal task folder and Z: drive before assembling.")
    return all_ok


def main():
    parser = argparse.ArgumentParser(
        description="Assemble a Winwater submittal package PDF."
    )
    parser.add_argument(
        "--project",
        required=True,
        help='Project folder name under submittals/ (e.g., "Double-RR")',
    )
    parser.add_argument(
        "--output",
        default=None,
        help="Output PDF filename (default: auto-generated from project name)",
    )
    parser.add_argument(
        "--manifest",
        default=None,
        help="Manifest CSV filename (default: manifest.csv in project dir). "
             "Used for bookmark labels.",
    )
    parser.add_argument(
        "--validate-only",
        action="store_true",
        help="Only validate project structure, do not assemble",
    )
    args = parser.parse_args()

    print(f"\n{'='*60}")
    print(f"  Winwater Submittal Assembly Tool")
    print(f"  Project: {args.project}")
    print(f"{'='*60}\n")

    ready = validate_project_structure(args.project)

    if args.validate_only:
        sys.exit(0 if ready else 1)

    if not ready:
        print("\n⚠️  Proceeding with assembly despite missing sections...")

    print("\nAssembling submittal package...")
    assemble_submittal(args.project, args.output)


if __name__ == "__main__":
    main()
