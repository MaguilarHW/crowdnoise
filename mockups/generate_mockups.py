#!/usr/bin/env python3
"""
Generate simple dark-mode SVG UI mockups for crowd·noise.
No deps; writes .svg files into ./mockups
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


ROOT = Path(__file__).resolve().parent


@dataclass(frozen=True)
class Theme:
    bg: str = "#0b0b0d"
    panel: str = "#111114"
    stroke: str = "#2a2a33"
    text: str = "#f2f2f2"
    muted: str = "#b6b6bf"
    faint: str = "#7a7a86"
    accent: str = "#ffffff"  # keep it [untitled]-neutral


T = Theme()


def svg_header(w: int = 1170, h: int = 2532) -> str:
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}">
<defs>
  <style>
    .bg {{ fill: {T.bg}; }}
    .panel {{ fill: {T.panel}; stroke: {T.stroke}; stroke-width: 2; }}
    .rule {{ stroke: {T.stroke}; stroke-width: 2; }}
    .title {{ fill: {T.text}; font: 600 44px -apple-system, BlinkMacSystemFont, "SF Pro Display", "Helvetica Neue", Arial, sans-serif; letter-spacing: 0.4px; }}
    .h2 {{ fill: {T.text}; font: 600 32px -apple-system, BlinkMacSystemFont, "SF Pro Display", "Helvetica Neue", Arial, sans-serif; }}
    .body {{ fill: {T.text}; font: 400 28px -apple-system, BlinkMacSystemFont, "SF Pro Text", "Helvetica Neue", Arial, sans-serif; }}
    .muted {{ fill: {T.muted}; font: 400 24px -apple-system, BlinkMacSystemFont, "SF Pro Text", "Helvetica Neue", Arial, sans-serif; }}
    .faint {{ fill: {T.faint}; font: 400 22px -apple-system, BlinkMacSystemFont, "SF Pro Text", "Helvetica Neue", Arial, sans-serif; }}
    .pill {{ fill: transparent; stroke: {T.stroke}; stroke-width: 2; rx: 999; }}
    .pillText {{ fill: {T.text}; font: 500 22px -apple-system, BlinkMacSystemFont, "SF Pro Text", "Helvetica Neue", Arial, sans-serif; letter-spacing: 0.3px; }}
    .cta {{ fill: {T.text}; font: 600 26px -apple-system, BlinkMacSystemFont, "SF Pro Text", "Helvetica Neue", Arial, sans-serif; }}
    .ctaBox {{ fill: {T.text}; rx: 20; }}
    .ctaBoxText {{ fill: {T.bg}; font: 700 26px -apple-system, BlinkMacSystemFont, "SF Pro Text", "Helvetica Neue", Arial, sans-serif; }}
  </style>
</defs>
"""


def phone_frame() -> str:
    # subtle phone edge; keep minimal
    return f"""
<rect x="60" y="60" width="1050" height="2412" rx="72" class="panel"/>
<rect x="60" y="60" width="1050" height="2412" rx="72" fill="none" stroke="{T.stroke}" stroke-width="2"/>
"""


def topbar(title: str) -> str:
    return f"""
<text x="120" y="170" class="title">{title}</text>
<text x="1040" y="170" text-anchor="end" class="muted">•••</text>
<line x1="120" y1="220" x2="1050" y2="220" class="rule"/>
"""


def pill(x: int, y: int, w: int, label: str) -> str:
    return f"""
<rect x="{x}" y="{y}" width="{w}" height="54" rx="999" class="pill"/>
<text x="{x + 18}" y="{y + 36}" class="pillText">{label}</text>
"""


def card(x: int, y: int, w: int, h: int, title: str, subtitle: str) -> str:
    return f"""
<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="28" fill="#0f0f13" stroke="{T.stroke}" stroke-width="2"/>
<text x="{x + 26}" y="{y + 56}" class="h2">{title}</text>
<text x="{x + 26}" y="{y + 92}" class="muted">{subtitle}</text>
"""


def cta(x: int, y: int, w: int, label: str) -> str:
    return f"""
<rect x="{x}" y="{y}" width="{w}" height="88" class="ctaBox"/>
<text x="{x + w/2:.1f}" y="{y + 57}" text-anchor="middle" class="ctaBoxText">{label}</text>
"""


def screen_home() -> str:
    body = [svg_header(), '<rect x="0" y="0" width="1170" height="2532" class="bg"/>', phone_frame(), topbar("crowd·noise")]

    body.append('<text x="120" y="280" class="muted">groups + active projects</text>')
    body.append(pill(120, 320, 220, "all"))
    body.append(pill(360, 320, 260, "active"))
    body.append(pill(640, 320, 300, "saved samples"))

    body.append('<text x="120" y="460" class="h2">your groups</text>')
    body.append(card(120, 510, 930, 180, "kitchen drums", "3 friends • 2 active projects"))
    body.append(card(120, 710, 930, 180, "hallway choir", "5 friends • 1 active project"))

    body.append('<text x="120" y="970" class="h2">active projects</text>')
    body.append(card(120, 1020, 930, 210, "ye (remake)", "progress: 42% cover revealed"))
    body.append('<text x="146" y="1160" class="faint">needs: kick, snare, keys, vocal texture</text>')

    body.append(card(120, 1250, 930, 210, "carti (too hard)", "progress: 8% cover revealed"))
    body.append('<text x="146" y="1390" class="faint">needs: hi-hats, glitch, adlibs</text>')

    body.append(cta(120, 2260, 930, "start a new project"))
    body.append('<text x="120" y="2385" class="faint">lowercase. no clutter. one thing at a time.</text>')

    body.append("</svg>")
    return "".join(body)


