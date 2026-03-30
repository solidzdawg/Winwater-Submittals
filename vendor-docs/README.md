# Vendor Docs

This directory stores vendor product data organized by manufacturer.
Files here are committed to the repository when they are small reference
documents. Larger PDF libraries live on the Z: drive and are pulled into
the local cache by `browse-docs.py` or `agent.py`.

---

## Directory Structure

```
vendor-docs/
  └── <Manufacturer>/
      ├── Cut-Sheets/
      │   └── <MfrAbbr>_<ModelNumber>_CutSheet.pdf
      ├── Certifications/
      │   ├── <MfrAbbr>_<ModelNumber>_NSF61.pdf
      │   └── <MfrAbbr>_<ModelNumber>_NSF372.pdf
      └── Installation-Manuals/
          └── <MfrAbbr>_<ModelNumber>_InstallManual.pdf
```

---

## Naming Convention

```
<ManufacturerAbbr>_<ModelNumber>_<DocType>.pdf
```

| Abbreviation | Manufacturer |
|-------------|-------------|
| WATTS | Watts Water Technologies |
| XYLEM | Xylem / Bell & Gossett |
| MUELLER | Mueller Water Products |
| NIBCO | NIBCO Inc. |
| ZURN | Zurn Industries |
| APOLLO | Apollo Valves |
| GF | Georg Fischer / Grundfos |
| AMTROL | Amtrol Inc. |
| SENSUS | Sensus Metering |
| AOS | A.O. Smith |

---

## Common Doc Types

| Suffix | Meaning |
|--------|---------|
| `CutSheet` | Product data / spec sheet |
| `NSF61` | NSF/ANSI 61 potable water cert |
| `NSF372` | NSF/ANSI 372 low-lead cert |
| `InstallManual` | Installation and maintenance manual |
| `SubmittalData` | Manufacturer's pre-formatted submittal data sheet |
