# Submittal Assembly Guide

This guide covers the full process for building a Winwater submittal package,
from gathering source documents through final PDF delivery.

> **Tip — use the autonomous agent for steps 1–6:**
> ```bash
> python scripts/agent.py --project "Double-RR"
> ```
> The agent caches docs from both source locations, matches vendor data to each
> manifest item, generates all PDF pages, and assembles the final package with
> no manual steps. See [`scripts/agent.py`](../scripts/agent.py).

---

## Prerequisites

- Python 3.8+
- Dependencies: `pip install pypdf fpdf2`
- Network access to Z: drive **or** a populated local cache (see Step 1)
- Project manifest CSV (`submittals/<project>/manifest.csv`)

---

## Step 1 — Cache Source Documents

Use `browse-docs.py` to scan both source locations and cache copies locally.
This lets you work offline and gives the agent a consistent local file tree.

```bash
# Cache everything from both sources
python scripts/browse-docs.py --cache

# Cache only docs for a specific project / manufacturer
python scripts/browse-docs.py --cache --project "Double-RR"
python scripts/browse-docs.py --cache --manufacturer "Watts"

# See what's in the cache
python scripts/browse-docs.py --status

# Browse the tree of available documents
python scripts/browse-docs.py --list
python scripts/browse-docs.py --list --project "Double-RR"
```

**Source locations** (edit `config/paths.json` to match your environment):

| Location | Default path |
|----------|-------------|
| Submittal task folder | `~/Documents/submittal-task/` |
| Z: drive vendor parts | `Z:\Vendor Parts\` |

---

## Step 2 — Prepare the Manifest

The manifest CSV is the agent's source of truth. One row per submittal item.
A starter manifest is at `submittals/<project>/manifest.csv`.

Required columns:

| Column | Description |
|--------|-------------|
| `item_number` | Sequential number (1, 2, 3 …) |
| `description` | Plain-English item description |
| `manufacturer` | Manufacturer name (must match Z: drive folder name) |
| `model_number` | Model number for document matching |
| `spec_section` | CSI spec section (e.g., `22 05 23`) |

Optional columns used for explicit path overrides:
`cut_sheet_path`, `cert_nsf61_path`, `cert_nsf372_path`, `other_certs`, `spec_pages_path`

---

## Step 3 — Run the Autonomous Agent

```bash
python scripts/agent.py --project "Double-RR"
```

The agent performs these steps automatically:

1. **Cache sources** — scans `~/Documents/submittal-task/` and `Z:\Vendor Parts\`
   and copies all docs to `.doc-cache/`
2. **Load manifest** — reads `submittals/<project>/manifest.csv`
3. **Match docs** — finds cut sheets, NSF-61, and NSF-372 certs for every item
   by searching the cache for `<manufacturer>/<model>` matches
4. **Build structure** — creates `01-cover/`, `02-index/`, `03-items/Item-XX/`,
   `04-attachments/` and copies matched docs into place
5. **Generate PDFs** — produces cover sheet, item index, per-item separator
   sheets, and disclaimer using `fpdf2`
6. **Assemble** — merges all PDFs into one final package via `assemble-submittal.py`
7. **Log** — writes `submittals/<project>/agent-run.log` with full match summary
   and a list of any items that need manual attention

**Dry run** (preview without writing files):
```bash
python scripts/agent.py --project "Double-RR" --dry-run
```

---

## Step 4 — Review the Agent Log

Open `submittals/<project>/agent-run.log` and check:

- Any `⚠️ WARNING` lines — these are items where the agent could not
  automatically find a document and you need to attach it manually
- The match summary at the bottom — one section per item showing which
  files were matched or flagged as missing

---

## Step 5 — Attach Missing Documents Manually

For any item flagged in the log:

1. Open `submittals/<project>/03-items/Item-XX/`
2. Copy the required PDF(s) into that folder
3. Re-run the assembly script:
   ```bash
   python scripts/assemble-submittal.py --project "Double-RR"
   ```

---

## Step 6 — Quality Check

Before sending, verify:

- [ ] Cover sheet has correct project name, submittal number, date, revision
- [ ] Item index page numbers match actual pages in the assembled PDF
- [ ] Every item folder has a separator sheet
- [ ] Cut sheets show highlighted model numbers
- [ ] NSF-61 certifications present for all potable water products
- [ ] Disclaimer page is last
- [ ] File is named per naming convention (`<Code>_SUB_NNN_RevR_PlumbingEquipment.pdf`)
- [ ] Total page count is reasonable

---

## Step 7 — Transmit

Upload to the project management platform (Procore, e-Builder, etc.) or email
to the GC submittal coordinator. Save a copy to:

```
Z:\Projects\<ProjectName>\Submittals\Submitted\
```

Log the submittal in the project submittal log.
