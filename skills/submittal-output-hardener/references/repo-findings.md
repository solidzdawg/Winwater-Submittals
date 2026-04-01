# Repo Findings: Why outputs can look bad and how to fix

## Findings from current repository

1. The primary builder (`scripts/build-submittal-sets.py`) already relies on the required Office templates for cover, item index, and separator generation via LibreOffice conversion.
2. The legacy/alternate flow in docs still references markdown templates and `assemble-submittal.py`, which can produce inconsistent aesthetics if used as the primary path.
3. Existing QC checks structure and completeness but did not enforce template presence/readiness or readability constraints that impact visual quality.
4. Item separator pages are populated from manifest strings directly; very long descriptions/manufacturer/model values can wrap awkwardly and make pages look unprofessional.

## Recommended output-quality policy

- Treat `build-submittal-sets.py` as the canonical render path for professional output.
- Require these templates to exist before build:
  - `templates/submittal cover.xlsx`
  - `templates/Item Index Template.docx`
  - `templates/Seperator Sheet Template.docx` (or corrected `Separator` spelling variant)
- Enforce readability constraints at manifest level:
  - Description <= 56 chars
  - Manufacturer <= 26 chars
  - Model <= 26 chars
- Require `spec_section` in CSI format: `XX XX XX`.
- Fail if any referenced `cut_sheet_path` PDF is missing.

## Practical pipeline

1. `python scripts/agents/template_compliance_agent.py --project <Project>`
2. `python scripts/agents/qc_agent.py --project <Project>`
3. `python scripts/orchestrator.py --project <Project> --full-run`
4. Review generated PDFs under `submittals/<Project>/sets/`.

## Agent/plugin architecture introduced

- **Plugin-like gate agent:** `scripts/agents/template_compliance_agent.py`
  - Enforces required template availability.
  - Checks manifest fields that correlate with poor visual layout.
  - Detects unresolved placeholders in markdown source files.
- **Orchestrator integration:** new `template-gate` step in `scripts/orchestrator.py`.
- **Reusable skill:** `skills/submittal-output-hardener`.

## Future hardening

- Add PDF-level linting (font-size/margin consistency) after generation.
- Add template fingerprinting (hash pinning) to detect unauthorized template drift.
- Add CI job to block merges when template compliance fails.
