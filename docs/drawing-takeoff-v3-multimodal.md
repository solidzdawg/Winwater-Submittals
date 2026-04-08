# Drawing Takeoff V3 Multimodal Strategy

V3 adds one important accuracy upgrade on top of the earlier pipeline:

- it uploads prioritized page images alongside the source PDFs

That matters because drawing PDFs often have weak or incomplete text layers exactly where the important information lives:

- schedule tables
- keyed note clouds
- legends
- dense plan callouts
- details with short labels

## What V3 Changes

1. Build the same deterministic PDF inventory as earlier versions.
2. Rank pages by likely extraction value.
3. Upload the top-ranked page images as vision inputs.
4. Upload the original PDFs as file inputs.
5. Ask for one strict-schema, evidence-backed output.

## Why This Helps

The PDF file gives the model full document context.
The selected images give the model cleaner access to the visually dense pages that are easiest to misread from the PDF text layer alone.

This is especially useful when the schedule exists as a flattened table or when note numbering is visually obvious but text extraction is messy.

## Page Ranking Signals

Priority pages are selected using deterministic signals:

- page classified as `schedule`
- page classified as `notes`
- page classified as `legend`
- page classified as `specifications`
- high drawing count
- high word count
- keywords like `fixture schedule`, `equipment schedule`, `keyed notes`, `legend`, `spec section`

## Outputs to Review

V3 writes these extra artifacts:

- `priority-pages.json`
  Shows which page images were selected and why.
- `review-queue.md`
  Keeps the riskiest rows at the top.

## Recommended Runtime Order

1. Run V3 in `inventory_only` mode first if you want to inspect page selection.
2. Run full V3 extraction with `OPENAI_API_KEY` configured.
3. Review `review-queue.md`.
4. Promote trusted rows into downstream manifest/submittal steps.
