# Vendor Documentation

This folder stores vendor product documentation organized by manufacturer.

## Structure

```
vendor-docs/
├── <Manufacturer>/
│   ├── Cut-Sheets/
│   │   └── <ManufacturerAbbr>_<ModelNumber>_CutSheet.pdf
│   ├── Certifications/
│   │   ├── <ManufacturerAbbr>_<ModelNumber>_NSF61.pdf
│   │   ├── <ManufacturerAbbr>_<ModelNumber>_NSF372.pdf
│   │   └── <ManufacturerAbbr>_<ModelNumber>_UL.pdf
│   └── Installation-Manuals/
│       └── <ManufacturerAbbr>_<ModelNumber>_InstallManual.pdf
```

## File Naming Convention

`<ManufacturerAbbr>_<ModelNumber>_<DocType>.pdf`

| Part        | Description                              | Example          |
|-------------|------------------------------------------|------------------|
| ManufacturerAbbr | Short manufacturer name (no spaces) | `WATTS`, `XYLEM` |
| ModelNumber | Exact model/catalog number              | `LF25AUB-Z3`     |
| DocType     | Document type                           | `CutSheet`, `NSF61`, `NSF372`, `UL`, `ASSE`, `InstallManual` |

## Sourcing Documents

All vendor documents should be sourced from the company Z: drive:
```
Z:\Vendor Parts\<Manufacturer>\Cut Sheets\
Z:\Vendor Parts\<Manufacturer>\Certifications\
```

Copy relevant files here when working on a project to keep a local archive.

## Common Manufacturers

- Watts Water Technologies
- Xylem / Bell & Gossett
- Mueller Water Products
- Nibco
- Zurn Industries
- Apollo Valves
- Honeywell / Resideo
- Siemens (controls)
