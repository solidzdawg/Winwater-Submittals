# Double RR — Complete Submittal Package
## Part B: Submittal Build

**Project:** Double RR
**Submittal Number:** WW-2024-001
**Revision:** 0 (Original Issue)
**Prepared by:** Winwater
**Status:** ✅ Package Structure Complete — Pending Vendor PDF Population

---

## Executive Summary

This document defines the complete structure for the Double RR submittal package.
It was built using the company's standard submittal format documented in
`docs/submittal-standard.md`.

The package contains **20 items** organized into **8 sections** (A–H) covering
all plumbing equipment and materials per CSI Division 22. All separator sheets,
cover page, and item index have been populated. Vendor cut sheets and
certifications must be placed into each item folder before final PDF assembly.

> **Remaining Steps:**
> - Place vendor PDFs (cut sheets + certs) into each `03-items/Item-XX/` folder
> - Confirm project address, PM, GC, and EOR details on cover sheet
> - Run `python scripts/assemble-submittal.py --project "Double-RR"` to build final PDF

---

## Final Submittal Structure

```
DoubleRR_SUB_001_Rev0_PlumbingEquipment.pdf
│
├── Page 1      COVER SHEET                                  [01-cover/]
├── Page 2      ITEM INDEX / TABLE OF CONTENTS               [02-index/]
│
│  ── SECTION A — PRESSURE REGULATION ──────────────────────────────────
├── Page 3      Item 01 Separator — PRV 2" Flanged           [03-items/Item-01/]
├── Page 4+     Cut Sheet · NSF 61 · NSF 372
├── Page X      Item 02 Separator — PRV 3/4" Threaded        [03-items/Item-02/]
├── Page X+     Cut Sheet · NSF 61 · NSF 372
│
│  ── SECTION B — BACKFLOW PREVENTION ──────────────────────────────────
├── Page X      Item 03 Separator — RPZ 2"                   [03-items/Item-03/]
├── Page X+     Cut Sheet · NSF 61 · NSF 372 · ASSE 1013
├── Page X      Item 04 Separator — DCVA 1"                  [03-items/Item-04/]
├── Page X+     Cut Sheet · NSF 61 · NSF 372 · ASSE 1015
│
│  ── SECTION C — VALVES ───────────────────────────────────────────────
├── Page X      Item 05 Separator — Ball Valve 2"            [03-items/Item-05/]
├── Page X+     Cut Sheet · NSF 372
├── Page X      Item 06 Separator — Ball Valve 3/4"          [03-items/Item-06/]
├── Page X+     Cut Sheet · NSF 372
├── Page X      Item 07 Separator — Butterfly Valve 4"       [03-items/Item-07/]
├── Page X+     Cut Sheet
├── Page X      Item 08 Separator — Silent Check 2"          [03-items/Item-08/]
├── Page X+     Cut Sheet · NSF 61 · NSF 372
│
│  ── SECTION D — METERING & INSTRUMENTATION ───────────────────────────
├── Page X      Item 09 Separator — Water Meter 2"           [03-items/Item-09/]
├── Page X+     Cut Sheet
├── Page X      Item 10 Separator — Pressure Gauge           [03-items/Item-10/]
├── Page X+     Cut Sheet
│
│  ── SECTION E — PUMPS ────────────────────────────────────────────────
├── Page X      Item 11 Separator — Booster Pump System      [03-items/Item-11/]
├── Page X+     Cut Sheet · UL
├── Page X      Item 12 Separator — Recirc Pump              [03-items/Item-12/]
├── Page X+     Cut Sheet · UL
│
│  ── SECTION F — DOMESTIC HOT WATER ───────────────────────────────────
├── Page X      Item 13 Separator — Water Heater 100 Gal     [03-items/Item-13/]
├── Page X+     Cut Sheet · NSF 61 · AHRI
├── Page X      Item 14 Separator — TMV 2"                   [03-items/Item-14/]
├── Page X+     Cut Sheet · NSF 61 · NSF 372 · ASSE 1017
├── Page X      Item 15 Separator — Expansion Tank 40 Gal    [03-items/Item-15/]
├── Page X+     Cut Sheet · NSF 61
├── Page X      Item 16 Separator — T&P Relief Valve         [03-items/Item-16/]
├── Page X+     Cut Sheet · NSF 61 · NSF 372
│
│  ── SECTION G — DRAINAGE & SPECIALTIES ───────────────────────────────
├── Page X      Item 17 Separator — Floor Drain 12"          [03-items/Item-17/]
├── Page X+     Cut Sheet
├── Page X      Item 18 Separator — Hose Bibb 3/4"          [03-items/Item-18/]
├── Page X+     Cut Sheet
│
│  ── SECTION H — SAFETY & INSULATION ─────────────────────────────────
├── Page X      Item 19 Separator — Emergency TMV            [03-items/Item-19/]
├── Page X+     Cut Sheet · NSF 61 · NSF 372 · ASSE 1071
├── Page X      Item 20 Separator — Pipe Insulation          [03-items/Item-20/]
├── Page X+     Cut Sheet
│
└── Last Page   STANDARD DISCLAIMER                          [04-attachments/]
```

