# Same Numbers, Different Stories

Datasets, code and figures behind the article **Same Numbers, Different Stories**, a working guide to
what descriptive statistics hide.

The argument is simple to state and hard to believe: a mean, a standard deviation and a correlation
can all be correct, can all describe the same numbers, and can still point you at the wrong decision.
This repository contains every dataset, generator and figure used in the article, plus the checks that
prove the numbers in the article are the numbers in the data.

## The headline result

Twelve datasets of 142 points each, carrying **exactly** the same five statistics:

| statistic | value |
|---|---|
| mean of x | 54.2600 |
| mean of y | 47.8300 |
| standard deviation of x | 16.7600 |
| standard deviation of y | 26.9300 |
| Pearson correlation | -0.0641 |

Largest disagreement between any two of the twelve, across all five statistics: **1.1e-14**, which is
floating point noise. The datasets look like a heart, a spiral, a five point star, a wave, three flat
lines and the initials DA. See `figures/own_dozen.png`.

## What each dataset demonstrates

| dataset | rows | the point it makes |
|---|---|---|
| `anscombe_quartet.csv` | 44 | The 1973 original. Four datasets, identical statistics to two decimal places, four different pictures. |
| `same_stats_shapes.csv` | 1,704 | Twelve shapes. Identical statistics to fifteen decimal places, built with an affine and orthogonal transform rather than simulated annealing. |
| `datasaurus_dozen.csv` | 1,846 | The published Datasaurus Dozen (Matejka and Fitzmaurice, 2017), redistributed for study. |
| `same_mean_sd_twins.csv` | 2,400 | Six distributions, all mean 50.00 and SD 10.00. Medians from 47.71 to 52.25, IQRs from 5.73 to 18.51. |
| `same_boxplot.csv` | 606 | Six datasets, one identical five-number summary: 10, 30, 50, 70, 90. Means still range from 44.82 to 55.83. |
| `same_correlation.csv` | 1,000 | Five relationships, all with Pearson r = 0.7000 exactly. Spearman's rho separates them. |
| `circle_r_zero.csv` | 400 | A perfect, deterministic relationship with a correlation of 0.00. |
| `simpson_berkeley_1973.csv` | 12 | Real admissions data from Berkeley, 1973. Men admitted more often overall, women admitted more often in four of six departments. |
| `simpson_schools.csv` | 120 | Synthetic. Revision and scores correlate negatively pooled and strongly positively within schools. |
| `gapminder_2007.csv` | 142 | Real. Log GDP per person and life expectancy correlate at 0.81 across countries and 0.45 within Africa. |
| `penguins.csv` | 342 | Real. Flipper length against body mass: 0.871 pooled, 0.468 to 0.703 within species. |

`data/summary_statistics.json` holds the verification report: every number the article prints came out
of that file.

## Running it

```bash
git clone https://github.com/AbdoDameen/same-stats-different-graphs.git
cd same-stats-different-graphs

uv venv --python 3.11 .venv
uv pip install --python .venv/bin/python numpy pandas scipy plotly kaleido matplotlib

python scripts/00_fetch_raw.py                 # downloads the third-party source datasets
.venv/bin/python scripts/01_make_datasets.py   # builds data/, prints the verification
.venv/bin/python scripts/02_build_figures.py   # builds figures/ and article/parts.json
.venv/bin/python scripts/03_build_article.py   # assembles the article
.venv/bin/python scripts/04_make_social_card.py
```

`01_make_datasets.py` runs its own checks and prints them. It reports the maximum spread across the
twelve identical datasets, the five-number summaries, and every correlation in the article. If the
arithmetic were wrong, the build would say so.

`03_build_article.py` refuses to write the page if any figure or table token is left unresolved, which
is what keeps the tables in the prose and the numbers in the charts from drifting apart.

## How the exact transform works

Take any cloud of points and transform it:

```python
u  = (a - a.mean()) / a.std()            # standardise
v  = (b - b.mean()) / b.std()
e  = v - (u @ v / len(u)) * u            # component of v perpendicular to u
e  = e / e.std()
v_ = r * u + np.sqrt(1 - r**2) * e       # correlation is now exactly r
x, y = m1 + s1 * u, m2 + s2 * v_         # means and SDs are now exactly the targets
```

A correlation is the cosine of the angle between two standardised vectors, so fixing the angle fixes
the correlation exactly and the affine step fixes the means and standard deviations exactly. Nothing
in the procedure inspects the shape of the cloud, which is precisely why the shape is free.

## Repository layout

```
data/       the datasets, committed so the article can be verified offline
figures/    static PNG copies of every chart
article/    template.html, figures and tables as parts.json, and the built page
scripts/    00 fetch, 01 datasets, 02 figures, 03 article, 04 social card
raw/        third-party source downloads (not committed, see 00_fetch_raw.py)
```

## Attribution

The Anscombe quartet, the Datasaurus Dozen, the Berkeley admissions table, the Gapminder series and the
Palmer Station penguin measurements come from the sources cited in the article. They are included here
for study and comparison, with attribution to their original authors. Everything generated by
`01_make_datasets.py` comes from seeded random draws and can be rebuilt to the last digit.

## Licence

Code: MIT (see `LICENSE`). Generated datasets: CC BY 4.0. Third-party datasets: the licences of their
original publishers, cited in the article.
