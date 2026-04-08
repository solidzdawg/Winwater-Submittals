#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(BASE_DIR))

from scripts.extract_drawing_takeoff import run_pipeline


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Agent wrapper for evidence-backed drawing takeoff extraction."
    )
    parser.add_argument("--sources", required=True, help="Path to the sources JSON file")
    parser.add_argument("--output-dir", default="_output/drawing-takeoff", help="Directory for generated artifacts")
    parser.add_argument("--dpi", type=int, default=150, help="Rasterization DPI for page images")
    parser.add_argument("--model", default="gpt-5", help="OpenAI model name")
    parser.add_argument("--inventory-only", action="store_true", help="Skip model extraction")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    result = run_pipeline(args)
    summary = {
        "project": result["project"],
        "item_count": len(result.get("items", [])),
        "needs_review": sum(1 for item in result.get("items", []) if item.get("needs_review")),
    }
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
