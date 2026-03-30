# Winwater Submittals

This repository manages professional submittal packages for Winwater projects.
It stores submittal templates, company standards documentation, and assembled
submittal packages organized by project — with an autonomous agent pipeline
for building, validating, and quality-checking submittals.

---

## Repository Structure

```
Winwater-Submittals/
├── docs/                          # Company standards and reference documents
│   ├── submittal-standard.md      # Company submittal format standard (Part A)
│   └── assembly-guide.md          # Step-by-step assembly instructions
├── templates/                     # Reusable template files
│   ├── cover-sheet.md             # Cover sheet template
│   ├── item-index.md              # Item index / table of contents template
│   └── separator-sheet.md         # Section separator sheet template
├── submittals/                    # Completed submittal packages by project
│   └── Double-RR/                 # Double RR project submittal (20 items, 8 sections)
│       ├── SUBMITTAL-PACKAGE.md   # Full package definition and status
│       ├── manifest.csv           # Item manifest (drives all automation)
│       ├── 01-cover/              # Cover sheet
│       ├── 02-index/              # Item index / table of contents
│       ├── 03-items/              # Per-item folders (Item-01 through Item-20)
│       └── 04-attachments/        # Disclaimer
├── vendor-docs/                   # Vendor product data organized by manufacturer
└── scripts/                       # Assembly and automation scripts
    ├── assemble-submittal.py      # PDF assembly with bookmarks
    ├── orchestrator.py            # Autonomous pipeline orchestrator
    └── agents/                    # Specialized agent modules
        ├── validate_agent.py      # Structure & manifest validation
        ├── separator_agent.py     # Auto-generate separator sheets from manifest
        ├── vendor_fetch_agent.py  # Audit vendor files, create missing dirs
        └── qc_agent.py            # Quality-control checks & scoring
```

---

## Quick Start

### Full Autonomous Run (Recommended)

Run the orchestrator to validate, generate separators, audit vendor files,
QC check, and assemble — all in one command:

```bash
python scripts/orchestrator.py --project "Double-RR"
```

### Run Individual Steps

```bash
# Validate project structure
python scripts/orchestrator.py --project "Double-RR" --step validate

# Generate separator sheets from manifest.csv
python scripts/orchestrator.py --project "Double-RR" --step separators

# Audit which vendor PDFs are missing
python scripts/orchestrator.py --project "Double-RR" --step vendor-audit

# Run QC checks
python scripts/orchestrator.py --project "Double-RR" --step qc

# Assemble final PDF
python scripts/orchestrator.py --project "Double-RR" --step assemble
```

### Manual Assembly Only

```bash
python scripts/assemble-submittal.py --project "Double-RR"
```

---

## Agent Pipeline

The orchestrator chains four specialized agents:

| Step | Agent              | What it does                                                  |
|------|--------------------|---------------------------------------------------------------|
| 1    | Validate Agent     | Checks directories, manifest fields, separator existence      |
| 2    | Separator Agent    | Generates separator.md for each item from manifest + template |
| 3    | Vendor Fetch Agent | Audits vendor-docs/ for missing cut sheets and certs          |
| 4    | QC Agent           | Scores completeness: cover, index, naming, CSI format, etc.   |
| 5    | Assembly           | Merges all PDFs with bookmarks into the final submittal       |

### Adding a New Project

1. Create `submittals/<ProjectName>/` with the standard directory structure
2. Populate `manifest.csv` with your item list
3. Run `python scripts/orchestrator.py --project "<ProjectName>"`
4. Place vendor PDFs in the item folders flagged by the vendor audit
5. Re-run to assemble the final PDF

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

---

## Projects

| Project    | Status                      | Submittal # | Items | Sections |
|------------|-----------------------------|-------------|-------|----------|
| Double RR  | Structure Complete — Needs PDFs | WW-2024-001 | 20    | 8 (A–H)  |

---

## Contact

Winwater — Internal submittal management repository.