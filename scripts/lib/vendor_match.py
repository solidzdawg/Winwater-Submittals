from __future__ import annotations

from pathlib import Path
from typing import Any
import re


EXCLUDED_DIR_NAMES = {".git", ".github", "_output", "artifacts", "page-images", "__pycache__"}


def tokenize(value: str) -> set[str]:
    return {token for token in re.split(r"[^A-Za-z0-9]+", value.upper()) if token}


def discover_pdf_catalog(base_dir: Path) -> list[dict[str, Any]]:
    catalog: list[dict[str, Any]] = []
    for path in base_dir.rglob("*.pdf"):
        if any(part in EXCLUDED_DIR_NAMES for part in path.parts):
            continue
        catalog.append(
            {
                "path": path.relative_to(base_dir).as_posix(),
                "name": path.name,
                "stem_tokens": tokenize(path.stem),
                "folder_tokens": tokenize(" ".join(path.parts[:-1])),
            }
        )
    return catalog


def score_candidate(item: dict[str, Any], candidate: dict[str, Any]) -> float:
    manufacturer_tokens = tokenize(item.get("manufacturer", ""))
    model_tokens = tokenize(item.get("model_number", ""))
    description_tokens = tokenize(item.get("description", ""))

    score = 0.0
    if manufacturer_tokens & candidate["stem_tokens"]:
        score += 3.0
    if manufacturer_tokens & candidate["folder_tokens"]:
        score += 2.0

    overlap_model = model_tokens & candidate["stem_tokens"]
    if overlap_model:
        score += 5.0 + min(2.0, len(overlap_model) * 0.5)

    overlap_desc = description_tokens & candidate["stem_tokens"]
    if overlap_desc:
        score += min(2.5, len(overlap_desc) * 0.35)

    path_lower = candidate["path"].lower()
    if "cut" in path_lower or "sheet" in path_lower:
        score += 1.5
    if "cert" in path_lower:
        score += 0.5
    if "spec" in path_lower:
        score += 0.25
    if "pre ordered equipment" in path_lower:
        score += 1.0

    return round(score, 2)


def match_vendor_documents(
    items: list[dict[str, Any]],
    base_dir: Path,
    min_score: float = 3.0,
    max_candidates: int = 5,
) -> list[dict[str, Any]]:
    catalog = discover_pdf_catalog(base_dir)
    results: list[dict[str, Any]] = []

    for item in items:
        ranked = []
        for candidate in catalog:
            score = score_candidate(item, candidate)
            if score < min_score:
                continue
            ranked.append(
                {
                    "path": candidate["path"],
                    "score": score,
                }
            )
        ranked.sort(key=lambda row: (-row["score"], row["path"]))
        results.append(
            {
                "item_number": item.get("item_number"),
                "description": item.get("description"),
                "manufacturer": item.get("manufacturer"),
                "model_number": item.get("model_number"),
                "candidates": ranked[:max_candidates],
            }
        )

    return results
