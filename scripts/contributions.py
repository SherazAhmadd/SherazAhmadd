"""Draw metrics/contribution-line.svg (last 30 days, GitHub greens) from the
public contributions calendar. No token needed.
"""
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
