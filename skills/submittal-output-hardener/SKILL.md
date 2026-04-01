---
name: submittal-output-hardener
description: Improve Winwater submittal output quality and enforce required template usage. Use when users ask to make submittals look professional, stop low-quality outputs, enforce Office template-driven generation, add quality gates, or convert repo findings into reusable automation agents/plugins.
---

# Submittal Output Hardener

Use this skill to produce polished, template-compliant submittal packages and to prevent regressions.

## Workflow

1. Run the template/presentation gate first:
   - `python scripts/agents/template_compliance_agent.py --project <ProjectName>`
2. Run standard QC:
   - `python scripts/agents/qc_agent.py --project <ProjectName>`
3. If both pass, run the orchestrated build pipeline:
   - `python scripts/orchestrator.py --project <ProjectName> --full-run`
4. If output quality is still weak, apply the field-length constraints from `references/repo-findings.md` and re-run step 1.

## Non-negotiable guardrails

- Use Office templates in `templates/` for cover, item index, and separator pages.
- Fail the run if required template files are missing.
- Treat unresolved placeholders in source markdown as warnings to resolve before release.
- Keep manifest text concise enough to avoid ugly wrapping in separators and index rows.

## What to read next

- Read `references/repo-findings.md` for concrete repo findings and remediation.
- Use `scripts/run_style_gate.sh` for a one-command preflight check.
