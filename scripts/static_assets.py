#!/usr/bin/env python3
"""Generate the static codec-themed SVG assets used by the profile README.

Usage: python3 scripts/static_assets.py [output_dir]
Fetches brand icon paths (CC0, simple-icons) at build time so the SVGs are self-contained.
"""
import os
import re
import sys
import urllib.request

OUT = sys.argv[1] if len(sys.argv) > 1 else "assets"
FONT = 'ui-monospace,SFMono-Regular,Menlo,Consolas,&quot;Liberation Mono&quot;,monospace'

DEFS = """    <pattern id="grid" width="24" height="24" patternUnits="userSpaceOnUse"><path d="M24 0H0V24" fill="none" stroke="#46F0A0" stroke-opacity=".06"/></pattern>
    <pattern id="scan" width="4" height="4" patternUnits="userSpaceOnUse"><rect width="4" height="1" fill="#000" fill-opacity=".35"/></pattern>
    <filter id="glow" x="-10%" y="-40%" width="120%" height="180%"><feGaussianBlur stdDeviation="2" result="b"/><feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge></filter>"""

STYLE = f"""      .m{{font-family:{FONT}}} .dim{{fill:#2FA36E}} .pri{{fill:#46F0A0}} .hi{{fill:#D8FFE9}} .soft{{fill:#8FD9B4}}
      .cursor{{animation:cursor 1s steps(1) infinite}}
      .status{{animation:blink 1.6s ease-in-out infinite}}
      @keyframes cursor{{50%{{fill-opacity:0}}}}
      @keyframes blink{{50%{{opacity:.15}}}}
      @media (prefers-reduced-motion:reduce){{*{{animation:none!important}}}}"""

CURSOR = '<tspan dx="10" class="pri cursor">&#x2588;</tspan>'


def svg(w, h, title, body, extra_defs=""):
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}" role="img" aria-labelledby="t">
  <title id="t">{title}</title>
  <defs>
{DEFS}
{extra_defs}
    <style>
{STYLE}
    </style>
  </defs>
  <rect width="{w}" height="{h}" fill="#050B08"/>
  <rect width="{w}" height="{h}" fill="url(#grid)"/>
{body}
  <rect width="{w}" height="{h}" fill="url(#scan)"/>
