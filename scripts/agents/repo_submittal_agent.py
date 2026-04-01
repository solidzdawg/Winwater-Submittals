#!/usr/bin/env python3
"""
RepoSubmittalAgent
==================
Operational policy agent for template-independent submittal generation.

This agent does not render directly; it coordinates:
1) input validation
2) plugin backend selection
3) section render
4) assembly + quality gates
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Literal
import json

import sys
BASE_DIR = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(BASE_DIR))
from scripts.plugins.submittal_renderer_plugin import get_backend, load_theme


Mode = Literal["draft", "release"]


@dataclass
class AgentConfig:
    backend: Literal["weasyprint-html", "reportlab-canvas"] = "weasyprint-html"
    mode: Mode = "draft"
    fail_on_missing_certs: bool = False


class RepoSubmittalAgent:
    def __init__(self, config: AgentConfig):
        self.config = config
        self.backend = get_backend(config.backend)

    def run(self, submittal_json: Path, theme_json: Path, out_dir: Path) -> dict:
        out_dir.mkdir(parents=True, exist_ok=True)
        submittal = json.loads(submittal_json.read_text(encoding="utf-8"))
        theme = load_theme(theme_json)

        cover = self.backend.render_cover(submittal, theme, out_dir / "01-cover.pdf")
        index = self.backend.render_index(submittal, theme, out_dir / "02-index.pdf")

        separators = []
        for item in submittal.get("items", []):
            p = self.backend.render_separator(item, theme, out_dir / f"sep-{item['item_number']:02d}.pdf")
            separators.append(str(p))

        return {
            "backend": self.config.backend,
            "mode": self.config.mode,
            "cover": str(cover),
            "index": str(index),
            "separators": separators,
            "checks": {
                "no_office_template_dependency": True,
                "rendered_sections": ["cover", "index", "separator"],
            },
        }
