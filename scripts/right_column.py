"""Combine the repositories/traffic panel, the one-line contribution strip and the
profile-view badge into metrics/right-column.svg.

GitHub positions README images only with left/right floats, and several
right-floated images next to a stack of pinned cards will not stay in one
column. One combined image keeps the right column intact. Visits are still
counted by a 1x1 copy of the counter in the README; the number shown here is
refreshed each time the workflow runs.
"""
import base64
import re
import urllib.request

BADGE = ("https://komarev.com/ghpvc/?username=sherazahmadd&label=profile%20views"
         "&color=F5C518&labelColor=0d0d0d&style=flat-square")
W = 480
GAP = 12


def size(svg):
    m = re.search(r'<svg[^>]*?width="([\d.]+)"[^>]*?height="([\d.]+)"', svg, re.S)
    return float(m.group(1)), float(m.group(2))


def uri(svg):
    return "data:image/svg+xml;base64," + base64.b64encode(svg.encode("utf-8")).decode()


parts = [open("metrics/traffic.svg", encoding="utf-8").read(),
         open("metrics/contribution-line.svg", encoding="utf-8").read()]
try:
    req = urllib.request.Request(BADGE, headers={"User-Agent": "profile-metrics"})
    badge = urllib.request.urlopen(req, timeout=60).read().decode("utf-8")
except Exception as exc:                      # keep the previous badge if the counter is down
    print("badge fetch failed:", exc)
    old = open("metrics/right-column.svg", encoding="utf-8").read() if __import__("os").path.exists("metrics/right-column.svg") else ""
    m = re.findall(r'href="(data:image/svg\+xml;base64,[^"]+)"', old)
    badge = base64.b64decode(m[-1].split(",", 1)[1]).decode("utf-8") if len(m) == 3 else None


def restyle(svg):
    """Dark label, and a dark number on the yellow box: readable on light and dark pages."""
    svg = svg.replace('fill="#555"', 'fill="#0D0D0F"')
    texts = re.findall(r'<text[^>]*>[^<]*</text>', svg)
    if len(texts) == 4:                                   # label shadow, label, value shadow, value
        svg = svg.replace(texts[2], "", 1)
        svg = svg.replace(texts[3], texts[3].replace("<text ", '<text fill="#0D0D0F" font-weight="bold" ', 1), 1)
    return svg


if badge:
    badge = restyle(badge)
y, images = 0.0, []
for svg in parts:
    w, h = size(svg)
    h = h * W / w
    images.append(f'<image href="{uri(svg)}" x="0" y="{y:.1f}" width="{W}" height="{h:.1f}"/>')
    y += h
if badge:
    bw, bh = size(badge)
    y += GAP
    images.append(f'<image href="{uri(badge)}" x="8" y="{y:.1f}" width="{bw * 20 / bh:.1f}" height="20"/>')
    y += 20

out = (f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{y:.0f}" viewBox="0 0 {W} {y:.0f}" '
       f'role="img" aria-label="Repositories, contributions and profile views">' + "".join(images) + "</svg>")
with open("metrics/right-column.svg", "w", encoding="utf-8") as fh:
    fh.write(out)
print(f"right-column.svg: {W}x{y:.0f}, badge {'included' if badge else 'missing'}")
