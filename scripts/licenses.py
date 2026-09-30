"""Render metrics/licenses.svg: a licenses overview across the account's public repos.

The metrics licenses plugin only analyses one repository's dependencies, so this
draws the same kind of panel for the whole profile: how the repositories are
licensed, then the permissions, limitations and conditions of the most used
license (from GitHub's licenses API). Uses the public REST API; for a local run
without it, LICENSES_JSON can point to {"repos": [...], "rules": {...}}.
"""
import base64
import collections
import html
import json
import os
import urllib.request

USER = "SherazAhmadd"
GOLD, GREY = "#B8860B", "#777777"
OK, NO, INFO = "#3FB950", "#F85149", "#58A6FF"
PALETTE = ["#6FA37A", "#5B8DB8", "#9A7FB5", "#4FA3A0", "#B5A06A"]
NONE_COLOUR = "#8A8F98"
SANS = "-apple-system,BlinkMacSystemFont,'Segoe UI',Helvetica,Arial,sans-serif"
LABELS = {"modifications": "Modification", "include-copyright": "License and copyright notice", "document-changes": "State changes",
          "disclose-source": "Disclose source", "same-license": "Same license", "network-use-disclose": "Network use is distribution",
          "patent-use": "Patent use", "trademark-use": "Trademark use", "commercial-use": "Commercial use", "private-use": "Private use"}
W = 420


def api(path):
    req = urllib.request.Request(f"https://api.github.com{path}", headers={"Accept": "application/vnd.github+json"})
    if os.environ.get("GITHUB_TOKEN"):
        req.add_header("Authorization", f"Bearer {os.environ['GITHUB_TOKEN']}")
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.load(resp)


local = json.load(open(os.environ["LICENSES_JSON"])) if os.environ.get("LICENSES_JSON") else None
repos = local["repos"] if local else api(f"/users/{USER}/repos?type=owner&per_page=100")
OWN_FORKS = {"PlantLTR-Scan"}                     # forks that are the account's own work
repos = [r for r in repos if not r["private"] and (not r["fork"] or r["name"] in OWN_FORKS)]
COLLABORATIONS = ["sajjadtahreem/Glunova-AI", "MuhammadZain-Butt/BioVix"]   # co-developed, hosted elsewhere
if not local:
    for full in COLLABORATIONS:
        try:
            repos.append(api(f"/repos/{full}"))
        except Exception as exc:
            print("skipped", full, exc)
SIGNATURES = {"MIT": "Permission is hereby granted, free of charge",
              "Apache-2.0": "Apache License", "GPL-3.0": "GNU GENERAL PUBLIC LICENSE"}


def identify(repo):
    """GitHub reports NOASSERTION when a license file has extra text around the
    standard wording (e.g. a heading); read the file and match the wording."""
    try:
        body = base64.b64decode(api(f"/repos/{repo['full_name']}/license")["content"]).decode("utf-8", "replace")
    except Exception:
        return "Other"
    return next((k for k, sig in SIGNATURES.items() if sig in body), "Other")


counts = collections.Counter()
for r in repos:
    spdx = (r.get("license") or {}).get("spdx_id")
    if spdx == "NOASSERTION":
        spdx = identify(r) if not local else "Other"
    counts[None if spdx == "Other" else spdx] += 1     # unidentified files join "Others"
named = sorted(((k, n) for k, n in counts.items() if k), key=lambda kv: (kv[0] == "Other", -kv[1]))
top = named[0][0] if named and named[0][0] != "Other" else None
if local:
    rules = local["rules"]
else:
    rules = api(f"/licenses/{top.lower()}") if top else {"permissions": [], "limitations": [], "conditions": []}

e = html.escape
text = lambda x, y, s, size=12, fill=GREY, extra="": (f'<text x="{x}" y="{y}" font-family="{SANS}" font-size="{size}" '
                                                        f'fill="{fill}"{extra}>{s}</text>')
out = [text(0, 17, "Licenses", 14, GOLD, ' font-weight="600"')]
if top:
    out.append(text(W, 17, f"{e(top)} is the most used", 11, GREY, ' text-anchor="end"'))

# ratio bar and legend: licensed repositories by license, then the unlicensed ones
parts = [(k, n, PALETTE[i % len(PALETTE)]) for i, (k, n) in enumerate(named)]
if counts.get(None):
    parts.append(("Others", counts[None], NONE_COLOUR))
total = sum(n for _, n, _ in parts) or 1
out.append(f'<clipPath id="bar"><rect x="0" y="27" width="{W}" height="8" rx="4"/></clipPath><g clip-path="url(#bar)">')
x = 0.0
for _, n, colour in parts:
    out.append(f'<rect x="{x:.1f}" y="27" width="{W * n / total:.1f}" height="8" fill="{colour}"/>')
    x += W * n / total
out.append("</g>")
x = 0
for name, n, colour in parts:
    label = f"{e(name)} <tspan font-size=\"10.5\">{n}</tspan>"
    out.append(f'<circle cx="{x + 5}" cy="49" r="4.5" fill="{colour}"/>' + text(x + 14, 53, label, 12))
    x += 14 + int(7 * len(name) + 30)

# permissions, limitations and conditions of the most used license
columns = [("Permissions", rules.get("permissions", []), "✓", OK),
           ("Limitations", rules.get("limitations", []), "✕", NO),
           ("Conditions", rules.get("conditions", []), "i", INFO)]
for c, (head, keys, mark, colour) in enumerate(columns):
    cx = (0, 125, 230)[c]
    out.append(text(cx, 78, head, 12, GREY, ' font-weight="600"'))
    for i, key in enumerate(keys[:4]):
        y = 96 + i * 17
        label = LABELS.get(key, key.replace("-", " ").capitalize())
        out.append(text(cx, y, mark, 11.5, colour, ' font-weight="700"') + text(cx + 14, y, e(label), 11.5))
rows = max([len(k[:4]) for _, k, _, _ in columns] + [1])
H = 96 + (rows - 1) * 17 + 6

svg = (f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" role="img" '
       f'aria-label="Licenses overview"><title>Licenses overview</title>' + "".join(out) + "</svg>")
os.makedirs("metrics", exist_ok=True)
with open("metrics/licenses.svg", "w", encoding="utf-8") as fh:
    fh.write(svg)
print(f"licenses.svg: {dict(counts)}; most used {top}")
