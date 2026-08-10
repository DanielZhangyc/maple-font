from __future__ import annotations

import unittest

from ufoLib2 import Font as UFOFont

from scripts.add_agent_icons import ADVANCE_WIDTH, ICONS, add_agent_icons


class AgentIconTest(unittest.TestCase):
    def test_adds_every_icon_with_stable_metrics_and_order(self) -> None:
        font = UFOFont()
        font.newGlyph(".notdef")

        add_agent_icons(font)
        add_agent_icons(font)

        expected_names = [icon.glyph_name for icon in ICONS]
        self.assertEqual(font.glyphOrder[-len(ICONS) :], expected_names)
        for icon in ICONS:
            glyph = font[icon.glyph_name]
            self.assertEqual(glyph.width, ADVANCE_WIDTH)
            self.assertEqual(glyph.unicodes, [icon.codepoint])
            self.assertGreater(len(glyph), 0)

    def test_rejects_codepoint_collision(self) -> None:
        font = UFOFont()
        occupied = font.newGlyph("occupied")
        occupied.unicodes = [ICONS[0].codepoint]

        with self.assertRaisesRegex(ValueError, "already mapped to occupied"):
            add_agent_icons(font)


if __name__ == "__main__":
    unittest.main()
