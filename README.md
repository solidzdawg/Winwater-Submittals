# Winwater Submittals

This repository manages professional submittal packages for Winwater projects.
It stores submittal templates, company standards documentation, and assembled
submittal packages organized by project.

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
│   └── Double-RR/                 # Double RR project submittal
│       ├── SUBMITTAL-PACKAGE.md   # Full assembled package manifest
│       ├── 01-cover/              # Cover sheet files
│       ├── 02-index/              # Item index files
│       ├── 03-items/              # Per-item folders (separator + product data)
│       └── 04-attachments/        # Disclaimers, certifications, spec pages
├── vendor-docs/                   # Vendor product data organized by manufacturer
└── scripts/                       # Assembly and automation scripts
    └── assemble-submittal.py      # Python script to assemble PDF packages
```

---

## Quick Start

### Assembling a New Submittal

1. Copy the templates from `templates/` to a new folder under `submittals/<project-name>/`
2. Fill in the cover sheet with project-specific information
3. Populate the item index with all submittal items
4. Add per-item product data to `03-items/`
5. Run the assembly script:
   ```bash
   python scripts/assemble-submittal.py --project "Double-RR"
   ```

### Adding Vendor Documentation

Place vendor spec sheets and certifications in `vendor-docs/<manufacturer>/`.
File-naming convention: `<ManufacturerAbbr>_<ModelNumber>_<DocType>.pdf`
Example: `XYLEM_LF122_CutSheet.pdf`, `XYLEM_LF122_NSFCert.pdf`

---

## Projects

| Project    | Status      | Submittal #  | Date       |
|------------|-------------|--------------|------------|
| Double RR  | In Progress | WW-2024-001  | 2024       |

---

## Contact

Winwater — Internal submittal management repository.