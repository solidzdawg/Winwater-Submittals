# Drawing Takeoff Accuracy Strategy

This repo now has a review-first extraction path aimed at making PDF-driven takeoffs trustworthy enough to use as a submittal starting point.

## Accuracy Principles

- Prefer omission over hallucination.
- Keep every extracted row tied to document evidence.
- Surface uncertainty with `needs_review` instead of hiding it.
- Separate deterministic preprocessing from model judgment.
- Keep reviewer effort focused on ambiguous rows.

## Current Pipeline Layers

1. Deterministic inventory
   - page rasterization
   - text extraction
   - block capture
   - sheet/page classification
2. Deterministic note extraction
   - numbered notes
   - keyed notes
   - note-to-spec-section hints
3. Structured multimodal extraction
   - direct PDF input
   - strict JSON schema
   - evidence-required outputs
4. Deterministic post-processing
   - spec section normalization
   - row deduplication
   - confidence thresholds
   - review flagging
5. Deterministic vendor matching
   - filename/folder token scoring against repo PDFs

## Why This Beats Text-Only Parsing

A text-only pass usually loses:

- sheet context
- note numbering
- schedule-to-detail relationships
- page provenance
- geometry-heavy plan sheets with sparse text

The new path keeps page inventory and evidence references around the model, so it can cite where a row came from and the reviewer can verify it quickly.

## Reviewer Outputs

- `traceability.md`
  Shows each item with its evidence lines.
- `review-queue.md`
  Sorts rows so the riskiest rows are reviewed first.
- `vendor-match-candidates.json`
  Suggests likely repo PDFs to attach as cut sheets.

## Recommended Acceptance Rules

Treat a row as near-ready only when all are true:

- confidence >= 0.85
- manufacturer is present
- model number is present
- spec section matches `XX XX XX`
- at least one strong evidence quote exists
- quantity is supported by schedule or repeated callout evidence

## Best Next Improvements

- OCR fallback for scanned sheets with weak text layers
- page-region crops for schedule tables and note clouds
- spec paragraph extraction tied to the same spec section as the row
- vendor PDF title-page parsing instead of filename-only matching
- comparison against the materials takeoff workbook once a parser is added
