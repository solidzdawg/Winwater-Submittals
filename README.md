# Winwater Submittals

Document management, PDF assembly, and **autonomous submittal generation** for
Winwater plumbing projects.

---

## Quick Start — One Command

```bash
pip install pypdf fpdf2
python scripts/agent.py --project "Double-RR"
```

The autonomous agent scans both source document locations, caches all vendor
docs locally, matches cut sheets and certifications to every manifest item,
generates cover sheet / item index / separator sheet PDFs, assembles the final
package, and logs everything — with no approvals or manual steps needed.

---

## Repository Structure

```
Winwater-Submittals/
├── config/
│   └── paths.json                 # ← Edit this: set your Documents & Z: drive paths
├── docs/
│   ├── submittal-standard.md      # Company submittal format standard
│   └── assembly-guide.md          # Full assembly guide (manual + agent)
├── templates/
│   ├── cover-sheet.md             # Cover sheet template (markdown)
│   ├── item-index.md              # Item index template (markdown)
│   └── separator-sheet.md         # Section separator template
├── submittals/
│   └── Double-RR/
│       ├── manifest.csv           # Equipment schedule — one row per item
│       ├── SUBMITTAL-PACKAGE.md   # Project status and checklist
│       ├── 01-cover/              # Generated cover sheet PDF
│       ├── 02-index/              # Generated item index PDF
│       ├── 03-items/              # Per-item folders (separator + matched docs)
│       └── 04-attachments/        # Disclaimer and general attachments
├── vendor-docs/
│   └── README.md                  # Vendor doc naming conventions
└── scripts/
    ├── agent.py                   # ★ Autonomous submittal agent
    ├── browse-docs.py             # Doc browser and cache utility
    └── assemble-submittal.py      # PDF assembly (merges all sections)
```

---

## Source Document Locations

Edit `config/paths.json` to set your two source paths:

```json
{
  "submittal_task_dir": "~/Documents/submittal-task",
  "z_drive_vendor_parts": "Z:\\Vendor Parts"
}
```

| Location | What it contains |
|----------|-----------------|
| `~/Documents/submittal-task/<Project>/` | Equipment schedule, spec sections, engineer letters |
| `Z:\Vendor Parts\<Manufacturer>\Cut Sheets\` | Vendor cut sheets and product data |
| `Z:\Vendor Parts\<Manufacturer>\Certifications\` | NSF-61, NSF-372, ASSE listings |

---

## Scripts

### `agent.py` — Autonomous Submittal Agent

Builds the entire submittal package autonomously:

```bash
# Full autonomous run
python scripts/agent.py --project "Double-RR"

# Preview what the agent will do (no files written)
python scripts/agent.py --project "Double-RR" --dry-run

# Use a custom manifest file
python scripts/agent.py --project "Double-RR" --manifest path/to/manifest.csv

# List available projects
python scripts/agent.py --list-projects
```

**What the agent does (7 steps, no approvals needed):**

1. **Cache sources** — scans `~/Documents/submittal-task/` and `Z:\Vendor Parts\`
   and copies all documents to `.doc-cache/` for offline use
2. **Load manifest** — reads `submittals/<project>/manifest.csv`
3. **Match docs** — finds cut sheets, NSF-61 certs, NSF-372 certs, and spec pages
   for every item by fuzzy-matching manufacturer name + model number in the cache
4. **Build structure** — creates the `01-cover/`, `02-index/`, `03-items/Item-XX/`,
   and `04-attachments/` folder tree and copies matched docs into place
5. **Generate PDFs** — produces cover sheet, item index table, per-item separator
   sheets (with ✅/❌ doc checklist), and the disclaimer/transmittal page
6. **Assemble** — merges all PDFs into one final package PDF
7. **Log** — writes `agent-run.log` with full activity log, warnings, and a
   per-item match summary showing exactly what was found or is still missing

After the run, review `submittals/<project>/agent-run.log`. Any items the agent
could not automatically match will be listed as warnings — copy those PDFs into
the `03-items/Item-XX/` folder and re-run the assembler.

---

### `browse-docs.py` — Doc Browser & Cache

Browse and cache documents from both source locations independently:

```bash
# List all available docs (tree view)
python scripts/browse-docs.py --list
python scripts/browse-docs.py --list --project "Double-RR"
python scripts/browse-docs.py --list --manufacturer "Watts"

# Cache docs to .doc-cache/
python scripts/browse-docs.py --cache
python scripts/browse-docs.py --cache --manufacturer "Watts"
python scripts/browse-docs.py --cache --refresh   # re-copy even if already cached

# Show cache status
python scripts/browse-docs.py --status

# Open a document (tries cache first, then source)
python scripts/browse-docs.py --open "Watts/Cut Sheets/WATTS_LF25AUB_CutSheet.pdf"
```

---

### `assemble-submittal.py` — PDF Assembler

Merges all section PDFs into one final package (called automatically by the agent):

```bash
python scripts/assemble-submittal.py --project "Double-RR"
python scripts/assemble-submittal.py --project "Double-RR" --validate-only
```

---

## The Manifest CSV

`submittals/<project>/manifest.csv` tells the agent what to build.
Minimum required columns:

| Column | Example |
|--------|---------|
| `item_number` | `1` |
| `description` | `2-inch Pressure Reducing Valve` |
| `manufacturer` | `Watts` |
| `model_number` | `LF25AUB-Z3` |
| `spec_section` | `22 05 23` |

Optional override columns (leave blank to let the agent auto-match):
`cut_sheet_path`, `cert_nsf61_path`, `cert_nsf372_path`, `spec_pages_path`

---

## Projects

| Project | Submittal # | Status |
|---------|-------------|--------|
| Double RR | WW-001 | In Progress |

---

## Requirements

```bash
pip install pypdf fpdf2
```

Python 3.10+ recommended.