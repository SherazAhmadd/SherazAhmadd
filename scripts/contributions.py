"""Draw metrics/isocalendar.svg and metrics/contribution-line.svg from the public
contributions calendar (no token needed).

The isometric calendar reuses the geometry of the metrics isocalendar plugin
(cube paths, week/day offsets, heights relative to the busiest day, darker
side faces) with GitHub's green contribution colours, drawn a little larger and viewed
a quarter turn round.
"""
import datetime as dt
import re
import urllib.request

USER = "SherazAhmadd"
GOLD, GREY = "#B8860B", "#777777"
SANS = "-apple-system,BlinkMacSystemFont,'Segoe UI',Helvetica,Arial,sans-serif"
WEEKS = 26            # half a year, the plugin's default range
SCALE = 5.4           # plugin uses 4
ROTATE = True         # view the grid a quarter turn round: weeks run upper-right to lower-left
HEIGHT = 7             # bar height in cube units (plugin uses 6)
GREENS = ["#ebedf0", "#9be9a8", "#40c463", "#30a14e", "#216e39"]   # GitHub contribution colours by level

page = urllib.request.urlopen(urllib.request.Request(
    f"https://github.com/users/{USER}/contributions", headers={"User-Agent": "profile-metrics"}), timeout=60).read().decode()
cells = re.findall(r'<td[^>]*data-date="([\d-]+)"[^>]*id="([^"]+)"[^>]*data-level="(\d)"', page)
tips = dict(re.findall(r'<tool-tip[^>]*for="([^"]+)"[^>]*>([^<]+)</tool-tip>', page))


def count(tip):
    m = re.match(r"\s*(\d+)\s+contribution", tip or "")
    return int(m.group(1)) if m else 0


days = sorted((date, count(tips.get(cid)), int(level)) for date, cid, level in cells)
total = re.findall(r"([\d,]+)\s+contributions?\s+in the last year", page)
total = total[0] if total else str(sum(c for _, c, _ in days))

# ---- isometric calendar ----
start = dt.date.fromisoformat(days[-1][0]) - dt.timedelta(weeks=WEEKS)
start -= dt.timedelta(days=(start.weekday() + 1) % 7)                 # the plugin starts on a Sunday
recent = [d for d in days if dt.date.fromisoformat(d[0]) >= start]
reference = max((c for _, c, _ in recent), default=0) or 1

# streaks and per-day figures, as the plugin reports them
best = cur = run = 0
for _, c, _ in recent:
    run = run + 1 if c else 0
    best = max(best, run)
for _, c, _ in reversed(recent):
    if not c:
        break
    cur += 1
highest = max((c for _, c, _ in recent), default=0)
average = sum(c for _, c, _ in recent) / max(len(recent), 1)


def darker(hexc, slope):
    r, g, b = (int(hexc[i:i + 2], 16) for i in (1, 3, 5))
    return "#%02x%02x%02x" % (int(r * slope), int(g * slope), int(b * slope))


cubes = []
for d, c, level in recent:
    date = dt.date.fromisoformat(d)
    i = (date - start).days // 7                                      # week
    j = (date.weekday() + 1) % 7                                      # day (Sunday = 0)
    ratio = c / reference
    col = GREENS[level]
    cubes.append(
        f'<g transform="translate({(j - i if ROTATE else i - j) * 1.7:.2f},{i + j + (1 - ratio) * HEIGHT:.2f})">'
        f'<path fill="{col}" d="M1.7,2 0,1 1.7,0 3.4,1 z"/>'
        f'<path fill="{darker(col, 0.6)}" d="M0,1 1.7,2 1.7,{2 + ratio * HEIGHT:.2f} 0,{1 + ratio * HEIGHT:.2f} z"/>'
        f'<path fill="{darker(col, 0.8)}" d="M1.7,2 3.4,1 3.4,{1 + ratio * HEIGHT:.2f} 1.7,{2 + ratio * HEIGHT:.2f} z"/></g>')

W, H = 480, 262
stats = [("Commits streaks", True), (f"Current streak {cur} day{'s' if cur != 1 else ''}", False),
         (f"Best streak {best} day{'s' if best != 1 else ''}", False), ("Commits per day", True),
         (f"Highest in a day at {highest}", False), (f"Average per day at ~{average:.2f}", False)]
text = "".join(
    f'<text x="330" y="{58 + k * 19}" font-family="{SANS}" font-size="{12.5 if head else 12}" '
    f'font-weight="{600 if head else 400}" fill="{GREY}">{t}</text>' for k, (t, head) in enumerate(stats))
svg = (f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" role="img" '
       f'aria-label="Contributions calendar"><title>Contributions calendar</title>'
       f'<text x="0" y="18" font-family="{SANS}" font-size="14" font-weight="600" fill="{GOLD}">Contributions calendar</text>'
       f'<text x="0" y="38" font-family="{SANS}" font-size="12" fill="{GREY}">{total} contributions in the last year</text>'
       + text +
       (f'<g transform="translate(226 34) scale({SCALE})">' if ROTATE else f'<g transform="translate(18 26) scale({SCALE}) translate(12 0)">') + "".join(cubes) + "</g></svg>")
with open("metrics/isocalendar.svg", "w", encoding="utf-8") as fh:
    fh.write(svg)

# ---- one-line strip: last 30 days ----
green = {1: "#0e4429", 2: "#006d32", 3: "#26a641", 4: "#39d353"}
last = days[-30:]
w = len(last) * 15
strip = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="23" viewBox="0 -6 {w} 23" role="img" '
         'aria-label="Contributions in the last 30 days">']
strip += [f'<rect x="{i * 15}" y="0" width="11" height="11" rx="2" fill="{green.get(l, "#8b949e33")}"><title>{d}</title></rect>'
          for i, (d, c, l) in enumerate(last)]
strip.append("</svg>")
with open("metrics/contribution-line.svg", "w", encoding="utf-8") as fh:
    fh.write("\n".join(strip))
print(f"contributions: {len(days)} days, {total} in the last year; calendar {len(recent)} days, busiest {reference}")
