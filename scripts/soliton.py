#!/usr/bin/env python3
"""Render the GitHub contribution calendar as a Metal Gear style Soliton Radar SVG.

Usage: GITHUB_TOKEN=... GITHUB_USER=... python3 scripts/soliton.py [output_dir]
Standard library only, so it runs on a bare GitHub Actions runner.
"""
import json
import os
import sys
import urllib.request
from datetime import datetime, timezone

QUERY = """
query($login: String!) {
  user(login: $login) {
    contributionsCollection {
      contributionCalendar {
        totalContributions
        weeks { contributionDays { date contributionCount contributionLevel weekday } }
      }
    }
  }
}
"""

LEVEL_FILL = {
    "NONE": "#0B1A12",
    "FIRST_QUARTILE": "#0F3D26",
    "SECOND_QUARTILE": "#16663F",
    "THIRD_QUARTILE": "#22A565",
    "FOURTH_QUARTILE": "#46F0A0",
}

W, H = 1200, 420
CELL, PITCH = 16, 19
GX, GY = 84, 108
SWEEP = 9.0


def fetch_calendar():
    user = os.environ.get("GITHUB_USER") or os.environ["GITHUB_REPOSITORY_OWNER"]
    token = os.environ["GITHUB_TOKEN"]
    req = urllib.request.Request(
        "https://api.github.com/graphql",
        data=json.dumps({"query": QUERY, "variables": {"login": user}}).encode(),
        headers={"Authorization": f"bearer {token}", "Content-Type": "application/json", "User-Agent": "soliton-radar"},
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        payload = json.load(resp)
    if "errors" in payload:
        raise SystemExit(f"GraphQL error: {payload['errors']}")
    return payload["data"]["user"]["contributionsCollection"]["contributionCalendar"]


def streaks(days):
    counts = [d["contributionCount"] for d in days]
    end = len(counts)
    if end and counts[-1] == 0:
        end -= 1  # today may simply not have happened yet
    current = 0
    for c in reversed(counts[:end]):
        if c == 0:
            break
        current += 1
    longest = run = 0
    for c in counts:
        run = run + 1 if c else 0
        longest = max(longest, run)
    return current, longest


def render(calendar):
    weeks = calendar["weeks"]
    days = [d for w in weeks for d in w["contributionDays"]]
    total = calendar["totalContributions"]
    current, longest = streaks(days)
    peak = max(days, key=lambda d: d["contributionCount"])
    peak_label = datetime.strptime(peak["date"], "%Y-%m-%d").strftime("%d %b").upper()
    last30 = days[-30:]
    active30 = sum(1 for d in last30 if d["contributionCount"])
    grid_w = len(weeks) * PITCH
    synced = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

    cells, pings = [], []
    for col, week in enumerate(weeks):
        for d in week["contributionDays"]:
            x = GX + col * PITCH
            y = GY + d["weekday"] * PITCH
            cells.append(f'<rect x="{x}" y="{y}" width="{CELL}" height="{CELL}" fill="{LEVEL_FILL[d["contributionLevel"]]}"/>')
            if d["contributionCount"]:
                delay = SWEEP * (col * PITCH + CELL / 2) / grid_w
                pings.append(f'<rect class="p" x="{x}" y="{y}" width="{CELL}" height="{CELL}" style="animation-delay:{delay:.2f}s"/>')

    months, prev = [], None
    for col, week in enumerate(weeks):
        m = datetime.strptime(week["contributionDays"][0]["date"], "%Y-%m-%d").strftime("%b").upper()
        if m != prev:
            months.append((col, m))
            prev = m
    if len(months) > 1 and months[1][0] - months[0][0] < 3:
        months.pop(0)
    month_txt = "".join(f'<text x="{GX + c * PITCH}" y="{GY - 12}" class="m dim" font-size="11" letter-spacing="2">{m}</text>' for c, m in months)

    day_txt = "".join(
        f'<text x="44" y="{GY + wd * PITCH + 12}" class="m dim" font-size="10" letter-spacing="1">{name}</text>'
        for wd, name in ((1, "MON"), (3, "WED"), (5, "FRI"))
    )

    last = weeks[-1]["contributionDays"][-1]
    lx = GX + (len(weeks) - 1) * PITCH - 3
    ly = GY + last["weekday"] * PITCH - 3
    lock = (
        f'<path d="M{lx} {ly + 6}V{ly}H{lx + 6}M{lx + 16} {ly}H{lx + 22}V{ly + 6}M{lx + 22} {ly + 16}V{ly + 22}H{lx + 16}M{lx + 6} {ly + 22}H{lx}V{ly + 16}" '
        f'class="lock" fill="none" stroke="#D8FFE9" stroke-width="1.5"/>'
    )

    legend_x = max(GX, GX + grid_w - 5 * 14 - 74)
    legend = f'<text x="{legend_x}" y="256" class="m dim" font-size="10" letter-spacing="2">LOW</text>'
    for i, fill in enumerate(LEVEL_FILL.values()):
        legend += f'<rect x="{legend_x + 40 + i * 14}" y="247" width="10" height="10" fill="{fill}"/>'
    legend += f'<text x="{legend_x + 40 + 5 * 14 + 6}" y="256" class="m dim" font-size="10" letter-spacing="2">HIGH</text>'

    def stat(x, label, value, unit=""):
        u = f'<tspan class="soft" font-size="16" dx="8">{unit}</tspan>' if unit else ""
        return (
            f'<text x="{x}" y="296" class="m dim" font-size="11" letter-spacing="3">{label}</text>'
            f'<text x="{x}" y="338" class="m hi" font-size="42" font-weight="700" filter="url(#glow)">{value}{u}</text>'
        )

    stats = (
        stat(44, "TOTAL CONTACTS // 12 MO", f"{total:,}")
        + stat(330, "CURRENT STREAK", str(current), "DAYS")
        + stat(616, "LONGEST STREAK // 12 MO", str(longest), "DAYS")
        + stat(902, f"PEAK DAY // {peak_label}", str(peak["contributionCount"]), "CONTACTS")
    )

    gauge = "".join(
        f'<rect x="{262 + i * 13}" y="372" width="10" height="14" fill="{"#46F0A0" if d["contributionCount"] else "#0F2A1C"}"/>'
        for i, d in enumerate(last30)
    )

    font = 'ui-monospace,SFMono-Regular,Menlo,Consolas,&quot;Liberation Mono&quot;,monospace'
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" role="img" aria-labelledby="t">
  <title id="t">Soliton radar. {total:,} contributions in the last 12 months, current streak {current} days, active on {active30} of the last {len(last30)} days.</title>
  <defs>
    <pattern id="grid" width="24" height="24" patternUnits="userSpaceOnUse"><path d="M24 0H0V24" fill="none" stroke="#46F0A0" stroke-opacity=".06"/></pattern>
    <pattern id="scan" width="4" height="4" patternUnits="userSpaceOnUse"><rect width="4" height="1" fill="#000" fill-opacity=".35"/></pattern>
    <radialGradient id="vig" cx="50%" cy="50%" r="75%"><stop offset="60%" stop-color="#000" stop-opacity="0"/><stop offset="100%" stop-color="#000" stop-opacity=".6"/></radialGradient>
    <linearGradient id="trail" x1="0" x2="1" y1="0" y2="0"><stop offset="0" stop-color="#46F0A0" stop-opacity="0"/><stop offset="1" stop-color="#46F0A0" stop-opacity=".28"/></linearGradient>
    <filter id="glow" x="-10%" y="-40%" width="120%" height="180%"><feGaussianBlur stdDeviation="2.5" result="b"/><feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge></filter>
    <clipPath id="clip"><rect x="{GX - 4}" y="{GY - 6}" width="{grid_w + 8}" height="{7 * PITCH + 8}"/></clipPath>
    <style>
      .m{{font-family:{font}}} .dim{{fill:#2FA36E}} .pri{{fill:#46F0A0}} .hi{{fill:#D8FFE9}} .soft{{fill:#8FD9B4}}
      .p{{fill:#D8FFE9;opacity:0;animation:ping {SWEEP}s linear infinite}}
      @keyframes ping{{0%{{opacity:0}}1%{{opacity:.95}}9%{{opacity:0}}100%{{opacity:0}}}}
      .beam{{animation:sweep {SWEEP}s linear infinite}}
      @keyframes sweep{{from{{transform:translateX({GX}px)}}to{{transform:translateX({GX + grid_w}px)}}}}
      .lock{{animation:blink 1.2s ease-in-out infinite}}
      .status{{animation:blink 1.6s ease-in-out infinite}}
      @keyframes blink{{50%{{opacity:.2}}}}
      @media (prefers-reduced-motion:reduce){{*{{animation:none!important}}}}
    </style>
  </defs>

  <rect width="{W}" height="{H}" fill="#050B08"/>
  <rect width="{W}" height="{H}" fill="url(#grid)"/>
  <rect x="16.5" y="16.5" width="1167" height="{H - 33}" fill="none" stroke="#1F6B4A"/>
  <path d="M16 46V16H46M1154 16H1184V46M1184 {H - 46}V{H - 16}H1154M46 {H - 16}H16V{H - 46}" fill="none" stroke="#46F0A0" stroke-width="3"/>

  <text x="44" y="50" class="m dim" font-size="13" letter-spacing="3">SOLITON RADAR // CONTACT LOG // LAST 12 MONTHS</text>
  <circle class="status" cx="996" cy="45" r="5" fill="#46F0A0"/>
  <text x="1156" y="50" text-anchor="end" class="m pri" font-size="13" letter-spacing="3">RADAR ACTIVE</text>
  <path d="M44 66H1156" stroke="#1F6B4A" stroke-dasharray="2 6"/>

  {month_txt}
  {day_txt}
  {"".join(cells)}
  {"".join(pings)}
  <g clip-path="url(#clip)"><g class="beam" style="transform:translateX({GX}px)">
    <rect x="-90" y="{GY - 6}" width="90" height="{7 * PITCH + 8}" fill="url(#trail)"/>
    <rect x="-1" y="{GY - 6}" width="2" height="{7 * PITCH + 8}" fill="#D8FFE9" fill-opacity=".9"/>
  </g></g>
  {lock}
  {legend}

  <path d="M44 272H1156" stroke="#1F6B4A" stroke-dasharray="2 6"/>
  {stats}
  <path d="M44 360H1156" stroke="#1F6B4A" stroke-dasharray="2 6"/>
  <text x="44" y="383" class="m dim" font-size="11" letter-spacing="3">ACTIVE DAYS // LAST {len(last30)}</text>
  {gauge}
  <text x="662" y="384" class="m pri" font-size="15" letter-spacing="2">{active30}/{len(last30)}</text>
  <text x="1156" y="383" text-anchor="end" class="m dim" font-size="10" letter-spacing="2">LAST SYNC {synced}</text>

  <rect width="{W}" height="{H}" fill="url(#scan)"/>
  <rect width="{W}" height="{H}" fill="url(#vig)"/>
</svg>
'''


def main():
    out_dir = sys.argv[1] if len(sys.argv) > 1 else "dist"
    os.makedirs(out_dir, exist_ok=True)
    svg = render(fetch_calendar())
    path = os.path.join(out_dir, "soliton-radar.svg")
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(svg)
    print(f"wrote {path} ({len(svg)} bytes)")


if __name__ == "__main__":
    main()
