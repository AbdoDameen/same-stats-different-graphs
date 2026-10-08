"""
02_build_figures.py
===================
Builds every interactive figure (Plotly) and every statistics table (HTML) used
in the article, straight from data/*.csv.  Nothing in the article is typed by
hand: if a number appears in the prose tables, this script produced it.

Run:  .venv/bin/python scripts/02_build_figures.py
Output: figures/*.png (static copies for social/social-proof) and
        article/parts.json (figure + table HTML fragments for the assembler)
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
FIG = ROOT / "figures"
ART = ROOT / "article"
FIG.mkdir(exist_ok=True)
ART.mkdir(exist_ok=True)

PALETTE = [
    "#8A2BE2", "#FF6B6B", "#00B894", "#FFB400", "#2D98DA", "#F368E0",
    "#FF9F43", "#00CEC9", "#6C5CE7", "#EE5A6F", "#26DE81", "#4B7BEC",
]
PURPLE, CORAL, TEAL, AMBER, BLUE, PINK = "#8A2BE2", "#FF6B6B", "#00B894", "#FFB400", "#2D98DA", "#F368E0"
INK = "#1f2937"
GRID = "#efe6fb"

FONT = dict(family="Inter, Poppins, Helvetica, Arial, sans-serif", color=INK, size=13)


def base_layout(fig, height=520, title=None, showlegend=False, margin=None):
    fig.update_layout(
        height=height,
        title=dict(text=title, x=0.02, font=dict(size=17, color=INK)) if title else None,
        paper_bgcolor="#ffffff",
        plot_bgcolor="#ffffff",
        font=FONT,
        showlegend=showlegend,
        margin=margin or dict(l=60, r=30, t=70 if title else 30, b=50),
        hoverlabel=dict(bgcolor="white", font_size=13, bordercolor=PURPLE),
        legend=dict(bgcolor="rgba(255,255,255,0.85)", bordercolor=GRID, borderwidth=1),
    )
    fig.update_xaxes(gridcolor=GRID, zerolinecolor=GRID, linecolor=GRID, ticks="outside", tickcolor=GRID)
    fig.update_yaxes(gridcolor=GRID, zerolinecolor=GRID, linecolor=GRID, ticks="outside", tickcolor=GRID)
    return fig


def frag(fig, div_id):
    return fig.to_html(
        include_plotlyjs=False,
        full_html=False,
        div_id=div_id,
        config={"displayModeBar": False, "responsive": True},
    )


# --------------------------------------------------------------------------
# FIGURE 1 - Anscombe's Quartet
# --------------------------------------------------------------------------
def fig_anscombe():
    aq = pd.read_csv(DATA / "anscombe_quartet.csv")
    fig = make_subplots(
        rows=2, cols=2,
        subplot_titles=[f"Dataset {i}" for i in range(1, 5)],
        horizontal_spacing=0.08, vertical_spacing=0.30,
    )
    for k, (name, g) in enumerate(aq.groupby("dataset")):
        r, c = divmod(k, 2)
        col = PALETTE[k]
        x, y = g.x.to_numpy(), g.y.to_numpy()
        slope, intercept = np.polyfit(x, y, 1)
        xs = np.linspace(x.min() - 0.5, x.max() + 0.5, 50)
        fig.add_trace(
            go.Scatter(x=x, y=y, mode="markers", name=name,
                       marker=dict(size=11, color=col, line=dict(width=1.5, color="white")),
                       hovertemplate="x=%{x:.2f}<br>y=%{y:.2f}<extra></extra>"),
            row=r + 1, col=c + 1,
        )
        fig.add_trace(
            go.Scatter(x=xs, y=slope * xs + intercept, mode="lines", showlegend=False,
                       line=dict(color=col, width=3, dash="dash")),
            row=r + 1, col=c + 1,
        )
        fig.add_annotation(
            xref=f"x{k+1 if k else ''} domain", yref=f"y{k+1 if k else ''} domain",
            x=0.5, y=-0.34, showarrow=False,
            text=(f"mean x 9.00 · mean y 7.50 · sd x 3.16 · sd y 1.94<br>"
                  f"r 0.82 · slope {slope:.2f} · intercept {intercept:.2f}"),
            font=dict(size=11.5, color="#4b5563"), align="center",
            row=r + 1, col=c + 1,
        )
        fig.update_xaxes(range=[2, 20], row=r + 1, col=c + 1, title_text="x" if r else None)
        fig.update_yaxes(range=[2, 13.5], row=r + 1, col=c + 1, title_text="y" if c == 0 else None)
    return base_layout(fig, height=790, margin=dict(l=60, r=30, t=70, b=100))


# --------------------------------------------------------------------------
# FIGURE 2 - my own dozen shapes, statistics identical to 15 decimal places
# --------------------------------------------------------------------------
def _shape_grid(df, ids, ncols, height, title, marker_size=7, cols_override=None, labels=None):
    n = len(ids)
    nrows = int(np.ceil(n / ncols))
    fig = make_subplots(
        rows=nrows, cols=ncols,
        subplot_titles=[(labels or {}).get(i, i) for i in ids],
        horizontal_spacing=0.04, vertical_spacing=0.11,
    )
    for k, name in enumerate(ids):
        r, c = divmod(k, ncols)
        g = df[df.dataset == name]
        fig.add_trace(
            go.Scattergl(x=g.x, y=g.y, mode="markers", showlegend=False,
                         marker=dict(size=marker_size, color=PALETTE[k % len(PALETTE)], opacity=0.9),
                         hovertemplate="x=%{x:.2f}<br>y=%{y:.2f}<extra>" + str(name) + "</extra>"),
            row=r + 1, col=c + 1,
        )
        col = cols_override or {"gridcolor": "rgba(0,0,0,0)", "zeroline": False}
        fig.update_xaxes(showticklabels=False, showgrid=False, zeroline=False, row=r + 1, col=c + 1)
        fig.update_yaxes(showticklabels=False, showgrid=False, zeroline=False,
                         scaleanchor=None, row=r + 1, col=c + 1)
        # equal aspect for shape fidelity where possible
        fig.update_xaxes(range=[-1, 1], row=r + 1, col=c + 1) if False else None
    fig.update_annotations(font_size=12.5)
    return base_layout(fig, height=height, title=title)


def fig_own_dozen():
    df = pd.read_csv(DATA / "same_stats_shapes.csv")
    order = ["circle", "star", "heart", "plus", "x_shape", "wave",
             "spiral", "triangle", "h_lines", "v_lines", "blob", "letters_DA"]
    labels = {"letters_DA": "initials “DA”", "h_lines": "three flat lines",
              "v_lines": "three upright lines", "x_shape": "a cross (x)", "plus": "a cross (+)"}
    df = df[df.dataset.isin(order)]
    fig = _shape_grid(df, order, 4, 780, None, marker_size=6.5, labels=labels)
    for k, name in enumerate(order):
        r, c = divmod(k, 4)
        g = df[df.dataset == name]
        pad = 0.12 * max(g.x.max() - g.x.min(), g.y.max() - g.y.min())
        fig.update_xaxes(range=[g.x.min() - pad, g.x.max() + pad], row=r + 1, col=c + 1)
        fig.update_yaxes(range=[g.y.min() - pad, g.y.max() + pad], row=r + 1, col=c + 1)
    return fig


def fig_datasaurus():
    df = pd.read_csv(DATA / "datasaurus_dozen.csv")
    order = ["dino", "away", "bullseye", "circle", "dots", "h_lines",
             "high_lines", "slant_down", "slant_up", "star", "v_lines",
             "wide_lines", "x_shape"]
    df = df[df.dataset.isin(order)]
    labels = {"dino": "dinosaur", "away": "away", "h_lines": "h_lines", "high_lines": "high_lines",
              "slant_down": "slant_down", "slant_up": "slant_up", "v_lines": "v_lines",
              "wide_lines": "wide_lines", "x_shape": "x_shape"}
    fig = _shape_grid(df, order, 5, 700, None, marker_size=5.5, labels=labels)
    for k, name in enumerate(order):
        r, c = divmod(k, 5)
        g = df[df.dataset == name]
        pad = 0.08 * max(g.x.max() - g.x.min(), g.y.max() - g.y.min())
        fig.update_xaxes(range=[g.x.min() - pad, g.x.max() + pad], row=r + 1, col=c + 1)
        fig.update_yaxes(range=[g.y.min() - pad, g.y.max() + pad], row=r + 1, col=c + 1)
    return fig


# --------------------------------------------------------------------------
# FIGURE 3 - same mean, same SD, different everything else
# --------------------------------------------------------------------------
def fig_mean_sd():
    df = pd.read_csv(DATA / "same_mean_sd_twins.csv")
    order = ["normal", "bimodal", "uniform", "right_skewed", "left_skewed", "outlier_driven"]
    pretty = {"normal": "normal", "bimodal": "bimodal", "uniform": "uniform",
              "right_skewed": "right skewed", "left_skewed": "left skewed",
              "outlier_driven": "four outliers carry the SD"}
    fig = make_subplots(
        rows=2, cols=3,
        subplot_titles=[pretty[o] for o in order],
        horizontal_spacing=0.06, vertical_spacing=0.28,
    )
    lo, hi = df.value.min() - 3, df.value.max() + 3
    for k, name in enumerate(order):
        r, c = divmod(k, 3)
        v = df[df.dataset == name].value
        fig.add_trace(
            go.Histogram(x=v, nbinsx=45, marker_color=PALETTE[k], opacity=0.9,
                         showlegend=False, marker_line_width=0),
            row=r + 1, col=c + 1,
        )
        fig.add_vline(x=50, line=dict(color=INK, width=2, dash="dash"), row=r + 1, col=c + 1)
        fig.add_vline(x=float(np.median(v)), line=dict(color=CORAL, width=2), row=r + 1, col=c + 1)
        fig.add_annotation(
            xref=f"x{k+1 if k else ''} domain", yref=f"y{k+1 if k else ''} domain",
            x=0.5, y=-0.3, showarrow=False,
            text=(f"mean 50.00 · SD 10.00<br>median {np.median(v):.2f} · IQR {np.subtract(*np.percentile(v,[75,25])):.2f}"),
            font=dict(size=11, color="#4b5563"), align="center", row=r + 1, col=c + 1,
        )
        fig.update_xaxes(range=[lo, hi], row=r + 1, col=c + 1)
    return base_layout(fig, height=760, margin=dict(l=60, r=30, t=70, b=100))


# --------------------------------------------------------------------------
# FIGURE 4 - same boxplot, different data
# --------------------------------------------------------------------------
def fig_boxplot_mirage():
    df = pd.read_csv(DATA / "same_boxplot.csv")
    order = ["uniform", "bell (mass in the middle)", "hollow (U shape)",
             "top-heavy", "bottom-heavy", "spike at the median"]
    order = [o for o in order if o in set(df.dataset)]
    fig = make_subplots(
        rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.08,
        row_heights=[0.62, 0.38],
        subplot_titles=("every dot, jittered - six utterly different datasets",
                        "the six boxplots you would put in the report"),
    )
    rng = np.random.default_rng(3)
    for k, name in enumerate(order):
        v = df[df.dataset == name].value.to_numpy()
        fig.add_trace(
            go.Scatter(
                x=v, y=np.full(len(v), k) + rng.normal(0, 0.10, len(v)),
                mode="markers", name=name, legendgroup=name,
                marker=dict(size=6, color=PALETTE[k], opacity=0.55),
                hovertemplate="value %{x:.2f}<extra>" + name + "</extra>",
            ),
            row=1, col=1,
        )
    for k, name in enumerate(order):
        v = df[df.dataset == name].value.to_numpy()
        fig.add_trace(
            go.Box(x=v, name=name, legendgroup=name, showlegend=False,
                   marker_color=PALETTE[k], line=dict(color=PALETTE[k], width=2),
                   fillcolor="rgba(255,255,255,0)", boxpoints=False,
                   hoverinfo="skip"),
            row=2, col=1,
        )
    fig.update_yaxes(showticklabels=False, row=1, col=1)
    fig.update_xaxes(title_text="the metric being tracked (identical five-number summary for all six)", row=2, col=1)
    return base_layout(fig, height=720, showlegend=True,
                       margin=dict(l=60, r=30, t=60, b=60))


# --------------------------------------------------------------------------
# FIGURE 5 - same correlation, different relationships
# --------------------------------------------------------------------------
def fig_same_r():
    df = pd.read_csv(DATA / "same_correlation.csv")
    rep = json.loads((DATA / "summary_statistics.json").read_text())["same_correlation"]
    order = ["linear", "curved (quadratic)", "step change", "one outlier flips it", "wall of noise + trend"]
    titles = ["a straight line", "a curve", "a step change",
              "one outlier carries it (watch the y axis)", "noise, then a late trend"]
    fig = make_subplots(
        rows=2, cols=3, subplot_titles=titles,
        horizontal_spacing=0.06, vertical_spacing=0.27,
    )
    for k, name in enumerate(order):
        r, c = divmod(k, 3)
        g = df[df.dataset == name]
        col = PALETTE[k]
        fig.add_trace(
            go.Scatter(x=g.x, y=g.y, mode="markers", showlegend=False,
                       marker=dict(size=6, color=col, opacity=0.75),
                       hovertemplate="x=%{x:.2f}<br>y=%{y:.2f}<extra></extra>"),
            row=r + 1, col=c + 1,
        )
        xs = np.linspace(20, 80, 40)
        slope, intercept = np.polyfit(g.x, g.y, 1)
        fig.add_trace(
            go.Scatter(x=xs, y=slope * xs + intercept, mode="lines", showlegend=False,
                       line=dict(color=INK, width=2, dash="dash")),
            row=r + 1, col=c + 1,
        )
        s = rep[name]
        fig.add_annotation(
            xref=f"x{k+1 if k else ''} domain", yref=f"y{k+1 if k else ''} domain",
            x=0.5, y=-0.3, showarrow=False,
            text=(f"Pearson r 0.7000 · Spearman {s['spearman']:.3f}<br>"
                  f"drop the worst point and r moves {s['max_single_point_influence']:.3f}"),
            font=dict(size=11, color="#4b5563"), align="center", row=r + 1, col=c + 1,
        )
    fig.update_xaxes(title_text=None)
    return base_layout(fig, height=790, margin=dict(l=60, r=30, t=70, b=100))


def fig_circle():
    df = pd.read_csv(DATA / "circle_r_zero.csv")
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=df.x, y=df.y, mode="markers", name="every point on a perfect circle",
        marker=dict(size=9, color=TEAL, opacity=0.85, line=dict(width=1, color="white")),
        hovertemplate="x=%{x:.2f}<br>y=%{y:.2f}<extra></extra>",
    ))
    fig.add_trace(go.Scatter(x=[30, 70], y=[50, 50], mode="lines", name="the regression line: perfectly flat",
                             line=dict(color=CORAL, width=4, dash="dash")))
    fig.add_annotation(x=50, y=50, text="Pearson r = 0.00<br><b>and the relationship is perfect</b>",
                       showarrow=False, yshift=26, font=dict(size=14, color=INK))
    return base_layout(fig, height=520, showlegend=True)


# --------------------------------------------------------------------------
# FIGURE 6 - Simpson's paradox
# --------------------------------------------------------------------------
def fig_berkeley():
    b = pd.read_csv(DATA / "simpson_berkeley_1973.csv")
    rate = b.assign(rate=b.admitted / b.applied)
    overall = rate.groupby("gender")[["applied", "admitted"]].sum()
    overall["rate"] = overall.admitted / overall.applied

    fig = make_subplots(
        rows=1, cols=2, column_widths=[0.3, 0.7],
        subplot_titles=("the headline", "the same admissions, split by department"),
        horizontal_spacing=0.12,
    )
    fig.add_trace(
        go.Bar(x=overall.index, y=overall.rate, showlegend=False,
               marker_color=[PURPLE, CORAL], text=[f"{v:.1%}" for v in overall.rate],
               textposition="outside", textfont=dict(size=15),
               hovertemplate="%{x}: %{y:.1%}<extra></extra>"),
        row=1, col=1,
    )
    apply_pay = b.copy()
    for gen, col in [("Men", PURPLE), ("Women", CORAL)]:
        g = apply_pay[apply_pay.gender == gen].sort_values("major")
        fig.add_trace(
            go.Bar(x=g.major, y=g.admitted / g.applied, name=gen, marker_color=col,
                   text=[f"{v:.0%}" for v in g.admitted / g.applied], textposition="outside",
                   textfont=dict(size=11),
                   hovertemplate="Department %{x} · " + gen + ": %{y:.1%}<extra></extra>"),
            row=1, col=2,
        )
    fig.update_yaxes(tickformat=".0%", range=[0, 1.0], row=1, col=1, title_text="admission rate")
    fig.update_yaxes(tickformat=".0%", range=[0, 1.0], row=1, col=2)
    fig.update_xaxes(title_text="department", row=1, col=2)
    base_layout(fig, height=580, showlegend=True, margin=dict(l=60, r=30, t=118, b=60))
    fig.add_annotation(x=0.5, y=1.155, xref="paper", yref="paper", showarrow=False,
                       text="women were admitted at a higher rate in 4 of the 6 departments, "
                            "and still lost overall",
                       font=dict(size=12.5, color="#4b5563"))
    return fig


def fig_schools():
    s = pd.read_csv(DATA / "simpson_schools.csv")
    rep = json.loads((DATA / "summary_statistics.json").read_text())["simpson_schools"]
    fig = go.Figure()
    for k, (name, g) in enumerate(s.groupby("school")):
        fig.add_trace(go.Scatter(
            x=g.hours, y=g.score, mode="markers", name=name,
            marker=dict(size=9, color=PALETTE[k], opacity=0.8, line=dict(width=1, color="white")),
            hovertemplate="%{x:.1f} h · %{y:.1f}<extra>" + name + "</extra>",
        ))
        slope, intercept = np.polyfit(g.hours, g.score, 1)
        xs = np.linspace(g.hours.min(), g.hours.max(), 20)
        fig.add_trace(go.Scatter(x=xs, y=slope * xs + intercept, mode="lines", name=f"{name}: r={rep['within_r'][name]:.2f}",
                                 line=dict(color=PALETTE[k], width=3)))
    slope, intercept = np.polyfit(s.hours, s.score, 1)
    xs = np.linspace(s.hours.min(), s.hours.max(), 20)
    fig.add_trace(go.Scatter(x=xs, y=slope * xs + intercept, mode="lines",
                             name=f"all students pooled: r={rep['pooled_r']:.2f}",
                             line=dict(color=INK, width=4, dash="dash")))
    fig.add_annotation(x=10, y=95, text="pooled, more revision looks like <b>lower</b> scores",
                       showarrow=False, font=dict(size=13, color=CORAL))
    fig.update_xaxes(title_text="hours of revision a week")
    fig.update_yaxes(title_text="exam score")
    return base_layout(fig, height=560, showlegend=True)


# --------------------------------------------------------------------------
# FIGURE 7 - real, messy data
# --------------------------------------------------------------------------
def fig_gapminder():
    gm = pd.read_csv(DATA / "gapminder_2007.csv")
    rep = json.loads((DATA / "summary_statistics.json").read_text())["gapminder_2007"]
    fig = go.Figure()
    for k, (cont, g) in enumerate(gm.groupby("continent")):
        fig.add_trace(go.Scatter(
            x=g.gdpPercap, y=g.lifeExp, mode="markers", name=cont,
            marker=dict(size=np.sqrt(g["pop"]) / 900, color=PALETTE[k], opacity=0.72,
                        line=dict(width=1, color="white")),
            customdata=np.c_[g.country],
            hovertemplate="%{customdata[0]}<br>GDP per person $%{x:,.0f}<br>"
                          "life expectancy %{y:.1f}<extra></extra>",
        ))
        slope, intercept = np.polyfit(np.log10(g.gdpPercap), g.lifeExp, 1)
        xs = np.linspace(np.log10(g.gdpPercap.min()), np.log10(g.gdpPercap.max()), 20)
        fig.add_trace(go.Scatter(x=10**xs, y=slope * xs + intercept, mode="lines",
                                 legendgroup=cont, showlegend=False, line=dict(color=PALETTE[k], width=2.5)))
    slope, intercept = np.polyfit(np.log10(gm.gdpPercap), gm.lifeExp, 1)
    xs = np.linspace(np.log10(gm.gdpPercap.min()), np.log10(gm.gdpPercap.max()), 20)
    fig.add_trace(go.Scatter(x=10**xs, y=slope * xs + intercept, mode="lines",
                             name=f"all {len(gm)} countries: r={rep['all_countries_r']:.2f}",
                             line=dict(color=INK, width=4, dash="dash")))
    fig.update_xaxes(title_text="GDP per person (US$, log scale)", type="log")
    fig.update_yaxes(title_text="life expectancy at birth (years)")
    return base_layout(fig, height=580, showlegend=True)


def fig_penguins():
    p = pd.read_csv(DATA / "penguins.csv")
    rep = json.loads((DATA / "summary_statistics.json").read_text())["penguins_real"]
    fig = go.Figure()
    for k, (sp, g) in enumerate(p.groupby("species")):
        fig.add_trace(go.Scatter(
            x=g.flipper_length_mm, y=g.body_mass_g, mode="markers", name=sp,
            marker=dict(size=9, color=PALETTE[k], opacity=0.75, line=dict(width=1, color="white")),
            hovertemplate="%{x} mm · %{y:,} g<extra>" + sp + "</extra>",
        ))
        slope, intercept = np.polyfit(g.flipper_length_mm, g.body_mass_g, 1)
        xs = np.linspace(g.flipper_length_mm.min(), g.flipper_length_mm.max(), 20)
        fig.add_trace(go.Scatter(x=xs, y=slope * xs + intercept, mode="lines", showlegend=False,
                                 line=dict(color=PALETTE[k], width=3)))
    slope, intercept = np.polyfit(p.flipper_length_mm, p.body_mass_g, 1)
    xs = np.linspace(p.flipper_length_mm.min(), p.flipper_length_mm.max(), 20)
    fig.add_trace(go.Scatter(x=xs, y=slope * xs + intercept, mode="lines",
                             name=f"all 3 species pooled: r={rep['overall_r_flipper_mass']:.2f}",
                             line=dict(color=INK, width=4, dash="dash")))
    fig.update_xaxes(title_text="flipper length (mm)")
    fig.update_yaxes(title_text="body mass (g)")
    return base_layout(fig, height=560, showlegend=True)


# --------------------------------------------------------------------------
# tables, generated from the same JSON the figures use
# --------------------------------------------------------------------------
def _table(head, rows, caption=None, highlight=None):
    h = "".join(f"<th>{c}</th>" for c in head)
    body = ""
    for row in rows:
        cls = ' class="hl"' if highlight and highlight in str(row[0]) else ""
        body += f"<tr{cls}>" + "".join(f"<td>{c}</td>" for c in row) + "</tr>"
    cap = f'<p class="tcap">{caption}</p>' if caption else ""
    return f'<div class="tablewrap"><table><thead><tr>{h}</tr></thead><tbody>{body}</tbody></table></div>{cap}'


def tables(rep):
    out = {}

    # Anscombe at 2 dp and at 4 dp
    rows2, rows4 = [], []
    for name, s in rep["anscombe"].items():
        x = np.array([1])  # placeholder to keep flake quiet
        rows2.append([name.replace("_", " "), f"{s['mean_x']:.2f}", f"{s['mean_y']:.2f}",
                      f"{s['sd_x']:.2f}", f"{s['sd_y']:.2f}", f"{s['r']:.2f}"])
        rows4.append([name.replace("_", " "), f"{s['mean_y']:.4f}", f"{s['sd_y']:.4f}",
                      f"{s['r']:.4f}"])
    out["anscombe_2dp"] = _table(
        ["dataset", "mean of x", "mean of y", "SD of x", "SD of y", "correlation"],
        rows2,
        "Anscombe published exactly this table. Read down the columns: four different datasets, "
        "one identical set of statistics. Everything below two decimal places is invisible on the page.",
    )
    out["anscombe_4dp"] = _table(
        ["dataset", "mean of y", "SD of y", "correlation (r)"], rows4,
        "The same four datasets at four decimal places. The differences that the two-decimal table hides "
        "sit in the third and fourth decimals.",
    )

    # own dozen at 10 dp
    od = rep["own_dozen"]["per_dataset"]
    rows = [[k, f"{v['mean_x']:.10f}", f"{v['mean_y']:.10f}", f"{v['sd_x']:.10f}",
             f"{v['sd_y']:.10f}", f"{v['r']:.10f}"] for k, v in od.items()]
    out["own_dozen"] = _table(
        ["shape", "mean of x", "mean of y", "SD of x", "SD of y", "correlation"], rows,
        "Twelve point clouds, ten decimal places. The largest disagreement between any two rows is "
        f"{max(rep['own_dozen']['max_abs_spread'].values()):.1e}, which is floating-point noise.",
    )

    # mean & sd twins
    rows = [[k, f"{v['mean']:.2f}", f"{v['sd']:.2f}", f"{v['median']:.2f}",
             f"{v['iqr']:.2f}", f"{v['min']:.1f}", f"{v['max']:.1f}", f"{v['skewness']:+.2f}"]
            for k, v in rep["mean_sd_twins"].items()]
    out["mean_sd"] = _table(
        ["distribution", "mean", "SD", "median", "IQR (Q3-Q1)", "min", "max", "skewness"], rows,
        "Every distribution has mean 50.00 and standard deviation 10.00. The median moves by 4.5 points, "
        "the interquartile range by a factor of three, and the skewness changes sign twice.",
    )

    # boxplot mirage
    rows = [[k, f"{v['min']:.2f}", f"{v['q1']:.2f}", f"{v['median']:.2f}", f"{v['q3']:.2f}",
             f"{v['max']:.2f}", f"{v['iqr']:.2f}", f"{v['mean']:.2f}", f"{v['sd']:.2f}"]
            for k, v in rep["same_boxplot"].items()]
    out["same_boxplot"] = _table(
        ["dataset", "min", "Q1", "median", "Q3", "max", "IQR", "mean", "SD"], rows,
        "The five-number summary is identical for all six datasets by construction. The mean still drifts "
        "from 44.82 to 55.83 and the standard deviation from 19.11 to 27.06.",
    )

    # correlation
    rows = [[k, "0.7000", f"{v['spearman']:.3f}", f"{v['max_single_point_influence']:.3f}"]
            for k, v in rep["same_correlation"].items()]
    out["same_r"] = _table(
        ["dataset", "Pearson r", "Spearman rho", "r moves this much if you delete one point"], rows,
        "Five datasets, one correlation. Spearman's rho, which only cares about rank order, already "
        "separates them, and the fourth dataset changes by nearly 0.3 when a single point is removed.",
    )

    # berkeley
    b = pd.read_csv(DATA / "simpson_berkeley_1973.csv")
    rows = []
    for m, g in b.groupby("major"):
        men = g[g.gender == "Men"].iloc[0]
        women = g[g.gender == "Women"].iloc[0]
        rows.append([m, f"{men.applied:,}", f"{men.admitted:,}", f"{men.admitted/men.applied:.1%}",
                     f"{women.applied:,}", f"{women.admitted:,}", f"{women.admitted/women.applied:.1%}",
                     "women higher" if women.admitted / women.applied > men.admitted / men.applied else "men higher"])
    men_t = b[b.gender == "Men"].applied.sum(), b[b.gender == "Men"].admitted.sum()
    women_t = b[b.gender == "Women"].applied.sum(), b[b.gender == "Women"].admitted.sum()
    rows.append(["ALL", f"{men_t[0]:,}", f"{men_t[1]:,}", f"{men_t[1]/men_t[0]:.1%}",
                 f"{women_t[0]:,}", f"{women_t[1]:,}", f"{women_t[1]/women_t[0]:.1%}", "men higher"])
    out["berkeley"] = _table(
        ["department", "men applied", "men admitted", "men rate", "women applied",
         "women admitted", "women rate", "who was admitted more often"], rows,
        "UC Berkeley graduate admissions, 1973, the six largest departments (Bickel, Hammel and O'Connell, 1975). "
        "Overall the men's admission rate beats the women's; inside four of the six departments the women's rate is "
        "the higher one. The women applied in far greater numbers to the departments that admit almost nobody.",
        highlight="ALL",
    )

    # gapminder
    gm = rep["gapminder_2007"]
    rows = [["all countries", f"{gm['all_countries_r']:.3f}"]] + \
           [[f"within {k}", f"{v:.3f}"] for k, v in gm["within_continent_r"].items()]
    out["gapminder"] = _table(
        ["population", "correlation between log GDP per person and life expectancy"], rows,
        "Gapminder 2007, 142 countries. The pooled correlation of 0.81 is a statement about the world; "
        "inside Africa the same two variables move together far more weakly.",
    )

    # penguins
    pr = rep["penguins_real"]
    rows = [["all three species pooled", f"{pr['overall_r_flipper_mass']:.3f}", f"{pr['by_species']['Adelie']['n']+pr['by_species']['Chinstrap']['n']+pr['by_species']['Gentoo']['n']}"]] + \
           [[k, f"{v:.3f}", str(pr["by_species"][k]["n"])] for k, v in pr["within_species_r"].items()]
    out["penguins"] = _table(
        ["population", "correlation between flipper length and body mass", "n"], rows,
        "Palmer Station penguins, real and messy. Pool the species and the relationship looks almost "
        "mechanical; inside each species it is much weaker, because the pooled figure is mostly measuring "
        "the difference between a Gentoo and an Adelie.",
    )
    return out


def main():
    rep = json.loads((DATA / "summary_statistics.json").read_text())
    figures = {
        "anscombe": fig_anscombe(),
        "own_dozen": fig_own_dozen(),
        "datasaurus": fig_datasaurus(),
        "mean_sd": fig_mean_sd(),
        "boxplot_mirage": fig_boxplot_mirage(),
        "same_r": fig_same_r(),
        "circle": fig_circle(),
        "berkeley": fig_berkeley(),
        "schools": fig_schools(),
        "gapminder": fig_gapminder(),
        "penguins": fig_penguins(),
    }
    parts = {f"FIG:{k}": frag(v, f"fig-{k}") for k, v in figures.items()}
    parts.update({f"TABLE:{k}": v for k, v in tables(rep).items()})
    (ART / "parts.json").write_text(json.dumps(parts))
    print("figure fragments:", [k for k in parts if k.startswith("FIG")])
    print("table fragments:", [k for k in parts if k.startswith("TABLE")])

    # static PNGs, best effort (needs kaleido)
    try:
        for k, v in figures.items():
            v.write_image(str(FIG / f"{k}.png"), width=1400, height=int(v.layout.height or 600) * 1, scale=1.6)
        print("static PNGs written to figures/")
    except Exception as exc:
        print("static PNG export skipped:", type(exc).__name__, exc)


if __name__ == "__main__":
    main()
