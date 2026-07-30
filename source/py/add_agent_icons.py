"""Add the monochrome agent icons to Maple Mono's variable font sources."""

from dataclasses import dataclass
from pathlib import Path
import sys
import xml.etree.ElementTree as ET

from fontTools.pens.cu2quPen import Cu2QuPen
from fontTools.pens.transformPen import TransformPen
from fontTools.pens.ttGlyphPen import TTGlyphPen
from fontTools.svgLib.path import parse_path
from fontTools.ttLib import TTFont


ROOT = Path(__file__).resolve().parents[2]
ADVANCE_WIDTH = 600
ICON_BOX = 700
ICON_BOTTOM = 20
MAX_CURVE_ERROR = 1.0


@dataclass(frozen=True)
class Icon:
    name: str
    codepoint: int
    svg_path: Path

    @property
    def glyph_name(self) -> str:
        return f"agent.{self.name.lower()}"


ICONS = (
    Icon("Claude", 0xF2000, ROOT / "svg" / "claude.svg"),
    Icon("Codex", 0xF2001, ROOT / "svg" / "codex.svg"),
    Icon("Gemini", 0xF2002, ROOT / "svg" / "gemini.svg"),
    Icon("OpenCode", 0xF2003, ROOT / "svg" / "opencode.svg"),
    Icon("Pi", 0xF2004, ROOT / "svg" / "pi.svg"),
)

FONT_PATHS = (
    ROOT / "source" / "MapleMono[wght]-VF.ttf",
    ROOT / "source" / "MapleMono-Italic[wght]-VF.ttf",
)


def svg_to_glyph(svg_path: Path):
    root = ET.parse(svg_path).getroot()
    view_box = root.get("viewBox")
    if not view_box:
        raise ValueError(f"{svg_path} has no viewBox")

    min_x, min_y, width, height = (float(value) for value in view_box.split())
    if width <= 0 or height <= 0:
        raise ValueError(f"{svg_path} has an invalid viewBox")

    scale = ICON_BOX / max(width, height)
    scaled_width = width * scale
    scaled_height = height * scale
    x_left = (ADVANCE_WIDTH - scaled_width) / 2
    y_bottom = ICON_BOTTOM + (ICON_BOX - scaled_height) / 2
    transform = (
        scale,
        0,
        0,
        -scale,
        x_left - min_x * scale,
        y_bottom + (min_y + height) * scale,
    )

    glyph_pen = TTGlyphPen(None)
    curve_pen = Cu2QuPen(glyph_pen, MAX_CURVE_ERROR)
    pen = TransformPen(curve_pen, transform)
    path_count = 0
    for element in root.iter():
        if element.tag.rsplit("}", 1)[-1] != "path":
            continue
        path_data = element.get("d")
        if path_data:
            parse_path(path_data, pen)
            path_count += 1

    if not path_count:
        raise ValueError(f"{svg_path} has no drawable paths")
    return glyph_pen.glyph()


def add_icons(font_path: Path) -> None:
    font = TTFont(font_path, recalcTimestamp=False)
    # Decompile variable tables before extending the glyph order. Their binary
    # headers still contain the original glyph count at this point.
    gvar_variations = font["gvar"].variations if "gvar" in font else None
    hvar_mapping = None
    if "HVAR" in font and font["HVAR"].table.AdvWidthMap is not None:
        hvar_mapping = font["HVAR"].table.AdvWidthMap.mapping

    glyph_order = font.getGlyphOrder()
    glyphs = font["glyf"]
    metrics = font["hmtx"].metrics

    unicode_cmaps = [
        table
        for table in font["cmap"].tables
        if table.isUnicode() and table.format in (12, 13)
    ]
    if not unicode_cmaps:
        raise ValueError(f"{font_path} has no full-Unicode cmap")

    for icon in ICONS:
        for cmap in unicode_cmaps:
            current_name = cmap.cmap.get(icon.codepoint)
            if current_name not in (None, icon.glyph_name):
                raise ValueError(
                    f"U+{icon.codepoint:05X} is already mapped to {current_name}"
                )

        glyph = svg_to_glyph(icon.svg_path)
        if icon.glyph_name not in glyph_order:
            glyph_order.append(icon.glyph_name)
        glyphs[icon.glyph_name] = glyph
        glyph.recalcBounds(glyphs)
        metrics[icon.glyph_name] = (ADVANCE_WIDTH, glyph.xMin)

        for cmap in unicode_cmaps:
            cmap.cmap[icon.codepoint] = icon.glyph_name
        if gvar_variations is not None:
            gvar_variations[icon.glyph_name] = []
        if hvar_mapping is not None:
            hvar_mapping[icon.glyph_name] = 0

    font.setGlyphOrder(glyph_order)
    font["maxp"].numGlyphs = len(glyph_order)
    font.save(font_path)
    font.close()


def verify(font_path: Path) -> None:
    font = TTFont(font_path)
    best_cmap = font.getBestCmap()
    for icon in ICONS:
        actual = best_cmap.get(icon.codepoint)
        if actual != icon.glyph_name:
            raise ValueError(
                f"{font_path}: U+{icon.codepoint:05X} maps to {actual}, "
                f"expected {icon.glyph_name}"
            )
        if font["hmtx"][icon.glyph_name][0] != ADVANCE_WIDTH:
            raise ValueError(f"{font_path}: {icon.glyph_name} is not monospaced")
    font.close()


def main() -> int:
    for font_path in FONT_PATHS:
        print(f"Adding agent icons to {font_path.relative_to(ROOT)}")
        add_icons(font_path)
        verify(font_path)
    return 0


if __name__ == "__main__":
    sys.exit(main())
