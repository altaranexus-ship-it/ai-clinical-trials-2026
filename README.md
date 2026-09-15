# The State of AI in Clinical Trials — 2026

[![License: MIT](https://img.shields.io/badge/Code-MIT-yellow.svg)](LICENSE)
[![Data: CC0](https://img.shields.io/badge/Data-CC0--1.0-blue.svg)](DATA_LICENSE)
[![DOI](https://img.shields.io/badge/DOI-pending-lightgrey.svg)](CITATION.cff)
[![Python 3.9+](https://img.shields.io/badge/python-3.9%2B-blue.svg)](https://www.python.org/)
[![Registry](https://img.shields.io/badge/Source-ClinicalTrials.gov%20API%20v2-00695c.svg)](https://clinicaltrials.gov/)

**K-Dense Science Lab — Market Analysis Division**
*Data snapshot: 2026-09-15T17:56:58Z · Registry: ClinicalTrials.gov API v2 · Studies analyzed: 4,250*

A reproducible market analysis of every ClinicalTrials.gov study whose intervention
description references "artificial intelligence" or "machine learning" — 4,250 studies,
~0.7% of the 602,897-study registry. Ships with the raw registry extract, a flattened
CSV, computed statistics, a zero-dependency Python pipeline, and four
publication-grade figures.

## Headline findings

1. **The curve is still steepening.** Annual AI/ML postings grew 137 (2019) → 712 (2024); 2026 logged 933 by Sep 15 — already 15% above all of 2025.
2. **AI is validated like an instrument, not developed like a drug.** 55.6% observational; only **80** of 1,886 interventional studies carry any formal phase designation (1.9%).
3. **Academic medicine runs the field.** 85% non-industry sponsors; industry leads just 10.6%.
4. **China ≈ US parity.** Sites in China: 807 studies · US: 783 · next tier (Italy 240) not close.
5. **Oncology + cardiology are the beachheads.** Breast cancer (87), heart failure (77), CAD (51) top the conditions list.

Full narrative, methodology, caveats, and market implications: [`report/README.md`](report/README.md).

## Quickstart

```bash
git clone https://github.com/<owner>/ai-clinical-trials-2026.git
cd ai-clinical-trials-2026

# Refresh everything from the live registry (~30 s, stdlib only, no API keys):
python3 code/fetch_build.py      # → data/ai_trials_raw.jsonl + ai_trials_flat.csv + stats.json

# Rebuild the four figures (needs matplotlib):
pip install matplotlib
python3 code/make_figures.py     # → figures/fig1..fig4 (.png 300dpi + .pdf)
```

Or skip the pipeline and work with the shipped snapshot directly:

```python
import pandas as pd
df = pd.read_csv("data/ai_trials_flat.csv")
df.shape  # (4250, 14)
```

## Repository layout

| Path | Contents |
|---|---|
| `code/fetch_build.py` | Fetch AI/ML-flagged studies from ClinicalTrials.gov API v2, flatten to CSV, compute all statistics to `stats.json` (stdlib only) |
| `code/make_figures.py` | Four publication-grade figures from `stats.json` (Okabe-Ito palette, PNG 300 dpi + vector PDF) |
| `data/ai_trials_raw.jsonl` | 4,250 raw field-pruned registry records (5.2 MB) |
| `data/ai_trials_flat.csv` | Flattened table: 4,250 rows × 14 fields |
| `data/stats.json` | All computed statistics, machine-readable |
| `figures/` | fig1 postings by year · fig2 status distribution · fig3 top 12 countries · fig4 top 10 conditions (PNG + PDF) |
| `report/README.md` | Full market report: methodology, findings, caveats, market implications |

## Dataset dictionary — `data/ai_trials_flat.csv`

One row per study. 4,250 unique `nctId`s, no duplicates.

| # | Column | Type | Description | Example / values |
|---|---|---|---|---|
| 1 | `nctId` | string | ClinicalTrials.gov registry identifier (primary key) | `NCT07420790` |
| 2 | `briefTitle` | string | Official brief title of the study | `Design and Validation of a Generative AI…` |
| 3 | `overallStatus` | enum | Registry study status, verbatim (not imputed) | `RECRUITING`, `COMPLETED`, `UNKNOWN` (legacy artifact; 793 studies = 18.7%) |
| 4 | `startDate` | ISO date | Study start date; empty if not reported | `2026-02-20` |
| 5 | `firstPosted` | ISO date | First posting date on the registry (basis for yearly trend) | `2026-02-19` |
| 6 | `completionDate` | ISO date (month or day precision) | Primary completion date; empty if ongoing/not reported | `2021-09-10`, `2026-12` |
| 7 | `studyType` | enum | Registry design class | `OBSERVATIONAL` (2,363) · `INTERVENTIONAL` (1,886) · `EXPANDED_ACCESS` (1) |
| 8 | `phases` | enum | Formal phase designation; blank for observational, `NA` for unphased interventional | `PHASE2`, `PHASE3`, `EARLY_PHASE1`; only 80 interventional studies phased |
| 9 | `enrollment` | integer | Target/actual enrollment; blank if not reported (2 studies) | `1941` |
| 10 | `leadSponsor` | string | Lead sponsor organization name | `Mayo Clinic` |
| 11 | `sponsorClass` | enum | Registry sponsor class | `OTHER` (academic/non-profit) · `INDUSTRY` · `NIH` · `FED` · `OTHER_GOV` · `NETWORK` |
| 12 | `conditions` | string | Studied conditions, `\|`-separated when multiple | `Acute Myeloid Leukemia` · `COVID-19 \| Cardiovascular Risk Factor` |
| 13 | `nLocations` | integer | Number of registered study sites | `1` |
| 14 | `countries` | string | Site countries, `\|`-separated (study-level: multi-site studies count per country in country aggregates) | `Italy` · `United States \| China` |

**`data/stats.json` keys:** `meta` (source, query, snapshot timestamp, counts) · `posting_by_year` · `status_distribution` · `study_type_distribution` · `phase_distribution` · `sponsor_class_distribution` · `top15_sponsors` · `top15_conditions` · `top12_countries` · `enrollment` (median 250 / mean 30,274 / p90 4,882) · `interventional_share_pct` · `ai_as_intervention` (443 studies / 10.4% naming AI/ML as the intervention, with derivation).

## Methodology (short form)

- **Source.** ClinicalTrials.gov API v2, the authoritative U.S. NLM/NIH registry.
- **Query.** `query.intr = "artificial intelligence" OR "machine learning"` (full-text on intervention descriptions) — a *lower bound*: trials using AI without naming it are not captured.
- **Collection.** Paginated field-pruned requests (500/page), 2026-09-15T17:56:58Z snapshot.
- **Verification.** Every headline statistic recomputed from the flattened CSV through an independent code path; 9/9 cross-checks passed; 4,250 unique NCT IDs.
- **Caveats.** Partial-year 2026 (Jan 1–Sep 15); `UNKNOWN` statuses reported verbatim (legacy registry artifact); country counts are study-level. Full caveat list in [`report/README.md`](report/README.md) §2.

## License & citation

- **Code** (`code/`): [MIT](LICENSE) — © 2026 K-Dense Science Lab.
- **Data** (`data/`): [CC0 1.0](DATA_LICENSE) — derived from public-domain ClinicalTrials.gov records; registry attribution requested: *"Source: ClinicalTrials.gov, U.S. National Library of Medicine."*
- **Figures / report text**: CC0 with attribution appreciated.

Cite via [`CITATION.cff`](CITATION.cff):

> K-Dense Science Lab, *The State of AI in Clinical Trials — 2026*, dataset + report, version 1.0.0, 2026-09-15.

## Suggested GitHub topics

`clinical-trials` · `health-ai` · `market-research` · `clinicaltrials-gov` · `data-analysis` · `reproducible-research`

---

*Owner publish runbook (do not execute from the lab — owner-gated per channel plan KDE-5):*

```bash
cd repo
gh repo create ai-clinical-trials-2026 --public --source=. --push \
  --description "Reproducible market analysis of 4,250 AI/ML-flagged ClinicalTrials.gov studies (2026)" \
  --homepage https://kdense.science
# Then: Settings → About → Topics: add the six topics above. Optional: enable CITATION.cff in "Cite this repository".
```
