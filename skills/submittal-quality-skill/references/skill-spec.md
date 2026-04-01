# SubmittalQualitySkill Spec

## Inputs

```yaml
project_code: string
submittal_path: path/to/submittal.json
theme_path: path/to/theme.json
backend: weasyprint-html | reportlab-canvas
mode: draft | release
```

## Validation rules

- Schema validation must pass against `schemas/submittal_output.schema.json`.
- Theme validation must pass against `schemas/render_theme.schema.json`.
- Every `documents[].path` must exist in release mode.
- Descriptions should be <= 72 chars for index readability.

## Output quality checks

- Font families must be resolved (no fallback warnings).
- First page must contain submittal title + project name.
- Index must include every item in order.
- Every separator must include ITEM number and description.
- No page with clipped text bounding boxes.

## Suggested tools

- `scripts/plugins/submittal_renderer_plugin.py`
- `scripts/agents/repo_submittal_agent.py`
- `pypdf`, `weasyprint`
