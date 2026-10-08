"""
00_fetch_raw.py
===============
Downloads the third-party source datasets into raw/ so the rest of the pipeline
can be rebuilt from a clean clone.  These files are not committed: they belong
to their original publishers, and the article cites them.

Run:  .venv/bin/python scripts/00_fetch_raw.py
"""

from pathlib import Path
import urllib.request

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "raw"
RAW.mkdir(exist_ok=True)

SOURCES = {
    # Anscombe's Quartet, from the R datasets collection
    "anscombe.csv": "https://vincentarelbundock.github.io/Rdatasets/csv/datasets/anscombe.csv",
    # The Datasaurus Dozen (Matejka & Fitzmaurice, CHI 2017), via the R datasets collection
    "datasaurus_dozen.csv": "https://vincentarelbundock.github.io/Rdatasets/csv/quartets/datasaurus_dozen.csv",
    # Real world data: GDP per person and life expectancy, 2007
    "gapminder2007.csv": "https://raw.githubusercontent.com/plotly/datasets/master/gapminder2007.csv",
    # Real world data: Palmer Station penguin measurements
    "penguins.csv": "https://raw.githubusercontent.com/mwaskom/seaborn-data/master/penguins.csv",
}


def main():
    for name, url in SOURCES.items():
        dest = RAW / name
        if dest.exists() and dest.stat().st_size > 200:
            print(f"  have  {name} ({dest.stat().st_size // 1024} KB)")
            continue
        print(f"  fetch {name}")
        urllib.request.urlretrieve(url, dest)
        print(f"        wrote {dest.stat().st_size // 1024} KB")
    print("raw/ ready")


if __name__ == "__main__":
    main()
