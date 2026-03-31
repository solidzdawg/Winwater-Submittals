#!/usr/bin/env python3
"""
build-submittal-sets.py
=======================
Generates 11 individual submittal-set PDFs for a project.

Each set contains:
  1. Cover page      (from submittal cover.xlsx, filled via openpyxl)
  2. Item index page  (from Item Index Template.docx, filled via python-docx)
  3. Per-item:  separator page (Seperator Sheet Template.docx) + vendor cut-sheet PDF

All Office-to-PDF conversion uses LibreOffice headless.
Final assembly uses pypdf with bookmarks.

Usage:
    python build-submittal-sets.py --project Double-RR
    python build-submittal-sets.py --project Double-RR --inspect

Requirements:
    System:  libreoffice
    Python:  pip install pypdf openpyxl python-docx
"""

import argparse
import csv
import copy
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

try:
    from pypdf import PdfWriter, PdfReader
except ImportError:
    sys.exit("ERROR: pypdf not installed.  pip install pypdf")

try:
    import openpyxl
except ImportError:
    sys.exit("ERROR: openpyxl not installed.  pip install openpyxl")

try:
    from docx import Document
    from docx.shared import Pt, RGBColor
    from docx.enum.text import WD_ALIGN_PARAGRAPH
except ImportError:
    sys.exit("ERROR: python-docx not installed.  pip install python-docx")

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
BASE_DIR = Path(__file__).resolve().parent.parent
TEMPLATES_DIR = BASE_DIR / "templates"
SUBMITTALS_DIR = BASE_DIR / "submittals"

# ---------------------------------------------------------------------------
# Project-specific info  (edit per job)
# ---------------------------------------------------------------------------
PROJECT_INFO = {
    "project_name": "Double RR Ranch \u2014 East Cabins",
    "project_number": "DRLR-2026-001",
    "submittal_prefix": "WW",
    "revision": "0",
    "date": "03/31/2026",
    "to_name": "",
    "to_company": "",
    "to_address": "",
    "submitted_by": "Grand Junction Winwater Company",
}

# ---------------------------------------------------------------------------
# The 11 submittal sets  (item numbers reference manifest.csv)
# ---------------------------------------------------------------------------
SUBMITTAL_SETS = [
    {"id": "01", "name": "Pressure Reducing Valves",  "items": [1, 2],           "spec": "22 05 23"},
    {"id": "02", "name": "Backflow Prevention",       "items": [3, 4],           "spec": "22 05 29"},
    {"id": "03", "name": "Ball Valves",               "items": [5, 6],           "spec": "22 05 23"},
    {"id": "04", "name": "Butterfly Valve",            "items": [7],              "spec": "22 05 23"},
    {"id": "05", "name": "Check Valve",                "items": [8],              "spec": "22 05 23"},
    {"id": "06", "name": "Water Meter",                "items": [9],              "spec": "22 05 19"},
    {"id": "07", "name": "Pressure Gauge",             "items": [10],             "spec": "22 05 23"},
    {"id": "08", "name": "Pumps",                      "items": [11, 12],         "spec": "22 11 19"},
    {"id": "09", "name": "Domestic Hot Water",         "items": [13, 14, 15, 16], "spec": "22 34 00"},
    {"id": "10", "name": "Drainage & Specialties",     "items": [17, 18],         "spec": "22 40 00"},
    {"id": "11", "name": "Safety & Insulation",        "items": [19, 20],         "spec": "22 42 00"},
]


# ===================================================================
# Helpers
# ===================================================================

def load_manifest(project_dir: Path) -> dict[int, dict]:
    """Return manifest keyed by item_number (int)."""
    path = project_dir / "manifest.csv"
    with open(path, newline="", encoding="utf-8") as f:
        return {int(row["item_number"]): row for row in csv.DictReader(f)}


def count_pdf_pages(pdf_path: Path) -> int:
    try:
        return len(PdfReader(str(pdf_path)).pages)
    except Exception:
        return 0


def lo_convert(input_path: Path, output_dir: Path) -> Path | None:
    """Convert an Office file to PDF via LibreOffice headless."""
    env = os.environ.copy()
    env["HOME"] = str(output_dir)          # avoid profile lock issues in CI
    cmd = [
        "libreoffice", "--headless", "--norestore",
        "--convert-to", "pdf",
        "--outdir", str(output_dir),
        str(input_path),
    ]
    result = subprocess.run(cmd, capture_output=True, text=True,
                            timeout=180, env=env)
    if result.returncode != 0:
        print(f"  \u26a0\ufe0f  LO convert failed: {input_path.name}")
        print(f"      stderr: {result.stderr[:600]}")
        return None
    pdf_path = output_dir / (input_path.stem + ".pdf")
    return pdf_path if pdf_path.exists() else None