def screen_sample_editing() -> str:
    body = [svg_header(), '<rect x="0" y="0" width="1170" height="2532" class="bg"/>', phone_frame(), topbar("sample editing")]

    body.append('<text x="120" y="280" class="muted">trim (0.1s - 10s) • realtime preview</text>')

    # waveform placeholder
    body.append('<rect x="120" y="330" width="930" height="260" rx="28" fill="#0f0f13" stroke="#2a2a33" stroke-width="2"/>')
    body.append('<text x="146" y="390" class="faint">waveform</text>')
    for i in range(30):
        x = 160 + i * 28
        h = 40 + (i * 13) % 160
        y = 560 - h
        body.append(f'<rect x="{x}" y="{y}" width="10" height="{h}" fill="#2a2a33" rx="4"/>')
    # trim handles
    body.append('<rect x="170" y="350" width="6" height="220" fill="#f2f2f2" rx="3"/>')
    body.append('<rect x="940" y="350" width="6" height="220" fill="#f2f2f2" rx="3"/>')

    body.append('<text x="120" y="660" class="h2">sound changer</text>')
    body.append(card(120, 710, 930, 150, "tone", "warm  •  neutral  •  bright"))
    body.append(card(120, 880, 930, 150, "shape", "punch  •  soft  •  clipped"))
    body.append(card(120, 1050, 930, 150, "space", "dry  •  room  •  haze"))

    body.append('<text x="120" y="1250" class="muted">preview</text>')
    body.append('<rect x="120" y="1290" width="930" height="110" rx="28" fill="#0f0f13" stroke="#2a2a33" stroke-width="2"/>')
    body.append('<text x="160" y="1360" class="body">▶︎</text>')
    body.append('<text x="220" y="1363" class="muted">table tap — edited</text>')

    body.append(cta(120, 2260, 930, "save to shared library"))
    body.append("</svg>")
    return "".join(body)


def screen_provenance_original() -> str:
    body = [svg_header(), '<rect x="0" y="0" width="1170" height="2532" class="bg"/>', phone_frame(), topbar("provenance")]

    body.append('<text x="120" y="280" class="muted">tap any sound to rewind to the original</text>')

    body.append(card(120, 330, 930, 190, "current sound", "snare — “kitchen drum”"))
    body.append('<text x="146" y="470" class="faint">derived from: clip #12 • 0.6s • @miles</text>')

    body.append('<text x="120" y="590" class="h2">chain</text>')
    # chain nodes
    nodes = [
        ("original clip", "video + audio • recorded 9:14pm"),
        ("trim", "0.45s - 1.05s"),
        ("tone", "warm"),
        ("shape", "punch"),
        ("export", "snare.wav"),
    ]
    y = 650
    for i, (a, b) in enumerate(nodes):
        body.append(f'<rect x="120" y="{y}" width="930" height="112" rx="24" fill="#0f0f13" stroke="#2a2a33" stroke-width="2"/>')
        body.append(f'<text x="150" y="{y+48}" class="body">{a}</text>')
        body.append(f'<text x="150" y="{y+84}" class="faint">{b}</text>')
        if i < len(nodes) - 1:
            body.append(f'<line x1="170" y1="{y+112}" x2="170" y2="{y+146}" class="rule"/>')
        y += 140

    body.append('<text x="120" y="1545" class="h2">original</text>')
    body.append('<rect x="120" y="1595" width="930" height="420" rx="28" fill="#0f0f13" stroke="#2a2a33" stroke-width="2"/>')
    body.append('<text x="146" y="1665" class="faint">video preview</text>')
    body.append('<text x="146" y="1745" class="body">▶︎</text>')
    body.append('<text x="220" y="1748" class="muted">play original clip (0.6s)</text>')

    body.append(cta(120, 2260, 930, "credit + save provenance card"))
    body.append("</svg>")
    return "".join(body)


def screen_voting() -> str:
    body = [svg_header(), '<rect x="0" y="0" width="1170" height="2532" class="bg"/>', phone_frame(), topbar("voting")]

    body.append('<text x="120" y="280" class="muted">vote on creativity • keep it simple</text>')
    body.append(card(120, 330, 930, 240, "weekly remakes", "most creative uses of real sounds"))
    body.append('<text x="146" y="475" class="faint">this week: “ye” bar 3</text>')

    # entry card
    body.append('<rect x="120" y="610" width="930" height="540" rx="28" fill="#0f0f13" stroke="#2a2a33" stroke-width="2"/>')
    body.append('<text x="146" y="680" class="h2">kitchen drums</text>')
    body.append('<text x="146" y="724" class="muted">used: basketball dribble as kick • key clack as hat</text>')
    body.append('<rect x="146" y="770" width="878" height="160" rx="24" fill="#0b0b0d" stroke="#2a2a33" stroke-width="2"/>')
    body.append('<text x="176" y="860" class="muted">▶︎ listen</text>')
    body.append('<text x="146" y="980" class="faint">tap to see provenance</text>')

    body.append('<text x="146" y="1060" class="muted">creativity</text>')
    # rating pills
    body.append(pill(146, 1086, 150, "1"))
    body.append(pill(316, 1086, 150, "2"))
    body.append(pill(486, 1086, 150, "3"))
    body.append(pill(656, 1086, 150, "4"))
    body.append(pill(826, 1086, 198, "5"))

    body.append(cta(120, 2260, 930, "submit vote"))
    body.append("</svg>")
    return "".join(body)


def main() -> int:
    screens = {
        "home.svg": screen_home(),
        "sample_editing.svg": screen_sample_editing(),
        "provenance_original.svg": screen_provenance_original(),
        "voting_creativity.svg": screen_voting(),
    }

    for name, svg in screens.items():
        (ROOT / name).write_text(svg, encoding="utf-8")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())

