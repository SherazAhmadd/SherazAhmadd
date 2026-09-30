"""Draw metrics/isocalendar.svg (isometric year, yellow palette) and
metrics/contribution-line.svg (last 30 days, GitHub greens) from the public
contributions calendar. No token needed.
"""
import datetime as dt
import re
import urllib.request

USER = "SherazAhmadd"
GOLD, GREY = "#B8860B", "#777777"
SANS = "-apple-system,BlinkMacSystemFont,'Segoe UI',Helvetica,Arial,sans-serif"

page = urllib.request.urlopen(urllib.request.Request(
    f"https://github.com/users/{USER}/contributions", headers={"User-Agent": "profile-metrics"}), timeout=60).read().decode()
days = sorted(re.findall(r'data-date="(\d{4}-\d\d-\d\d)"[^>]*data-level="(\d)"', page))
total = re.findall(r"([\d,]+)\s+contributions?\s+in the last year", page)
total = total[0] if total else str(sum(1 for _, level in days if level != "0"))

# ---- isometric year ----
cols = ["#2B2E35", "#6B5A1A", "#A8871F", "#D9AE1F", "#F5C518"]


def shade(hexc, f):
    r, g, b = (int(hexc[i:i + 2], 16) for i in (1, 3, 5))
    return "#%02x%02x%02x" % tuple(max(0, min(255, int(v * f))) for v in (r, g, b))


start = dt.date.fromisoformat(days[0][0])
start -= dt.timedelta(days=(start.weekday() + 1) % 7)
cells = [((dt.date.fromisoformat(d) - start).days // 7, (dt.date.fromisoformat(d).weekday() + 1) % 7, int(l))
         for d, l in days]
s = 3.4
out = ['<svg xmlns="http://www.w3.org/2000/svg" width="480" height="250" viewBox="0 0 480 250" role="img" '
       'aria-label="Contributions calendar">',
       f'<text x="8" y="20" font-family="{SANS}" font-size="14" font-weight="600" fill="{GOLD}">Contributions calendar</text>',
       f'<text x="8" y="40" font-family="{SANS}" font-size="12" fill="{GREY}">{total} contributions in the last year</text>']
for w, d, level in sorted(cells, key=lambda c: (c[0] + c[1], c[0])):
    x = 100 + (w - d) * s + w * s * 0.72
    y = 70 + (w + d) * s * 0.5 - w * s * 0.12 + d * s * 0.9
    h = 2 + level * 6
    col = cols[level]
    top = f"{x},{y-h} {x+s},{y-h-s*0.5} {x+2*s},{y-h} {x+s},{y-h+s*0.5}"
    left = f"{x},{y-h} {x+s},{y-h+s*0.5} {x+s},{y+s*0.5} {x},{y}"
    right = f"{x+s},{y-h+s*0.5} {x+2*s},{y-h} {x+2*s},{y} {x+s},{y+s*0.5}"
    out.append(f'<polygon points="{top}" fill="{col}"/><polygon points="{left}" fill="{shade(col, .72)}"/>'
               f'<polygon points="{right}" fill="{shade(col, .55)}"/>')
out.append("</svg>")
with open("metrics/isocalendar.svg", "w", encoding="utf-8") as fh:
    fh.write("\n".join(out))

# ---- one-line strip: last 30 days ----
green = {"1": "#0e4429", "2": "#006d32", "3": "#26a641", "4": "#39d353"}
last = days[-30:]
w = len(last) * 15
strip = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="23" viewBox="0 -6 {w} 23" role="img" '
         'aria-label="Contributions in the last 30 days">']
strip += [f'<rect x="{i * 15}" y="0" width="11" height="11" rx="2" fill="{green.get(l, "#8b949e33")}"><title>{d}</title></rect>'
          for i, (d, l) in enumerate(last)]
strip.append("</svg>")
with open("metrics/contribution-line.svg", "w", encoding="utf-8") as fh:
    fh.write("\n".join(strip))
print(f"contributions: {len(days)} days, {total} in the last year")
