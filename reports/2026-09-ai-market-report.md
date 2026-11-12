# Harpd AI Market Report — 2026-09

**Question.** How is the Harpd product catalog composed across categories, and how much paid placement does it actually carry?

> **Domain caveat.** Rank Points are promotional placement bought with Credits — NOT an editorial quality score. Any ordering below is a promotional placement ordering, not a ranking of product quality.

## Data timestamp

- Dataset `generatedAt`: `2026-11-11T17:14:47.274Z`
- Dataset `lastUpdated`: `2026-11-11T17:14:52.533Z`
- Snapshot date used for this report: `2026-11-11`

The snapshot date is taken from the dataset itself, not from the clock at
render time. Re-running the generator against an unchanged snapshot
reproduces this file byte for byte.

## Sample size

- Records analysed: **972**

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
| other        | Other          |            246 |      25.31 |
| developer    | Developer      |            112 |      11.52 |
| ai-media     | AI Media       |            109 |      11.21 |
| agents       | Agents         |             66 |       6.79 |
| marketing    | Marketing      |             49 |       5.04 |
| seo          | SEO            |             45 |       4.63 |
| productivity | Productivity   |             44 |       4.53 |
| audio        | Audio          |             40 |       4.12 |
| business     | Business       |             32 |       3.29 |
| design       | Design         |             27 |       2.78 |
| hiring       | Hiring         |             23 |       2.37 |
| education    | Education      |             22 |       2.26 |
| health       | Health         |             22 |       2.26 |
| writing      | Writing        |             18 |       1.85 |
| directories  | Directories    |             17 |       1.75 |

### Category board state

| state        |   categories |   products |
|:-------------|-------------:|-----------:|
| LISTED_NO_RP |           27 |        863 |
| ACTIVE       |            1 |        109 |

### Largest category boards

| slug         | name         |   productCount |   rankedProductCount |   totalRankPoints | state        | topRankOpen   |
|:-------------|:-------------|---------------:|---------------------:|------------------:|:-------------|:--------------|
| other        | Other        |            246 |                    0 |                 0 | LISTED_NO_RP | True          |
| developer    | Developer    |            112 |                    0 |                 0 | LISTED_NO_RP | True          |
| ai-media     | AI Media     |            109 |                    1 |               368 | ACTIVE       | False         |
| agents       | Agents       |             66 |                    0 |                 0 | LISTED_NO_RP | True          |
| marketing    | Marketing    |             49 |                    0 |                 0 | LISTED_NO_RP | True          |
| seo          | SEO          |             45 |                    0 |                 0 | LISTED_NO_RP | True          |
| productivity | Productivity |             44 |                    0 |                 0 | LISTED_NO_RP | True          |
| audio        | Audio        |             40 |                    0 |                 0 | LISTED_NO_RP | True          |
| business     | Business     |             32 |                    0 |                 0 | LISTED_NO_RP | True          |
| design       | Design       |             27 |                    0 |                 0 | LISTED_NO_RP | True          |
| hiring       | Hiring       |             23 |                    0 |                 0 | LISTED_NO_RP | True          |
| education    | Education    |             22 |                    0 |                 0 | LISTED_NO_RP | True          |

## Findings

- The catalog contains 972 products across 28 categories.
- The largest category by listing count is 'Other' with 246 products (25.31% of the catalog).
- Only 1 of 972 products (0.1029%) carry any Rank Points at all; 971 carry zero.
- Total Rank Points across the whole catalog is 368, and 2 distinct point values exist.
- Category board states: LISTED_NO_RP = 27 categories / 863 products; ACTIVE = 1 categories / 109 products.
- Because placement coverage is near zero, this report deliberately does not compute a placement distribution, a placement leaderboard, or any concentration statistic beyond the raw counts shown above — the data cannot support them.

## Notes

- Manifest declares version `2026.11` with `updatedAt` 2026-11-11T17:14:52.533Z.
- Manifest lists 11 published datasets.
- The market index file independently reports 972 products across 28 categories, consistent with the catalog count.

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

Harpd. (2026). *Harpd AI Datasets — Products & Category Boards*. https://harpd.com/data/ (Accessed: 2026-11-11)

### Licence

Dataset content is published under CC BY 4.0. Attribution: Harpd (https://harpd.com).

Canonical data home: <https://harpd.com/data/>