---

## Section Detail

### Section 1 — Cover Sheet

| Field                | Value                                              | Status     |
|----------------------|----------------------------------------------------|------------|
| Project Name         | Double RR                                          | ✅ Set      |
| Project Address      | [TO BE CONFIRMED]                                  | ⚠️ Pending  |
| Submittal Number     | WW-2024-001                                        | ✅ Set      |
| Revision             | 0                                                  | ✅ Set      |
| Submittal Title      | Plumbing Equipment and Materials                   | ✅ Set      |
| Spec Sections        | 22 05 19, 22 05 23, 22 05 29, 22 07 19, 22 11 19, 22 11 23, 22 34 00, 22 40 00, 22 42 00 | ✅ Set |
| Date                 | [TO BE FILLED AT SUBMISSION]                       | ⚠️ Pending  |
| PM / GC / EOR        | [TO BE CONFIRMED]                                 | ⚠️ Pending  |

**Source File:** `01-cover/cover-sheet.md` → generate PDF

---

### Section 2 — Item Index

The item index contains all 20 items organized by section (A–H).
**Source File:** `02-index/item-index.md` → generate PDF

---

### Section 3 — Item Sections (03-items/)

Each item folder contains:
1. **Separator sheet** (`separator.md`) — ✅ Created for all 20 items
2. **Cut sheet** — vendor product data PDF (from `vendor-docs/` or `Z:\Vendor Parts\`)
3. **NSF 61 cert** — where applicable (potable water contact)
4. **NSF 372 cert** — where applicable (lead-free compliance)
5. **Other certs** — ASSE, UL, AHRI as required per item
6. **Referenced spec pages** — highlighted pages from project specification

---

#### Section A — Pressure Regulation

| Item | Description                      | Manufacturer | Model          | Spec     | Separator | Cut Sheet | Certs Needed           |
|------|----------------------------------|-------------|----------------|----------|-----------|-----------|------------------------|
| 01   | PRV — 2" Flanged                 | Watts       | LF25AUB-GG-Z3 | 22 05 23 | ✅         | ⬜         | NSF 61, NSF 372        |
| 02   | PRV — 3/4" Threaded              | Watts       | LF25AUB-Z3    | 22 05 23 | ✅         | ⬜         | NSF 61, NSF 372        |

#### Section B — Backflow Prevention

| Item | Description                      | Manufacturer | Model          | Spec     | Separator | Cut Sheet | Certs Needed           |
|------|----------------------------------|-------------|----------------|----------|-----------|-----------|------------------------|
| 03   | RPZ Backflow — 2"                | Watts       | LF909-QT       | 22 05 29 | ✅         | ⬜         | NSF 61, NSF 372, ASSE 1013 |
| 04   | DCVA — 1"                        | Watts       | LF007M1-QT    | 22 05 29 | ✅         | ⬜         | NSF 61, NSF 372, ASSE 1015 |

#### Section C — Valves

| Item | Description                      | Manufacturer | Model          | Spec     | Separator | Cut Sheet | Certs Needed           |
|------|----------------------------------|-------------|----------------|----------|-----------|-----------|------------------------|
| 05   | Ball Valve — 2" Full Port        | Apollo      | 94ALF-200      | 22 05 23 | ✅         | ⬜         | NSF 372                |
| 06   | Ball Valve — 3/4" Full Port      | Apollo      | 94ALF-100      | 22 05 23 | ✅         | ⬜         | NSF 372                |
| 07   | Butterfly Valve — 4" Lug         | Nibco       | LD-3010        | 22 05 23 | ✅         | ⬜         | —                      |
| 08   | Silent Check Valve — 2"          | Watts       | LF2000B        | 22 05 23 | ✅         | ⬜         | NSF 61, NSF 372        |

#### Section D — Metering & Instrumentation

| Item | Description                      | Manufacturer   | Model               | Spec     | Separator | Cut Sheet | Certs Needed    |
|------|----------------------------------|---------------|-------------------  |----------|-----------|-----------|-----------------|
| 09   | Water Meter — 2" Turbine         | Badger Meter  | Recordall Turbo 250 | 22 05 19 | ✅         | ⬜         | —               |
| 10   | Pressure Gauge — 4-1/2" LF       | Watts         | LFDPG1              | 22 05 23 | ✅         | ⬜         | —               |

#### Section E — Pumps

| Item | Description                      | Manufacturer         | Model              | Spec     | Separator | Cut Sheet | Certs Needed |
|------|----------------------------------|---------------------|--------------------|----------|-----------|-----------|--------------|
| 11   | Booster Pump System              | Xylem / Bell & Gossett | e-HM Technologic | 22 11 19 | ✅         | ⬜         | UL           |
| 12   | Inline Circulator — HW Return    | Xylem / Bell & Gossett | Ecocirc XL 20-35 | 22 11 23 | ✅         | ⬜         | UL           |

#### Section F — Domestic Hot Water

| Item | Description                      | Manufacturer | Model          | Spec     | Separator | Cut Sheet | Certs Needed           |
|------|----------------------------------|-------------|----------------|----------|-----------|-----------|------------------------|
| 13   | Water Heater — 100 Gal Gas       | A.O. Smith  | BTH-500A       | 22 34 00 | ✅         | ⬜         | NSF 61, AHRI           |
| 14   | TMV — 2"                         | Watts       | LFL111-3       | 22 34 00 | ✅         | ⬜         | NSF 61, NSF 372, ASSE 1017 |
| 15   | Expansion Tank — 40 Gal          | Watts       | PLT-40         | 22 05 23 | ✅         | ⬜         | NSF 61                 |
| 16   | T&P Relief Valve                 | Watts       | LF100XL        | 22 34 00 | ✅         | ⬜         | NSF 61, NSF 372        |

#### Section G — Drainage & Specialties

| Item | Description                      | Manufacturer | Model          | Spec     | Separator | Cut Sheet | Certs Needed |
|------|----------------------------------|-------------|----------------|----------|-----------|-----------|--------------|
| 17   | Floor Drain — 12" Cast Iron      | Zurn        | ZN415-12       | 22 05 23 | ✅         | ⬜         | —            |
| 18   | Hose Bibb — 3/4" Freeze-Resist   | Zurn        | Z1365-3/4      | 22 40 00 | ✅         | ⬜         | —            |

#### Section H — Safety & Insulation

| Item | Description                      | Manufacturer      | Model           | Spec     | Separator | Cut Sheet | Certs Needed           |
|------|----------------------------------|-------------------|-----------------|----------|-----------|-----------|------------------------|
| 19   | Emergency TMV                    | Watts             | LF1170M2-US     | 22 42 00 | ✅         | ⬜         | NSF 61, NSF 372, ASSE 1071 |
| 20   | Pipe Insulation — Fiberglass/ASJ | Johns Manville    | Micro-Lok HP    | 22 07 19 | ✅         | ⬜         | —            |
4. Create a folder `03-items/Item-XX/` for each item
5. Copy cut sheet, certs, and spec pages into each folder

---

### Section 4 — Attachments

| Attachment | Description         | Source File                     | Status    |
|------------|---------------------|---------------------------------|-----------|
| A          | Standard Disclaimer | `04-attachments/disclaimer.md`  | ✅ Ready   |

---

## Remaining Items Before Final Assembly

| # | Item                              | Action Required                             |
|---|-----------------------------------|---------------------------------------------|
| 1 | Project address                   | Confirm from PM / submittal task folder     |
| 2 | GC name and contact               | Confirm from project info                   |
| 3 | EOR name and contact              | Confirm from project specs                  |
| 4 | Winwater PM name and contact      | Confirm internal PM assignment              |
| 5 | Submission date                   | Fill at time of transmittal                 |
| 6 | Vendor cut sheets (20 items)      | Copy from `Z:\Vendor Parts\` into item folders |
| 7 | NSF / ASSE / UL / AHRI certs     | Copy from `Z:\Vendor Parts\` per manifest   |
| 8 | Referenced spec pages             | Extract and highlight from project spec PDF |

---

## Completion Checklist

- [x] Repository structure created
- [x] Company submittal standard documented (Part A)
- [x] Templates created (cover sheet, item index, separator sheet)
- [x] Double RR submittal framework defined (Part B)
- [x] Assembly script created (`scripts/assemble-submittal.py`)
- [x] Standard disclaimer text created
- [x] Equipment schedule populated — 20 items in manifest.csv
- [x] Spec sections identified (9 sections across Div. 22)
- [x] Cover sheet populated with spec sections and contents summary
- [x] Item index populated with 20 items in 8 sections (A–H)
- [x] All 20 separator sheets created with product detail
- [ ] Project info (address, GC, EOR) confirmed on cover sheet
- [ ] Vendor cut sheets placed in item folders
- [ ] Certifications placed in item folders
- [ ] Referenced spec pages extracted and highlighted
- [ ] Item index page numbers updated after PDF assembly
- [ ] Final PDF assembled and QC reviewed
- [ ] Submitted to GC / EOR

---

## Assembly Instructions

```bash
# 1. Confirm all vendor PDFs are placed in each Item-XX folder
# 2. Update cover sheet with project details
# 3. Run assembly script:
python scripts/assemble-submittal.py --project "Double-RR" --manifest manifest.csv

# 4. QC the output PDF per docs/assembly-guide.md
# 5. Transmit to GC / EOR
```
