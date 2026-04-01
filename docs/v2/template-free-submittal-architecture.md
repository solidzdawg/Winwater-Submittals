# Template-Free Submittal Architecture (V2)

## Overview

- The current repo has two render paths: (1) Office-template based (`build-submittal-sets.py`), and (2) HTML/CSS rendering via WeasyPrint (`build-package.py`).
- Output quality inconsistency is caused by split pipelines, hard-coded inline CSS, missing asset governance, and absent visual regression tests.
- To remove template dependency, promote a renderer plugin layer that consumes structured JSON instead of `.xlsx/.docx` templates.
- Introduce a single canonical schema (`submittal_output.schema.json`) and a theme token file (`render_theme.schema.json`) that controls typography, spacing, colors, and page behavior.
- Add `RepoSubmittalAgent` to orchestrate validate -> render -> assemble -> verify with strict guardrails and deterministic checks.
- Keep backward compatibility by preserving current scripts and adding a feature-flagged V2 path.

## Current system map

| Component | Path | Responsibility |
|---|---|---|
| Set builder (Office templates) | `scripts/build-submittal-sets.py` | Fills Excel/Word templates, converts via LibreOffice, merges PDFs into per-set outputs. |
| Combined package builder (HTML/CSS) | `scripts/build-package.py` | Generates cover/index/separators from inline HTML/CSS with WeasyPrint then merges vendor PDFs. |
| Legacy assembler | `scripts/assemble-submittal.py` | Concatenates PDFs in folder order and adds bookmarks. |
| Orchestrator | `scripts/orchestrator.py` | Chains validate, separators, vendor audit, template gate, QC, assemble. |
| Structural validation | `scripts/agents/validate_agent.py` | Validates project tree and manifest-linked artifacts. |
| QC checks | `scripts/agents/qc_agent.py` | Performs structural/content sanity checks and score. |
| Template compliance (V1 gate) | `scripts/agents/template_compliance_agent.py` | Ensures required templates and manifest readability constraints. |
| Templates | `templates/` | Office + markdown templates for cover/index/separator. |
| Project data | `submittals/<project>/manifest.csv`, `project.json` | Input data defining items, metadata, and set grouping. |

## Findings with evidence

- **Dual rendering systems cause drift**: Office-driven (`build-submittal-sets.py`) and HTML-driven (`build-package.py`) are both active, with different layouts and typography logic.
- **Inline CSS is brittle and hard to govern**: `build-package.py` defines large module-level CSS strings (`COVER_CSS`, `INDEX_CSS`, `SEPARATOR_CSS`) instead of tokenized theme definitions.
- **Brand assets are not centralized**: Cover/logo styling is hand-coded HTML text instead of asset-driven logo/font package.
- **Data model mismatch**: `project.json` drives set-level build, while `manifest.csv` drives item-level assembly; no canonical typed contract exists.
- **Quality checks are mostly structural**: validators catch missing files but not typography/page-break regressions.
- **Office dependency remains operational risk**: current primary path requires LibreOffice conversion and template files to exist and remain stable.

## Proposed architectures

| Option | Description | Pros | Cons | Verdict |
|---|---|---|---|---|
| A. WeasyPrint + JSON DSL (recommended) | Render cover/index/separators via semantic HTML from JSON schema + theme tokens; merge with pypdf. | Fast to implement in Python stack, deterministic, CSS styling flexibility, no Office templates required. | CSS print quirks and font install discipline needed. | ✅ Best migration path. |
| B. ReportLab canvas + layout primitives | Direct PDF drawing from Python layout code, zero HTML/CSS. | Strong deterministic control, no browser/CSS variability. | Higher engineering effort for tables/pagination and typography polish. | Useful fallback backend. |

## Recommended design

1. **Canonical input schema**
   - Use `schemas/submittal_output.schema.json` as the single source of truth.
   - Load data from existing `project.json` + `manifest.csv` via adapter.
2. **Theme tokens**
   - Use `schemas/render_theme.schema.json` and JSON theme files under `examples/themes/`.
3. **Renderer plugin**
   - `scripts/plugins/submittal_renderer_plugin.py` defines backend contract and adapters.
   - Backends: `weasyprint-html` (default), `reportlab-canvas` (fallback).
4. **Agent orchestration**
   - `scripts/agents/repo_submittal_agent.py` coordinates backend selection and section rendering.
5. **Quality gates**
   - Add snapshot checks and objective typography/page-break assertions before release mode.

## Implementation checklist

1. Add canonical schemas and adapters (new files under `schemas/` and `scripts/adapters/`).
2. Add renderer plugin and backend implementations (current scaffold in `scripts/plugins/submittal_renderer_plugin.py`).
3. Add repo agent policy for template-free render (current scaffold in `scripts/agents/repo_submittal_agent.py`).
4. Add V2 CLI entrypoint `scripts/render-submittal-v2.py` consuming schema + theme.
5. Add PDF quality checks: font presence, min margins, orphan/widow page rules, page-break assertions.
6. Add golden-file baseline for one project (Double-RR) and visual regression thresholds.
7. Wire orchestrator optional step `render-v2` under feature flag.
8. Deprecate Office-template dependency once V2 achieves stable parity.

## Example submittal schema (excerpt)

```json
{
  "schema_version": "2.0",
  "project": {
    "code": "Double-RR",
    "name": "Double RR Ranch - East Cabins",
    "number": "DRLR-2026-001"
  },
  "submittal_number": "WW-2026-001",
  "revision": "0",
  "submittal_title": "Plumbing Equipment and Materials",
  "items": [
    {
      "item_number": 1,
      "description": "Pressure Reducing Valve",
      "manufacturer": "Watts",
      "model_number": "LF25AUB-Z3",
      "spec_section": "22 05 23",
      "documents": [
        {"type": "cut_sheet", "path": "vendor-docs/Watts/Cut-Sheets/Watts_LF25AUB_Cut-Sheet.pdf"}
      ]
    }
  ]
}
```

## Example theme tokens (excerpt)

```json
{
  "name": "winwater-clean-v1",
  "page_size": "LETTER",
  "margin_in": {"top": 0.5, "right": 0.5, "bottom": 0.5, "left": 0.5},
  "fonts": {"title": "DejaVu Sans", "body": "DejaVu Sans", "mono": "DejaVu Sans Mono"},
  "font_sizes_pt": {"title": 18, "h1": 14, "h2": 12, "body": 10.5, "caption": 9},
  "colors": {"text": "#111111", "muted": "#666666", "accent": "#1F6FEB", "border": "#222222", "highlight": "#FFF176"},
  "spacing_pt": {"xxs": 2, "xs": 4, "sm": 6, "md": 10, "lg": 16, "xl": 24}
}
```

## Definition of Done

- V2 renderer can generate cover/index/separators without `.xlsx/.docx` templates.
- Build reproducibility: same inputs + theme produce byte-stable metadata-normalized PDFs.
- Quality gates pass:
  - schema validation
  - no missing referenced PDFs
  - typography/token lint
  - page-break checks
  - golden visual regression for baseline project.
- Backward compatibility preserved (`build-submittal-sets.py` unchanged).

## Minimal test plan

- Unit: schema loader, adapter mapping (`project.json` + `manifest.csv` -> canonical JSON).
- Unit: backend selection and render contract.
- Integration: render cover/index/separators using both backends.
- Regression: compare generated PDFs against golden images for first two pages + one separator.
- Policy: release mode fails on unresolved placeholders, missing docs, overflow warnings.
