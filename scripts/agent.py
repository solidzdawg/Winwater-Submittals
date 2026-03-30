#!/usr/bin/env python3
"""
Winwater Submittal Agent
=========================
Fully autonomous agent that builds a complete submittal package with no manual
intervention. Scans both source document locations, matches vendor docs to every
manifest item, generates all required PDF pages, assembles the final package, and
writes a detailed log of everything it did.

Usage:
    python agent.py --project "Double-RR"
    python agent.py --project "Double-RR" --dry-run
    python agent.py --project "Double-RR" --manifest path/to/manifest.csv
    python agent.py --list-projects

Requirements:
    pip install pypdf fpdf2
"""

import argparse
import csv
import hashlib
import json
import os
import platform
import re
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

try:
    from fpdf import FPDF
    from fpdf.enums import XPos, YPos
except ImportError:
    print("ERROR: fpdf2 is not installed. Run: pip install fpdf2")
    sys.exit(1)

try:
    from pypdf import PdfWriter, PdfReader
except ImportError:
    print("ERROR: pypdf is not installed. Run: pip install pypdf")
    sys.exit(1)


BASE_DIR = Path(__file__).resolve().parent.parent
CONFIG_FILE = BASE_DIR / "config" / "paths.json"
SUBMITTALS_DIR = BASE_DIR / "submittals"
CACHE_DIR = BASE_DIR / ".doc-cache"
CACHE_INDEX_FILE = CACHE_DIR / "cache-index.json"

SUPPORTED_EXTENSIONS = {".pdf", ".docx", ".doc", ".xlsx", ".xls", ".csv", ".png", ".jpg"}
COMPANY = "WINWATER"
BRAND_BLUE = (0, 80, 160)


# --------------------------------------------------------------------------- #
# Config                                                                       #
# --------------------------------------------------------------------------- #

def load_config() -> dict:
    defaults = {
        "submittal_task_dir": str(Path.home() / "Documents" / "submittal-task"),
        "z_drive_vendor_parts": "Z:\\Vendor Parts",
        "cache_dir": str(CACHE_DIR),
    }
    if CONFIG_FILE.exists():
        with open(CONFIG_FILE) as f:
            cfg = json.load(f)
        for k, v in defaults.items():
            cfg.setdefault(k, v)
        for key in ("submittal_task_dir", "cache_dir"):
            cfg[key] = str(Path(cfg[key]).expanduser())
        return cfg
    return {k: str(Path(v).expanduser()) if "~" in str(v) else v for k, v in defaults.items()}


# --------------------------------------------------------------------------- #
# Cache                                                                        #
# --------------------------------------------------------------------------- #

def load_cache_index() -> dict:
    if CACHE_INDEX_FILE.exists():
        with open(CACHE_INDEX_FILE) as f:
            return json.load(f)
    return {"cached_files": {}}


def save_cache_index(index: dict):
    CACHE_INDEX_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(CACHE_INDEX_FILE, "w") as f:
        json.dump(index, f, indent=2)


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def cache_directory(root: Path, label: str, cache_root: Path, index: dict, log: list) -> int:
    """Copy all supported docs from root into cache_root/label/. Returns new-file count."""
    if not root.exists():
        log.append(f"SKIP  cache {label}: source not accessible ({root})")
        return 0

    copied = 0
    dest_root = cache_root / label

    for src_path in sorted(root.rglob("*")):
        if not src_path.is_file():
            continue
        if src_path.suffix.lower() not in SUPPORTED_EXTENSIONS:
            continue

        rel = str(src_path.relative_to(root))
        cache_key = f"{label}/{rel}"
        dest = dest_root / rel
        entry = index["cached_files"].get(cache_key)

        # Skip if cached and source file is unchanged (size + mtime match)
        if dest.exists() and entry:
            try:
                stat = src_path.stat()
                if (
                    entry.get("size_bytes") == stat.st_size
                    and entry.get("mtime")
                    == datetime.fromtimestamp(stat.st_mtime, tz=timezone.utc).isoformat()
                ):
                    continue
            except OSError:
                pass

        dest.parent.mkdir(parents=True, exist_ok=True)
        try:
            shutil.copy2(src_path, dest)
            stat = src_path.stat()
            index["cached_files"][cache_key] = {
                "source_label": label,
                "source_path": str(src_path),
                "cached_path": str(dest),
                "cached_at": datetime.now(tz=timezone.utc).isoformat(),
                "size_bytes": stat.st_size,
                "mtime": datetime.fromtimestamp(stat.st_mtime, tz=timezone.utc).isoformat(),
                "sha256": sha256_file(dest),
            }
            copied += 1
            log.append(f"CACHE {cache_key}")
        except (OSError, PermissionError) as e:
            log.append(f"ERROR cache {cache_key}: {e}")

    return copied


