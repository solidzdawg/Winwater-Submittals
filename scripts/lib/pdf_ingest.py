from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any
import re

import fitz


SHEET_PATTERNS = [
    re.compile(r"\b([A-Z]{1,3}[\-.]?\d{1,3}(?:\.\d{1,2})?)\b"),
    re.compile(r"\b(SHEET\s+[A-Z]{1,3}[\-.]?\d{1,3}(?:\.\d{1,2})?)\b", re.IGNORECASE),
]

KEYWORD_GROUPS = {
    "schedule": ("schedule", "equipment schedule", "fixture schedule", "valve schedule"),
    "notes": ("general notes", "keyed notes", "note:", "notes:"),
    "legend": ("legend", "abbreviations", "symbols"),
    "detail": ("detail", "section", "elevation"),
    "plan": ("floor plan", "site plan", "plumbing plan", "mechanical plan", "electrical plan"),
    "specifications": ("section ", "part 1", "part 2", "part 3", "summary of work"),
}


@dataclass
class PageInventory:
    document_path: str
    document_kind: str
    page_number: int
    page_label: str
    sheet_id: str | None
    classifications: list[str]
    text_excerpt: str
    block_count: int
    word_count: int
    drawing_count: int
    image_path: str
    blocks: list[dict[str, Any]]


def slugify(value: str) -> str:
    cleaned = re.sub(r"[^A-Za-z0-9]+", "-", value).strip("-")
    return cleaned.lower() or "document"


def normalize_whitespace(text: str) -> str:
    text = text.replace("\r", "\n")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def detect_sheet_id(text: str, page_label: str) -> str | None:
    head = "\n".join(text.splitlines()[:18])
    for candidate in (page_label, head):
        if not candidate:
            continue
        for pattern in SHEET_PATTERNS:
            match = pattern.search(candidate)
            if match:
                return match.group(1).upper().replace("SHEET ", "")
    return None


def classify_page(text: str, drawing_count: int) -> list[str]:
    lowered = text.lower()
    classes: list[str] = []
    for label, keywords in KEYWORD_GROUPS.items():
        if any(keyword in lowered for keyword in keywords):
            classes.append(label)
    if drawing_count > 100 and "plan" not in classes:
        classes.append("drawing-heavy")
    if not classes:
        classes.append("unclassified")
    return classes


def build_document_inventory(
    pdf_path: Path,
    output_dir: Path,
    kind: str = "drawings",
    dpi: int = 150,
) -> dict[str, Any]:
    pdf_path = pdf_path.resolve()
    image_dir = output_dir / "page-images" / slugify(pdf_path.stem)
    image_dir.mkdir(parents=True, exist_ok=True)

    document = fitz.open(pdf_path)
    pages: list[dict[str, Any]] = []

    for index, page in enumerate(document):
        page_number = index + 1
        page_label = page.get_label() or str(page_number)
        text = normalize_whitespace(page.get_text("text", sort=True))
        blocks_raw = page.get_text("blocks", sort=True)
        words = page.get_text("words", sort=True)

        try:
            drawing_count = len(page.get_drawings())
        except Exception:
            drawing_count = 0

        clipped_blocks: list[dict[str, Any]] = []
        for block in blocks_raw[:50]:
            x0, y0, x1, y1, block_text, *_rest = block
            cleaned = normalize_whitespace(str(block_text))
            if not cleaned:
                continue
            clipped_blocks.append(
                {
                    "bbox": [round(x0, 1), round(y0, 1), round(x1, 1), round(y1, 1)],
                    "text": cleaned[:500],
                }
            )

        pixmap = page.get_pixmap(dpi=dpi, alpha=False)
        image_path = image_dir / f"page-{page_number:03d}.png"
        pixmap.save(image_path)

        record = PageInventory(
            document_path=pdf_path.name,
            document_kind=kind,
            page_number=page_number,
            page_label=str(page_label),
            sheet_id=detect_sheet_id(text, str(page_label)),
            classifications=classify_page(text, drawing_count),
            text_excerpt=text[:4000],
            block_count=len(clipped_blocks),
            word_count=len(words),
            drawing_count=drawing_count,
            image_path=image_path.as_posix(),
            blocks=clipped_blocks,
        )
        pages.append(asdict(record))

    document.close()
    return {
        "document_path": pdf_path.name,
        "document_kind": kind,
        "page_count": len(pages),
        "pages": pages,
    }


def build_inventory_summary(inventory: dict[str, Any]) -> str:
    lines: list[str] = []
    for document in inventory.get("documents", []):
        lines.append(
            f"Document: {document['document_path']} ({document['document_kind']}, {document['page_count']} pages)"
        )
        for page in document.get("pages", []):
            classes = ", ".join(page["classifications"])
            excerpt = page["text_excerpt"].replace("\n", " ")[:280]
            lines.append(
                f"- page {page['page_number']} label={page['page_label']} sheet={page['sheet_id']} classes={classes}: {excerpt}"
            )
    return "\n".join(lines)
