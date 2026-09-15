#!/usr/bin/env python3
"""KDE-4: Four publication-grade figures from analysis/stats.json.

Palette: Okabe-Ito (colorblind-safe). Outputs: PNG (300 dpi) + vector PDF per figure.
Source attribution on every figure: 'ClinicalTrials.gov, K-Dense analysis, Sep 2026'.
"""
import json
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.ticker import MultipleLocator

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STATS = os.path.join(BASE, "data", "stats.json")
OUT = os.path.join(BASE, "figures")
os.makedirs(OUT, exist_ok=True)

with open(STATS) as f:
    S = json.load(f)

# Okabe-Ito colorblind-safe palette
BLUE, ORANGE, GREEN, RED, PURPLE = "#0072B2", "#E69F00", "#009E73", "#D55E00", "#CC79A7"
SKY, YELLOW, TEAL, GREY = "#56B4E9", "#F0E442", "#009E73", "#999999"
ATTR = "Source: ClinicalTrials.gov, K-Dense analysis, Sep 2026"

plt.rcParams.update({
    "font.family": "DejaVu Sans",
    "font.size": 10,
    "axes.titlesize": 12.5,
    "axes.titleweight": "bold",
    "axes.labelsize": 10.5,
    "axes.spines.top": False,
    "axes.spines.right": False,
    "axes.edgecolor": "#444444",
    "axes.grid": True,
    "grid.color": "#DDDDDD",
    "grid.linewidth": 0.6,
    "figure.dpi": 300,
    "savefig.bbox": "tight",
    "savefig.facecolor": "white",
})


def finish(fig, ax, name, caption):
    for ext in ("png", "pdf"):
        fig.savefig(os.path.join(OUT, f"{name}.{ext}"))
    plt.close(fig)
    print(f"wrote {name}.png/.pdf — {caption}")


# ---------------------------------------------------------------- Fig 1: trend
years = sorted(int(y) for y in S["posting_by_year"])
vals = [S["posting_by_year"][str(y)] for y in years]
ytd_year = 2026

fig, ax = plt.subplots(figsize=(7.5, 4.6))
ax.plot(years[:-1], vals[:-1], "-o", color=BLUE, lw=2.2, ms=4.5,
        mfc=BLUE, mec="white", mew=0.7, zorder=3, label="Full-year postings")
# 2026 YTD: dashed connector + open marker (partial year through Sep 15)
ax.plot(years[-2:], vals[-2:], "--", color=ORANGE, lw=2.2, zorder=3)
ax.plot(years[-1], vals[-1], "o", ms=8, mfc="white", mec=ORANGE, mew=2.2,
        zorder=4, label="2026 YTD (to Sep 15)")

ax.annotate(f"2026 YTD: {vals[-1]:,}\n(+{vals[-1]/vals[-2]-1:.0%} vs. all of 2025)\n3.5 months remaining",
            xy=(ytd_year, vals[-1]), xytext=(2017.6, 830),
            fontsize=9.5, color=ORANGE, fontweight="bold",
            arrowprops=dict(arrowstyle="->", color=ORANGE, lw=1.4))
ax.annotate(f"{vals[15]} (2016)", xy=(2016, vals[15]), xytext=(2012.8, 120),
            fontsize=8.5, color="#555555",
            arrowprops=dict(arrowstyle="->", color="#999999", lw=0.9))

ax.set_title("AI/ML Clinical Trial Postings on ClinicalTrials.gov, 2005–2026")
ax.set_xlabel("Year of study posting")
ax.set_ylabel("New trials posted")
ax.set_xticks(range(2005, 2027, 3))
ax.yaxis.set_major_locator(MultipleLocator(200))
ax.set_ylim(0, 1000)
ax.set_xlim(2004, 2027.5)
ax.legend(loc="upper left", frameon=False, fontsize=9)
fig.text(0.99, 0.01, ATTR, ha="right", va="bottom", fontsize=7.5, color="#666666", style="italic")
finish(fig, ax, "fig1_postings_by_year",
       "trend line 2005–2026, 2026 YTD annotated (933, +15% vs 2025, partial year)")

# ------------------------------------------------------- Fig 2: status bars
status_labels = {
    "COMPLETED": "Completed",
    "RECRUITING": "Recruiting",
    "UNKNOWN": "Unknown\nstatus",
    "NOT_YET_RECRUITING": "Not yet\nrecruiting",
    "ACTIVE_NOT_RECRUITING": "Active, not\nrecruiting",
    "ENROLLING_BY_INVITATION": "Enrolling by\ninvitation",
    "WITHDRAWN": "Withdrawn",
    "TERMINATED": "Terminated",
    "SUSPENDED": "Suspended",
    "NO_LONGER_AVAILABLE": "No longer\navailable",
}
items = sorted(S["status_distribution"].items(), key=lambda kv: -kv[1])
labels = [status_labels.get(k, k.title()) for k, _ in items]
counts = [v for _, v in items]
total = sum(counts)
# one hue, depth-coded; recruiting-state hues distinct via Okabe-Ito accents
palette = [BLUE, ORANGE, SKY, GREEN, PURPLE, YELLOW, GREY, RED, "#8C8C8C", "#CCCCCC"]

