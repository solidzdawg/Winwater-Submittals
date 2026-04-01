#!/usr/bin/env python3
"""
SubmittalRendererPlugin
=======================
Template-independent rendering plugin for Winwater-style submittals.

This module defines:
- A backend-agnostic render contract
- Render theme tokens
- Two backend adapters (WeasyPrint HTML/CSS and ReportLab)

It is intentionally composable so orchestrators/agents can call one plugin API
without knowing which renderer is active.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Protocol, Literal, Any
import json


BackendName = Literal["weasyprint-html", "reportlab-canvas"]


@dataclass
class RenderTheme:
    name: str
    page_size: str
    margin_in: dict[str, float]
    fonts: dict[str, str]
    font_sizes_pt: dict[str, float]
    colors: dict[str, str]
    spacing_pt: dict[str, float]


class RenderBackend(Protocol):
    backend_name: BackendName

    def render_cover(self, submittal: dict[str, Any], theme: RenderTheme, out_pdf: Path) -> Path:
        ...

    def render_index(self, submittal: dict[str, Any], theme: RenderTheme, out_pdf: Path) -> Path:
        ...

    def render_separator(self, item: dict[str, Any], theme: RenderTheme, out_pdf: Path) -> Path:
        ...


class WeasyprintHtmlBackend:
    backend_name: BackendName = "weasyprint-html"

    def render_cover(self, submittal: dict[str, Any], theme: RenderTheme, out_pdf: Path) -> Path:
        from weasyprint import HTML

        html = f"""
        <html><body style=\"font-family:{theme.fonts['body']}; margin:0;\">
          <h1 style=\"font-size:{theme.font_sizes_pt['title']}pt;\">{submittal['submittal_title']}</h1>
          <p>Project: {submittal['project']['name']}</p>
          <p>Submittal: {submittal['submittal_number']}</p>
        </body></html>
        """
        HTML(string=html).write_pdf(str(out_pdf))
        return out_pdf

    def render_index(self, submittal: dict[str, Any], theme: RenderTheme, out_pdf: Path) -> Path:
        from weasyprint import HTML

        rows = "".join(
            f"<tr><td>{i['item_number']}</td><td>{i['description']}</td><td>{i['manufacturer']}</td></tr>"
            for i in submittal["items"]
        )
        html = f"<html><body><table>{rows}</table></body></html>"
        HTML(string=html).write_pdf(str(out_pdf))
        return out_pdf

    def render_separator(self, item: dict[str, Any], theme: RenderTheme, out_pdf: Path) -> Path:
        from weasyprint import HTML

        html = f"<html><body><h1>ITEM {item['item_number']}</h1><h2>{item['description']}</h2></body></html>"
        HTML(string=html).write_pdf(str(out_pdf))
        return out_pdf


class ReportlabCanvasBackend:
    backend_name: BackendName = "reportlab-canvas"

    def render_cover(self, submittal: dict[str, Any], theme: RenderTheme, out_pdf: Path) -> Path:
        from reportlab.lib.pagesizes import letter
        from reportlab.pdfgen import canvas

        c = canvas.Canvas(str(out_pdf), pagesize=letter)
        c.setFont("Helvetica-Bold", theme.font_sizes_pt.get("title", 18))
        c.drawString(72, 720, submittal["submittal_title"])
        c.setFont("Helvetica", theme.font_sizes_pt.get("body", 11))
        c.drawString(72, 700, f"Project: {submittal['project']['name']}")
        c.drawString(72, 684, f"Submittal: {submittal['submittal_number']}")
        c.showPage()
        c.save()
        return out_pdf

    def render_index(self, submittal: dict[str, Any], theme: RenderTheme, out_pdf: Path) -> Path:
        from reportlab.lib.pagesizes import letter
        from reportlab.pdfgen import canvas

        c = canvas.Canvas(str(out_pdf), pagesize=letter)
        y = 740
        c.setFont("Helvetica-Bold", 14)
        c.drawString(72, y, "Submittal Index")
        y -= 26
        c.setFont("Helvetica", 10)
        for item in submittal["items"]:
            c.drawString(72, y, f"{item['item_number']:>2}  {item['description']} ({item['manufacturer']})")
            y -= 14
            if y < 72:
                c.showPage()
                y = 740
        c.showPage()
        c.save()
        return out_pdf

    def render_separator(self, item: dict[str, Any], theme: RenderTheme, out_pdf: Path) -> Path:
        from reportlab.lib.pagesizes import letter
        from reportlab.pdfgen import canvas

        c = canvas.Canvas(str(out_pdf), pagesize=letter)
        c.setFont("Helvetica-Bold", 42)
        c.drawCentredString(306, 440, f"ITEM {item['item_number']}")
        c.setFont("Helvetica-Bold", 20)
        c.drawCentredString(306, 390, item["description"])
        c.showPage()
        c.save()
        return out_pdf


def load_theme(path: Path) -> RenderTheme:
    data = json.loads(path.read_text(encoding="utf-8"))
    return RenderTheme(**data)


def get_backend(name: BackendName) -> RenderBackend:
    if name == "weasyprint-html":
        return WeasyprintHtmlBackend()
    if name == "reportlab-canvas":
        return ReportlabCanvasBackend()
    raise ValueError(f"Unknown backend: {name}")
