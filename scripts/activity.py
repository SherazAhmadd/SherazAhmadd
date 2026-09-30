"""Render metrics/activity.svg: the repositories most recently pushed to.

Replaces the metrics activity plugin, which fails on GitHub's current
PushEvent payload. Uses the public REST API only.
"""
import datetime as dt
import html
import json
import os
import urllib.request

USER = "SherazAhmadd"
SKIP = {f"{USER}/{USER}"}                 # the profile repo is updated by this workflow every day
LIMIT = 5
GOLD, GREY = "#B8860B", "#777777"
SANS = "-apple-system,BlinkMacSystemFont,'Segoe UI',Helvetica,Arial,sans-serif"


def api(path):
    req = urllib.request.Request(f"https://api.github.com{path}", headers={"Accept": "application/vnd.github+json"})
    token = os.environ.get("GITHUB_TOKEN")
    if token:
        req.add_header("Authorization", f"Bearer {token}")
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.load(resp)


repos = api(f"/users/{USER}/repos?type=owner&sort=pushed&per_page=30")
recent = [r for r in repos if r["full_name"] not in SKIP and not r["private"]][:LIMIT]


def when(stamp):
    days = (dt.datetime.now(dt.timezone.utc) - dt.datetime.fromisoformat(stamp.replace("Z", "+00:00"))).days
    if days == 0:
        return "today"
    if days < 31:
        return f"{days} day{'s' if days != 1 else ''} ago"
    return dt.date.fromisoformat(stamp[:10]).strftime("%b %Y")


rows = []
for i, r in enumerate(recent):
    y = 46 + i * 24
    verb = "Updated fork" if r["fork"] else "Pushed to"
    rows.append(f'<text x="0" y="{y}" font-family="{SANS}" font-size="12.5" fill="{GREY}">{verb} '
                f'<tspan font-weight="600">{html.escape(r["full_name"])}</tspan></text>'
                f'<text x="420" y="{y}" text-anchor="end" font-family="{SANS}" font-size="11" fill="{GREY}">'
                f'{when(r["pushed_at"])}</text>')
if not rows:
    rows.append(f'<text x="0" y="46" font-family="{SANS}" font-size="12.5" fill="{GREY}">No recent public activity</text>')

height = 46 + max(len(recent), 1) * 24 - 8
svg = (f'<svg xmlns="http://www.w3.org/2000/svg" width="420" height="{height}" viewBox="0 0 420 {height}" '
       f'role="img" aria-label="Recent activity"><title>Recent activity</title>'
       f'<text x="0" y="18" font-family="{SANS}" font-size="14" font-weight="600" fill="{GOLD}">Recent activity</text>'
       + "".join(rows) + "</svg>")
os.makedirs("metrics", exist_ok=True)
with open("metrics/activity.svg", "w", encoding="utf-8") as fh:
    fh.write(svg)
print(f"activity.svg: {len(recent)} repositories")