fig, ax = plt.subplots(figsize=(8.6, 4.6))
bars = ax.bar(range(len(labels)), counts, color=palette[:len(labels)],
              edgecolor="white", linewidth=0.6)
for b, c in zip(bars, counts):
    ax.text(b.get_x() + b.get_width()/2, c + 18, f"{c:,} ({c/total:.0%})",
            ha="center", va="bottom", fontsize=8.6, fontweight="bold", color="#333333")
ax.set_xticks(range(len(labels)))
ax.set_xticklabels(labels, rotation=0, fontsize=7.2)
ax.set_title(f"Study Status Distribution — AI/ML Trials (n = {total:,})")
ax.set_ylabel("Number of trials")
ax.set_ylim(0, max(counts) * 1.18)
ax.grid(axis="x", visible=False)
fig.text(0.99, 0.01, ATTR, ha="right", va="bottom", fontsize=7.5, color="#666666", style="italic")
finish(fig, ax, "fig2_status_distribution",
       f"status distribution bar chart, n={total}")

# ------------------------------------------- Fig 3: top-12 countries, parity
countries = S["top12_countries"]
names = list(countries.keys())[::-1]        # reversed so largest on top
counts = [countries[n] for n in names]
china, usa = countries["China"], countries["United States"]

fig, ax = plt.subplots(figsize=(7.5, 5.0))
colors = []
for n in names:
    if n == "China":
        colors.append(RED)
    elif n == "United States":
        colors.append(BLUE)
    else:
        colors.append("#AAB4BE")
bars = ax.barh(names, counts, color=colors, edgecolor="white", linewidth=0.6)
for b, c in zip(bars, counts):
    ax.text(c + 8, b.get_y() + b.get_height()/2, f"{c:,}",
            va="center", fontsize=8.8, fontweight="bold", color="#333333")

ax.set_title("Top 12 Countries Hosting AI/ML Clinical Trials")
ax.set_xlabel("Number of trials (site-location records)")
ax.set_xlim(0, max(counts) * 1.14)
ax.grid(axis="y", visible=False)
# parity callout
gap = china - usa
ax.annotate(f"China–US parity: {china:,} vs {usa:,}\n(gap of {gap} trials, 3%)",
            xy=(china * 0.5, len(names) - 0.5), xytext=(china * 0.52, len(names) - 3.6),
            fontsize=9.5, color="#333333",
            bbox=dict(boxstyle="round,pad=0.45", fc="#FFF3E0", ec=ORANGE, lw=1.1),
            arrowprops=dict(arrowstyle="-", color=ORANGE, lw=1.0))
from matplotlib.patches import Patch
ax.legend(handles=[Patch(fc=RED, label="China"), Patch(fc=BLUE, label="United States")],
          loc="lower right", frameon=False, fontsize=9)
fig.text(0.99, 0.01, ATTR, ha="right", va="bottom", fontsize=7.5, color="#666666", style="italic")
finish(fig, ax, "fig3_top12_countries",
       f"top-12 countries horizontal bars, China {china} vs US {usa} highlighted")

# --------------------------- Fig 4: top-10 conditions excl. AI/ML-as-condition
EXCLUDE = {"Artificial Intelligence", "Artificial Intelligence (Ai)", "Machine Learning"}
all_cond = sorted(S["top15_conditions"].items(), key=lambda kv: -kv[1])
excluded = [(k, v) for k, v in all_cond if k in EXCLUDE]
kept = [(k, v) for k, v in all_cond if k not in EXCLUDE][:10]
labels = [k for k, _ in kept][::-1]
counts = [v for _, v in kept][::-1]

fig, ax = plt.subplots(figsize=(7.5, 4.8))
bars = ax.barh(labels, counts, color=TEAL, edgecolor="white", linewidth=0.6)
for b, c in zip(bars, counts):
    ax.text(c + 1, b.get_y() + b.get_height()/2, f"{c}",
            va="center", fontsize=8.8, fontweight="bold", color="#333333")
ax.set_title("Top 10 Clinical Conditions in AI/ML Trials\n(therapeutic/disease areas; AI/ML-as-condition entries excluded)")
ax.set_xlabel("Number of trials (condition-tagged records)")
ax.set_xlim(0, max(counts) * 1.14)
ax.grid(axis="y", visible=False)
excl_txt = "Excluded as AI/ML-as-condition (method, not disease): " + \
    " · ".join(f"{k} — {v} trials" for k, v in excluded)
fig.text(0.99, 0.052, excl_txt, ha="right", va="bottom",
         fontsize=8.0, color="#555555", style="italic")
fig.text(0.99, 0.01, ATTR, ha="right", va="bottom", fontsize=7.5, color="#666666", style="italic")
finish(fig, ax, "fig4_top10_conditions",
       "top-10 conditions excluding " + ", ".join(f"{k} ({v})" for k, v in excluded))

print("ALL FIGURES DONE")