# --------------------------------------------------------------------------- #
# Doc matching                                                                 #
# --------------------------------------------------------------------------- #

def _normalize(s: str) -> str:
    """Lowercase, remove non-alphanumeric for fuzzy comparison."""
    return re.sub(r"[^a-z0-9]", "", s.lower())


def find_cached_docs(
    cache_label_root: Path,
    manufacturer: str,
    model: str,
    doc_type_keywords: list[str],
) -> list[Path]:
    """
    Search the cache for PDFs matching manufacturer + model + doc type keywords.
    Returns matched paths, type-matched results listed first.
    """
    if not cache_label_root.exists():
        return []

    mfr_n = _normalize(manufacturer)
    model_n = _normalize(model)
    type_kws = [_normalize(t) for t in doc_type_keywords]

    type_matches: list[Path] = []
    other_matches: list[Path] = []

    for p in sorted(cache_label_root.rglob("*.pdf")):
        path_n = _normalize(str(p))
        parts_n = [_normalize(part) for part in p.parts]

        # Manufacturer must appear somewhere in the path
        if mfr_n and not any(
            mfr_n in pn or pn in mfr_n for pn in parts_n if len(pn) > 2
        ):
            continue

        # Model must appear in filename (exact or partial: any 4-char slice)
        fn_n = _normalize(p.name)
        if model_n and model_n not in fn_n:
            if not (
                len(model_n) >= 4
                and any(model_n[i : i + 4] in fn_n for i in range(len(model_n) - 3))
            ):
                continue

        if type_kws and any(kw in path_n for kw in type_kws):
            type_matches.append(p)
        else:
            other_matches.append(p)

    return type_matches + other_matches


# --------------------------------------------------------------------------- #
# PDF generation (fpdf2)                                                       #
# --------------------------------------------------------------------------- #

class _WinwaterPDF(FPDF):
    def __init__(self, project: str = "", submittal_no: str = ""):
        super().__init__()
        self._project = project
        self._submittal_no = submittal_no

    def header(self):
        self.set_font("Helvetica", "B", 9)
        self.set_text_color(100, 100, 100)
        self.cell(0, 8, COMPANY, new_x=XPos.LMARGIN, new_y=YPos.NEXT, align="R")
        self.set_draw_color(200, 200, 200)
        self.line(self.l_margin, self.get_y(), self.w - self.r_margin, self.get_y())
        self.ln(3)
        self.set_text_color(0, 0, 0)

    def footer(self):
        self.set_y(-14)
        self.set_font("Helvetica", "I", 8)
        self.set_text_color(130, 130, 130)
        label = f"Page {self.page_no()}  |  {self._project}  |  {self._submittal_no}"
        self.cell(0, 10, label, align="C")
        self.set_text_color(0, 0, 0)


