#!/usr/bin/env python3
"""
Build Package - Winwater Submittal Assembly Pipeline
====================================================
Generates cover page, materials index, and section separator PDFs,
then assembles them with vendor cut sheet PDFs into a single
bookmarked submittal package.

Matches the official Grand Junction Winwater Company format:
  Page 1: Submittal Cover Page (form-based)
  Page 2: Materials Submittal Index (grouped by section)
  Then for each section:
    - Section separator page (bold text, yellow highlight, centered)
    - Vendor cut sheet PDFs for all items in that section

Usage:
    python build-package.py --project "Double-RR"

Requirements:
    pip install pypdf weasyprint
"""

import argparse
import csv
import shutil
import sys
from collections import OrderedDict
from html import escape as esc
from pathlib import Path

try:
    import weasyprint
    from pypdf import PdfWriter, PdfReader
except ImportError:
    print("ERROR: Required packages missing. Run:")
    print("  pip install pypdf weasyprint")
    sys.exit(1)


BASE_DIR = Path(__file__).resolve().parent.parent
SUBMITTALS_DIR = BASE_DIR / "submittals"


def load_manifest(project_dir: Path) -> list[dict]:
    path = project_dir / "manifest.csv"
    with open(path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def group_by_section(manifest: list[dict]) -> OrderedDict:
    sections = OrderedDict()
    for row in manifest:
        sec = row.get("section_name", "Other").strip()
        if sec not in sections:
            sections[sec] = []
        sections[sec].append(row)
    return sections


def count_pdf_pages(pdf_path: Path) -> int:
    try:
        return len(PdfReader(str(pdf_path)).pages)
    except Exception:
        return 0


# ---------------------------------------------------------------------------
# CSS (module-level strings so curly braces don't conflict with f-strings)
# ---------------------------------------------------------------------------

COVER_CSS = """
@page { size: letter; margin: 0.4in 0.5in; }
body {
    font-family: 'DejaVu Sans', Calibri, Arial, sans-serif;
    font-size: 10.5pt; color: #000; margin: 0; padding: 0;
}
table.cover { border-collapse: collapse; width: 100%; border: 1.5px solid #000; }
table.cover td { border: 1px solid #000; padding: 3px 6px; vertical-align: top; }
.title-cell {
    text-align: center; font-size: 16pt; font-weight: bold;
    padding: 8px; background: #D6E4F0; border-bottom: 1.5px solid #000;
}
.logo-cell { padding: 8px 12px; width: 55%; vertical-align: top; }
.info-label { font-weight: bold; font-size: 10pt; padding: 3px 6px; white-space: nowrap; }
.info-value { font-size: 10.5pt; padding: 3px 6px; }
.summary-hdr {
    text-align: center; font-weight: bold; font-size: 11pt;
    padding: 6px; background: #F2F2F2; border-top: 1.5px solid #000;
}
.summary-body { height: 200px; }
.att-label { font-weight: bold; font-size: 10pt; width: 130px; padding: 4px 6px; }
.att-value { font-size: 10.5pt; padding: 4px 6px; }
.nbt { border-top: none !important; }
.nbb { border-bottom: none !important; }
"""

INDEX_CSS = """
@page { size: letter; margin: 0.6in 0.75in 0.5in 0.75in; }
body {
    font-family: 'DejaVu Sans', Calibri, Arial, sans-serif;
    font-size: 11pt; color: #000; margin: 0; padding: 0;
}
.logo { text-align: center; margin-bottom: 16px; padding-top: 4px; }
.logo .co { font-size: 11pt; font-weight: bold; font-style: italic; letter-spacing: 4px; }
.logo .nm { font-size: 38pt; font-weight: bold; margin: -6px 0; }
.logo .nm .w { color: #000; }
.logo .nm .wt { color: #42A5D9; }
.pl { font-size: 15pt; margin-bottom: 2px; }
h2 { font-size: 13pt; margin: 18px 0 4px 0; }
h3 { font-size: 12pt; margin: 8px 0 2px 0; }
.bi { font-size: 10pt; font-weight: bold; margin-left: 12px; margin-bottom: 8px; }
table { width: 100%; border-collapse: collapse; }
td { padding: 2px 6px; vertical-align: top; font-size: 11pt; }
td.sn { font-weight: bold; padding-top: 14px; }
td.sm { font-weight: bold; padding-top: 14px; }
td.sp { font-weight: bold; padding-top: 14px; text-align: right; }
td.id { padding-left: 16px; }
td.ip { text-align: right; }
"""

SEPARATOR_CSS = """
@page { size: letter; margin: 0; }
html, body { margin: 0; padding: 0; height: 11in; width: 8.5in; }
table.f { width: 100%; height: 11in; border: none; border-collapse: collapse; }
td.c { text-align: center; vertical-align: middle; border: none; }
.label {
    font-family: Arial, 'DejaVu Sans', Helvetica, sans-serif;
    font-size: 28pt; font-weight: bold; color: #000;
    background-color: #FFFF00; padding: 2px 10px;
}
"""


# ---------------------------------------------------------------------------
# HTML generators
# ---------------------------------------------------------------------------

def cover_html(
    customer="[Customer Name]", contact="[Contact Name]",
    address="[Project Address]", project_num="[Project Number]",
    submittal_num="1", revision="", date="[Date]",
    pm_name="[PM Name]", company="Grand Junction Winwater Company",
):
    return (
        '<!DOCTYPE html><html><head><meta charset="utf-8">'
        f'<style>{COVER_CSS}</style></head><body>'
        '<table class="cover">'
        '  <tr><td colspan="4" class="title-cell">Submittal Cover Page</td></tr>'
        '  <tr>'
        '    <td rowspan="6" colspan="2" class="logo-cell">'
        '      <div style="margin-bottom:8px;">'
        '        <div style="font-size:9pt;font-weight:bold;font-style:italic;letter-spacing:3px;">'
        '          G R A N D &nbsp; J U N C T I O N</div>'
        '        <div style="font-size:30pt;font-weight:bold;margin:-4px 0;">'
        '          <span style="color:#000;">Win</span>'
        '          <span style="color:#42A5D9;">water</span></div>'
        '        <div style="font-size:9pt;font-weight:bold;font-style:italic;letter-spacing:5px;margin-top:-6px;">'
        '          C O M P A N Y</div>'
        '      </div>'
        f'      <div style="margin-top:14px;"><strong>TO:</strong>'
        f'        <span style="margin-left:16px;border-bottom:1px solid #000;padding:0 4px;">{esc(customer)}</span><br>'
        f'        <span style="margin-left:38px;border-bottom:1px solid #000;padding:0 4px;">{esc(contact)}</span>'
        '      </div>'
        '    </td>'
        f'    <td class="info-label nbb">{esc("Submittal #")}</td>'
        f'    <td class="info-value nbb">{esc(submittal_num)}</td>'
        '  </tr>'
        '  <tr>'
        '    <td class="info-label nbt">Submittal Revision #</td>'
        f'    <td class="info-value nbt">{esc(revision)}</td>'
        '  </tr>'
        '  <tr>'
        f'    <td class="info-label nbb" style="border-top:1.5px solid #000;">DATE</td>'
        f'    <td class="info-value nbb" style="border-top:1.5px solid #000;">{esc(date)}</td>'
        '  </tr>'
        '  <tr>'
        '    <td class="info-label nbt">Project Name</td>'
        '    <td class="info-value nbt"></td>'
        '  </tr>'
        '  <tr>'
        f'    <td colspan="2" style="padding:4px 8px;font-size:10pt;">'
        f'      {esc(address)}<br><strong>PROJECT #</strong><br>{esc(project_num)}</td>'
        '  </tr>'
        '  <tr></tr>'
        '  <tr><td colspan="4" class="summary-hdr">Summary</td></tr>'
        '  <tr><td colspan="4" class="summary-body">&nbsp;</td></tr>'
        '  <tr>'
        '    <td class="att-label nbb">ATTACHMENTS:</td>'
        '    <td colspan="3" class="att-value nbb">Materials Technical Data Sheets</td>'
        '  </tr>'
        '  <tr><td class="att-label nbt nbb">&nbsp;</td><td colspan="3" class="att-value nbt nbb">&nbsp;</td></tr>'
        '  <tr><td class="att-label nbt nbb">&nbsp;</td><td colspan="3" class="att-value nbt nbb">&nbsp;</td></tr>'
        '  <tr><td class="att-label nbt">&nbsp;</td><td colspan="3" class="att-value nbt">&nbsp;</td></tr>'
        '  <tr>'
        f'    <td class="att-label nbb">SUBMITTED BY:</td>'
        f'    <td colspan="3" class="att-value nbb">{esc(pm_name)}</td>'
        '  </tr>'
        '  <tr>'
        '    <td class="att-label nbt">&nbsp;</td>'
        f'    <td colspan="3" class="att-value nbt">{esc(company)}</td>'
        '  </tr>'
        '</table></body></html>'
    )


def index_html(sections, customer="[Customer Name]",
              job1="[Job Name Line 1]", job2="[Job Name Line 2]"):
    rows = ""
    for sec_name, items in sections.items():
        rows += (
            f'<tr><td class="sn">{esc(sec_name)}</td>'
            f'<td class="sm">Manufacturer</td>'
            f'<td class="sp"># of Pages</td></tr>'
        )
        for item in items:
            cut = item.get("cut_sheet_path", "").strip()
            pages = count_pdf_pages(BASE_DIR / cut) if cut else 0
            pstr = str(pages) if pages else ""
            rows += (
                f'<tr><td class="id">{esc(item["description"])}</td>'
                f'<td>{esc(item["manufacturer"])}</td>'
                f'<td class="ip">{pstr}</td></tr>'
            )
    return (
        '<!DOCTYPE html><html><head><meta charset="utf-8">'
        f'<style>{INDEX_CSS}</style></head><body>'
        '<div class="logo">'
        '  <div class="co">G R A N D &nbsp; J U N C T I O N</div>'
        '  <div class="nm"><span class="w">Win</span><span class="wt">water</span></div>'
        '  <div class="co">C O M P A N Y</div>'
        '</div>'
        f'<div class="pl">{esc(customer)}</div>'
        f'<div class="pl">{esc(job1)}</div>'
        f'<div class="pl">{esc(job2)}</div>'
        '<h2>Materials Submittal Index</h2>'
        '<h3>Materials List</h3>'
        '<div class="bi">Bid Item</div>'
        f'<table>{rows}</table>'
        '</body></html>'
    )


def separator_html(section_name):
    return (
        '<!DOCTYPE html><html><head><meta charset="utf-8">'
        f'<style>{SEPARATOR_CSS}</style></head><body>'
        f'<table class="f"><tr><td class="c"><span class="label">{esc(section_name)}</span>'
        '</td></tr></table></body></html>'
    )


# ---------------------------------------------------------------------------
# Build pipeline
# ---------------------------------------------------------------------------

def build(project: str):
    project_dir = (SUBMITTALS_DIR / project).resolve()
    if not project_dir.is_relative_to(SUBMITTALS_DIR.resolve()):
        print(f"ERROR: Invalid project path: {project}")
        sys.exit(1)

    if not project_dir.exists():
        print(f"ERROR: project folder not found: {project_dir}")
        sys.exit(1)

    print(f"\n{'='*60}")
    print(f"  Building submittal package: {project}")
    print(f"  Format: Winwater Standard")
    print(f"{'='*60}\n")

    manifest = load_manifest(project_dir)
    sections = group_by_section(manifest)

    build_dir = project_dir / "_build"
    if build_dir.exists():
        shutil.rmtree(build_dir)
    build_dir.mkdir()

    # -- 1. Cover page -----------------------------------------------
    print(">>> Cover page")
    cover_pdf = build_dir / "00-cover.pdf"
    weasyprint.HTML(string=cover_html()).write_pdf(str(cover_pdf))
    print(f"  OK cover -> {cover_pdf.name}")

    # -- 2. Materials index ------------------------------------------
    print(">>> Materials index")
    idx_pdf = build_dir / "01-index.pdf"
    weasyprint.HTML(string=index_html(sections)).write_pdf(str(idx_pdf))
    print(f"  OK index -> {idx_pdf.name}")

    # -- 3. Sections: separator + cut sheets -------------------------
    print(">>> Sections")
    sec_num = 0
    for sec_name, items in sections.items():
        sec_num += 1
        tag = sec_name.replace(" ", "-").replace("&", "and")
        prefix = f"{sec_num + 1:02d}"

        # Separator PDF
        sep_pdf = build_dir / f"{prefix}a-sep-{tag}.pdf"
        weasyprint.HTML(string=separator_html(sec_name)).write_pdf(str(sep_pdf))
        print(f"  OK separator: {sec_name}")

        # Copy vendor cut sheets (deduplicate within section)
        seen = set()
        for item in items:
            inum = item["item_number"].zfill(2)
            cut = item.get("cut_sheet_path", "").strip()
            if not cut:
                print(f"  SKIP Item {inum}: no cut_sheet_path")
                continue
            src = BASE_DIR / cut
            if not src.exists():
                print(f"  WARN Item {inum}: NOT FOUND -> {cut}")
                continue
            if src.name in seen:
                print(f"  OK Item {inum}: (shared) {src.name}")
                continue
            seen.add(src.name)
            dst = build_dir / f"{prefix}b-item{inum}-{src.name}"
            shutil.copy2(src, dst)
            print(f"  OK Item {inum}: {src.name}")

    # -- 4. Assemble final PDF ---------------------------------------
    print("\n>>> Assembling final PDF...")
    writer = PdfWriter()
    total = 0
    sections_bm = None

    for pdf in sorted(build_dir.glob("*.pdf")):
        reader = PdfReader(str(pdf))
        bm_page = total
        for pg in reader.pages:
            writer.add_page(pg)
        total += len(reader.pages)

        name = pdf.name
        if name.startswith("00-"):
            writer.add_outline_item("Cover Page", bm_page)
        elif name.startswith("01-"):
            writer.add_outline_item("Materials Index", bm_page)
        elif "-sep-" in name:
            lbl = name.split("-sep-")[1].replace(".pdf", "").replace("-", " ").replace(" and ", " & ")
            if sections_bm is None:
                sections_bm = writer.add_outline_item("Sections", bm_page)
            writer.add_outline_item(lbl, bm_page, parent=sections_bm)

    safe = project.replace(" ", "-")
    out_name = f"{safe}_SUB_001_Rev0_PlumbingEquipment.pdf"
    out_path = project_dir / out_name
    with open(out_path, "wb") as f:
        writer.write(f)

    shutil.rmtree(build_dir)

    print(f"\nDONE: {out_path}")
    print(f"Total pages: {total}")

    # Assembly log
    log = project_dir / "assembly-log.txt"
    with open(log, "w") as f:
        f.write(f"Winwater Submittal Assembly Log\n")
        f.write(f"Project: {project}\n")
        f.write(f"Output: {out_name}\n")
        f.write(f"Pages: {total}\n")
        f.write(f"Sections: {len(sections)}\n")
        f.write(f"Items: {len(manifest)}\n\n")
        for sn, its in sections.items():
            f.write(f"  {sn}:\n")
            for i in its:
                f.write(f"    Item {i['item_number']}: {i['description']} ({i['manufacturer']})\n")

    return out_path


if __name__ == "__main__":
    p = argparse.ArgumentParser(description="Build Winwater submittal package")
    p.add_argument("--project", required=True)
    args = p.parse_args()
    build(args.project)