# ===================================================================
# Template inspection  (--inspect mode)
# ===================================================================

def inspect_xlsx(path: Path):
    wb = openpyxl.load_workbook(path, data_only=True)
    for name in wb.sheetnames:
        ws = wb[name]
        print(f"\n  Sheet '{name}'  ({ws.max_row} rows x {ws.max_column} cols)")
        for row in ws.iter_rows(min_row=1, max_row=ws.max_row,
                                max_col=ws.max_column):
            for cell in row:
                if cell.value is not None:
                    print(f"    {cell.coordinate}: {repr(cell.value)}")


def inspect_docx(path: Path):
    doc = Document(path)
    print(f"\n  Paragraphs: {len(doc.paragraphs)}")
    for i, p in enumerate(doc.paragraphs):
        if p.text.strip():
            align = p.alignment
            print(f"    P{i}: align={align}  {repr(p.text[:120])}")
    print(f"  Tables: {len(doc.tables)}")
    for i, tbl in enumerate(doc.tables):
        print(f"    Table {i}: {len(tbl.rows)} rows x {len(tbl.columns)} cols")
        for j, row in enumerate(tbl.rows[:6]):
            cells_txt = [c.text[:40] for c in row.cells]
            print(f"      Row {j}: {cells_txt}")


# ===================================================================
# Template fill functions
# ===================================================================

def fill_cover(template_path: Path, output_path: Path,
               set_info: dict, project_info: dict) -> Path:
    """Copy the XLSX cover template and fill project / set fields."""
    wb = openpyxl.load_workbook(template_path)
    ws = wb.active

    submittal_num = f"{project_info['submittal_prefix']}-{set_info['id']}"
    set_label = f"Submittal {set_info['id']} \u2014 {set_info['name']}"

    # Build a lookup: uppercase cell value -> (row, col)
    for row in ws.iter_rows(min_row=1, max_row=ws.max_row,
                            max_col=ws.max_column):
        for cell in row:
            val = str(cell.value or "").strip()
            up = val.upper()

            # Right-neighbour cell (the value cell)
            right = ws.cell(row=cell.row, column=cell.column + 1)
            below = ws.cell(row=cell.row + 1, column=cell.column)

            def _set(target, value):
                """Set a cell only if it looks empty or placeholder-ish."""
                tv = str(target.value or "").strip()
                if tv == "" or tv.startswith("{") or tv.startswith("<"):
                    target.value = value

            if "SUBMITTAL" in up and ("#" in up or "NO" in up or "NUM" in up):
                _set(right, submittal_num)
            elif up in ("DATE:", "DATE"):
                _set(right, project_info["date"])
            elif up.startswith("TO:") or up == "TO":
                _set(right, project_info.get("to_name", ""))
            elif "PROJECT" in up and ("#" in up or "NO" in up or "NUM" in up or "NAME" in up):
                _set(right, project_info["project_name"])
            elif up in ("RE:", "SUBJECT:", "DESCRIPTION:", "SUMMARY:"):
                _set(right, set_label)
            elif up in ("SUBMITTED BY:", "FROM:", "PREPARED BY:"):
                _set(right, project_info["submitted_by"])
            elif up in ("REVISION:", "REV:", "REV"):
                _set(right, project_info["revision"])
            elif up in ("SPEC SECTION:", "SPECIFICATION:", "SPEC:"):
                _set(right, set_info["spec"])
            # Also try filling cells that contain placeholder markers
            if "{{" in val:
                for key, replacement in {
                    "{{SUBMITTAL_NUM}}": submittal_num,
                    "{{DATE}}": project_info["date"],
                    "{{PROJECT_NAME}}": project_info["project_name"],
                    "{{PROJECT_NUMBER}}": project_info["project_number"],
                    "{{SET_NAME}}": set_info["name"],
                    "{{SPEC}}": set_info["spec"],
                    "{{SUBMITTED_BY}}": project_info["submitted_by"],
                    "{{REVISION}}": project_info["revision"],
                }.items():
                    if key in val:
                        cell.value = val.replace(key, replacement)
                        val = str(cell.value)

    wb.save(output_path)
    return output_path


def fill_separator(template_path: Path, output_path: Path,
                   label_text: str) -> Path:
    """Copy separator DOCX and replace the placeholder text with *label_text*."""
    doc = Document(template_path)
    replaced = False

    for para in doc.paragraphs:
        txt = para.text.strip()
        if not txt:
            continue
        # Replace the first non-empty paragraph (the placeholder)
        if para.runs:
            para.runs[0].text = label_text
            for run in para.runs[1:]:
                run.text = ""
        else:
            para.text = label_text
        replaced = True
        break

    if not replaced:
        p = doc.add_paragraph(label_text)
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER

    doc.save(output_path)
    return output_path


