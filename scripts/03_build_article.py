"""
03_build_article.py
===================
Assembles the final, self-contained article page.

It reads article/template.html (the prose and the design), replaces every
<!--FIG:name--> and <!--TABLE:name--> token with the Plotly div and the HTML
table produced by 02_build_figures.py, and refuses to write the page if any
token is left unreplaced.  That check is the reason the numbers in the prose
tables and the numbers in the charts can never drift apart.

Run:  .venv/bin/python scripts/03_build_article.py
Output: article/same-numbers-different-stories.html
"""

from __future__ import annotations

import json
import re
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ART = ROOT / "article"
TEMPLATE = ART / "template.html"
PARTS = ART / "parts.json"
OUT = ART / "same-numbers-different-stories.html"
SITE = ROOT / "site"  # optional: a copy dropped next to the website's index.html

TOKEN = re.compile(r"<!--(FIG|TABLE):([a-z0-9_]+)-->")


def main():
    template = TEMPLATE.read_text()
    parts = json.loads(PARTS.read_text())

    missing = []

    def swap(match):
        key = f"{match.group(1)}:{match.group(2)}"
        if key not in parts:
            missing.append(key)
            return match.group(0)
        return parts[key]

    html = TOKEN.sub(swap, template)

    if missing:
        raise SystemExit(f"unresolved tokens, refusing to write: {missing}")
    if TOKEN.search(html):
        raise SystemExit("a token survived substitution")

    OUT.write_text(html)

    size_kb = OUT.stat().st_size / 1024
    print(f"wrote {OUT.relative_to(ROOT)}  ({size_kb:.0f} KB)")
    print(f"figures embedded: {sum(1 for k in parts if k.startswith('FIG'))}")
    print(f"tables embedded:  {sum(1 for k in parts if k.startswith('TABLE'))}")

    # sanity checks on the rendered document
    checks = {
        "plotly script tag": 'cdn.plot.ly/plotly-4.1.1.min.js' in html,
        "plotly local fallback": 'plotly.min.js' in html,
        "every figure div present": html.count('class="plotly-graph-div"') >= 11,
        "no template tokens left": "<!--FIG:" not in html and "<!--TABLE:" not in html,
        "no em dashes": "\u2014" not in html,
    }
    for name, ok in checks.items():
        print(("  OK   " if ok else "  FAIL ") + name)

    # copy the reusable assets next to the site if that folder exists
    if SITE.exists():
        shutil.copy(OUT, SITE / OUT.name)
        if (ART / "plotly.min.js").exists():
            shutil.copy(ART / "plotly.min.js", SITE / "plotly.min.js")
        print(f"copied the page and the local plotly bundle into {SITE}")
    return 0 if all(checks.values()) else 1


if __name__ == "__main__":
    raise SystemExit(main())
