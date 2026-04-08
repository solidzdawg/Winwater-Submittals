# Winwater Submittals

This branch adds a cloud-runnable drawing takeoff pipeline that works from the source PDFs already in this repository.

The goal is not to guess faster. The goal is to produce submittal and takeoff drafts that are:

- grounded in the drawing/spec PDFs
- traceable back to sheet and page evidence
- explicit about low-confidence rows
- exportable into a draft `manifest.csv` for downstream submittal assembly

## What This Adds

- `scripts/extract_drawing_takeoff.py`
  Builds a page inventory from the PDFs, optionally runs multimodal extraction, then exports normalized outputs.
- `scripts/agents/drawing_takeoff_agent.py`
  Thin agent wrapper around the same pipeline.
- `scripts/lib/pdf_ingest.py`
  Page-level inventory utilities built on PyMuPDF.
- `schemas/drawing_takeoff.schema.json`
  Evidence-first JSON contract for extracted rows.
- `.github/workflows/drawing-takeoff.yml`
  Manual GitHub Actions workflow so the pipeline can run in a cloud environment.
- `projects/Double-RR/sources.example.json`
  Example source bundle pointing at the current repo PDFs.

## Output Artifacts

A normal run writes these files under `_output/drawing-takeoff/`:

- `inventory.json`
  Page-by-page document inventory with classifications, sheet guesses, text excerpts, and rendered page images.
- `takeoff.raw.json`
  Raw model output or a fallback stub if model extraction is skipped.
- `takeoff.normalized.json`
  Deduplicated, normalized, evidence-backed takeoff rows.
- `manifest.draft.csv`
  Reviewer-friendly draft manifest shaped for Winwater-style downstream submittal work.
- `traceability.md`
  Human-readable evidence report linking every extracted row back to page references.

## Why This Is More Accurate

The pipeline combines two layers:

1. Deterministic PDF inventory
   - page rasterization
   - text extraction
   - sheet/page classification
   - explicit evidence locations

2. Structured multimodal extraction
   - uploaded PDFs are read directly
   - output must match `schemas/drawing_takeoff.schema.json`
   - every row requires page-level evidence
   - uncertain rows are marked `needs_review` instead of being silently invented

That means review effort gets concentrated on the risky rows instead of rechecking everything.

## Local Usage

```bash
pip install -r requirements.txt
python scripts/extract_drawing_takeoff.py \
  --sources projects/Double-RR/sources.example.json \
  --output-dir _output/drawing-takeoff
```

If you only want the deterministic inventory layer:

```bash
python scripts/extract_drawing_takeoff.py \
  --sources projects/Double-RR/sources.example.json \
  --output-dir _output/drawing-takeoff \
  --inventory-only
```

## Cloud Usage

Run the GitHub Actions workflow:

- Workflow: `Extract Drawing Takeoff`
- Input `sources`: `projects/Double-RR/sources.example.json`
- Optional secret: `OPENAI_API_KEY`

If the secret is present, the workflow will run multimodal extraction.
If the secret is absent, the workflow can still produce the page inventory with `inventory_only=true`.

## Source Bundle Format

Example:

```json
{
  "project_code": "Double-RR",
  "project_name": "Double RR Ranch - East Cabins",
  "documents": [
    {"path": "20260309 - DRLR Construction Docs - 252128.ENV.pdf", "kind": "drawings"},
    {"path": "Div 15 - Mechanical Specs - 20230319.pdf", "kind": "specifications"},
    {"path": "Div 16 - Electrical Specs - 20260311.pdf", "kind": "specifications"}
  ]
}
```

## Review Expectations

Rows are intentionally conservative.

A row should land in `needs_review` when any of these are true:

- manufacturer or model number is not clearly supported by the documents
- spec section is malformed or missing
- quantity is ambiguous
- the model confidence is below `0.75`
- page-level evidence is weak or absent

That is by design. High-confidence rows should be easy to trust, and low-confidence rows should be easy to find.

## Next Steps

Natural follow-ons for even better accuracy:

- add OCR fallback for scanned sheets with weak text layers
- add vendor cut-sheet matching against `Pre Ordered Equipment/`
- add spec-section cross-checking against Division 15/16 paragraphs
- reintroduce the old submittal builder using `manifest.draft.csv` as the handoff point
