from __future__ import annotations

from typing import Any


CLASS_SCORES = {
    "schedule": 12.0,
    "notes": 10.0,
    "legend": 8.0,
    "specifications": 7.0,
    "detail": 6.0,
    "plan": 5.5,
    "drawing-heavy": 4.0,
    "unclassified": 1.0,
}


def score_page(page: dict[str, Any]) -> tuple[float, list[str]]:
    score = 0.0
    reasons: list[str] = []
    classes = page.get("classifications", [])

    for label in classes:
        class_score = CLASS_SCORES.get(label, 0.0)
        if class_score:
            score += class_score
            reasons.append(label)

    word_count = int(page.get("word_count", 0))
    drawing_count = int(page.get("drawing_count", 0))
    block_count = int(page.get("block_count", 0))

    if word_count > 300:
        score += 2.0
        reasons.append("dense-text")
    elif word_count > 100:
        score += 1.0
        reasons.append("useful-text")

    if drawing_count > 150:
        score += 1.5
        reasons.append("geometry-rich")
    elif drawing_count > 50:
        score += 0.75
        reasons.append("some-geometry")

    if block_count > 20:
        score += 0.5
        reasons.append("many-blocks")

    excerpt = (page.get("text_excerpt") or "").lower()
    bonus_terms = {
        "fixture schedule": 4.0,
        "equipment schedule": 4.0,
        "valve schedule": 4.0,
        "keyed notes": 3.0,
        "general notes": 3.0,
        "legend": 2.5,
        "abbreviations": 2.0,
        "spec section": 2.5,
        "section ": 1.5,
    }
    for term, bonus in bonus_terms.items():
        if term in excerpt:
            score += bonus
            reasons.append(term)

    return round(score, 2), reasons


def select_priority_pages(inventory: dict[str, Any], max_pages: int = 12) -> list[dict[str, Any]]:
    candidates: list[dict[str, Any]] = []

    for document in inventory.get("documents", []):
        for page in document.get("pages", []):
            score, reasons = score_page(page)
            if score <= 0:
                continue
            candidates.append(
                {
                    "document_path": document["document_path"],
                    "document_kind": document.get("document_kind", "unknown"),
                    "page_number": page["page_number"],
                    "page_label": page["page_label"],
                    "sheet_id": page.get("sheet_id"),
                    "image_path": page["image_path"],
                    "score": score,
                    "reasons": reasons,
                    "text_excerpt": page.get("text_excerpt", "")[:500],
                }
            )

    candidates.sort(
        key=lambda row: (-row["score"], row["document_path"], row["page_number"])
    )

    selected: list[dict[str, Any]] = []
    seen_doc_pages: set[tuple[str, int]] = set()
    for candidate in candidates:
        key = (candidate["document_path"], candidate["page_number"])
        if key in seen_doc_pages:
            continue
        seen_doc_pages.add(key)
        selected.append(candidate)
        if len(selected) >= max_pages:
            break

    return selected
