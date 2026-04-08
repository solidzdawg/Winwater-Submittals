# Manifest Promotion Flow

Once a takeoff run produces `takeoff.normalized.json` and `vendor-match-candidates.json`, you can promote the trusted rows into a Winwater-style manifest CSV.

## Why This Exists

The extraction pipeline is intentionally conservative.
Not every row should go straight into production submittal assembly.

This promotion step gives you a clean thresholded handoff:

- promote high-confidence rows
- skip risky rows automatically
- auto-fill likely `cut_sheet_path` values when vendor matching is strong enough
- keep a machine-readable skipped-item report for follow-up review

## Command

```bash
python scripts/promote_takeoff_to_manifest.py \
  --takeoff _output/drawing-takeoff-v3/takeoff.normalized.json \
  --vendor-matches _output/drawing-takeoff-v3/vendor-match-candidates.json \
  --output-csv _output/promoted/manifest.promoted.csv \
  --skipped-json _output/promoted/skipped-items.json
```

## Default Promotion Rules

A row is promoted only if:

- `confidence >= 0.85`
- `needs_review == false`
- manufacturer is present
- model number is present
- spec section is present
- source evidence exists

A vendor PDF is auto-selected for `cut_sheet_path` only when the best candidate score is at least `4.0`.

## Outputs

- `manifest.promoted.csv`
  Ready for downstream template/submittal steps.
- `skipped-items.json`
  Lists every excluded row and the exact reason it was held back.

## Recommended Workflow

1. Run `drawing-takeoff-v3`.
2. Review `review-queue.md`.
3. Promote trusted rows with this script.
4. Resolve skipped rows manually or rerun extraction with better source documents.
