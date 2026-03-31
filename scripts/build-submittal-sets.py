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
import os
import shutil
import subprocess
import sys
import tempfile
import traceback
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

DIVIDER = "-" * 60

# ---------------------------------------------------------------------------
# Project-specific info  (edit per job)
# ---------------------------------------------------------------------------
PROJECT_INFO = {
    "project_name": "Double RR Ranch - East Cabins",
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

def load_manifest(project_dir):
    """Return manifest keyed by item_number (int)."""
    path = project_dir / "manifest.csv"
    with open(path, newline="", encoding="utf-8") as f:
        return {int(row["item_number"]): row for row in csv.DictReader(f)}


def count_pdf_pages(pdf_path):
    try:
        return len(PdfReader(str(pdf_path)).pages)
    except Exception:
        return 0


def find_libreoffice():
    """Return the LibreOffice binary name available on this system."""
    for name in ["libreoffice", "soffice", "/usr/bin/libreoffice", "/usr/bin/soffice"]:
        if shutil.which(name):
            return name
    return "libreoffice"  # fallback, will error if not found


LO_BIN = None  # resolved lazily


def lo_convert(input_path, output_dir):
    """Convert an Office file to PDF via LibreOffice headless."""
    global LO_BIN
    if LO_BIN is None:
        LO_BIN = find_libreoffice()
        print("  LibreOffice binary: " + LO_BIN)

    env = os.environ.copy()
    env["HOME"] = str(output_dir)
    cmd = [
        LO_BIN, "--headless", "--norestore",
        "--convert-to", "pdf",
        "--outdir", str(output_dir),
        str(input_path),
    ]
    print("  CMD: " + " ".join(cmd))
    result = subprocess.run(cmd, capture_output=True, text=True,
                            timeout=180, env=env)
    if result.returncode != 0:
        print("  WARNING: LO convert failed for: " + input_path.name)
        print("      stdout: " + result.stdout[:400])
        print("      stderr: " + result.stderr[:400])
        return None
    if result.stdout:
        print("      LO stdout: " + result.stdout[:200])
    pdf_path = output_dir / (input_path.stem + ".pdf")
    if pdf_path.exists():
        return pdf_path
    # Sometimes LO changes the name slightly; search for it
    candidates = list(output_dir.glob(input_path.stem + "*.pdf"))
    if candidates:
        return candidates[0]
    print("  WARNING: Expected PDF not found: " + str(pdf_path))
    # List what IS in the output dir
    print("      Files in output_dir: " + str(list(output_dir.glob("*.pdf"))))
    return None


# ===================================================================
# Template inspection  (--inspect mode)
# ===================================================================

def inspect_xlsx(path):
    wb = openpyxl.load_workbook(path, data_only=True)
    for name in wb.sheetnames:
        ws = wb[name]
        print("  Sheet '{}' ({} rows x {} cols)".format(name, ws.max_row, ws.max_column))
        for row in ws.iter_rows(min_row=1, max_row=ws.max_row,
                                max_col=ws.max_column):
            for cell in row:
                if cell.value is not None:
                    print("    {}: {}".format(cell.coordinate, repr(cell.value)))


def inspect_docx(path):
    doc = Document(path)
    print("  Paragraphs: {}".format(len(doc.paragraphs)))
    for i, p in enumerate(doc.paragraphs):
        if p.text.strip():
            print("    P{}: align={}  {}".format(i, p.alignment, repr(p.text[:120])))
    print("  Tables: {}".format(len(doc.tables)))
    for i, tbl in enumerate(doc.tables):
        print("    Table {}: {} rows x {} cols".format(i, len(tbl.rows), len(tbl.columns)))
        for j, row in enumerate(tbl.rows[:6]):
            cells_txt = [c.text[:40] for c in row.cells]
            print("      Row {}: {}".format(j, cells_txt))


# ===================================================================
# Template fill functions
# ===================================================================

def _set_cell_if_empty(target, value):
    """Set a cell only if it looks empty or placeholder-ish."""
    tv = str(target.value or "").strip()
    if tv == "" or tv.startswith("{") or tv.startswith("<"):
        target.value = value


def fill_cover(template_path, output_path, set_info, project_info):
    """Copy the XLSX cover template and fill project / set fields."""
    wb = openpyxl.load_workbook(template_path)
    ws = wb.active

    submittal_num = "{}-{}".format(project_info["submittal_prefix"], set_info["id"])
    set_label = "Submittal {} - {}".format(set_info["id"], set_info["name"])

    for row in ws.iter_rows(min_row=1, max_row=ws.max_row,
                            max_col=ws.max_column):
        for cell in row:
            val = str(cell.value or "").strip()
            up = val.upper()

            right = ws.cell(row=cell.row, column=cell.column + 1)

            if "SUBMITTAL" in up and ("#" in up or "NO" in up or "NUM" in up):
                _set_cell_if_empty(right, submittal_num)
            elif up in ("DATE:", "DATE"):
                _set_cell_if_empty(right, project_info["date"])
            elif up.startswith("TO:") or up == "TO":
                _set_cell_if_empty(right, project_info.get("to_name", ""))
            elif "PROJECT" in up and ("#" in up or "NO" in up or "NUM" in up or "NAME" in up):
                _set_cell_if_empty(right, project_info["project_name"])
            elif up in ("RE:", "SUBJECT:", "DESCRIPTION:", "SUMMARY:"):
                _set_cell_if_empty(right, set_label)
            elif up in ("SUBMITTED BY:", "FROM:", "PREPARED BY:"):
                _set_cell_if_empty(right, project_info["submitted_by"])
            elif up in ("REVISION:", "REV:", "REV"):
                _set_cell_if_empty(right, project_info["revision"])
            elif up in ("SPEC SECTION:", "SPECIFICATION:", "SPEC:"):
                _set_cell_if_empty(right, set_info["spec"])

            # Also try filling cells that contain placeholder markers
            if "{{" in val:
                replacements = {
                    "{{SUBMITTAL_NUM}}": submittal_num,
                    "{{DATE}}": project_info["date"],
                    "{{PROJECT_NAME}}": project_info["project_name"],
                    "{{PROJECT_NUMBER}}": project_info["project_number"],
                    "{{SET_NAME}}": set_info["name"],
                    "{{SPEC}}": set_info["spec"],
                    "{{SUBMITTED_BY}}": project_info["submitted_by"],
                    "{{REVISION}}": project_info["revision"],
                }
                for key, replacement in replacements.items():
                    if key in val:
                        cell.value = val.replace(key, replacement)
                        val = str(cell.value)

    wb.save(output_path)
    return output_path


def fill_separator(template_path, output_path, label_text):
    """Copy separator DOCX and replace the placeholder text with label_text."""
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


def fill_index(template_path, output_path, set_info, item_list, page_counts):
    """Copy the item-index DOCX and populate the table with items."""
    doc = Document(template_path)

    # --- Try to fill header/paragraph placeholders -------------------------
    for para in doc.paragraphs:
        for run in para.runs:
            replacements = {
                "{{SET_NAME}}": set_info["name"],
                "{{SPEC}}": set_info["spec"],
                "{{DATE}}": PROJECT_INFO["date"],
                "{{PROJECT_NAME}}": PROJECT_INFO["project_name"],
            }
            for tag, repl in replacements.items():
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
            mfr = item.get("manufacturer", "")
            pages = page_counts.get(item_num, "-")
            row = tbl.add_row()
            cells = row.cells
            cells[0].text = desc
            if len(cells) > 1:
                cells[1].text = mfr
            if len(cells) > 2:
                cells[2].text = str(pages)
    else:
        # No table found - append a simple list
        doc.add_paragraph("")
        doc.add_paragraph("Submittal Set {} - {}".format(set_info["id"], set_info["name"]))
        for item in item_list:
            item_num = int(item["item_number"])
            desc = item.get("description", "")
            mfr = item.get("manufacturer", "")
            pages = page_counts.get(item_num, "-")
            doc.add_paragraph("{}  |  {}  |  {} pages".format(desc, mfr, pages))

    doc.save(output_path)
    return output_path


# ===================================================================
# Build one submittal set
# ===================================================================

def build_set(set_info, manifest, project_dir, output_dir, work_dir):
    sid = set_info["id"]
    name = set_info["name"]
    items = set_info["items"]

    print("")
    print(DIVIDER)
    print("  SET {}: {}".format(sid, name))
    print("  Items: {}".format(items))
    print(DIVIDER)

    # Collect (label, pdf_path) pairs in assembly order
    parts = []

    # -- 1. Cover page -------------------------------------------------------
    cover_tmpl = TEMPLATES_DIR / "submittal cover.xlsx"
    if cover_tmpl.exists():
        cover_out = work_dir / "cover_{}.xlsx".format(sid)
        try:
            fill_cover(cover_tmpl, cover_out, set_info, PROJECT_INFO)
            pdf = lo_convert(cover_out, work_dir)
            if pdf:
                parts.append(("Cover Sheet", pdf))
                print("  OK: Cover page")
            else:
                print("  WARNING: Cover page conversion failed")
        except Exception as exc:
            print("  ERROR in cover: {}".format(exc))
            traceback.print_exc()
    else:
        print("  WARNING: Cover template not found: {}".format(cover_tmpl))

    # -- 2. Item Index -------------------------------------------------------
    page_counts = {}
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
        index_out = work_dir / "index_{}.docx".format(sid)
        try:
            fill_index(index_tmpl, index_out, set_info, item_rows, page_counts)
            pdf = lo_convert(index_out, work_dir)
            if pdf:
                parts.append(("Item Index", pdf))
                print("  OK: Item index")
            else:
                print("  WARNING: Item index conversion failed")
        except Exception as exc:
            print("  ERROR in index: {}".format(exc))
            traceback.print_exc()
    else:
        print("  WARNING: Item Index template not found: {}".format(index_tmpl))

    # -- 3. Per-item: separator + cut sheet ---------------------------------
    sep_tmpl = TEMPLATES_DIR / "Seperator Sheet Template.docx"
    if not sep_tmpl.exists():
        print("  WARNING: Separator template not found: {}".format(sep_tmpl))
        # Try alternate spelling
        alt = TEMPLATES_DIR / "Separator Sheet Template.docx"
        if alt.exists():
            sep_tmpl = alt
            print("  Found alternate: {}".format(alt.name))

    for inum in items:
        row = manifest.get(inum, {})
        desc = row.get("description", "Item {}".format(inum))
        mfr = row.get("manufacturer", "")
        model = row.get("model_number", "")

        sep_label = desc
        if mfr:
            sep_label += "\n" + mfr
        if model:
            sep_label += " " + model

        # Separator page
        if sep_tmpl.exists():
            sep_out = work_dir / "sep_{}_{:02d}.docx".format(sid, inum)
            try:
                fill_separator(sep_tmpl, sep_out, sep_label)
                pdf = lo_convert(sep_out, work_dir)
                if pdf:
                    parts.append(("Item {:02d} - {}".format(inum, desc), pdf))
                    print("  OK: Separator: Item {:02d}".format(inum))
                else:
                    print("  WARNING: Separator conversion failed: Item {:02d}".format(inum))
            except Exception as exc:
                print("  ERROR in separator {}: {}".format(inum, exc))
                traceback.print_exc()

        # Cut sheet
        cp = row.get("cut_sheet_path", "").strip()
        if cp:
            full = BASE_DIR / cp
            if full.exists():
                parts.append(("Cut Sheet - {}".format(desc), full))
                print("  OK: Cut sheet: Item {:02d} ({})".format(inum, full.name))
            else:
                print("  WARNING: Cut sheet NOT FOUND: {}".format(cp))

    # -- 4. Assemble ---------------------------------------------------------
    if not parts:
        print("  FAIL: No PDFs to merge for SET {}".format(sid))
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
            print("  WARNING: Error merging {}: {}".format(pdf_path.name, exc))
            traceback.print_exc()

    safe = name.replace(" ", "-").replace("&", "and")
    fname = "Double-RR_SUB-{}_{}.pdf".format(sid, safe)
    out = output_dir / fname
    with open(out, "wb") as f:
        writer.write(f)

    mb = out.stat().st_size / 1_048_576
    print("  DONE: {} - {} pages ({:.1f} MB)".format(fname, total, mb))
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
        sys.exit("ERROR: project folder not found: {}".format(project_dir))

    print("")
    print("=" * 60)
    print("  Winwater Submittal Set Builder")
    print("  Project: {}".format(args.project))
    print("  Mode:    {}".format("INSPECT" if args.inspect else "BUILD"))
    print("=" * 60)

    # List templates
    print("")
    print("Templates directory: {}".format(TEMPLATES_DIR))
    if TEMPLATES_DIR.exists():
        for p in sorted(TEMPLATES_DIR.iterdir()):
            print("  {} ({:.0f} KB)".format(p.name, p.stat().st_size / 1024))
    else:
        sys.exit("ERROR: templates directory not found: {}".format(TEMPLATES_DIR))

    # -- Inspect mode --------------------------------------------------------
    if args.inspect:
        print("")
        print("=== TEMPLATE INSPECTION ===")
        for path in sorted(TEMPLATES_DIR.iterdir()):
            if path.suffix == ".xlsx":
                print("")
                print("> {}".format(path.name))
                inspect_xlsx(path)
            elif path.suffix == ".docx":
                print("")
                print("> {}".format(path.name))
                inspect_docx(path)
        return

    # -- Build mode ----------------------------------------------------------
    manifest = load_manifest(project_dir)
    print("")
    print("Manifest: {} items loaded".format(len(manifest)))

    # Verify vendor-docs exist
    missing = 0
    for inum, row in manifest.items():
        cp = row.get("cut_sheet_path", "").strip()
        if cp:
            full = BASE_DIR / cp
            if not full.exists():
                print("  MISSING: Item {} - {}".format(inum, cp))
                missing += 1
    if missing:
        print("  WARNING: {} vendor PDFs missing".format(missing))
    else:
        print("  All vendor PDFs found")

    # Output directory
    output_dir = project_dir / "sets"
    output_dir.mkdir(parents=True, exist_ok=True)

    # Temp working directory
    work_dir = Path(tempfile.mkdtemp(prefix="winwater_"))
    print("Work dir: {}".format(work_dir))
    print("Output dir: {}".format(output_dir))

    # Build each set
    results = []
    for si in SUBMITTAL_SETS:
        try:
            res = build_set(si, manifest, project_dir, output_dir, work_dir)
            results.append((si, res))
        except Exception as exc:
            print("  FATAL ERROR building set {}: {}".format(si["id"], exc))
            traceback.print_exc()
            results.append((si, None))

    # Summary
    print("")
    print("=" * 60)
    print("  BUILD SUMMARY")
    print("=" * 60)
    ok = 0
    for si, res in results:
        if res and res.exists():
            mb = res.stat().st_size / 1_048_576
            print("  OK  SET-{}: {} ({:.1f} MB)".format(si["id"], si["name"], mb))
            ok += 1
        else:
            print("  FAIL SET-{}: {}".format(si["id"], si["name"]))
    print("")
    print("  {}/{} sets built successfully".format(ok, len(SUBMITTAL_SETS)))
    print("  Output: {}".format(output_dir))

    # Cleanup temp dir
    shutil.rmtree(work_dir, ignore_errors=True)

    if ok == 0:
        sys.exit(1)
    elif ok < len(SUBMITTAL_SETS):
        print("  WARNING: Some sets failed, but partial results committed")


if __name__ == "__main__":
    main()
