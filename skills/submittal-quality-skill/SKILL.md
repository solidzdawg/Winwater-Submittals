---
name: submittal-quality-skill
description: Design and run a template-independent submittal generation workflow that produces professional PDFs from schema-driven inputs using pluggable render backends, strict quality gates, and agent orchestration. Use when replacing Office template dependencies or improving document quality/reliability.
---

# SubmittalQualitySkill

## Contract

Input artifacts:
- `submittal.json` compliant with `schemas/submittal_output.schema.json`
- `theme.json` compliant with `schemas/render_theme.schema.json`
- Optional backend selection: `weasyprint-html` or `reportlab-canvas`

Output artifacts:
- `01-cover.pdf`
- `02-index.pdf`
- `sep-XX.pdf` for each item
- Quality report with pass/fail checks

## Execution sequence

1. Validate schema and required document paths.
2. Load render theme tokens.
3. Render sections through `SubmittalRendererPlugin` backend.
4. Merge with vendor/cert/spec PDFs.
5. Run release quality gates (typography/page-break/visual regression).

## Guardrails

- Do not depend on `.xlsx/.docx` templates.
- Fail release mode on missing document paths.
- Enforce spec-section format `XX XX XX`.
- Enforce deterministic output ordering by `item_number`.

## References

- `references/skill-spec.md`
- `docs/v2/template-free-submittal-architecture.md`