def fill_index(template_path: Path, output_path: Path,
               set_info: dict, item_list: list[dict],
               page_counts: dict[int, int]) -> Path:
    """Copy the item-index DOCX and populate the table with items."""
    doc = Document(template_path)

    # --- Try to fill header/paragraph placeholders -------------------------
    for para in doc.paragraphs:
        for run in para.runs:
            for tag, repl in {
                "{{SET_NAME}}": set_info["name"],
                "{{SPEC}}": set_info["spec"],
                "{{DATE}}": PROJECT_INFO["date"],
                "{{PROJECT_NAME}}": PROJECT_INFO["project_name"],
            }.items():
                if tag in run.text:
                    run.text = run.text.replace(tag, repl)

    # --- Fill the first table found ----------------------------------------
    if doc.tables:
        tbl = doc.tables[0]
        # Keep header row(s): assume first row is header
        header_count = 1
        while len(tbl.rows) > header_count:
            tr = tbl.rows[-1]._tr
            tbl._tbl.remove(tr)

        for item in item_list:
            item_num = int(item["item_number"])
            desc = item.get("description", "")
            mfr  = item.get("manufacturer", "")
            pages = page_counts.get(item_num, "\u2014")
            row = tbl.add_row()
            row.cells[0].text = desc
            if len(row.cells) > 1:
                row.cells[1].text = mfr
            if len(row.cells) > 2:
                row.cells[2].text = str(pages)
    else:
        # No table found \u2014 append a simple list
        doc.add_paragraph("")
        doc.add_paragraph(f"Submittal Set {set_info['id']} \u2014 {set_info['name']}")
        for item in item_list:
            item_num = int(item["item_number"])
            desc = item.get("description", "")
            mfr  = item.get("manufacturer", "")
            pages = page_counts.get(item_num, "\u2014")
            doc.add_paragraph(f"{desc}  |  {mfr}  |  {pages} pages")

    doc.save(output_path)
    return output_path


# ===================================================================
# Build one submittal set
# ===================================================================

def build_set(set_info: dict, manifest: dict[int, dict],
              project_dir: Path, output_dir: Path,
              work_dir: Path) -> Path | None:
    sid  = set_info["id"]
    name = set_info["name"]
    items = set_info["items"]

    print(f"\n{'\u2500'*60}")
    print(f"  SET {sid}: {name}")
    print(f"  Items: {items}")
    print(f"{'\u2500'*60}")

    # Collect (label, pdf_path) pairs in assembly order
    parts: list[tuple[str, Path]] = []

    # \u2500\u2500 1. Cover page \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500
    cover_tmpl = TEMPLATES_DIR / "submittal cover.xlsx"
    if cover_tmpl.exists():
        cover_out = work_dir / f"cover_{sid}.xlsx"
        fill_cover(cover_tmpl, cover_out, set_info, PROJECT_INFO)
        pdf = lo_convert(cover_out, work_dir)
        if pdf:
            parts.append(("Cover Sheet", pdf))
            print(f"  \u2705 Cover page")
        else:
            print(f"  \u26a0\ufe0f  Cover page conversion failed")
    else:
        print(f"  \u26a0\ufe0f  Cover template not found")

    # \u2500\u2500 2. Item Index \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500
    page_counts: dict[int, int] = {}
    for inum in items:
        row = manifest.get(inum, {})
        cp = row.get("cut_sheet_path", "").strip()
        if cp:
            p = BASE_DIR / cp
            if p.exists():
                page_counts[inum] = count_pdf_pages(p)

    index_tmpl = TEMPLATES_DIR / "Item Index Template.docx"
    if index_tmpl.exists():
        item_rows = [manifest[i] for i in items if i in manifest]
        index_out = work_dir / f"index_{sid}.docx"
        fill_index(index_tmpl, index_out, set_info, item_rows, page_counts)
        pdf = lo_convert(index_out, work_dir)
        if pdf:
            parts.append(("Item Index", pdf))
            print(f"  \u2705 Item index")
        else:
            print(f"  \u26a0\ufe0f  Item index conversion failed")
    else:
        print(f"  \u26a0\ufe0f  Item Index template not found")

    # \u2500\u2500 3. Per-item: separator + cut sheet \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500
    sep_tmpl = TEMPLATES_DIR / "Seperator Sheet Template.docx"

    for inum in items:
        row = manifest.get(inum, {})
        desc  = row.get("description", f"Item {inum}")
        mfr   = row.get("manufacturer", "")
        model = row.get("model_number", "")

        sep_label = desc
        if mfr:
            sep_label += f"\n{mfr}"
        if model:
            sep_label += f" {model}"

        # Separator page
        if sep_tmpl.exists():
            sep_out = work_dir / f"sep_{sid}_{inum:02d}.docx"
            fill_separator(sep_tmpl, sep_out, sep_label)
            pdf = lo_convert(sep_out, work_dir)
            if pdf:
                parts.append((f"Item {inum:02d} \u2014 {desc}", pdf))
                print(f"  \u2705 Separator: Item {inum:02d}")
            else:
                print(f"  \u26a0\ufe0f  Separator conversion failed: Item {inum:02d}")

        # Cut sheet
        cp = row.get("cut_sheet_path", "").strip()
        if cp:
            full = BASE_DIR / cp
            if full.exists():
                parts.append((f"Cut Sheet \u2014 {desc}", full))
                print(f"  \u2705 Cut sheet: Item {inum:02d} ({full.name})")
            else:
                print(f"  \u26a0\ufe0f  Cut sheet NOT FOUND: {cp}")

    # \u2500\u2500 4. Assemble \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500
    if not parts:
        print(f"  \u274c No PDFs to merge for SET {sid}")
        return None

    writer = PdfWriter()
    total = 0
    for label, pdf_path in parts:
        try:
            reader = PdfReader(str(pdf_path))
            bm_page = total
            for page in reader.pages:
                writer.add_page(page)
                total += 1
            writer.add_outline_item(label, bm_page)
        except Exception as exc:
            print(f"  \u26a0\ufe0f  Error merging {pdf_path.name}: {exc}")

    safe = name.replace(" ", "-").replace("&", "and")
    fname = f"Double-RR_SUB-{sid}_{safe}.pdf"
    out = output_dir / fname
    with open(out, "wb") as f:
        writer.write(f)

    print(f"\n  \ud83d\udcc4 {fname} \u2014 {total} pages")
    return out


