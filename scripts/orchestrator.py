#!/usr/bin/env python3
"""
Winwater Submittal Orchestrator
================================
Autonomous workflow that chains all agents to build, validate, and QC
a complete submittal package.

Usage:
    python orchestrator.py --project "Double-RR"
    python orchestrator.py --project "Double-RR" --step validate
    python orchestrator.py --project "Double-RR" --step separators
    python orchestrator.py --project "Double-RR" --step vendor-audit
    python orchestrator.py --project "Double-RR" --step qc
    python orchestrator.py --project "Double-RR" --step assemble
    python orchestrator.py --project "Double-RR" --full-run

Steps (executed in order for --full-run):
    1. validate      — Check project structure & manifest
    2. separators    — Generate separator sheets from manifest
    3. vendor-audit  — Audit vendor files, create missing dirs
    4. template-gate — Verify required templates + visual-quality readiness
    5. qc            — Quality-control checks
    6. assemble      — Merge all PDFs into final submittal
"""

import argparse
import sys
import time
from pathlib import Path

# Add parent to path so we can import agents
sys.path.insert(0, str(Path(__file__).resolve().parent))

from agents.validate_agent import validate_project, print_report
from agents.separator_agent import run as generate_separators
from agents.vendor_fetch_agent import check_vendor_files, print_vendor_report
from agents.qc_agent import qc_check, print_qc_report
from agents.template_compliance_agent import compliance_check, print_compliance_report


BANNER = """
╔══════════════════════════════════════════════════════════════╗
║                                                              ║
║   WINWATER SUBMITTAL ORCHESTRATOR                            ║
║   Autonomous Submittal Build Agent                           ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝
"""


def step_validate(project: str) -> bool:
    print("\n" + "─" * 60)
    print("  STEP 1: VALIDATE PROJECT STRUCTURE")
    print("─" * 60)
    report = validate_project(project)
    print_report(report)
    return report["ready"]


def step_separators(project: str, force: bool = False) -> bool:
    print("\n" + "─" * 60)
    print("  STEP 2: GENERATE SEPARATOR SHEETS")
    print("─" * 60)
    result = generate_separators(project, force)
    print(f"\n  Created: {result['created']}  Skipped: {result['skipped']}")
    if result["errors"]:
        for e in result["errors"]:
            print(f"  ❌ {e}")
        return False
    print("  ✅ Separator generation complete")
    return True


def step_vendor_audit(project: str, create_dirs: bool = True) -> bool:
    print("\n" + "─" * 60)
    print("  STEP 3: VENDOR FILE AUDIT")
    print("─" * 60)
    result = check_vendor_files(project, create_dirs)
    print_vendor_report(result)
    # Vendor audit is informational — doesn't block the pipeline
    return True


def step_template_gate(project: str) -> bool:
    print("\n" + "─" * 60)
    print("  STEP 4: TEMPLATE + PRESENTATION GATE")
    print("─" * 60)
    report = compliance_check(project)
    print_compliance_report(report)
    return len(report["failed"]) == 0


def step_qc(project: str) -> bool:
    print("\n" + "─" * 60)
    print("  STEP 5: QUALITY CONTROL")
    print("─" * 60)
    report = qc_check(project)
    print_qc_report(report)
    return len(report["failed"]) == 0


def step_assemble(project: str, output: str | None = None) -> bool:
    print("\n" + "─" * 60)
    print("  STEP 6: ASSEMBLE PDF")
    print("─" * 60)
    # Import the assembly script
    import importlib.util
    script_path = Path(__file__).resolve().parent / "assemble-submittal.py"
    try:
        spec = importlib.util.spec_from_file_location("assemble_submittal", str(script_path))
        if spec is None or spec.loader is None:
            raise ImportError("Could not load assemble-submittal.py")
        assemble_submittal_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(assemble_submittal_module)

        assemble_submittal = assemble_submittal_module.assemble_submittal
        validate_project_structure = assemble_submittal_module.validate_project_structure

        validate_project_structure(project)
        assemble_submittal(project, output)
        return True
    except SystemExit:
        return False
    except ImportError:
        print("  ❌ Could not import assemble-submittal.py")
        print("  Make sure pypdf is installed: pip install pypdf")
        return False
    except Exception as e:
        print(f"  ❌ Assembly failed: {e}")
        return False


def full_run(project: str) -> None:
    """Execute all steps in sequence."""
    start = time.time()
    steps = [
        ("Validate", lambda: step_validate(project)),
        ("Separators", lambda: step_separators(project)),
        ("Vendor Audit", lambda: step_vendor_audit(project)),
        ("Template Gate", lambda: step_template_gate(project)),
        ("QC Check", lambda: step_qc(project)),
        ("Assemble", lambda: step_assemble(project)),
    ]

    results = []
    for name, fn in steps:
        ok = fn()
        results.append((name, ok))
        if not ok and name in ("Validate",):
            print(f"\n  ⛔ Pipeline halted at {name} — fix errors and re-run")
            break

    elapsed = time.time() - start

    print("\n" + "=" * 60)
    print("  PIPELINE SUMMARY")
    print("=" * 60)
    for name, ok in results:
        status = "✅ PASS" if ok else "❌ FAIL"
        print(f"  {status}  {name}")
    print(f"\n  Elapsed: {elapsed:.1f}s")
    print("=" * 60 + "\n")


def main():
    parser = argparse.ArgumentParser(
        description="Winwater Submittal Orchestrator — autonomous build pipeline."
    )
    parser.add_argument("--project", required=True, help="Project folder name")
    parser.add_argument(
        "--step",
        choices=["validate", "separators", "vendor-audit", "template-gate", "qc", "assemble"],
        help="Run a single step (default: full run)",
    )
    parser.add_argument("--full-run", action="store_true", help="Run all steps in sequence")
    parser.add_argument("--output", default=None, help="Output PDF filename for assembly")
    parser.add_argument("--force-separators", action="store_true",
                        help="Force overwrite of existing separator sheets")

    args = parser.parse_args()

    print(BANNER)
    print(f"  Project: {args.project}")

    if args.step:
        dispatch = {
            "validate": lambda: step_validate(args.project),
            "separators": lambda: step_separators(args.project, args.force_separators),
            "vendor-audit": lambda: step_vendor_audit(args.project),
            "template-gate": lambda: step_template_gate(args.project),
            "qc": lambda: step_qc(args.project),
            "assemble": lambda: step_assemble(args.project, args.output),
        }
        ok = dispatch[args.step]()
        sys.exit(0 if ok else 1)
    else:
        full_run(args.project)


if __name__ == "__main__":
    main()
