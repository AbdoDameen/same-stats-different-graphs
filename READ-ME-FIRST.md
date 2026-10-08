# Same Numbers, Different Stories, everything in one folder

This folder is the complete package for the article **Same Numbers, Different Stories**: the built web
page, every dataset, every figure, the code that produced all of it, and the guide below for using it.

Public repository: **https://github.com/AbdoDameen/same-stats-different-graphs**

---

## 1. The three files you need to publish the article

These already sit in the top level of this folder, ready to drop next to your website's `index.html`:

| file | what it is |
|---|---|
| `article/same-numbers-different-stories.html` | the complete article page, 393 KB, self-contained apart from the chart library |
| `article/plotly.min.js` | the chart library, 4.7 MB, loaded automatically if the CDN is unreachable |
| `article/same-numbers-different-stories-card.png` | the social sharing image, 1200 by 630, referenced by the page's meta tags |

To publish: copy those three files into the same folder as your website's `index.html`, keeping the names
exactly as they are, then link to `same-numbers-different-stories.html`. The page pulls the Inter font and
Font Awesome icons from CDNs; the charts work from `cdn.plot.ly` and fall back to the local
`plotly.min.js` if that CDN is blocked.

A copy of the same three files is already in your website folder, so the page can be previewed there now.

---

## 2. What is in each folder

```
article/    the built page, the HTML template the prose lives in, the figures and tables as
            parts.json, the local plotly bundle, the social card
data/       eleven datasets plus summary_statistics.json, the verification report that every
            number in the article is generated from
figures/    static PNG of every one of the eleven charts, for slides or social posts
scripts/    00 download the third-party sources, 01 build and verify the datasets,
            02 build the figures and the tables, 03 assemble the article, 04 social card
raw/        the third-party source files as downloaded, kept so nothing is missing
README.md   the repository readme, in full
LICENSE     MIT for the code, CC BY 4.0 for the generated datasets
```

The `.venv` folder and the git history were left out of this copy to keep it small. The repository link
above has both.

---

## 3. The headline result, in case you need it in a hurry

Twelve datasets of 142 points each. All twelve share these five statistics **exactly**:

- mean of x = 54.2600
- mean of y = 47.8300
- standard deviation of x = 16.7600
- standard deviation of y = 26.9300
- Pearson correlation = -0.0641

The largest disagreement between any two of the twelve, across all five statistics, is **1.1 × 10^-14**,
which is floating point noise. See `figures/own_dozen.png` and `data/same_stats_shapes.csv`.

The other demonstrations, with the numbers each one puts on the table:

| demonstration | the numbers |
|---|---|
| Anscombe's quartet (1973) | four datasets, identical statistics to two decimal places, four different pictures |
| The Datasaurus Dozen (2017) | thirteen published shapes, one summary: mean 54.26 and 47.83, SD 16.76 and 26.93, r -0.06 |
| Mean and SD twins | six distributions, all mean 50.00 and SD 10.00, medians from 47.71 to 52.25 |
| The boxplot mirage | six datasets, one five-number summary (10, 30, 50, 70, 90), means from 44.82 to 55.83 |
| One correlation, five relationships | Pearson r = 0.7000 in all five, Spearman's rho from 0.543 to 0.968 |
| A perfect relationship with no correlation | every point on a circle, r = 0.00 |
| Simpson's paradox, Berkeley 1973 (real) | men admitted 44.5 per cent overall, women 30.3 per cent, women higher in four of six departments |
| Simpson's paradox, schools (synthetic) | pooled r = 0.636 negative, within-school r between 0.898 and 0.969 |
| Gapminder 2007 (real) | log GDP against life expectancy: r = 0.81 across countries, 0.45 within Africa |
| Penguins (real) | flipper against body mass: r = 0.871 pooled, 0.468 to 0.703 within species |

---

## 4. Rebuilding any of it

You need Python 3.11 and `uv`. From the top level of a fresh clone:

```
git clone https://github.com/AbdoDameen/same-stats-different-graphs.git
cd same-stats-different-graphs

uv venv --python 3.11 .venv
uv pip install --python .venv/bin/python numpy pandas scipy plotly kaleido matplotlib

.venv/bin/python scripts/00_fetch_raw.py        # re-download the third-party sources
.venv/bin/python scripts/01_make_datasets.py    # rebuild data/ and print the verification
.venv/bin/python scripts/02_build_figures.py    # rebuild figures/ and the tables
.venv/bin/python scripts/03_build_article.py    # rebuild the article page
.venv/bin/python scripts/04_make_social_card.py # rebuild the sharing card
```

Two guarantees are built into the pipeline. `01_make_datasets.py` computes every statistic in the
article and prints its own verification, so a mistake in the arithmetic fails the build rather than
reaching the page. `03_build_article.py` refuses to write the page if any chart or table is missing, so
the tables in the prose cannot drift away from the numbers in the data.

---

## 5. How the exact statistics are produced

The article's own dozen uses an affine and orthogonal transform, not simulated annealing. Take any
cloud of points and:

```python
u  = (a - a.mean()) / a.std()             # standardise
v  = (b - b.mean()) / b.std()
e  = v - (u @ v / len(u)) * u             # the part of v at right angles to u
e  = e / e.std()
v_ = r * u + np.sqrt(1 - r**2) * e        # correlation is now exactly r
x, y = m1 + s1 * u, m2 + s2 * v_          # means and SDs are now exactly the targets
```

A correlation is the cosine of the angle between two standardised vectors, so fixing the angle fixes the
correlation exactly, and the affine step fixes the means and standard deviations exactly. Nothing in the
procedure looks at the shape of the cloud, which is exactly why the shape is free to be anything.

---

## 6. Attribution

The Anscombe quartet, the Datasaurus Dozen, the Berkeley 1973 admissions table, the Gapminder series and
the Palmer Station penguin measurements belong to their original authors and are redistributed here for
study, with full citations in section 10 of the article. Everything else was generated by
`scripts/01_make_datasets.py` from seeded random draws and can be rebuilt to the last digit.

Written by Abdelrhman Dameen, Dameen Analytics, October 2026.
