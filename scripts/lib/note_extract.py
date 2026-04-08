from __future__ import annotations

from typing import Any
import re

from scripts.lib.pdf_ingest import normalize_whitespace


NUMBERED_NOTE_RE = re.compile(r"^(?:NOTE\s*)?(\d{1,3}|[A-Z]{1,2})[\).:\-]\s+(.*)$", re.IGNORECASE)
INLINE_NOTE_RE = re.compile(r"\b(?:KEYED\s+)?NOTE\s*(\d{1,3}|[A-Z]{1,2})\b[:\- ]*(.*)$", re.IGNORECASE)
SPEC_SECTION_RE = re.compile(r"\b(\d{2}\s?\d{2}\s?\d{2})\b")


def extract_notes_from_inventory(inventory: dict[str, Any]) -> list[dict[str, Any]]:
    notes: list[dict[str, Any]] = []
    seen: set[tuple[str, int, str, str]] = set()

    for document in inventory.get("documents", []):
        for page in document.get("pages", []):
            page_classes = set(page.get("classifications", []))
            candidate_blocks = page.get("blocks", [])
            for block in candidate_blocks:
                block_text = normalize_whitespace(block.get("text", ""))
                if not block_text:
                    continue

                for raw_line in block_text.splitlines() or [block_text]:
                    line = normalize_whitespace(raw_line)
                    if not line:
                        continue

                    match = NUMBERED_NOTE_RE.match(line) or INLINE_NOTE_RE.search(line)
                    if not match and "notes" not in page_classes and "legend" not in page_classes:
                        continue
                    if not match:
                        continue

                    note_id = str(match.group(1)).upper()
                    text = normalize_whitespace(match.group(2))
                    if not text:
                        continue

                    signature = (document["document_path"], int(page["page_number"]), note_id, text)
                    if signature in seen:
                        continue
                    seen.add(signature)

                    notes.append(
                        {
                            "document_path": document["document_path"],
                            "page_number": int(page["page_number"]),
                            "page_label": str(page["page_label"]),
                            "sheet_id": page.get("sheet_id"),
                            "note_id": note_id,
                            "text": text,
                            "spec_sections": sorted({normalize_spec_section(m) for m in SPEC_SECTION_RE.findall(text)}),
                        }
                    )

    return sorted(notes, key=lambda row: (row["document_path"], row["page_number"], row["note_id"]))


def normalize_spec_section(raw: str) -> str:
    digits = re.findall(r"\d+", raw)
    if len(digits) >= 3:
        return f"{digits[0].zfill(2)} {digits[1].zfill(2)} {digits[2].zfill(2)}"
    return normalize_whitespace(raw)


def summarize_notes(notes: list[dict[str, Any]], limit: int = 60) -> str:
    lines: list[str] = []
    for note in notes[:limit]:
        sections = f" sections={','.join(note['spec_sections'])}" if note.get("spec_sections") else ""
        lines.append(
            f"- {note['document_path']} page {note['page_number']} sheet={note.get('sheet_id')} note={note['note_id']}{sections}: {note['text'][:220]}"
        )
    return "\n".join(lines)
