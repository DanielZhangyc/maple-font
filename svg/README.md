# Agent icon glyphs

The SVG files in this directory are monochrome source artwork for custom Maple
Mono glyphs. They are embedded in both upright and italic variable font sources
by `source/py/add_agent_icons.py`.

| Agent | Code point | Shell escape | Glyph name |
| --- | --- | --- | --- |
| Claude | `U+F2000` | `\U000F2000` | `agent.claude` |
| Codex | `U+F2001` | `\U000F2001` | `agent.codex` |
| Gemini | `U+F2002` | `\U000F2002` | `agent.gemini` |
| OpenCode | `U+F2003` | `\U000F2003` | `agent.opencode` |
| Pi | `U+F2004` | `\U000F2004` | `agent.pi` |

These code points are in Unicode's Plane 15 Private Use Area and are outside
the ranges occupied by the Nerd Fonts 3.4.0 glyph set bundled by this branch.
