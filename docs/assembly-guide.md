# Submittal Assembly Guide

This guide describes the step-by-step process for assembling a complete Winwater
submittal package from source files.

---

## Prerequisites

- Python 3.8+ (for the assembly script)
- `pypdf` library: `pip install pypdf`
- Access to Z: drive (vendor parts folder)
- Project submittal task folder (from submitter's Documents)

---

## Step 1 — Gather Source Files

### From the Project Submittal Task Folder
Locate the project folder in `Documents\submittal-task\<ProjectName>\` and collect:
- [ ] Equipment schedule or item list (Excel / CSV)
- [ ] Project specifications (relevant sections, PDF)
- [ ] Any pre-filled submittal forms
- [ ] Engineer's submittal requirements letter (if provided)

### From Z: Drive — Vendor Parts
For each item on the equipment schedule:
1. Open `Z:\Vendor Parts\<Manufacturer>\Cut Sheets\`
2. Locate the correct model number cut sheet
3. Open `Z:\Vendor Parts\<Manufacturer>\Certifications\`
4. Locate NSF 61, NSF 372, and any other required certs

---

## Step 2 — Create the Project Folder

```
submittals/<ProjectName>/
├── 01-cover/
│   └── cover-sheet.pdf          ← fill in template
├── 02-index/
│   └── item-index.pdf           ← generated from equipment schedule
├── 03-items/
│   ├── Item-01/
│   │   ├── separator.pdf
│   │   ├── cutsheet.pdf
│   │   └── cert-NSF61.pdf
│   ├── Item-02/
│   │   └── ...
└── 04-attachments/
    └── disclaimer.pdf
```

---

## Step 3 — Fill the Cover Sheet

Open `templates/cover-sheet.md` and substitute all `{{ }}` placeholders with
project-specific values. Convert to PDF or fill in the Word/InDesign version.

---

## Step 4 — Build the Item Index

Open `templates/item-index.md` and add one row per submittal item.
Assign sequential item numbers starting at 1.

---

## Step 5 — Prepare Each Item Package

For each item:
1. Copy `templates/separator-sheet.md` to `03-items/Item-XX/separator.md`
2. Fill in item number, description, manufacturer, model, spec section
3. Attach cut sheet PDF (highlight model number)
4. Attach certification PDFs
5. Attach relevant spec pages (highlighted)

---

## Step 6 — Run the Assembly Script

```bash
cd Winwater-Submittals
python scripts/assemble-submittal.py \
  --project "Double-RR" \
  --output "DoubleRR_SUB_001_Rev0_PlumbingEquipment.pdf"
```

The script will:
- Merge all PDFs in the correct order
- Add page numbers to the footer
- Generate a final package PDF

---

## Step 7 — Quality Check

Before sending:
- [ ] Cover sheet has correct project name, submittal number, date, revision
- [ ] Item index page numbers match actual pages in the package
- [ ] Every item has a separator sheet
- [ ] Cut sheets show highlighted model numbers
- [ ] NSF certifications present for all potable water products
- [ ] Disclaimer page is last
- [ ] File is named per naming convention
- [ ] PDF is bookmarked (one bookmark per item)
- [ ] Total page count matches item index

---

## Step 8 — Transmit

Upload to project management platform (Procore, e-Builder, etc.) or email
to the GC submittal coordinator. Save a copy to:
```
Z:\Projects\<ProjectName>\Submittals\Submitted\
```

Log the submittal in the project submittal log.
