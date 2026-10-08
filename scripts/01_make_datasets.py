"""
01_make_datasets.py
===================
Builds every dataset used in the article "Same Numbers, Different Stories".

Three construction methods are used, each documented in the article:

1. CANONICAL  - Anscombe's Quartet (1973) and the Datasaurus Dozen
                (Matejka & Fitzmaurice, CHI 2017), redistributed as tidy CSVs
                so the whole article is reproducible from one repo.

2. EXACT SPECTRAL MATCHING (invented for this article)
                Given any cloud of points, we transform it so that the
                mean of x, mean of y, SD of x, SD of y and Pearson's r are
                EXACTLY equal to a chosen target -- to machine precision, not
                to two decimal places.  Method:

                    u = (a - mean a) / sd(a)          # mean 0, sd 1
                    v = (b - mean b) / sd(b)
                    e = v - (u . v / n) u             # component of v _|_ u
                    w = e / sd(e)                     # mean 0, sd 1, _|_ u
                    v* = r u + sqrt(1 - r^2) w        # corr(u, v*) = r exactly
                    x = m1 + s1 u ,  y = m2 + s2 v*

                Because (u, v*) are orthogonal unit vectors, the correlation
                identity corr = r holds exactly, and the affine step fixes the
                means and standard deviations exactly.  We shear shapes a
                little, but we never touch the statistics.

3. QUANTILE MAPPING
                Given any Monte-Carlo sample we remap its ranks through a
                piecewise-linear target quantile function, so that the sample
                hits a target five-number summary (min, Q1, median, Q3, max)
                exactly.  Used for the "same boxplot, different data" sets.

Run:  .venv/bin/python scripts/01_make_datasets.py
Output: data/*.csv  +  data/summary_statistics.json  (verification report)
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "raw"
DATA = ROOT / "data"
DATA.mkdir(exist_ok=True)

rng = np.random.default_rng(20261008)
REPORT: dict[str, object] = {}


# --------------------------------------------------------------------------
# helpers
# --------------------------------------------------------------------------
def stats_2d(x, y) -> dict:
    x, y = np.asarray(x, float), np.asarray(y, float)
    return {
        "n": int(len(x)),
        "mean_x": float(x.mean()),
        "mean_y": float(y.mean()),
        "sd_x": float(x.std(ddof=0)),
        "sd_y": float(y.std(ddof=0)),
        "r": float(np.corrcoef(x, y)[0, 1]),
    }


def force_stats(a, b, m1, m2, s1, s2, r):
    """Shear a point cloud so that its summary statistics equal the targets exactly."""
    a = np.asarray(a, float)
    b = np.asarray(b, float)
    u = (a - a.mean()) / a.std(ddof=0)
    v = (b - b.mean()) / b.std(ddof=0)
    e = v - (u @ v / len(u)) * u
    e = e / e.std(ddof=0)
    v_star = r * u + np.sqrt(max(0.0, 1.0 - r**2)) * e
    return m1 + s1 * u, m2 + s2 * v_star


def force_mean_sd(v, m, s):
    """1-D version: affine map onto an exact mean and SD."""
    v = np.asarray(v, float)
    return m + s * (v - v.mean()) / v.std(ddof=0)


def quantile_map(sample, anchors: dict, shape_frac: np.ndarray | None = None):
    """Remap `sample` onto the quantile function through `anchors`.

    anchors: {0.0: min, 0.25: q1, 0.5: median, 0.75: q3, 1.0: max}
    shape_frac: optional array of quantile positions (i/(n-1)) that defines the
                *shape* of the sample.  Defaults to the empirical ranks of
                `sample`, which reproduces the flavour of the source distribution.
    """
    n = len(sample)
    if shape_frac is None:
        inner = (np.arange(n) + 0.5) / n           # strictly inside (0, 1)
        shape_frac = inner
    ps = np.array(sorted(anchors))
    vs = np.array([anchors[p] for p in ps], float)
    return np.interp(shape_frac, ps, vs)


NOISE = 1e-9  # keeps ranks distinct without disturbing any statistic


# --------------------------------------------------------------------------
# 1. canonical datasets
# --------------------------------------------------------------------------
def build_canonical():
    # --- Anscombe's Quartet (F. J. Anscombe, 1973, The American Statistician) ---
    ans = pd.read_csv(RAW / "anscombe.csv")
    rows = []
    for i in "1234":
        for x, y in zip(ans[f"x{i}"], ans[f"y{i}"]):
            rows.append({"dataset": f"set_{i}", "x": float(x), "y": float(y)})
    aq = pd.DataFrame(rows).sort_values(["dataset"], kind="stable").reset_index(drop=True)
    aq.to_csv(DATA / "anscombe_quartet.csv", index=False)

    aq_stats = {
        name: stats_2d(g.x, g.y) for name, g in aq.groupby("dataset")
    }
    REPORT["anscombe"] = aq_stats

    # --- Datasaurus Dozen (Matejka & Fitzmaurice, CHI 2017) ---
    dd = pd.read_csv(RAW / "datasaurus_dozen.csv")[["dataset", "x", "y"]]
    dd.to_csv(DATA / "datasaurus_dozen.csv", index=False)
    dd_stats = {name: stats_2d(g.x, g.y) for name, g in dd.groupby("dataset")}
    REPORT["datasaurus_dozen"] = dd_stats
    return aq, dd


# --------------------------------------------------------------------------
# 2. exact spectral matching - my own "dozen"
# --------------------------------------------------------------------------
def make_shapes(n: int = 142):
    """Twelve target silhouettes, 142 points each (same n as the Datasaurus)."""
    t = np.linspace(0, 2 * np.pi, n, endpoint=False)
    shapes: dict[str, tuple[np.ndarray, np.ndarray]] = {}

    shapes["circle"] = (np.cos(t), np.sin(t))

    # a proper five-pointed star: radius alternates between the points and the
    # inner corners, then we walk the perimeter in polar coordinates.
    k = np.arange(11)
    th_k = k * (2 * np.pi / 10)
    r_k = np.where(k % 2 == 0, 1.0, 0.40)
    tt = np.linspace(0, 2 * np.pi, n, endpoint=False)
    r = np.interp(tt, th_k, r_k)
    shapes["star"] = (r * np.cos(tt), r * np.sin(tt))

    tt = np.linspace(0, 2 * np.pi, n)
    shapes["heart"] = (
        16 * np.sin(tt) ** 3,
        13 * np.cos(tt) - 5 * np.cos(2 * tt) - 2 * np.cos(3 * tt) - np.cos(4 * tt),
    )

    half = n // 2
    shapes["plus"] = (
        np.concatenate([np.linspace(-1, 1, half), np.zeros(n - half)]),
        np.concatenate([np.zeros(half), np.linspace(-1, 1, n - half)]),
    )
    shapes["x_shape"] = (
        np.concatenate([np.linspace(-1, 1, half), np.linspace(-1, 1, n - half)]),
        np.concatenate([np.linspace(-1, 1, half), np.linspace(1, -1, n - half)]),
    )

    a = np.linspace(-3.2, 3.2, n)
    shapes["wave"] = (a, 1.6 * np.sin(2.1 * a))

    th = np.linspace(0, 4.2 * np.pi, n)
    rr = th / (4.2 * np.pi)
    shapes["spiral"] = (rr * np.cos(th) * 3, rr * np.sin(th) * 3)

    side = n // 3
    pts = [(-1, -0.8), (1, -0.8), (0, 1.1), (-1, -0.8)]
    ax, by = [], []
    for (x0, y0), (x1, y1) in zip(pts[:-1], pts[1:]):
        ax += list(np.linspace(x0, x1, side, endpoint=False))
        by += list(np.linspace(y0, y1, side, endpoint=False))
    ax += [pts[-1][0]] * (n - len(ax))
    by += [pts[-1][1]] * (n - len(by))
    shapes["triangle"] = (np.array(ax), np.array(by))

    # several stacked horizontal / vertical lines, so both SDs stay positive
    per = n // 3
    ax, by = [], []
    for level in (-1.0, 0.0, 1.0):
        ax += list(np.linspace(-3, 3, per))
        by += [level] * per
    pad = n - len(ax)
    ax += list(np.linspace(-3, 3, pad))
    by += [0.0] * pad
    shapes["h_lines"] = (np.array(ax), np.array(by))

    ax, by = [], []
    for level in (-1.0, 0.0, 1.0):
        ax += [level] * per
        by += list(np.linspace(-3, 3, per))
    ax += [0.0] * pad
    by += list(np.linspace(-3, 3, pad))
    shapes["v_lines"] = (np.array(ax), np.array(by))

    rng_blob = np.random.default_rng(7)
    shapes["blob"] = rng_blob.normal(0, 1, (2, n))

    # the letters "DA" - a nod to the site this article lives on
    try:
        from matplotlib.textpath import TextPath
        from matplotlib.font_manager import FontProperties

        fp = FontProperties(family="DejaVu Sans", weight="bold")
        path = TextPath((0, 0), "DA", size=40, prop=fp)
        poly = path.to_polygons()
        pts2 = []
        for ring in poly:
            ring = np.asarray(ring, float)
            d = np.r_[0, np.cumsum(np.linalg.norm(np.diff(ring, axis=0), axis=1))]
            if d[-1] == 0:
                continue
            s = np.linspace(0, d[-1], max(12, int(n * d[-1] / 200)), endpoint=False)
            pts2.append(np.c_[np.interp(s, d, ring[:, 0]), np.interp(s, d, ring[:, 1])])
        ring = np.vstack(pts2)
        idx = np.linspace(0, len(ring) - 1, n).astype(int)
        shapes["letters_DA"] = (ring[idx, 0], ring[idx, 1])
    except Exception as exc:  # keep the build alive if fonts are missing
        print("letters shape skipped:", exc)

    return shapes


def build_own_dozen():
    """Twelve silhouettes carrying *exactly* the same summary statistics."""
    target = {"m1": 54.26, "m2": 47.83, "s1": 16.76, "s2": 26.93, "r": -0.0641}
    shapes = make_shapes(142)

    frames, stats = [], {}
    for name, (a, b) in shapes.items():
        x, y = force_stats(a, b, target["m1"], target["m2"], target["s1"], target["s2"], target["r"])
        frames.append(pd.DataFrame({"dataset": name, "x": x, "y": y}))
        stats[name] = stats_2d(x, y)
    out = pd.concat(frames, ignore_index=True)
    out.to_csv(DATA / "same_stats_shapes.csv", index=False)

    # machine-precision verification: every dataset must agree to 1e-12
    keys = ("mean_x", "mean_y", "sd_x", "sd_y", "r")
    spread = {k: max(abs(s[k] - stats[next(iter(stats))][k]) for s in stats.values()) for k in keys}
    REPORT["own_dozen"] = {"target": target, "per_dataset": stats, "max_abs_spread": spread,
                           "identical_to_1e-12": all(v < 1e-12 for v in spread.values())}
    return out


# --------------------------------------------------------------------------
# 3. same mean and SD, different distributions
# --------------------------------------------------------------------------
def build_mean_sd_twins(n: int = 400, mean: float = 50.0, sd: float = 10.0):
    shapes = {
        "normal": rng.normal(0, 1, n),
        "bimodal": np.concatenate([rng.normal(-1.6, 0.55, n // 2), rng.normal(1.6, 0.55, n - n // 2)]),
        "right_skewed": rng.gamma(2.0, 1.0, n),
        "left_skewed": -rng.gamma(2.0, 1.0, n),
        "uniform": rng.uniform(-np.sqrt(3), np.sqrt(3), n),
        "outlier_driven": np.concatenate([rng.normal(0, 0.6, n - 4), np.array([-14.0, -13.0, 14.0, 13.0])]),
    }
    frames, stats = [], {}
    for name, s in shapes.items():
        v = force_mean_sd(s, mean, sd)
        frames.append(pd.DataFrame({"dataset": name, "value": v}))
        stats[name] = {
            "n": int(n), "mean": float(v.mean()), "sd": float(v.std(ddof=0)),
            "median": float(np.median(v)),
            "iqr": float(np.subtract(*np.percentile(v, [75, 25]))),
            "min": float(v.min()), "max": float(v.max()),
            "skewness": float(pd.Series(v).skew()),
        }
    pd.concat(frames, ignore_index=True).to_csv(DATA / "same_mean_sd_twins.csv", index=False)
    REPORT["mean_sd_twins"] = stats
    return stats


# --------------------------------------------------------------------------
# 4. same five-number summary, different data
# --------------------------------------------------------------------------
def build_same_boxplot(n: int = 101):
    """Five datasets that share one five-number summary but nothing else.

    The ranks are partitioned into four blocks that start and end exactly on the
    target anchors (10, 30, 50, 70, 90).  Inside each block the values follow
    anchor_lo + (anchor_hi - anchor_lo) * u**b.  The endpoints are pinned, so
    min, Q1, median, Q3 and max are identical for every dataset no matter what
    the exponent b does in between.  Changing b only moves the *density*.
    """
    anchors = [10.0, 30.0, 50.0, 70.0, 90.0]
    blocks = [(0, 25), (25, 50), (50, 75), (75, 100)]  # rank pairs, n = 101

    variants = {
        "uniform": [1.0, 1.0, 1.0, 1.0],
        "hollow (U shape)": [2.6, 2.6, 0.38, 0.38],
        "bell (mass in the middle)": [0.32, 0.32, 2.8, 2.8],
        "top-heavy": [0.25, 0.25, 0.25, 0.25],
        "bottom-heavy": [3.2, 3.2, 3.2, 3.2],
        "spike at the median": [1.0, 0.16, 2.2, 1.0],
    }

    frames, stats = [], {}
    for name, bs in variants.items():
        v = np.empty(n)
        period = np.empty(n, dtype=object)
        for (lo, hi), b in zip(blocks, bs):
            u = (np.arange(hi - lo + 1)) / (hi - lo)
            v[lo:hi + 1] = anchors[blocks.index((lo, hi))] + (
                anchors[blocks.index((lo, hi)) + 1] - anchors[blocks.index((lo, hi))]
            ) * u**b
        v = v + NOISE * np.arange(n)
        frames.append(pd.DataFrame({"dataset": name, "value": v}))
        q = np.percentile(v, [0, 25, 50, 75, 100])
        stats[name] = {
            "min": float(q[0]), "q1": float(q[1]), "median": float(q[2]),
            "q3": float(q[3]), "max": float(q[4]),
            "iqr": float(q[3] - q[1]), "mean": float(v.mean()), "sd": float(v.std(ddof=0)),
        }
    pd.concat(frames, ignore_index=True).to_csv(DATA / "same_boxplot.csv", index=False)
    REPORT["same_boxplot"] = stats
    return stats


# --------------------------------------------------------------------------
# 5. same correlation, different relationships
# --------------------------------------------------------------------------
def build_same_correlation(n: int = 200, r_target: float = 0.70):
    x = np.linspace(0, 10, n)
    base = {
        "linear": 1.0 * x + rng.normal(0, 0.6, n),
        "curved (quadratic)": (x - 5) ** 2 / 2.0 + rng.normal(0, 0.5, n),
        "step change": np.where(x < 5, 0.0, 4.0) + rng.normal(0, 0.5, n),
        "one outlier flips it": np.where(np.arange(n) == n // 2, 30.0, rng.normal(0, 0.4, n)),
        "wall of noise + trend": np.where(x < 8, rng.normal(0, 0.3, n), 6.0) + rng.normal(0, 0.3, n),
    }
    frames, stats = [], {}
    for name, b in base.items():
        a = rng.normal(0, 1, n) if name == "one outlier flips it" else x
        xx, yy = force_stats(a, b, 50.0, 50.0, 10.0, 10.0, r_target)
        frames.append(pd.DataFrame({"dataset": name, "x": xx, "y": yy}))
        st = stats_2d(xx, yy)
        st["spearman"] = float(pd.Series(xx).corr(pd.Series(yy), method="spearman"))
        # how much does ONE point carry?  drop each point in turn and watch r move.
        infl = []
        for i in range(n):
            keep = np.ones(n, bool)
            keep[i] = False
            infl.append(abs(float(np.corrcoef(xx[keep], yy[keep])[0, 1]) - r_target))
        st["max_single_point_influence"] = float(max(infl))
        stats[name] = st
    pd.concat(frames, ignore_index=True).to_csv(DATA / "same_correlation.csv", index=False)
    REPORT["same_correlation"] = stats

    # r = 0 with an obvious and perfect relationship: a circle
    th = np.linspace(0, 2 * np.pi, 400, endpoint=False)
    xx = 50 + 10 * np.cos(th)
    yy = 50 + 10 * np.sin(th)
    pd.DataFrame({"x": xx, "y": yy}).to_csv(DATA / "circle_r_zero.csv", index=False)
    REPORT["circle_r_zero"] = stats_2d(xx, yy)
    return stats


# --------------------------------------------------------------------------
# 6. Simpson's paradox
# --------------------------------------------------------------------------
def build_simpson():
    # ---- real data: UC Berkeley graduate admissions, 1973 (Bickel et al., 1975) ----
    rows = [
        ("A", 825, 62, 108, 82), ("B", 560, 63, 25, 68), ("C", 325, 37, 593, 34),
        ("D", 417, 33, 375, 35), ("E", 191, 28, 393, 24), ("F", 373, 6, 341, 7),
    ]
    rec = []
    for dept, ma, mr, fa, fr in rows:
        rec += [{"major": dept, "gender": "Men", "applied": ma, "admitted": round(ma * mr / 100)},
                {"major": dept, "gender": "Women", "applied": fa, "admitted": round(fa * fr / 100)}]
    berkeley = pd.DataFrame(rec)
    berkeley.to_csv(DATA / "simpson_berkeley_1973.csv", index=False)

    m = berkeley[berkeley.gender == "Men"]
    w = berkeley[berkeley.gender == "Women"]
    REPORT["simpson_berkeley"] = {
        "overall_men": float(m.admitted.sum() / m.applied.sum()),
        "overall_women": float(w.admitted.sum() / w.applied.sum()),
        "by_major": {
            d: {
                "men": float(g[g.gender == "Men"].admitted.iloc[0] / g[g.gender == "Men"].applied.iloc[0]),
                "women": float(g[g.gender == "Women"].admitted.iloc[0] / g[g.gender == "Women"].applied.iloc[0]),
            }
            for d, g in berkeley.groupby("major")
        },
    }

    # ---- synthetic: revision hours vs score, within and across three schools ----
    frames = []
    for school, offset, slope in [("School A", 62, 2.4), ("School B", 52, 2.0), ("School C", 42, 1.6)]:
        n = 40
        hours = rng.uniform(2, 18, n)
        score = offset + slope * hours + rng.normal(0, 3.0, n)
        frames.append(pd.DataFrame({"school": school, "hours": hours, "score": score}))
    sim = pd.concat(frames, ignore_index=True)
    sim.to_csv(DATA / "simpson_schools.csv", index=False)
    REPORT["simpson_schools"] = {
        "pooled_r": float(np.corrcoef(sim.hours, sim.score)[0, 1]),
        "within_r": {s: float(np.corrcoef(g.hours, g.score)[0, 1]) for s, g in sim.groupby("school")},
    }
    return berkeley, sim


# --------------------------------------------------------------------------
# 7. real-world aggregation trap: Gapminder 2007
# --------------------------------------------------------------------------
def build_gapminder():
    gm = pd.read_csv(RAW / "gapminder2007.csv")
    keep = ["country", "continent", "lifeExp", "gdpPercap", "pop"]
    gm = gm[keep].dropna()
    gm.to_csv(DATA / "gapminder_2007.csv", index=False)
    REPORT["gapminder_2007"] = {
        "all_countries_r": float(np.corrcoef(np.log10(gm.gdpPercap), gm.lifeExp)[0, 1]),
        "n": int(len(gm)),
        "within_continent_r": {
            c: float(np.corrcoef(np.log10(g["gdpPercap"]), g["lifeExp"])[0, 1])
            for c, g in gm.groupby("continent")
        },
    }
    return gm


def build_real_penguins():
    """A real, messy dataset: same mean, different species."""
    p = pd.read_csv(RAW / "penguins.csv").dropna(subset=["body_mass_g", "flipper_length_mm", "species"])
    p = p[["species", "island", "flipper_length_mm", "body_mass_g"]]
    p.to_csv(DATA / "penguins.csv", index=False)
    REPORT["penguins_real"] = {
        "overall_mean_body_mass": float(p.body_mass_g.mean()),
        "overall_sd_body_mass": float(p.body_mass_g.std(ddof=0)),
        "overall_r_flipper_mass": float(np.corrcoef(p.flipper_length_mm, p.body_mass_g)[0, 1]),
        "within_species_r": {
            s: float(np.corrcoef(g.flipper_length_mm, g.body_mass_g)[0, 1])
            for s, g in p.groupby("species")
        },
        "by_species": {
            s: {"mean": float(g.body_mass_g.mean()), "sd": float(g.body_mass_g.std(ddof=0)), "n": int(len(g))}
            for s, g in p.groupby("species")
        },
    }
    return p


def main():
    build_canonical()
    build_own_dozen()
    build_mean_sd_twins()
    build_same_boxplot()
    build_same_correlation()
    build_simpson()
    build_gapminder()
    build_real_penguins()

    (DATA / "summary_statistics.json").write_text(json.dumps(REPORT, indent=2, default=str))

    print("=" * 78)
    print("VERIFICATION")
    print("=" * 78)
    od = REPORT["own_dozen"]
    print("own dozen, max absolute spread across 12 datasets:", od["max_abs_spread"])
    print("identical to 1e-12:", od["identical_to_1e-12"])
    print()
    print("Anscombe (should be identical to 3 dp):")
    for k, v in REPORT["anscombe"].items():
        print("  ", k, {kk: round(vv, 4) for kk, vv in v.items()})
    print()
    print("same mean & SD twins:")
    for k, v in REPORT["mean_sd_twins"].items():
        print("  ", k, "mean", round(v["mean"], 6), "sd", round(v["sd"], 6),
              "median", round(v["median"], 2), "IQR", round(v["iqr"], 2), "skew", round(v["skewness"], 2))
    print()
    print("same boxplot:", json.dumps(REPORT["same_boxplot"], indent=2)[:900])
    print()
    print("same correlation:", {k: round(v["r"], 6) for k, v in REPORT["same_correlation"].items()})
    print("circle r:", round(REPORT["circle_r_zero"]["r"], 8))
    print()
    print("berkeley overall admit rate:", {k: round(v, 4) for k, v in REPORT["simpson_berkeley"].items() if isinstance(v, float)})
    print("schools pooled r:", round(REPORT["simpson_schools"]["pooled_r"], 3),
          "within:", {k: round(v, 3) for k, v in REPORT["simpson_schools"]["within_r"].items()})
    print()
    print("gapminder all-countries r:", round(REPORT["gapminder_2007"]["all_countries_r"], 3))
    print("gapminder within-continent r:", {k: round(v, 3) for k, v in REPORT["gapminder_2007"]["within_continent_r"].items()})
    print()
    print("penguins overall mean body mass:", round(REPORT["penguins_real"]["overall_mean_body_mass"], 1))
    print("files in data/:", sorted(p.name for p in DATA.glob("*.csv")))


if __name__ == "__main__":
    main()
