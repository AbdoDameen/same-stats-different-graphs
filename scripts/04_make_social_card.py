"""
04_make_social_card.py
======================
Draws the social sharing card for the article: 1200 by 630, dark, and made of
the same datasets the article is built on.

Run:  .venv/bin/python scripts/04_make_social_card.py
Output: article/same-numbers-different-stories-card.png and figures/social-card.png
"""

from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
shapes = pd.read_csv(ROOT / "data" / "same_stats_shapes.csv")
DINO = pd.read_csv(ROOT / "data" / "datasaurus_dozen.csv")

fig = plt.figure(figsize=(12, 6.3), dpi=140)
fig.patch.set_facecolor("#1b1233")


def bare(rect):
    ax = fig.add_axes(rect)
    ax.set_xticks([])
    ax.set_yticks([])
    for side in ax.spines.values():
        side.set_visible(False)
    ax.set_facecolor("#1b1233")
    return ax


# the article's own shapes
for i, (name, colour) in enumerate([("heart", "#8A2BE2"), ("letters_DA", "#00CEC9")]):
    ax = bare([0.045 + i * 0.135, 0.30, 0.12, 0.42])
    g = shapes[shapes.dataset == name]
    ax.scatter(g.x, g.y, s=6, c=colour, alpha=0.95, linewidths=0)

# the published dinosaur
ax = bare([0.055, 0.71, 0.09, 0.22])
d = DINO[DINO.dataset == "dino"]
ax.scatter(d.x, d.y, s=3, c="#FF6B6B", alpha=0.95, linewidths=0)

fig.text(0.33, 0.72, "Same Numbers,", color="white", fontsize=41, fontweight="bold", family="DejaVu Sans")
fig.text(0.33, 0.585, "Different Stories", color="#C39BD3", fontsize=41, fontweight="bold", family="DejaVu Sans")
fig.text(0.33, 0.45,
         "Twelve datasets. Identical means, standard deviations\n"
         "and correlations, to fifteen decimal places.\n"
         "The statistics never notice.",
         color="#ded5ff", fontsize=15.5, family="DejaVu Sans", linespacing=1.55)
fig.text(0.33, 0.235, "mean 54.26   \u00b7   sd 16.76   \u00b7   r  \u2212 0.0641", color="#FFB400",
         fontsize=15, family="DejaVu Sans", fontweight="bold")
fig.text(0.33, 0.115, "Dameen Analytics   |   Abdelrhman Dameen", color="#a693d6", fontsize=13,
         family="DejaVu Sans")

for target in [ROOT / "article" / "same-numbers-different-stories-card.png",
               ROOT / "figures" / "social-card.png"]:
    fig.savefig(target, facecolor="#1b1233")
    print("wrote", target.relative_to(ROOT))
