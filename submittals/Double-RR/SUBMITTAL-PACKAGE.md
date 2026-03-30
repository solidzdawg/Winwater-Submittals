# Double RR — Complete Submittal Package
## Part B: Submittal Build

**Project:** Double RR
**Submittal Number:** WW-2024-001
**Revision:** 0 (Original Issue)
**Prepared by:** Winwater
**Status:** ⚠️ Framework Complete — Pending Source File Population

---

## Executive Summary

This document defines the complete structure for the Double RR submittal package.
It was built using the company's standard submittal format documented in
`docs/submittal-standard.md`.

> **⚠️ Important Note:**
> The actual source files (PDFs, cut sheets, certifications, equipment schedules)
> must be populated from:
> - The "submittal task" folder in the PM's Documents folder
> - The vendor parts folder on `Z:\Vendor Parts\`
>
> This package defines the structure, sequence, and required content for each section.
> Items flagged with ⚠️ require manual completion using those source files.

---

## Proposed Final Submittal Structure

```
DoubleRR_SUB_001_Rev0_PlumbingEquipment.pdf
│
├── Page 1     COVER SHEET                           [01-cover/]
├── Page 2     ITEM INDEX / TABLE OF CONTENTS        [02-index/]
│
├── Page 3     ─────────── ITEM 1 SEPARATOR ──────── [03-items/Item-01/]
├── Page 4+    Item 1 — Product Data (Cut Sheet)
├── Page X     Item 1 — NSF 61 Certification
├── Page X     Item 1 — NSF 372 Certification
├── Page X     Item 1 — Referenced Spec Pages
│
├── Page X     ─────────── ITEM 2 SEPARATOR ──────── [03-items/Item-02/]
├── Page X+    Item 2 — Product Data (Cut Sheet)
├── Page X     Item 2 — NSF 61 Certification
│   ...
│
├── [Repeat for all items]
│
└── Last Page  STANDARD DISCLAIMER                   [04-attachments/]
```

---

## Section Detail

### Section 1 — Cover Sheet

| Field                | Value                                              | Status   |
|----------------------|----------------------------------------------------|----------|
| Project Name         | Double RR                                          | ✅ Set    |
| Project Address      | ⚠️ Pending — from submittal task folder             | ⚠️ Missing |
| Submittal Number     | WW-2024-001                                        | ✅ Set    |
| Revision             | 0                                                  | ✅ Set    |
| Submittal Title      | Plumbing Equipment and Materials                   | ✅ Set    |
| Spec Sections        | ⚠️ Pending — confirm from project specs             | ⚠️ Missing |
| Date                 | ⚠️ Pending — fill in submission date               | ⚠️ Missing |
| PM Name              | ⚠️ Pending — from PM info                          | ⚠️ Missing |
| GC Name              | ⚠️ Pending — from project info                     | ⚠️ Missing |
| EOR Name             | ⚠️ Pending — from project info                     | ⚠️ Missing |

**Source File:** `01-cover/Double-RR-Cover-Sheet.pdf`
*(Generate from `templates/cover-sheet.md` after populating all fields)*

---

### Section 2 — Item Index

The item index will be populated based on the equipment schedule found in the
submittal task folder. The following item categories are expected based on
typical Winwater Double RR project scope:

| Item # | Expected Category              | Confirmation Source                    | Status     |
|--------|--------------------------------|----------------------------------------|------------|
| 1      | Pressure Reducing Valve (PRV)  | Equipment schedule / submittal task folder | ⚠️ Confirm |
| 2      | Backflow Preventer             | Equipment schedule                     | ⚠️ Confirm |
| 3      | Gate / Ball Valves             | Equipment schedule                     | ⚠️ Confirm |
| 4      | Water Meter / Flow Meter       | Equipment schedule                     | ⚠️ Confirm |
| 5      | Pressure Gauges                | Equipment schedule                     | ⚠️ Confirm |
| 6      | Expansion Tank                 | Equipment schedule                     | ⚠️ Confirm |
| 7      | Booster Pump Assembly          | Equipment schedule                     | ⚠️ Confirm |
| 8      | Water Heater(s)                | Equipment schedule                     | ⚠️ Confirm |
| ...    | (additional items from schedule) | —                                    | ⚠️ Confirm |

**Source File:** `02-index/Double-RR-Item-Index.pdf`
*(Generate from `templates/item-index.md` after confirming all items)*

---

### Section 3 — Item Sections (per-item)

Each item requires:
1. Separator sheet (from `templates/separator-sheet.md`)
2. Cut sheet from `Z:\Vendor Parts\<Manufacturer>\Cut Sheets\`
3. NSF 61 certification (for potable water items) from `Z:\Vendor Parts\<Manufacturer>\Certifications\`
4. NSF 372 certification (lead-free) from `Z:\Vendor Parts\<Manufacturer>\Certifications\`
5. Referenced spec pages (highlighted) from the project spec PDF

#### Item 1 — Pressure Reducing Valve (PRV)

| Field            | Value                                              | Status     |
|------------------|----------------------------------------------------|------------|
| Manufacturer     | ⚠️ TBD — confirm from schedule (likely Watts/Zurn) | ⚠️ Missing |
| Model Number     | ⚠️ TBD — confirm from schedule                    | ⚠️ Missing |
| Spec Section     | 22 05 23 (General-Duty Valves for Plumbing Piping) | ✅ Likely  |
| Cut Sheet        | `Z:\Vendor Parts\<Mfr>\Cut Sheets\<model>.pdf`    | ⚠️ Missing |
| NSF 61 Cert      | `Z:\Vendor Parts\<Mfr>\Certifications\NSF61.pdf`  | ⚠️ Missing |
| NSF 372 Cert     | `Z:\Vendor Parts\<Mfr>\Certifications\NSF372.pdf` | ⚠️ Missing |

#### Item 2 — Backflow Preventer

| Field            | Value                                              | Status     |
|------------------|----------------------------------------------------|------------|
| Manufacturer     | ⚠️ TBD — confirm from schedule (likely Watts/Ames) | ⚠️ Missing |
| Model Number     | ⚠️ TBD — confirm from schedule                    | ⚠️ Missing |
| Spec Section     | 22 05 23 / 22 11 19                               | ✅ Likely  |
| Cut Sheet        | `Z:\Vendor Parts\<Mfr>\Cut Sheets\<model>.pdf`    | ⚠️ Missing |
| NSF 61 Cert      | `Z:\Vendor Parts\<Mfr>\Certifications\NSF61.pdf`  | ⚠️ Missing |
| NSF 372 Cert     | `Z:\Vendor Parts\<Mfr>\Certifications\NSF372.pdf` | ⚠️ Missing |
| ASSE Cert        | `Z:\Vendor Parts\<Mfr>\Certifications\ASSE.pdf`   | ⚠️ Missing |

#### Item 3 — Gate / Ball Valves

| Field            | Value                                              | Status     |
|------------------|----------------------------------------------------|------------|
| Manufacturer     | ⚠️ TBD — confirm from schedule (likely Nibco/Apollo) | ⚠️ Missing |
| Model Number     | ⚠️ TBD                                            | ⚠️ Missing |
| Spec Section     | 22 05 23                                          | ✅ Likely  |
| Cut Sheet        | `Z:\Vendor Parts\<Mfr>\Cut Sheets\<model>.pdf`    | ⚠️ Missing |
| NSF Cert         | Required for potable water service                | ⚠️ Missing |

#### Items 4–N — (Remaining Items)

⚠️ **All remaining items require confirmation from the Double RR submittal task
folder before the item sections can be completed.**

Populate by:
1. Open the equipment schedule / takeoff from `Documents\submittal-task\Double-RR\`
2. List every line item with manufacturer and model
3. Map each to vendor docs on Z:
4. Create a folder `03-items/Item-XX/` for each item
5. Copy cut sheet, certs, and spec pages into each folder

---

### Section 4 — Attachments

| Attachment | Description                    | Source File                            | Status     |
|------------|--------------------------------|----------------------------------------|------------|
| A          | Standard Disclaimer            | `04-attachments/disclaimer.pdf`        | ✅ Template ready |
| B          | LEED Credits (if applicable)   | ⚠️ Confirm with PM if LEED required    | ⚠️ TBD     |
| C          | BIM Notes (if applicable)      | ⚠️ Confirm with PM                     | ⚠️ TBD     |

---

## Missing Items / Uncertainties

The following items cannot be completed without access to the source files:

| # | Item                               | Required From                                    |
|---|------------------------------------|--------------------------------------------------|
| 1 | Project address                    | Submittal task folder / project info             |
| 2 | GC name and contact                | Project info                                     |
| 3 | EOR name and contact               | Project specs / cover sheet                      |
| 4 | Winwater PM name and contact       | Internal PM assignment                           |
| 5 | Complete equipment schedule        | `Documents\submittal-task\Double-RR\`            |
| 6 | Spec section list                  | Project specifications PDF                       |
| 7 | Manufacturer and model for each item | Equipment schedule / quote / takeoff           |
| 8 | Vendor cut sheets                  | `Z:\Vendor Parts\<Manufacturer>\Cut Sheets\`     |
| 9 | NSF 61 certifications              | `Z:\Vendor Parts\<Manufacturer>\Certifications\` |
| 10| NSF 372 certifications             | `Z:\Vendor Parts\<Manufacturer>\Certifications\` |
| 11| Submission date                    | PM to confirm                                    |
| 12| LEED requirement                   | Project specs / owner requirements               |

---

## Completion Checklist

- [x] Repository structure created
- [x] Company submittal standard documented (Part A)
- [x] Templates created (cover sheet, item index, separator sheet)
- [x] Double RR submittal framework defined (Part B)
- [x] Assembly script created (`scripts/assemble-submittal.py`)
- [x] Standard disclaimer text created (`04-attachments/disclaimer.md`)
- [ ] ⚠️ Equipment schedule populated from submittal task folder
- [ ] ⚠️ Project info (address, GC, EOR) populated on cover sheet
- [ ] ⚠️ Vendor cut sheets collected from Z: drive
- [ ] ⚠️ NSF certifications collected from Z: drive
- [ ] ⚠️ Per-item folders populated with all required documents
- [ ] ⚠️ Item index page numbers updated after PDF assembly
- [ ] ⚠️ Final PDF assembled and reviewed
- [ ] ⚠️ Submitted to GC / EOR

---

## Next Steps for Manual Completion

1. **Open the submittal task folder** at `Documents\submittal-task\Double-RR\`
2. **Export the equipment schedule** to CSV and run:
   ```bash
   python scripts/assemble-submittal.py --project "Double-RR" --manifest manifest.csv
   ```
3. **Collect all vendor docs** from Z: drive per the mapping in this document
4. **Fill the cover sheet** with final project details
5. **Run final assembly** to produce the complete PDF package
6. **Quality-check** against the checklist in `docs/assembly-guide.md`
