"""Inject custom AI agent icons into prepared UFO build sources."""

from __future__ import annotations

import xml.etree.ElementTree as ET
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING

from fontTools.pens.boundsPen import BoundsPen
from fontTools.pens.transformPen import TransformPen
from fontTools.svgLib.path import parse_path

if TYPE_CHECKING:
    from ufoLib2 import Font as UFOFont

ROOT = Path(__file__).resolve().parents[1]
ADVANCE_WIDTH = 600
ICON_CENTER_Y = 370


@dataclass(frozen=True, slots=True)
class Icon:
    name: str
    codepoint: int
    svg_path: Path
    optical_size: int
    optical_height: int | None = None

    @property
    def glyph_name(self) -> str:
        return f"agent.{self.name.lower()}"


ICONS = (
    Icon("Claude", 0xF2000, ROOT / "svg" / "claude.svg", 880),
    Icon("Codex", 0xF2001, ROOT / "svg" / "codex.svg", 820),
    Icon("Gemini", 0xF2002, ROOT / "svg" / "gemini.svg", 860),
    Icon("OpenCode", 0xF2003, ROOT / "svg" / "opencode.svg", 840),
    Icon("Pi", 0xF2004, ROOT / "svg" / "pi.svg", 840),
    Icon("DeepSeek", 0xF2005, ROOT / "svg" / "deepseek.svg", 960, 780),
    Icon("Kimi", 0xF2006, ROOT / "svg" / "kimi.svg", 840),
)


def _svg_paths(icon: Icon) -> tuple[str, ...]:
    root = ET.parse(icon.svg_path).getroot()
    paths = tuple(
        path
        for element in root.iter()
        if element.tag.rsplit("}", 1)[-1] == "path"
        and (path := element.get("d")) is not None
    )
    if not paths:
        raise ValueError(f"{icon.svg_path} has no drawable paths")
    return paths


def _icon_transform(
    icon: Icon,
    paths: tuple[str, ...],
) -> tuple[float, float, float, float, float, float]:
    bounds_pen = BoundsPen(None)
    for path in paths:
        parse_path(path, bounds_pen)
    if bounds_pen.bounds is None:
        raise ValueError(f"{icon.svg_path} has no drawable bounds")

    min_x, min_y, max_x, max_y = bounds_pen.bounds
    width = max_x - min_x
    height = max_y - min_y
    if icon.optical_height is None:
        scale_x = scale_y = icon.optical_size / max(width, height)
    else:
        scale_x = icon.optical_size / width
        scale_y = icon.optical_height / height
    scaled_width = width * scale_x
    scaled_height = height * scale_y
    x_left = (ADVANCE_WIDTH - scaled_width) / 2
    y_bottom = ICON_CENTER_Y - scaled_height / 2
    return (
        scale_x,
        0,
        0,
        -scale_y,
        x_left - min_x * scale_x,
        y_bottom + max_y * scale_y,
    )


def add_agent_icons(font: UFOFont) -> None:
    """Add the custom icons to one temporary UFO master."""
    icon_names = {icon.glyph_name for icon in ICONS}
    glyph_order = [name for name in font.glyphOrder if name not in icon_names]

    for icon in ICONS:
        collision = next(
            (
                glyph.name
                for glyph in font
                if icon.codepoint in glyph.unicodes and glyph.name != icon.glyph_name
            ),
            None,
        )
        if collision is not None:
            raise ValueError(f"U+{icon.codepoint:05X} is already mapped to {collision}")

        if icon.glyph_name in font:
            del font[icon.glyph_name]
        glyph = font.newGlyph(icon.glyph_name)
        glyph.width = ADVANCE_WIDTH
        glyph.unicodes = [icon.codepoint]

        paths = _svg_paths(icon)
        pen = TransformPen(glyph.getPen(), _icon_transform(icon, paths))
        for path in paths:
            parse_path(path, pen)
        glyph_order.append(icon.glyph_name)

    font.glyphOrder = glyph_order