# ===================================================================
# Main
# ===================================================================

def main():
    parser = argparse.ArgumentParser(description="Build 11 submittal-set PDFs")
    parser.add_argument("--project", required=True)
    parser.add_argument("--inspect", action="store_true",
                        help="Print template structure and exit")
    args = parser.parse_args()

    project_dir = SUBMITTALS_DIR / args.project
    if not project_dir.exists():
        sys.exit(f"ERROR: project folder not found: {project_dir}")

    # \u2500\u2500 Inspect mode \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500
    if args.inspect:
        print("\n=== TEMPLATE INSPECTION ===")
        for path in sorted(TEMPLATES_DIR.iterdir()):
            if path.suffix == ".xlsx":
                print(f"\n\u25b6 {path.name}")
                inspect_xlsx(path)
            elif path.suffix == ".docx":
                print(f"\n\u25b6 {path.name}")
                inspect_docx(path)
        return

    # \u2500\u2500 Build mode \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500
    print(f"\n{'='*60}")
    print(f"  Building 11 Submittal Sets: {args.project}")
    print(f"{'='*60}")

    manifest = load_manifest(project_dir)
    print(f"\n  Manifest: {len(manifest)} items loaded")

    # Output directory
    output_dir = project_dir / "sets"
    output_dir.mkdir(parents=True, exist_ok=True)

    # Temp working directory
    work_dir = Path(tempfile.mkdtemp(prefix="winwater_"))
    print(f"  Work dir: {work_dir}")

    # Log template structure for debugging
    print("\n\u25b6 Template inspection (for build log):")
    for path in sorted(TEMPLATES_DIR.iterdir()):
        if path.suffix == ".xlsx":
            print(f"\n  {path.name}:")
            inspect_xlsx(path)
        elif path.suffix == ".docx" and "Template" in path.name:
            print(f"\n  {path.name}:")
            inspect_docx(path)

    # Build each set
    results = []
    for si in SUBMITTAL_SETS:
        res = build_set(si, manifest, project_dir, output_dir, work_dir)
        results.append((si, res))

    # Summary
    print(f"\n{'='*60}")
    print(f"  BUILD SUMMARY")
    print(f"{'='*60}")
    ok = 0
    for si, res in results:
        status = "\u2705" if res else "\u274c"
        size = ""
        if res and res.exists():
            mb = res.stat().st_size / 1_048_576
            size = f"  ({mb:.1f} MB)"
        print(f"  {status} SET-{si['id']}: {si['name']}{size}")
        if res:
            ok += 1
    print(f"\n  {ok}/{len(SUBMITTAL_SETS)} sets built successfully")
    print(f"  Output directory: {output_dir}")

    # Cleanup temp dir
    shutil.rmtree(work_dir, ignore_errors=True)

    if ok < len(SUBMITTAL_SETS):
        sys.exit(1)


if __name__ == "__main__":
    main()
