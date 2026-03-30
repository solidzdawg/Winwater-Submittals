# Part A — Company Submittal Standard

> **Source:** Derived from review of existing completed submittals on the company shared drive (Z:)
> and established industry best practices for water/mechanical systems contractors.

---

## 1. Overview

A Winwater submittal package is a compiled, bound PDF document sent to the engineer of record
(EOR) or general contractor for review and approval. Each submittal must demonstrate that the
proposed materials and equipment conform to the project specifications.

---

## 2. Typical Document Sequence

The standard Winwater submittal is assembled in the following fixed order:

| Position | Section                       | Description                                                   |
|----------|-------------------------------|---------------------------------------------------------------|
| 1        | **Cover Sheet**               | Project name, submittal number, date, contractor info, EOR    |
| 2        | **Item Index**                | Numbered list of all items included in the package            |
| 3        | **Item Sections** (repeating) | For each item: Separator → Product Data → Certs → Spec Pages  |
| 4        | **Attachments / Appendix**    | Standard disclaimer, BIM notes, LEED credits (if applicable)  |

Each item section follows this internal order:
1. Separator sheet (divider with item number, description, spec section)
2. Product data / cut sheet (manufacturer literature)
3. Compliance matrix or submittal form (if required by spec)
4. Certifications (NSF 61, NSF 372, UL listings, etc.)
5. Referenced specification pages (highlighted)

---

## 3. Required Sections

### 3.1 Cover Sheet
The cover sheet must include:
- **Company name and logo** (Winwater)
- **Project name** (e.g., "Double RR")
- **Project address / location**
- **Submittal number** — format: `WW-YYYY-###` (e.g., WW-2024-001)
- **Submittal title** (e.g., "Plumbing Equipment and Materials")
- **Spec section reference** (e.g., Section 22 00 00)
- **Date of submittal**
- **Submitted by** (Winwater PM name and signature block)
- **Submitted to** (GC name, EOR name)
- **Revision block** (Rev 0 = original; increment for resubmittals)
- **Status checkboxes**: □ For Review □ For Approval □ For Construction □ As-Built

### 3.2 Item Index
The item index is a numbered table listing every item in the package:

| Item # | Description             | Manufacturer     | Model / Part #   | Spec Section   | Page |
|--------|-------------------------|------------------|------------------|----------------|------|
| 1      | Pressure Reducing Valve | Watts             | LF25AUB-Z3       | 22 05 23       | 4    |
| 2      | ...                     | ...              | ...              | ...            | ...  |

Rules:
- Items are numbered sequentially (1, 2, 3 …)
- Each item occupies one row
- Page numbers reference the page within the submittal package
- Spec section numbers follow CSI MasterFormat

### 3.3 Item Separator Sheets
Each item begins with a full-page separator (tab divider) containing:
- **Item Number** (large, centered) — e.g., "ITEM 1"
- **Item Description** — short plain-English name
- **Manufacturer & Model**
- **Specification Section Reference**
- Winwater logo (footer or header)

Color convention (if printing):
- Blue separators = plumbing fixtures
- Yellow separators = mechanical equipment
- White separators = controls / electrical
- (Monochrome acceptable for digital submittals)

### 3.4 Product Data / Cut Sheets
- Attach the manufacturer's current published cut sheet (full sheet, not excerpts)
- Highlight or circle the specific model number and options selected
- Mark dimensions, ratings, and certifications relevant to the project
- Do **not** attach obsolete or superseded product data

### 3.5 Certifications
Required certifications (attach as applicable):
- **NSF/ANSI 61** — Drinking Water System Components (for any potable water products)
- **NSF/ANSI 372** — Lead-free compliance
- **UL / cUL listing** — Electrical/control components
- **IAPMO** — if applicable
- **ASSE** standards — per product type

### 3.6 Referenced Specification Pages
- Attach only the directly applicable spec pages (not the entire spec section)
- Highlight the relevant paragraphs in yellow
- Include spec section number in the page header

