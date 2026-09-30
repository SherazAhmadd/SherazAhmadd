"""Render metrics/languages.svg: most-used languages across owned, non-fork public
repos (notebooks, HTML and CSS excluded), as a bar with a legend."""
import json
import os
import urllib.request

USER = "SherazAhmadd"
IGNORED = {"Jupyter Notebook", "HTML", "CSS"}
PALETTE = ["#F5C518", "#5B8DB8", "#6FA37A", "#C9745B", "#9A7FB5", "#4FA3A0", "#B5A06A", "#8A8F98"]
GOLD, GREY = "#B8860B", "#777777"
SANS = "-apple-system,BlinkMacSystemFont,'Segoe UI',Helvetica,Arial,sans-serif"


def api(path):
    req = urllib.request.Request(f"https://api.github.com{path}", headers={"Accept": "application/vnd.github+json"})
    if os.environ.get("GITHUB_TOKEN"):
        req.add_header("Authorization", f"Bearer {os.environ['GITHUB_TOKEN']}")
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.load(resp)


totals = {}
for repo in api(f"/users/{USER}/repos?type=owner&per_page=100"):
    if repo["fork"] or repo["private"]:
        continue
    for name, size in api(f"/repos/{repo['full_name']}/languages").items():
        if name not in IGNORED:
            totals[name] = totals.get(name, 0) + size
total = sum(totals.values()) or 1
langs = sorted(totals.items(), key=lambda kv: -kv[1])[:8]

W = 720
COLS = min(max(len(langs), 1), 6)                 # legend on one line (up to six languages per line)
rows = (len(langs) + COLS - 1) // COLS
H = 44 + rows * 22
out = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" role="img" aria-label="Most used languages">',
       f'<text x="0" y="14" font-family="{SANS}" font-size="11.8" font-weight="600" fill="{GOLD}">Most used languages</text>',
       f'<clipPath id="bar"><rect x="0" y="22" width="{W}" height="8" rx="4"/></clipPath><g clip-path="url(#bar)">']
x = 0.0
for i, (name, size) in enumerate(langs):
    w = W * size / total
    out.append(f'<rect x="{x:.1f}" y="22" width="{max(w, 2):.1f}" height="8" fill="{PALETTE[i]}"/>')
    x += w
out.append("</g>")
for i, (name, size) in enumerate(langs):
    cx, cy = (i % COLS) * (W // COLS), 52 + (i // COLS) * 22
    out.append(f'<circle cx="{cx + 5}" cy="{cy - 4}" r="5" fill="{PALETTE[i]}"/>'
               f'<text x="{cx + 16}" y="{cy}" font-family="{SANS}" font-size="12.5" fill="{GREY}">{name} '
               f'<tspan font-size="11">{size / total:.1%}</tspan></text>')
out.append("</svg>")
with open("metrics/languages.svg", "w", encoding="utf-8") as fh:
    fh.write("\n".join(out))
print("languages.svg:", [f"{n} {s / total:.0%}" for n, s in langs])
