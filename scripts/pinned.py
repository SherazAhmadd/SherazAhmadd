"""Render one clickable card per pinned repository and write them into README.md.

Each card is its own SVG (metrics/pinned-N.svg) wrapped in a link to the repo,
because a single image in a README can only link to one place. The README block
between the pinned markers is regenerated so links always match the pins.

Pins come from the GraphQL API (needs GITHUB_TOKEN); for a local run without a
token, PINNED_JSON can point to a JSON list of the same fields.
"""
import html
import json
import os
import re
import urllib.request

USER = "SherazAhmadd"
GOLD, GREY = "#B8860B", "#777777"
SANS = "-apple-system,BlinkMacSystemFont,'Segoe UI',Helvetica,Arial,sans-serif"
QUERY = """query($login:String!){user(login:$login){pinnedItems(first:6,types:REPOSITORY){nodes{
  ... on Repository{nameWithOwner url description isFork stargazerCount forkCount primaryLanguage{name}}}}}}"""


def pinned():
    if os.environ.get("PINNED_JSON"):
        return json.load(open(os.environ["PINNED_JSON"]))
    req = urllib.request.Request("https://api.github.com/graphql",
                                 data=json.dumps({"query": QUERY, "variables": {"login": USER}}).encode(),
                                 headers={"Authorization": f"Bearer {os.environ['GITHUB_TOKEN']}",
                                          "Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        nodes = json.load(resp)["data"]["user"]["pinnedItems"]["nodes"]
    return [{"name": n["nameWithOwner"], "url": n["url"], "description": n["description"] or "",
             "language": (n["primaryLanguage"] or {}).get("name"), "stars": n["stargazerCount"],
             "forks": n["forkCount"], "fork": n["isFork"]} for n in nodes]


def card(repo):
    e = html.escape
    desc = repo["description"]
    desc = desc if len(desc) <= 62 else desc[:61].rstrip() + "…"
    meta = "   ".join(x for x in [repo.get("language") or "", f"★ {repo['stars']}", f"forks {repo['forks']}",
                                  "fork" if repo.get("fork") else ""] if x)
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="420" height="54" viewBox="0 0 420 54" role="img" '
            f'aria-label="{e(repo["name"])}"><title>{e(repo["name"])}</title>'
            f'<text x="0" y="15" font-family="{SANS}" font-size="14" font-weight="600" fill="{GREY}">{e(repo["name"])}</text>'
            f'<text x="0" y="33" font-family="{SANS}" font-size="12.5" fill="{GREY}">{e(desc)}</text>'
            f'<text x="0" y="50" font-family="{SANS}" font-size="12" fill="{GREY}">{e(meta)}</text></svg>')


repos = pinned()
os.makedirs("metrics", exist_ok=True)
for old in [f for f in os.listdir("metrics") if re.fullmatch(r"pinned-\d+\.svg", f)]:
    os.remove(os.path.join("metrics", old))
lines = ['<img src="assets/icons/label-pinned-repositories.svg" align="left" width="49%" alt="Pinned repositories">']
for i, repo in enumerate(repos, start=1):
    with open(f"metrics/pinned-{i}.svg", "w", encoding="utf-8") as fh:
        fh.write(card(repo))
    lines.append(f'<a href="{repo["url"]}"><img src="metrics/pinned-{i}.svg" align="left" width="49%" '
                 f'alt="{html.escape(repo["name"])}"></a>')

readme = open("README.md", encoding="utf-8").read()
block = "<!-- pinned:start -->\n" + "\n".join(lines) + "\n<!-- pinned:end -->"
readme = re.sub(r"<!-- pinned:start -->.*?<!-- pinned:end -->", lambda _: block, readme, flags=re.S)
with open("README.md", "w", encoding="utf-8") as fh:
    fh.write(readme)
print(f"pinned: {len(repos)} cards -> {[r['name'] for r in repos]}")