### 3.7 Disclaimer / Transmittal Cover
Standard language appended at end of all submittals:

> *The information contained in this submittal has been reviewed for general compliance with
> the project specifications. Final determination of compliance rests with the engineer of
> record. Winwater assumes no liability for approval or rejection. Shop drawings and submittals
> do not supersede contract documents.*

---

## 4. Formatting Conventions

| Element           | Convention                                                       |
|-------------------|------------------------------------------------------------------|
| Paper size        | 8.5" × 11" (letter); 11" × 17" for large drawings               |
| Orientation       | Portrait for most pages; landscape for schedules/drawings        |
| Margins           | 1" all sides (standard)                                          |
| Font              | Arial or Calibri, 10–12pt body, 14–16pt headers                 |
| Page numbering    | Consecutive throughout the entire package (not per section)      |
| Headers           | Project name + submittal number on every page (right-aligned)    |
| Footers           | Page X of Y + Winwater + date                                    |
| Revision block    | Located in header; lists Rev #, date, description of change      |

---

## 5. Naming Conventions

### File Naming (digital packages)
Format: `<ProjectCode>_SUB_<SubmittalNumber>_<Rev>_<Title>.pdf`

Examples:
- `DoubleRR_SUB_001_Rev0_PlumbingEquipment.pdf`
- `DoubleRR_SUB_001_Rev1_PlumbingEquipment.pdf`

### Individual Item Files (working files)
Format: `<ItemNum>_<Description>_<Manufacturer>_<Model>.pdf`

Examples:
- `01_PressureReducingValve_Watts_LF25AUB-Z3.pdf`
- `02_BackflowPreventer_Watts_909-QT.pdf`

### Vendor Documentation Files
Format: `<ManufacturerAbbr>_<ModelNumber>_<DocType>.pdf`

Examples:
- `WATTS_LF25AUB-Z3_CutSheet.pdf`
- `WATTS_LF25AUB-Z3_NSF61Cert.pdf`

---

## 6. How Product Documentation Is Organized

Vendor documentation is stored on the company Z: drive under:
```
Z:\Vendor Parts\
  ├── Watts\
  ├── Xylem\
  ├── Mueller\
  ├── Nibco\
  ├── Zurn\
  ├── Apollo\
  └── [Manufacturer]\
      ├── Cut Sheets\
      ├── Certifications\
      └── Installation Manuals\
```

For each item in a submittal:
1. Locate the manufacturer folder on Z:\Vendor Parts\
2. Find the appropriate cut sheet for the exact model number
3. Find associated certifications (NSF 61, NSF 372, UL, etc.)
4. Copy relevant pages to the project working folder
5. Highlight applicable model on cut sheet before inserting

---

## 7. Recurring Patterns Observed in Existing Submittals

- Every submittal opens with the cover sheet — no exceptions
- The item index always follows directly after the cover sheet
- Items are always separated by distinct separator/divider pages
- NSF certifications are always included for any product touching potable water
- Spec pages are always included for items with specific spec section callouts
- A standard disclaimer page is always the last page of the package
- Resubmittals include a revision summary table on the cover sheet
- Submittal numbers are never reused — resubmittals increment the revision letter

---

## 8. Typical Item Types in Winwater Submittals

Based on recurring items in past submittals:

| Category                 | Typical Products                                              |
|--------------------------|---------------------------------------------------------------|
| Pressure control         | PRVs, pressure gauges, pressure relief valves                 |
| Backflow prevention      | Double-check assemblies, RPZ assemblies, vacuum breakers      |
| Valves                   | Gate, ball, butterfly, check, solenoid                        |
| Meters / monitoring      | Flow meters, water meters, BTU meters                         |
| Piping / fittings        | Copper, PEX, HDPE, grooved fittings, flanges                  |
| Pumps                    | Booster pumps, circulation pumps, sump pumps                  |
| Water heaters            | Tank-type, tankless, heat pump                                |
| Specialty                | Mixing valves, trap primers, expansion tanks                  |
| Controls                 | Control panels, sensors, transmitters                         |
