#!/usr/bin/env python3
"""
Build Package — Prepare & Assemble Submittal
=============================================
Converts markdown pages to PDF, copies vendor cut sheets into
each Item folder, then runs the assembly script to produce the
final bookmarked PDF.

Usage:
    python build-package.py --project "Double-RR"

Requirements:
    pip install pypdf weasyprint markdown
"""

import argparse
import csv
import shutil
import subprocess
import sys
from pathlib import Path

try:
    import markdown as md_lib
    import weasyprint
except ImportError:
    print("ERROR: Required packages missing. Run:")
    print("  pip install weasyprint markdown")
    sys.exit(1)

BASE_DIR = Path(__file__).resolve().parent.parent
SUBMITTALS_DIR = BASE_DIR / "submittals"

# ---------------------------------------------------------------------------
# CSS Themes
# ---------------------------------------------------------------------------

CSS_DOCUMENT = """
@page {
    size: letter;
    margin: 0.75in;
}
body {
    font-family: 'DejaVu Sans', Arial, Helvetica, sans-serif;
    font-size: 11pt;
    line-height: 1.4;
    color: #000;
}
h1 { font-size: 18pt; text-align: center; margin-bottom: 0.3em; }
h2 { font-size: 14pt; margin-top: 1em; }
h3 { font-size: 12pt; }
hr { border: 1px solid #333; margin: 1em 0; }
pre, code {
    font-family: 'DejaVu Sans Mono', 'Courier New', monospace;
    font-size: 8pt;
    line-height: 1.15;
    white-space: pre;
}
pre {
    background: #fff;
    padding: 0;
    border: none;
    page-break-inside: avoid;
}
table {
    width: 100%;
    border-collapse: collapse;
    margin: 1em 0;
}
th, td {
    border: 1px solid #333;
    padding: 4pt 8pt;
    text-align: left;
    font-size: 10pt;
}
th { background: #f0f0f0; font-weight: bold; }
"""

# Separator & cover sheets are monospace box-art — need tighter layout
CSS_BOXART = """
@page {
    size: letter;
    margin: 0.5in 0.35in;
}
body {
    font-family: 'DejaVu Sans Mono', 'Courier New', monospace;
    font-size: 9pt;
    line-height: 1.15;
    color: #000;
}
h1

 { display: none; }
hr { display: none; }
pre, code {
    font-family: 'DejaVu Sans Mono', 'Courier New', monospace;
    font-size: 9pt;
    line-height: 1.15;
    white-space: pre;
}
pre {
    background: #fff;
    padding: 0;
    border: none;
}
"""


def md_to_pdf(md_path: Path, pdf_path: Path, css: str = CSS_DOCUMENT):
    """Convert a Markdown file to PDF via Markdown → HTML → WeasyPrint."""
    text = md_path.read_text(encoding="utf-8")
    html_body = md_lib.markdown(text, extensions=["tables", "fenced_code"])
    full_html = (
        '<!DOCTYPE html><html><head><meta charset="utf-8">'
        f'<style>{css}</style></head><body>{html_body}</body></html>'
    )
    weasyprint.HTML(string=full_html).write_pdf(str(pdf_path))
    print(f"  ✅ {md_path.name} → {pdf_path.name}")


def load_manifest(project_dir: Path) -> list[dict]:
    path = project_dir / "manifest.csv"
    with open(path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def build(project: str):
    project_dir = SUBMITTALS_DIR / project
    if not project_dir.exists():
        print(f"ERROR: project folder not found: {project_dir}")
        sys.exit(1)

    print(f"\n{'='*60}")
    print(f"  Building submittal package: {project}")
    print(f"{'='*60}\n")

    # ── 1. Cover sheet ────────────────────────────────────────────
    print("▶ Cover sheet")
    cover_md = project_dir / "01-cover" / "cover-sheet.md"
    if cover_md.exists():
        md_to_pdf(cover_md, project_dir / "01-cover" / "cover-sheet.pdf", CSS_BOXART)

    # ── 2. Item index ─────────────────────────────────────────────
    print("▶ Item index")
    index_md = project_dir / "02-index" / "item-index.md"
    if index_md.exists():
        md_to_pdf(index_md, project_dir / "02-index" / "item-index.pdf", CSS_DOCUMENT)

    # ── 3. Per-item: separator PDF + vendor cut sheet copy ────────
    print("▶ Items")
    manifest = load_manifest(project_dir)

    for row in manifest:
        item_num = row["item_number"].zfill(2)
        item_dir = project_dir / "03-items" / f"Item-{item_num}"
        item_dir.mkdir(parents=True, exist_ok=True)

        # Separator → PDF
        sep_md = item_dir / "separator.md"
        if sep_md.exists():
            md_to_pdf(sep_md, item_dir / f"01-separator.pdf", CSS_BOXART)

        # Vendor cut sheet → copy into item folder
        cut_path_str = row.get("cut_sheet_path", "").strip()
        if cut_path_str:
            src = BASE_DIR / cut_path_str
            if src.exists():
                dst = item_dir / f"02-{src.name}"
                shutil.copy2(src, dst)
                print(f"  ✅ Item {item_num}: copied {src.name}")
            else:
                print(f"  ⚠️  Item {item_num}: NOT FOUND → {cut_path_str}")

    # ── 4. Disclaimer ──────────────────────────────────────────────
    print("▶ Disclaimer")
    disc_md = project_dir / "04-attachments" / "disclaimer.md"
    if disc_md.exists():
        md_to_pdf(disc_md, project_dir / "04-attachments" / "disclaimer.pdf", CSS_DOCUMENT)

    # ── 5. Assemble final PDF ─────────────────────────────────────
    print("\n▶ Assembling final bookmarked PDF...")
    result = subprocess.run(
        [
            sys.executable,
            str(BASE_DIR / "scripts" / "assemble-submittal.py"),
            "--project", project,
        ],
        cwd=str(BASE_DIR),
        capture_output=True,
        text=True,
    )
    print(result.stdout)
    if result.returncode != 0:
        print(result.stderr)
        sys.exit(1)

    print(f"\n{'='*60}")
    print("  ✅ PACKAGE BUILD COMPLETE")
    print(f"{'='*60}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Build submittal package")
    parser.add_argument("--project", required=True, help="Project folder name")
    args = parser.parse_args()
    build(args.project)
