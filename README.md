# Winwater Submittals

This repository manages professional submittal packages for Winwater projects.
It stores submittal templates, company standards documentation, and assembled
submittal packages organized by project — with an automated pipeline for
building individual submittal sets from real Office templates.

---

## Repository Structure

```
Winwater-Submittals/
├── docs/                          # Company standards and reference documents
│   ├── submittal-standard.md      # Company submittal format standard (Part A)
│   └── assembly-guide.md          # Step-by-step assembly instructions
├── templates/                     # Office templates used for PDF generation
│   ├── submittal cover.xlsx       # Excel cover-sheet template
│   ├── Item Index Template.docx   # Word item index template
│   ├── Seperator Sheet Template.docx  # Word separator-sheet template
│   ├── cover-sheet.md             # Markdown cover sheet reference
│   ├── item-index.md              # Markdown item index reference
│   └── separator-sheet.md        # Markdown separator reference
├── submittals/                    # Submittal packages by project
│   └── Double-RR/                 # Double RR project (20 items, 11 sets)
│       ├── project.json           # ← Project metadata & set definitions
│       ├── manifest.csv           # Item manifest (drives all automation)
│       ├── SUBMITTAL-PACKAGE.md   # Full package definition and status
│       ├── sets/                  # 11 built submittal-set PDFs
│       ├── 01-cover/              # Cover sheet assets
│       ├── 02-index/              # Item index assets
│       ├── 03-items/              # Per-item folders (Item-01 through Item-20)
│       └── 04-attachments/        # Disclaimer
├── vendor-docs/                   # Vendor product data organized by manufacturer
│   ├── Watts/
│   ├── Apollo/
│   ├── Zurn/
│   └── ...
└── scripts/                       # Assembly and automation scripts
    ├── build-submittal-sets.py    # ← Primary: builds 11 per-set PDFs from templates
    ├── build-package.py           # Builds a single combined package PDF (WeasyPrint)
    ├── assemble-submittal.py      # PDF assembly with bookmarks (legacy)
    ├── orchestrator.py            # Autonomous pipeline orchestrator
    └── agents/                    # Specialized agent modules
        ├── validate_agent.py      # Structure & manifest validation
        ├── separator_agent.py     # Auto-generate separator sheets from manifest
        ├── vendor_fetch_agent.py  # Audit vendor files, create missing dirs
        ├── template_compliance_agent.py # Template + presentation gate
        └── qc_agent.py            # Quality-control checks & scoring
```

---

## Installation

```bash
# Python dependencies
pip install -r requirements.txt

# System dependency (Ubuntu / Debian / GitHub Actions)
sudo apt-get install libreoffice
```

---

## Quick Start

### Build All Submittal Sets (Recommended)

Generates 11 individual PDFs — one per submittal set — using the real Office
templates (`submittal cover.xlsx`, `Item Index Template.docx`,
`Seperator Sheet Template.docx`) plus the vendor cut-sheet PDFs:

```bash
python scripts/build-submittal-sets.py --project "Double-RR"
```

Outputs go to `submittals/Double-RR/sets/`.


### Run Template/Presentation Compliance Gate

Before building sets, run the template gate to catch low-quality inputs
(long fields, missing templates, missing cut-sheet PDFs, unresolved placeholders):

```bash
python scripts/agents/template_compliance_agent.py --project "Double-RR"
```

You can also run it through the orchestrator:

```bash
python scripts/orchestrator.py --project "Double-RR" --step template-gate
```

### Build Combined Package PDF

Generates a single bookmarked PDF with cover → index → sections:

```bash
python scripts/build-package.py --project "Double-RR"
```

### Inspect Templates

Print the structure of all Office templates (no PDFs built):

```bash
python scripts/build-submittal-sets.py --project "Double-RR" --inspect
```


### Template-Free Rendering Architecture (V2)

For a no-Office-template rendering path (schema + theme + plugin backends), see:

- `docs/v2/template-free-submittal-architecture.md`
- `scripts/plugins/submittal_renderer_plugin.py`
- `scripts/agents/repo_submittal_agent.py`
- `skills/submittal-quality-skill/`

### CI / GitHub Actions

| Workflow | Trigger | What it does |
|---|---|---|
| Build Submittal Sets | push to main (or manual) | Runs `build-submittal-sets.py`, commits 11 set PDFs |
| Build Submittal Package | manual dispatch | Runs `build-package.py`, commits combined PDF |
| Sync Vendor Docs | manual dispatch | Pulls vendor PDFs from `solidzdawg/Winwater-Docs` |

---

## Project Configuration (`project.json`)

Each project folder contains a `project.json` file that holds all metadata
and set definitions.  `build-submittal-sets.py` reads this file automatically;
if it is missing the script falls back to built-in defaults.

```jsonc
// submittals/Double-RR/project.json
{
  "project_name": "Double RR Ranch - East Cabins",
  "project_number": "DRLR-2026-001",
  "submittal_prefix": "WW",
  "revision": "0",
  "date": "03/31/2026",
  "to_name": "",
  "submitted_by": "Grand Junction Winwater Company",
  "submittal_sets": [
    {"id": "01", "name": "Pressure Reducing Valves", "items": [1, 2], "spec": "22 05 23"},
    ...
  ]
}
```

To update a project date, customer name, or add/remove sets, edit `project.json`
and re-run the build — no code changes needed.

---

## Adding Vendor Documentation

Place vendor spec sheets and certifications in `vendor-docs/<Manufacturer>/`.

```
vendor-docs/
├── Watts/
│   ├── Cut-Sheets/
│   └── Certifications/
├── Apollo/
├── Zurn/
└── ...
```

File naming: `<MANUFACTURER>_<ModelNumber>_<DocType>.pdf`

Or sync from the `solidzdawg/Winwater-Docs` repository via the
**Sync Vendor Docs** workflow (requires `DOCS_TOKEN` secret).

---

## Projects

| Project    | Status                      | Submittal # | Items | Sets |
|------------|-----------------------------|-------------|-------|------|
| Double RR  | ✅ 11 Submittal Sets Built   | WW-2024-001 | 20    | 11   |

---

## Contact

Winwater — Internal submittal management repository.
