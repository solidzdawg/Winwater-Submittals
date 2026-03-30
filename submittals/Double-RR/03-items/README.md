# Items Folder — Double RR Submittal

This folder contains one subfolder per submittal item.

## Folder Structure

```
03-items/
├── Item-01/
│   ├── separator.pdf          ← Item separator/divider sheet
│   ├── cutsheet.pdf           ← Manufacturer product data
│   ├── cert-NSF61.pdf         ← NSF 61 certification
│   ├── cert-NSF372.pdf        ← NSF 372 lead-free certification
│   └── spec-pages.pdf         ← Referenced specification pages (highlighted)
├── Item-02/
│   └── ...
└── Item-NN/
    └── ...
```

## How to Populate

1. For each item in the item index, create a folder named `Item-XX/`
   (zero-padded number matching the item index, e.g., `Item-01`, `Item-02`)
2. Add the following PDFs in order:
   - `separator.pdf` — generated from `templates/separator-sheet.md`
   - `cutsheet.pdf` — from `Z:\Vendor Parts\<Manufacturer>\Cut Sheets\`
   - `cert-NSF61.pdf` — from `Z:\Vendor Parts\<Manufacturer>\Certifications\`
   - `cert-NSF372.pdf` — from `Z:\Vendor Parts\<Manufacturer>\Certifications\`
   - `spec-pages.pdf` — extracted and highlighted from project spec PDF

## File Naming

The assembly script (`scripts/assemble-submittal.py`) adds files within each
`Item-XX/` folder **in alphabetical order**. The `separator.pdf` naming ensures
it is always added first (before `cutsheet.pdf`, `cert-*.pdf`, `spec-pages.pdf`).

If you need a specific order, prefix files with numbers:
```
01-separator.pdf
02-cutsheet.pdf
03-cert-NSF61.pdf
04-cert-NSF372.pdf
05-spec-pages.pdf
```
