#!/usr/bin/env bash
set -euo pipefail

if [[ $# -lt 1 ]]; then
  echo "Usage: $0 <ProjectName>"
  exit 1
fi

PROJECT="$1"

echo "[1/2] Template compliance gate"
python scripts/agents/template_compliance_agent.py --project "$PROJECT"

echo "[2/2] QC gate"
python scripts/agents/qc_agent.py --project "$PROJECT"

echo "All style/compliance gates passed for $PROJECT"
