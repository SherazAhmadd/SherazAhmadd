"""Render metrics/activity.svg from real commits: "Pushed N commits to <repo>".

Commits are counted per repository and day across the account's public repos
(authored by the account or its known emails; bot commits are left out), then
the five most recent days are shown. Uses the public REST API.
"""
import collections
import datetime as dt
import html
import json
import os
import urllib.request

USER = "SherazAhmadd"
EMAILS = {"rana.a@lums.edu.pk", "ranasheraz.202101902@gcuf.edu.pk"}
LIMIT = 5
SINCE_DAYS = 365
GOLD, GREY = "#B8860B", "#777777"
SANS = "-apple-system,BlinkMacSystemFont,'Segoe UI',Helvetica,Arial,sans-serif"


def api(path):
    req = urllib.request.Request(f"https://api.github.com{path}", headers={"Accept": "application/vnd.github+json"})
    token = os.environ.get("GITHUB_TOKEN")
    if token:
        req.add_header("Authorization", f"Bearer {token}")
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.load(resp)


since = (dt.datetime.now(dt.timezone.utc) - dt.timedelta(days=SINCE_DAYS)).strftime("%Y-%m-%dT%H:%M:%SZ")
repos = api(f"/users/{USER}/repos?type=owner&sort=pushed&per_page=100")
groups = collections.Counter()                     # (date, repo) -> commits
for repo in repos:
    if repo["private"]:
        continue
    try:
        commits = api(f"/repos/{repo['full_name']}/commits?since={since}&per_page=100")
    except Exception:                               # empty repositories answer 409
        continue
    for c in commits:
        login = (c.get("author") or {}).get("login", "")
        email = c["commit"]["author"].get("email", "")
        if login.endswith("[bot]") or "github-actions" in email:
            continue
        if login == USER or email in EMAILS:
            groups[(c["commit"]["author"]["date"][:10], repo["full_name"])] += 1

recent = sorted(groups.items(), key=lambda kv: kv[0][0], reverse=True)[:LIMIT]


def when(day):
    days = (dt.date.today() - dt.date.fromisoformat(day)).days
    if days <= 0:
        return "today"
    if days < 31:
        return f"{days} day{'s' if days != 1 else ''} ago"
    return dt.date.fromisoformat(day).strftime("%d %b %Y")


rows = []
for i, ((day, name), n) in enumerate(recent):
    y = 46 + i * 24
    rows.append(f'<text x="0" y="{y}" font-family="{SANS}" font-size="12.5" fill="{GREY}">Pushed {n} commit{"s" if n != 1 else ""} to '
                f'<tspan font-weight="600">{html.escape(name)}</tspan></text>'
                f'<text x="420" y="{y}" text-anchor="end" font-family="{SANS}" font-size="11" fill="{GREY}">{when(day)}</text>')
if not rows:
    rows.append(f'<text x="0" y="46" font-family="{SANS}" font-size="12.5" fill="{GREY}">No public commits in the last year</text>')

height = 46 + max(len(recent), 1) * 24 - 8
svg = (f'<svg xmlns="http://www.w3.org/2000/svg" width="420" height="{height}" viewBox="0 0 420 {height}" '
       f'role="img" aria-label="Recent activity"><title>Recent activity</title>'
       f'<text x="0" y="18" font-family="{SANS}" font-size="14" font-weight="600" fill="{GOLD}">Recent activity</text>'
       + "".join(rows) + "</svg>")
os.makedirs("metrics", exist_ok=True)
with open("metrics/activity.svg", "w", encoding="utf-8") as fh:
    fh.write(svg)
print(f"activity.svg: {sum(groups.values())} commits in {len(groups)} repo-days; showing {len(recent)}")
