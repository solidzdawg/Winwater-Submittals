# Winwater Submittal Format Standard

## Part A — Company Standard

This document defines the required format, sequence, and content for all
Winwater plumbing equipment submittals.

---

## 1. Purpose

A submittal package communicates to the Engineer of Record (EOR) that proposed
materials and equipment meet the contract specifications. Every item on the
plumbing equipment schedule requires documentation before procurement.

---

## 2. Required Document Sequence

Each submittal package shall be assembled in the following order:

| Position | Section | Contents |
|----------|---------|----------|
| 1 | Cover Sheet | Project name, submittal number, date, revision, preparer, contractor |
| 2 | Item Index | Table listing all items with page numbers |
| 3 | Items (per item) | Separator sheet → Cut sheet → NSF certs → Spec pages |
| 4 | Attachments | Disclaimer / transmittal, LEED docs, other general attachments |

---

## 3. Per-Item Package Contents

For each item on the equipment schedule, include **in this order**:

1. **Separator Sheet** — identifies the item number, description, manufacturer, model, and spec section
2. **Cut Sheet / Product Data Sheet** — manufacturer's technical data; highlight the applicable model number
3. **NSF 61 Certification** — required for all potable water contact products
4. **NSF 372 Certification** — required for low-lead compliance (if applicable)
5. **Other Certifications** — ASSE listings, UL listings, IAPMO listings as required by spec
6. **Specification Pages** — relevant pages from the project spec, with applicable paragraphs highlighted

---

## 4. Cover Sheet Requirements

The cover sheet shall include:
- Company name (WINWATER)
- Project name and address
- Submittal number (format: `WW-YYYY-NNN`)
- Date and revision number
- Prepared by (name and title)
- Contractor name
- Engineer / EOR name and firm
- Specification sections covered
- Summary list of all items

---

## 5. Naming Conventions

### Submittal Package PDF
```
<ProjectCode>_SUB_<NNN>_Rev<R>_PlumbingEquipment.pdf
```
Example: `DoubleRR_SUB_001_Rev0_PlumbingEquipment.pdf`

### Vendor Doc Files
```
<MfrAbbr>_<ModelNumber>_<DocType>.pdf
```
Examples:
- `WATTS_LF25AUB_CutSheet.pdf`
- `WATTS_LF25AUB_NSF61.pdf`
- `NIBCO_T113_CutSheet.pdf`

---

## 6. Z: Drive Vendor Parts Structure

All vendor documents are stored on the company Z: drive:

```
Z:\Vendor Parts\
  ├── Watts\
  │   ├── Cut Sheets\
  │   ├── Certifications\
  │   └── Installation Manuals\
  ├── Xylem\
  ├── Nibco\
  ├── Mueller\
  ├── Zurn\
  ├── Apollo\
  ├── Grundfos\
  ├── AO Smith\
  ├── Amtrol\
  ├── Sensus\
  └── [Manufacturer]\
      ├── Cut Sheets\
      ├── Certifications\
      └── Installation Manuals\
```

---

## 7. Project Submittal Task Folder

Each project has a task folder on the submitter's local machine:

```
~/Documents/submittal-task/
  └── <ProjectName>/
      ├── equipment-schedule.xlsx    ← source of truth for all items
      ├── manifest.csv               ← agent-readable version of schedule
      ├── spec-sections/             ← relevant specification PDFs
      └── misc/                      ← engineer letters, RFIs, etc.
```

---

## 8. Common Item Types

| Item Type | Typical Manufacturers | NSF 61 | NSF 372 |
|-----------|----------------------|--------|---------|
| Pressure Reducing Valve (PRV) | Watts, Zurn, Honeywell | ✅ | ✅ |
| Backflow Preventer (DCVA / RP) | Watts, Ames, Wilkins | ✅ | ✅ |
| Gate Valve | Nibco, Mueller, Hammond | ✅ | ✅ |
| Ball Valve | Apollo, Nibco, Milwaukee | ✅ | ✅ |
| Y-Strainer | Mueller, Watts, Keckley | ✅ | ✅ |
| Water Meter | Sensus, Badger, Neptune | ✅ | — |
| Expansion Tank | Amtrol, Watts, Extrol | — | — |
| Circulating Pump | Grundfos, Bell & Gossett | — | — |
| Water Heater | A.O. Smith, Rheem, Lochinvar | ✅ | — |
| Electronic Controls | Siemens, Honeywell, Belimo | — | — |

---

## 9. Formatting Requirements

- Paper size: 8.5" × 11" (letter)
- Margins: 1" all sides
- Font: Helvetica or Arial, 10pt body
- Page numbers: bottom center, format `Page N`
- All PDFs must be text-searchable (not scanned images)
- File size: keep under 25 MB for email transmittal

---

## 10. Revision Control

| Revision | Description |
|----------|-------------|
| Rev 0 | Initial submittal |
| Rev 1 | Resubmittal per engineer's comments |
| Rev 2 | Second resubmittal |

Always increment the revision number and resubmit the **complete** package.