</svg>
"""


def write(name, content):
    os.makedirs(OUT, exist_ok=True)
    with open(os.path.join(OUT, name), "w", encoding="utf-8") as fh:
        fh.write(content)
    print("wrote", name)


SECTIONS = [
    ("profile", "01", "PROFILE", "DOSSIER"),
    ("field-kit", "02", "FIELD KIT", "ACTIVE ASSETS"),
    ("loadout", "03", "LOADOUT", "EQUIPMENT"),
    ("protocol", "04", "PROTOCOL", "RULES OF ENGAGEMENT"),
    ("mission", "05", "MISSION", "CURRENT OBJECTIVE"),
    ("telemetry", "06", "TELEMETRY", "SOLITON RADAR"),
    ("channel", "07", "OPEN CHANNEL", "COMMS"),
]


def section_banner(slug, num, title, tag):
    body = f"""  <path d="M16 30V14H32M1168 14H1184V30M1184 52V68H1168M32 68H16V52" fill="none" stroke="#46F0A0" stroke-width="2"/>
  <rect x="40.5" y="20.5" width="62" height="40" fill="#0A1610" stroke="#46F0A0"/>
  <text x="71.5" y="50" text-anchor="middle" class="m pri" font-size="26" font-weight="700" filter="url(#glow)">{num}</text>
  <text x="126" y="51" class="m hi" font-size="28" font-weight="700" letter-spacing="8" filter="url(#glow)">{title}{CURSOR}</text>
  <text x="1160" y="46" text-anchor="end" class="m dim" font-size="12" letter-spacing="3">{tag}</text>
  <path d="M16 78H1184" stroke="#1F6B4A" stroke-dasharray="2 6"/>
  <rect x="16" y="77" width="120" height="2" fill="#46F0A0"/>"""
    write(f"sec-{slug}.svg", svg(1200, 84, f"{num} // {title}", body))


FILES = [("glint", "01", "GLINT", "CAPTURE"), ("whisker", "02", "WHISKER", "INPUT"), ("barback", "03", "BARBACK", "MENU BAR")]


def file_card(slug, num, name, kind):
    body = f"""  <rect x="1.5" y="1.5" width="397" height="69" fill="none" stroke="#1F6B4A"/>
  <path d="M1 16V1H16M384 1H399V16M399 56V71H384M16 71H1V56" fill="none" stroke="#46F0A0" stroke-width="2"/>
  <text x="20" y="24" class="m dim" font-size="12" letter-spacing="3">FILE {num} // {kind}</text>
  <text x="20" y="57" class="m hi" font-size="28" font-weight="700" letter-spacing="7" filter="url(#glow)">{name}</text>
  <circle class="status" cx="372" cy="22" r="4" fill="#46F0A0"/>"""
    write(f"file-{slug}.svg", svg(400, 72, f"File {num}: {name}", body))


ICONS = [
    ("swift", "SWIFT", "PRIMARY"), ("typescript", "TYPESCRIPT", "PRIMARY"), ("python", "PYTHON", "PRIMARY"), ("gnubash", "BASH", "PRIMARY"),
    ("react", "REACT", "SYSTEMS"), ("vite", "VITE", "SYSTEMS"), ("xcode", "XCODE", "SYSTEMS"), ("git", "GIT", "SYSTEMS"),
    ("githubactions", "ACTIONS", "SYSTEMS"), ("vercel", "VERCEL", "SYSTEMS"),
    ("githubcopilot", "COPILOT", "SUPPORT"), ("claude", "CLAUDE", "SUPPORT"),
]
GROUP_TITLES = {"PRIMARY": "PRIMARY // LANGUAGES", "SYSTEMS": "SYSTEMS // TOOLS", "SUPPORT": "SUPPORT // AI"}


def icon_path(name):
    url = f"https://cdn.jsdelivr.net/npm/simple-icons@latest/icons/{name}.svg"
    with urllib.request.urlopen(url, timeout=30) as resp:
        return "".join(re.findall(r'<path d="([^"]+)"', resp.read().decode()))


def equipment():
    slot, pitch, gap, x0, y0 = 78, 90, 24, 36, 56
    parts, xs, group_spans, x, prev = [], [], {}, x0, None
    for i, (icon, label, group) in enumerate(ICONS):
        if prev and group != prev:
            x += gap
        xs.append(x)
        group_spans.setdefault(group, [x, x])[1] = x + slot
        d = icon_path(icon)
        parts.append(
            f'<rect x="{x + .5}" y="{y0 + .5}" width="{slot}" height="{slot}" fill="#0A1610" stroke="#1F6B4A"/>'
            f'<text x="{x + 6}" y="{y0 + 14}" class="m dim" font-size="9" letter-spacing="1">{i + 1:02d}</text>'
            f'<g transform="translate({x + 21} {y0 + 21}) scale(1.5)"><path d="{d}" fill="#46F0A0"/></g>'
            f'<text x="{x + slot / 2}" y="{y0 + slot + 20}" text-anchor="middle" class="m soft" font-size="11" letter-spacing="1">{label}</text>'
        )
        x += pitch
        prev = group
    heads = "".join(
        f'<text x="{a}" y="38" class="m dim" font-size="12" letter-spacing="3">{GROUP_TITLES[g]}</text>'
        f'<path d="M{a} 46H{b}" stroke="#1F6B4A"/>'
        for g, (a, b) in group_spans.items()
    )
    positions = "".join(f"{i * 100 / len(xs):.4f}%{{transform:translateX({v - xs[0]}px)}}" for i, v in enumerate(xs))
    selector_style = (
        f"<style>.selector{{animation:select {len(xs) * 1.5}s steps(1) infinite}}"
        f"@keyframes select{{{positions}100%{{transform:translateX(0)}}}}</style>"
    )
    selector = (
        f'<rect class="selector" x="{xs[0] - 3}" y="{y0 - 3}" width="{slot + 7}" height="{slot + 7}" fill="none" stroke="#D8FFE9" stroke-width="2"/>'
    )
    h = 184
    body = (
        '  <rect x="16.5" y="16.5" width="1167" height="151" fill="none" stroke="#1F6B4A"/>\n'
        '  <path d="M16 36V16H36M1164 16H1184V36M1184 148V168H1164M36 168H16V148" fill="none" stroke="#46F0A0" stroke-width="2"/>\n'
        f"  {heads}\n  {''.join(parts)}\n  {selector}"
    )
    write("equipment.svg", svg(1200, h, "Equipment: " + ", ".join(l for _, l, _ in ICONS), body, selector_style))


if __name__ == "__main__":
    for s in SECTIONS:
        section_banner(*s)
    for f in FILES:
        file_card(*f)
    equipment()