def _blue_heading(pdf: _WinwaterPDF, text: str, size: int = 11):
    pdf.set_font("Helvetica", "B", size)
    pdf.set_text_color(*BRAND_BLUE)
    pdf.cell(0, 9, text, new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.set_text_color(0, 0, 0)
    pdf.ln(2)


def generate_cover_sheet(
    dest: Path,
    project: str,
    submittal_no: str,
    date_str: str,
    prepared_by: str,
    engineer: str,
    contractor: str,
    spec_sections: list[str],
    items_summary: str,
):
    pdf = _WinwaterPDF(project, submittal_no)
    pdf.add_page()

    # Company title
    pdf.ln(4)
    pdf.set_font("Helvetica", "B", 24)
    pdf.set_text_color(*BRAND_BLUE)
    pdf.cell(0, 14, COMPANY, new_x=XPos.LMARGIN, new_y=YPos.NEXT, align="C")
    pdf.set_font("Helvetica", "", 11)
    pdf.set_text_color(90, 90, 90)
    pdf.cell(0, 7, "Plumbing & Mechanical Submittal", new_x=XPos.LMARGIN, new_y=YPos.NEXT, align="C")
    pdf.ln(10)

    # Project banner
    pdf.set_fill_color(*BRAND_BLUE)
    pdf.set_text_color(255, 255, 255)
    pdf.set_font("Helvetica", "B", 16)
    pdf.cell(0, 14, project, new_x=XPos.LMARGIN, new_y=YPos.NEXT, align="C", fill=True)
    pdf.ln(10)

    # Info table
    def info_row(label: str, value: str):
        pdf.set_font("Helvetica", "B", 10)
        pdf.set_fill_color(235, 241, 250)
        pdf.set_text_color(50, 50, 50)
        pdf.cell(55, 9, label, border=1, fill=True)
        pdf.set_font("Helvetica", "", 10)
        pdf.set_fill_color(255, 255, 255)
        pdf.set_text_color(0, 0, 0)
        pdf.cell(0, 9, value, border=1, new_x=XPos.LMARGIN, new_y=YPos.NEXT, fill=True)

    info_row("Submittal No.:", submittal_no)
    info_row("Date:", date_str)
    info_row("Revision:", "0")
    info_row("Prepared By:", prepared_by)
    info_row("Contractor:", contractor)
    info_row("Engineer / EOR:", engineer)
    info_row("Spec Sections:", ", ".join(spec_sections) if spec_sections else "22 05 00")
    pdf.ln(10)

    _blue_heading(pdf, "SUBMITTAL CONTENTS")
    pdf.set_font("Helvetica", "", 10)
    pdf.multi_cell(0, 7, items_summary)
    pdf.ln(10)

    # Engineer stamp area
    _blue_heading(pdf, "ENGINEER'S REVIEW STAMP")
    pdf.set_draw_color(180, 180, 180)
    pdf.rect(pdf.l_margin, pdf.get_y(), pdf.w - pdf.l_margin - pdf.r_margin, 28)
    pdf.ln(22)
    pdf.set_font("Helvetica", "", 10)
    pdf.cell(50, 7, "[ ] Approved")
    pdf.cell(70, 7, "[ ] Approved as Noted")
    pdf.cell(0, 7, "[ ] Rejected / Resubmit", new_x=XPos.LMARGIN, new_y=YPos.NEXT)

    dest.parent.mkdir(parents=True, exist_ok=True)
    pdf.output(str(dest))


def generate_item_index(
    dest: Path,
    project: str,
    submittal_no: str,
    items: list[dict],
    page_estimates: dict[int, int],
):
    pdf = _WinwaterPDF(project, submittal_no)
    pdf.add_page()

    pdf.ln(2)
    _blue_heading(pdf, "ITEM INDEX", size=14)
    pdf.ln(2)

    col_w = [12, 68, 38, 30, 24, 16]
    headers = ["#", "Description", "Manufacturer", "Model No.", "Spec Sec.", "Page"]

    pdf.set_fill_color(*BRAND_BLUE)
    pdf.set_text_color(255, 255, 255)
    pdf.set_font("Helvetica", "B", 9)
    for w, h in zip(col_w, headers):
        pdf.cell(w, 9, h, border=1, fill=True, align="C")
    pdf.ln()

    pdf.set_text_color(0, 0, 0)
    for i, item in enumerate(items):
        fill = i % 2 == 0
        if fill:
            pdf.set_fill_color(247, 250, 255)
        else:
            pdf.set_fill_color(255, 255, 255)
        pdf.set_font("Helvetica", "", 9)
        item_num = int(item.get("item_number", i + 1))
        row = [
            str(item_num),
            item.get("description", "")[:40],
            item.get("manufacturer", "")[:22],
            item.get("model_number", "")[:18],
            item.get("spec_section", "")[:12],
            str(page_estimates.get(item_num, "-")),
        ]
        for w, val in zip(col_w, row):
            pdf.cell(w, 8, val, border=1, fill=fill)
        pdf.ln()

    dest.parent.mkdir(parents=True, exist_ok=True)
    pdf.output(str(dest))


def generate_separator_sheet(
    dest: Path,
    item_no: int,
    description: str,
    manufacturer: str,
    model: str,
    spec_section: str,
    project: str,
    submittal_no: str,
    has_cut_sheet: bool,
    has_nsf61: bool,
    has_nsf372: bool,
    has_spec_pages: bool,
):
    pdf = _WinwaterPDF(project, submittal_no)
    pdf.add_page()

    pdf.ln(8)
    pdf.set_fill_color(*BRAND_BLUE)
    pdf.set_text_color(255, 255, 255)
    pdf.set_font("Helvetica", "B", 38)
    pdf.cell(0, 22, f"ITEM  {item_no:02d}", new_x=XPos.LMARGIN, new_y=YPos.NEXT, align="C", fill=True)
    pdf.ln(10)

    pdf.set_text_color(0, 0, 0)
    pdf.set_font("Helvetica", "B", 15)
    pdf.cell(0, 11, description, new_x=XPos.LMARGIN, new_y=YPos.NEXT, align="C")
    pdf.ln(10)

    def info_row(label: str, value: str):
        pdf.set_font("Helvetica", "B", 10)
        pdf.set_fill_color(235, 241, 250)
        pdf.cell(52, 9, label, border=1, fill=True)
        pdf.set_font("Helvetica", "", 10)
        pdf.set_fill_color(255, 255, 255)
        pdf.cell(0, 9, value, border=1, new_x=XPos.LMARGIN, new_y=YPos.NEXT)

    info_row("Manufacturer:", manufacturer)
    info_row("Model Number:", model)
    info_row("Spec Section:", spec_section)
    pdf.ln(12)

    _blue_heading(pdf, "INCLUDED DOCUMENTS")

    def check_row(label: str, included: bool):
        icon = "[X]" if included else "[ ]"
        status = "Included" if included else "Not included -- attach manually"
        if included:
            pdf.set_text_color(0, 0, 0)
        else:
            pdf.set_text_color(190, 0, 0)
        pdf.set_font("Helvetica", "", 10)
        pdf.cell(0, 8, f"  {icon}  {label}  -  {status}", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        pdf.set_text_color(0, 0, 0)

    check_row("Cut Sheet / Product Data", has_cut_sheet)
    check_row("NSF 61 Certification", has_nsf61)
    check_row("NSF 372 Certification (Low-Lead)", has_nsf372)
    check_row("Specification Pages", has_spec_pages)

    dest.parent.mkdir(parents=True, exist_ok=True)
    pdf.output(str(dest))


def generate_disclaimer(
    dest: Path, project: str, submittal_no: str, date_str: str
):
    pdf = _WinwaterPDF(project, submittal_no)
    pdf.add_page()

    pdf.ln(4)
    _blue_heading(pdf, "SUBMITTAL TRANSMITTAL & DISCLAIMER", size=13)
    pdf.ln(4)

    text = (
        f"Project:         {project}\n"
        f"Submittal No.:   {submittal_no}\n"
        f"Date:            {date_str}\n\n"
        "This submittal has been prepared by WINWATER and is submitted for review "
        "and approval by the Engineer of Record (EOR). The materials and equipment "
        "described herein are submitted as being in conformance with the contract "
        "documents. Any deviations from the specified requirements are identified "
        "separately.\n\n"
        "Contractor certification: By submitting this package, the contractor "
        "certifies that the submitted products meet or exceed the requirements of "
        "the project specifications and that the contractor has reviewed the "
        "submittal for conformance with the contract documents.\n\n"
        "NOTE: Approval of this submittal does not authorize the contractor to "
        "deviate from the contract documents. All materials shall comply with "
        "applicable codes, standards, and local requirements including but not "
        "limited to NSF/ANSI 61 and NSF/ANSI 372 for potable water contact "
        "materials.\n\n"
        "This submittal package was assembled using the Winwater Submittal Agent.\n"
        f"Agent run date: {date_str}"
    )
    pdf.set_font("Helvetica", "", 10)
    pdf.multi_cell(0, 7, text)

    dest.parent.mkdir(parents=True, exist_ok=True)
    pdf.output(str(dest))


# --------------------------------------------------------------------------- #
# Autonomous agent                                                             #
# --------------------------------------------------------------------------- #

class SubmittalAgent:
    def __init__(
        self,
        project: str,
        config: dict,
        manifest_path: Path | None = None,
        dry_run: bool = False,
    ):
        self.project = project
        self.config = config
        self.dry_run = dry_run
        self.project_dir = SUBMITTALS_DIR / project
        self.manifest_path = manifest_path or (self.project_dir / "manifest.csv")
        self.cache_root = Path(config["cache_dir"])
        self.log: list[str] = []
        self.warnings: list[str] = []
        self.items: list[dict] = []
        self.matched: dict[str, list[Path]] = {}

        self.submittal_no = "WW-001"
        self.date_str = datetime.now().strftime("%B %d, %Y")
        self.prepared_by = "Winwater"
        self.engineer = "Engineer of Record"
        self.contractor = "Winwater"

    # ------------------------------------------------------------------ #

    def _log(self, msg: str):
        ts = datetime.now().strftime("%H:%M:%S")
        self.log.append(f"[{ts}] {msg}")
        print(f"  {msg}")

    def _warn(self, msg: str):
        self.warnings.append(msg)
        self._log(f"⚠️  {msg}")

    # ------------------------------------------------------------------ #

    def run(self):
        print(f"\n{'='*65}")
        print(f"  WINWATER SUBMITTAL AGENT  —  {self.project}")
        print(f"  {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        if self.dry_run:
            print("  DRY RUN — no files will be written")
        print(f"{'='*65}\n")

        self._step1_cache_sources()
        self._step2_load_manifest()
        self._step3_match_docs()

        if not self.dry_run:
            self._step4_build_structure()
            self._step5_generate_pdfs()
            self._step6_assemble()

        self._step7_write_log()

        print(f"\n{'='*65}")
        print(f"  Agent run complete.")
        if self.warnings:
            print(f"  ⚠️  {len(self.warnings)} warning(s) — see agent-run.log for manual action items")
        print(f"{'='*65}\n")

    # ------------------------------------------------------------------ #
    # Step 1                                                               #
    # ------------------------------------------------------------------ #

    def _step1_cache_sources(self):
        print("\n── STEP 1  Cache source documents ────────────────────────────")

        cache_index = load_cache_index()
        task_root = Path(self.config["submittal_task_dir"])
        zdrive_root = Path(self.config["z_drive_vendor_parts"])

        if task_root.exists():
            n = cache_directory(task_root, "submittal_task", self.cache_root, cache_index, self.log)
            self._log(f"✅ Submittal task folder cached: {n} new file(s)  ({task_root})")
        else:
            self._warn(f"Submittal task folder not found: {task_root}")

        if zdrive_root.exists():
            n = cache_directory(zdrive_root, "z_drive", self.cache_root, cache_index, self.log)
            self._log(f"✅ Z: drive vendor parts cached: {n} new file(s)  ({zdrive_root})")
        else:
            self._warn(f"Z: drive not accessible: {zdrive_root} — using existing cache if available")

        save_cache_index(cache_index)
        total = len(cache_index.get("cached_files", {}))
        self._log(f"Cache total: {total} file(s) in {self.cache_root}")

    # ------------------------------------------------------------------ #
    # Step 2                                                               #
    # ------------------------------------------------------------------ #

    def _step2_load_manifest(self):
        print("\n── STEP 2  Load manifest ──────────────────────────────────────")

        if not self.manifest_path.exists():
            self._warn(f"Manifest not found: {self.manifest_path}")
            return

        with open(self.manifest_path, newline="", encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            self.items = [row for row in reader if row.get("item_number", "").strip()]

        self._log(f"✅ Loaded {len(self.items)} item(s) from {self.manifest_path.name}")
        for item in self.items:
            self._log(
                f"   Item {item['item_number']:>2}: {item['description']}  "
                f"({item['manufacturer']} {item['model_number']})"
            )

    # ------------------------------------------------------------------ #
    # Step 3                                                               #
    # ------------------------------------------------------------------ #

    def _step3_match_docs(self):
        print("\n── STEP 3  Match cached docs to manifest items ────────────────")

        z_cache = self.cache_root / "z_drive"
        task_cache = self.cache_root / "submittal_task"

        for item in self.items:
            num = str(item["item_number"]).strip()
            mfr = item.get("manufacturer", "").strip()
            model = item.get("model_number", "").strip()
            found: list[Path] = []

            # Cut sheets
            cuts = find_cached_docs(
                z_cache, mfr, model,
                ["cut sheet", "cut-sheet", "cutsheet", "spec sheet", "data sheet", "submittal"],
            )
            if cuts:
                found.append(cuts[0])
                self._log(f"✅ Item {num} cut sheet : {cuts[0].name}")
            else:
                self._warn(f"Item {num} ({mfr} {model}): no cut sheet found in cache")

            # NSF 61
            certs61 = find_cached_docs(
                z_cache, mfr, model,
                ["nsf61", "nsf 61", "nsf-61"],
            )
            if not certs61:
                # broader search — any cert under manufacturer folder
                certs61 = find_cached_docs(
                    z_cache, mfr, model, ["cert", "certification", "listing"],
                )
            if certs61:
                found.append(certs61[0])
                self._log(f"✅ Item {num} NSF-61    : {certs61[0].name}")
            else:
                self._warn(f"Item {num} ({mfr} {model}): no NSF-61 cert found in cache")

            # NSF 372
            certs372 = find_cached_docs(z_cache, mfr, model, ["nsf372", "nsf 372", "nsf-372"])
            if certs372:
                found.append(certs372[0])
                self._log(f"✅ Item {num} NSF-372   : {certs372[0].name}")

            # Spec pages from task folder (keyed on spec section number)
            spec_sec = item.get("spec_section", "").strip()
            if spec_sec:
                spec_pages = find_cached_docs(
                    task_cache, "", spec_sec.replace(" ", ""),
                    ["spec", "specification", "section"],
                )
                if spec_pages:
                    found.append(spec_pages[0])
                    self._log(f"✅ Item {num} spec pages: {spec_pages[0].name}")

            # Honour explicit override paths from the manifest
            for col, label in [
                ("cut_sheet_path", "cut sheet override"),
                ("cert_nsf61_path", "NSF-61 override"),
                ("cert_nsf372_path", "NSF-372 override"),
                ("spec_pages_path", "spec pages override"),
            ]:
                override = item.get(col, "").strip()
                if override:
                    p = Path(override)
                    if p.exists():
                        found.append(p)
                        self._log(f"✅ Item {num} {label}: {p.name}  (from manifest path)")
                    else:
                        self._warn(f"Item {num} {label} path not found: {override}")

            self.matched[num] = found

        matched_count = sum(1 for docs in self.matched.values() if docs)
        self._log(f"\nMatched docs for {matched_count}/{len(self.items)} item(s)")

    # ------------------------------------------------------------------ #
    # Step 4                                                               #
    # ------------------------------------------------------------------ #

    def _step4_build_structure(self):
        print("\n── STEP 4  Build submittal folder structure ───────────────────")

        for d in ["01-cover", "02-index", "03-items", "04-attachments"]:
            (self.project_dir / d).mkdir(parents=True, exist_ok=True)

        for item in self.items:
            num = int(item["item_number"])
            item_dir = self.project_dir / "03-items" / f"Item-{num:02d}"
            item_dir.mkdir(parents=True, exist_ok=True)

            for src in self.matched.get(str(item["item_number"]), []):
                dest = item_dir / src.name
                if not dest.exists() or dest.stat().st_size != src.stat().st_size:
                    shutil.copy2(src, dest)
                    self._log(f"✅ Copied {src.name} → 03-items/Item-{num:02d}/")

        self._log(f"Folder structure ready under {self.project_dir}")

    # ------------------------------------------------------------------ #
    # Step 5                                                               #
    # ------------------------------------------------------------------ #

    def _step5_generate_pdfs(self):
        print("\n── STEP 5  Generate PDFs ──────────────────────────────────────")

        spec_sections = sorted(
            {item["spec_section"] for item in self.items if item.get("spec_section")}
        )
        items_summary = "\n".join(
            f"  Item {item['item_number']:>2}: {item['description']}  "
            f"({item['manufacturer']} {item['model_number']})"
            for item in self.items
        )

        # Estimate starting page for each item (cover=1, index=1)
        page_estimates: dict[int, int] = {}
        cursor = 3
        for item in self.items:
            n = int(item["item_number"])
            page_estimates[n] = cursor
            doc_count = len(self.matched.get(str(item["item_number"]), []))
            cursor += 1 + max(doc_count * 2, 1)

        # Cover sheet
        cover_path = self.project_dir / "01-cover" / "cover-sheet.pdf"
        generate_cover_sheet(
            dest=cover_path,
            project=self.project,
            submittal_no=self.submittal_no,
            date_str=self.date_str,
            prepared_by=self.prepared_by,
            engineer=self.engineer,
            contractor=self.contractor,
            spec_sections=spec_sections,
            items_summary=items_summary,
        )
        self._log(f"✅ Cover sheet generated: {cover_path.name}")

        # Item index
        index_path = self.project_dir / "02-index" / "item-index.pdf"
        generate_item_index(
            dest=index_path,
            project=self.project,
            submittal_no=self.submittal_no,
            items=self.items,
            page_estimates=page_estimates,
        )
        self._log(f"✅ Item index generated: {index_path.name}")

        # Separator sheets
        for item in self.items:
            num = int(item["item_number"])
            docs = self.matched.get(str(item["item_number"]), [])
            doc_names_n = [_normalize(d.name) for d in docs]

            has_cut = any("cut" in n or "spec" in n or "data" in n or "sheet" in n for n in doc_names_n)
            has_61 = any("nsf61" in n or "nsf-61" in n or ("61" in n and "cert" in n) for n in doc_names_n)
            has_372 = any("372" in n for n in doc_names_n)
            has_spec = any("spec" in n and "sheet" not in n for n in doc_names_n)

            sep_path = self.project_dir / "03-items" / f"Item-{num:02d}" / "00-separator.pdf"
            generate_separator_sheet(
                dest=sep_path,
                item_no=num,
                description=item.get("description", ""),
                manufacturer=item.get("manufacturer", ""),
                model=item.get("model_number", ""),
                spec_section=item.get("spec_section", ""),
                project=self.project,
                submittal_no=self.submittal_no,
                has_cut_sheet=has_cut,
                has_nsf61=has_61,
                has_nsf372=has_372,
                has_spec_pages=has_spec,
            )
            self._log(f"✅ Separator sheet generated: Item-{num:02d}/00-separator.pdf")

        # Disclaimer / transmittal
        disc_path = self.project_dir / "04-attachments" / "disclaimer.pdf"
        generate_disclaimer(disc_path, self.project, self.submittal_no, self.date_str)
        self._log(f"✅ Disclaimer generated: {disc_path.name}")

    # ------------------------------------------------------------------ #
    # Step 6                                                               #
    # ------------------------------------------------------------------ #

    def _step6_assemble(self):
        print("\n── STEP 6  Assemble final PDF ─────────────────────────────────")

        assembler = Path(__file__).parent / "assemble-submittal.py"
        if not assembler.exists():
            self._warn("assemble-submittal.py not found — skipping final assembly")
            return

        cmd = [sys.executable, str(assembler), "--project", self.project]
        result = subprocess.run(cmd, capture_output=True, text=True)

        output = (result.stdout + result.stderr).strip()
        for line in output.splitlines():
            self._log(f"   {line.strip()}")

        if result.returncode == 0:
            self._log("✅ Assembly complete")
        else:
            self._warn(f"Assembly script exited with code {result.returncode}")

    # ------------------------------------------------------------------ #
    # Step 7                                                               #
    # ------------------------------------------------------------------ #

    def _step7_write_log(self):
        lines = [
            "=" * 65,
            "WINWATER SUBMITTAL AGENT — RUN LOG",
            f"Project:     {self.project}",
            f"Run date:    {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            f"Dry run:     {self.dry_run}",
            f"Items:       {len(self.items)}",
            f"Warnings:    {len(self.warnings)}",
            "=" * 65,
            "",
            "ACTIVITY LOG",
            "-" * 65,
        ]
        lines += self.log
        lines += [
            "",
            "WARNINGS  (items requiring manual action)",
            "-" * 65,
        ]
        lines += self.warnings if self.warnings else ["  (none — all docs matched automatically)"]
        lines += [
            "",
            "MATCH SUMMARY",
            "-" * 65,
        ]
        for item in self.items:
            num = str(item["item_number"])
            docs = self.matched.get(num, [])
            lines.append(f"  Item {num:>2}: {item['description']}")
            lines.append(f"           {item['manufacturer']}  {item['model_number']}")
            if docs:
                for d in docs:
                    lines.append(f"           ✅ {d.name}")
            else:
                lines.append("           ❌ No docs matched — attach manually")
            lines.append("")

        log_path = self.project_dir / "agent-run.log"
        log_path.parent.mkdir(parents=True, exist_ok=True)
        with open(log_path, "w", encoding="utf-8") as f:
            f.write("\n".join(lines))

        print(f"\n  📋 Agent log written: {log_path}")
        if self.warnings:
            print(f"  ⚠️  {len(self.warnings)} item(s) need manual attention — review agent-run.log")


# --------------------------------------------------------------------------- #
# CLI                                                                          #
# --------------------------------------------------------------------------- #

def list_projects() -> list[str]:
    if not SUBMITTALS_DIR.exists():
        return []
    return [d.name for d in sorted(SUBMITTALS_DIR.iterdir()) if d.is_dir()]


def main():
    parser = argparse.ArgumentParser(
        description="Winwater autonomous submittal agent.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python agent.py --project "Double-RR"
  python agent.py --project "Double-RR" --dry-run
  python agent.py --project "Double-RR" --manifest path/to/manifest.csv
  python agent.py --list-projects
        """,
    )
    parser.add_argument(
        "--project", metavar="NAME",
        help='Project name matching a folder under submittals/',
    )
    parser.add_argument(
        "--manifest", metavar="PATH",
        help="Path to manifest CSV (default: submittals/<project>/manifest.csv)",
    )
    parser.add_argument(
        "--dry-run", action="store_true",
        help="Cache + match docs but do not write any submittal files",
    )
    parser.add_argument(
        "--list-projects", action="store_true",
        help="List available projects and exit",
    )
    args = parser.parse_args()

    if args.list_projects:
        projects = list_projects()
        if projects:
            print("Available projects:")
            for p in projects:
                print(f"  {p}")
        else:
            print("No projects found under submittals/")
        sys.exit(0)

    if not args.project:
        parser.error("--project is required (or use --list-projects)")

    config = load_config()
    manifest = Path(args.manifest) if args.manifest else None

    agent = SubmittalAgent(
        project=args.project,
        config=config,
        manifest_path=manifest,
        dry_run=args.dry_run,
    )
    agent.run()


if __name__ == "__main__":
    main()
