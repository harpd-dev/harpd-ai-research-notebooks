# Harpd AI Market Report — 2026-09

**Question.** How is the Harpd product catalog composed across categories, and how much paid placement does it actually carry?

> **Domain caveat.** Rank Points are promotional placement bought with Credits — NOT an editorial quality score. Any ordering below is a promotional placement ordering, not a ranking of product quality.

## Data timestamp

- Dataset `generatedAt`: `2026-11-04T17:20:26.880Z`
- Dataset `lastUpdated`: `2026-11-04T17:20:31.158Z`
- Snapshot date used for this report: `2026-11-04`

The snapshot date is taken from the dataset itself, not from the clock at
render time. Re-running the generator against an unchanged snapshot
reproduces this file byte for byte.

## Sample size

- Records analysed: **941**

## Methodology

- Load `data/products/products.json` and `data/rankings/categories.json` from the public raw dataset URL (or `HARPD_DATA_BASE` when set).
- `analysis.market_composition` groups products by category and computes each category's share of total listings.
- `analysis.placement_concentration` counts products with `rankPoints > 0` and sums total points across the catalog.
- `analysis.category_boards` reports each board's listing count and publisher-declared state.
- All arithmetic is integer counting and share division over the loaded records. No value is imputed, smoothed or modelled.
- The published `manifest.json` recordCount is cross-checked against the number of rows actually parsed.

## Analysis

### Catalog composition by category (count ordering, not quality)

| category     | categoryName   |   productCount |   sharePct |
|:-------------|:---------------|---------------:|-----------:|
| other        | Other          |            245 |      26.04 |
| developer    | Developer      |            106 |      11.26 |
| ai-media     | AI Media       |            100 |      10.63 |
| agents       | Agents         |             65 |       6.91 |
| marketing    | Marketing      |             47 |       4.99 |
| seo          | SEO            |             45 |       4.78 |
| productivity | Productivity   |             44 |       4.68 |
| audio        | Audio          |             39 |       4.14 |
| business     | Business       |             29 |       3.08 |
| design       | Design         |             27 |       2.87 |
| hiring       | Hiring         |             23 |       2.44 |
| education    | Education      |             21 |       2.23 |
| health       | Health         |             19 |       2.02 |
| writing      | Writing        |             18 |       1.91 |
| directories  | Directories    |             17 |       1.81 |

### Category board state

| state        |   categories |   products |
|:-------------|-------------:|-----------:|
| LISTED_NO_RP |           27 |        841 |
| ACTIVE       |            1 |        100 |

### Largest category boards

| slug         | name         |   productCount |   rankedProductCount |   totalRankPoints | state        | topRankOpen   |
|:-------------|:-------------|---------------:|---------------------:|------------------:|:-------------|:--------------|
| other        | Other        |            245 |                    0 |                 0 | LISTED_NO_RP | True          |
| developer    | Developer    |            106 |                    0 |                 0 | LISTED_NO_RP | True          |
| ai-media     | AI Media     |            100 |                    1 |               268 | ACTIVE       | False         |
| agents       | Agents       |             65 |                    0 |                 0 | LISTED_NO_RP | True          |
| marketing    | Marketing    |             47 |                    0 |                 0 | LISTED_NO_RP | True          |
| seo          | SEO          |             45 |                    0 |                 0 | LISTED_NO_RP | True          |
| productivity | Productivity |             44 |                    0 |                 0 | LISTED_NO_RP | True          |
| audio        | Audio        |             39 |                    0 |                 0 | LISTED_NO_RP | True          |
| business     | Business     |             29 |                    0 |                 0 | LISTED_NO_RP | True          |
| design       | Design       |             27 |                    0 |                 0 | LISTED_NO_RP | True          |
| hiring       | Hiring       |             23 |                    0 |                 0 | LISTED_NO_RP | True          |
| education    | Education    |             21 |                    0 |                 0 | LISTED_NO_RP | True          |

## Findings

- The catalog contains 941 products across 28 categories.
- The largest category by listing count is 'Other' with 245 products (26.04% of the catalog).
- Only 1 of 941 products (0.1063%) carry any Rank Points at all; 940 carry zero.
- Total Rank Points across the whole catalog is 268, and 2 distinct point values exist.
- Category board states: LISTED_NO_RP = 27 categories / 841 products; ACTIVE = 1 categories / 100 products.
- Because placement coverage is near zero, this report deliberately does not compute a placement distribution, a placement leaderboard, or any concentration statistic beyond the raw counts shown above — the data cannot support them.

## Notes

- Manifest declares version `2026.11` with `updatedAt` 2026-11-04T17:20:31.158Z.
- Manifest lists 11 published datasets.
- The market index file independently reports 941 products across 28 categories, consistent with the catalog count.

## Limitations

- Rank Points are promotional placement bought with Credits. Nothing in this report measures product quality, and no ordering here is a quality ranking.
- Harpd holds no first-party measurement of third-party traffic, revenue or user reviews; such figures are not present in this dataset and are not estimated here.
- 24 product records have no description; category composition counts listings, not active or maintained products.
- A category with a large listing count is not a large market — it is a large number of discovered listings.
- This snapshot is a single point in time. No trend, growth rate or period-over-period change is computed, because one snapshot cannot support one.

## Dataset link

- `data/products/products.json, data/rankings/categories.json`
- <https://harpd.com/data/>
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
@misc{harpd-ai-datasets-products,
  author       = {Harpd},
  title        = {Harpd AI Datasets — Products & Category Boards},
  year         = {2026},
  howpublished = {\url{https://harpd.com/data/}},
  note         = {Open data, licensed CC BY 4.0}
  url          = {https://harpd.com/data/}
}
```

### APA

Harpd. (2026). *Harpd AI Datasets — Products & Category Boards*. https://harpd.com/data/ (Accessed: 2026-11-04)

### Licence

Dataset content is published under CC BY 4.0. Attribution: Harpd (https://harpd.com).

Canonical data home: <https://harpd.com/data/>
