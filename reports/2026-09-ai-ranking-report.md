# Harpd AI Ranking & Placement Report — 2026-09

**Question.** What does the Harpd Rank board actually contain, and how much paid placement is present on it?

> **Domain caveat.** Rank Points are promotional placement bought with Credits — NOT an editorial quality score. Any ordering below is a promotional placement ordering, not a ranking of product quality.

## Data timestamp

- Dataset `generatedAt`: `2026-09-16T10:37:21.290Z`
- Dataset `lastUpdated`: `2026-09-16T10:37:21.880Z`
- Snapshot date used for this report: `2026-09-16`

The snapshot date is taken from the dataset itself, not from the clock at
render time. Re-running the generator against an unchanged snapshot
reproduces this file byte for byte.

## Sample size

- Records analysed: **1,122**

## Methodology

- Load `overall.json`, `monthly.json` and `weekly.json` from the public raw dataset URL.
- `analysis.ranking_board_comparison` compares record counts, distinct products, placement totals and category coverage per board.
- `analysis.placement_concentration` counts products with `rankPoints > 0` and reports total and maximum points.
- `analysis.top_placement` returns the products with points, ordered by points descending — explicitly a promotional placement ordering.
- No quality score, review score or traffic figure is read or derived, because the dataset contains none.

## Analysis

### Board comparison

| board   |   records |   distinctProducts |   productsWithPlacement |   totalRankPoints |   categoriesRepresented |
|:--------|----------:|-------------------:|------------------------:|------------------:|------------------------:|
| overall |      1122 |               1122 |                       1 |               233 |                      27 |
| monthly |      1122 |               1122 |                       1 |               233 |                      27 |
| weekly  |      1122 |               1122 |                       1 |               233 |                      27 |

### Products carrying placement (promotional placement ordering)

|   rank | name   | categoryName   |   rankPoints | verified   |
|-------:|:-------|:---------------|-------------:|:-----------|
|      1 | imgkit | AI Media       |          233 | True       |

## Findings

- All three boards (overall, monthly, weekly) are views over the same catalog of 1,122 products, so board size is identical across them.
- 1 of 1,122 products (0.0891%) hold any Rank Points.
- Total Rank Points on the overall board: 233.
- The single product carrying placement points is 'imgkit' with 233 Rank Points.
- Because placement coverage is effectively zero, no meaningful concentration curve, Gini coefficient or top-N share can be computed. This report states that rather than producing a statistic that would imply a distribution where none exists.

## Notes

- Period window for the overall board: monthKey `2026-09`.
- The table below is a **promotional placement ordering**, not a quality ranking. It lists products by Credits spent on placement.

## Limitations

- Rank Points are promotional placement bought with Credits — NOT an editorial quality score. A higher position means more Credits were spent, not that a product is better.
- Harpd's own evidence register lists 'that a higher-ranked product on Harpd Rank is a better product' under `notClaimed`, with the reason that Rank Points are promotional placement and Harpd holds no quality measurement that would support an ordering by merit.
- These boards are live views scoped to the current period window, not historical archives. Historical archives are published separately at https://harpd.com/rank/history/.
- No time series is computed: the published files carry one period each, and this repository does not have historical snapshots to compare.

## Dataset link

- `data/rankings/overall.json, monthly.json, weekly.json`
- <https://harpd.com/rank/>
- Registry: <https://github.com/harpd-dev/harpd-ai-datasets>

## Source

- Publisher: https://harpd.com
- Data home: <https://harpd.com/data/>
- Raw base: `https://github.com/harpd-dev/harpd-ai-datasets` (branch `main`)
- Licence: CC BY 4.0

## Reproduction instructions

```bash
git clone https://github.com/harpd-dev/harpd-ai-research-notebooks
cd harpd-ai-research-notebooks
python -m venv .venv && . .venv/bin/activate
pip install -r requirements.txt
python scripts/generate_reports.py
```

To reproduce offline against a local clone of the datasets:

```bash
HARPD_DATA_BASE=/path/to/harpd-ai-datasets/ python scripts/generate_reports.py
```

## Citation

If you use this report, cite the underlying datasets:

### BibTeX

```bibtex
@misc{harpd-ai-datasets-rankings,
  author       = {Harpd},
  title        = {Harpd AI Datasets — Rankings},
  year         = {2026},
  howpublished = {\url{https://harpd.com/rank/}},
  note         = {Open data, licensed CC BY 4.0}
  url          = {https://harpd.com/rank/}
}
```

### APA

Harpd. (2026). *Harpd AI Datasets — Rankings*. https://harpd.com/rank/ (Accessed: 2026-09-16)

### Licence

Dataset content is published under CC BY 4.0. Attribution: Harpd (https://harpd.com).

Canonical data home: <https://harpd.com/data/>
