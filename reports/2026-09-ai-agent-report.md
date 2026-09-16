# Harpd AI Agent Market Report — 2026-09

**Question.** How broad is the observed AI agent market in the Harpd discovery index, and how much of it reaches the rank board?

> **Domain caveat.** Rank Points are promotional placement bought with Credits — NOT an editorial quality score. Any ordering below is a promotional placement ordering, not a ranking of product quality.

## Data timestamp

- Dataset `generatedAt`: `2026-09-09T06:33:49.935Z`
- Dataset `lastUpdated`: `2026-09-16T10:37:21.880Z`
- Snapshot date used for this report: `2026-09-09`

The snapshot date is taken from the dataset itself, not from the clock at
render time. Re-running the generator against an unchanged snapshot
reproduces this file byte for byte.

## Sample size

- Records analysed: **334**

## Methodology

- Load `data/research/ai-agent-index.json` from the public raw dataset URL.
- `analysis.discovery_coverage` reports record count, distinct domains, rank-board coverage and the confidence distribution.
- `analysis.discovery_sources` counts records per discovery source.
- Category confidence is tabulated as a value-count distribution so the uniform confidence level is visible rather than averaged away.
- The slice definition (`category == ['agents']`) is read from the dataset's own `meta.sliceDefinition` and reported as given.

## Analysis

### Rank-board coverage

| label          |   records |   distinctDomains |   onRankBoard |   onRankBoardPct |   meanCategoryConfidence |   distinctDiscoverySources | observedAtMin                    | observedAtMax                    | hasData   |
|:---------------|----------:|------------------:|--------------:|-----------------:|-------------------------:|---------------------------:|:---------------------------------|:---------------------------------|:----------|
| AI agent index |       334 |               334 |             0 |                0 |                   0.8154 |                         11 | 2026-09-09T05:32:39.445000+00:00 | 2026-09-09T05:58:27.151000+00:00 | True      |

### Discovery sources

| discovered_from    |   recordCount |   sharePct |
|:-------------------|--------------:|-----------:|
| uneed.best         |           267 |      79.94 |
| outbid.lol         |            25 |       7.49 |
| appsumo.com        |            14 |       4.19 |
| whatlaunched.today |            11 |       3.29 |
| biddirectory.lol   |             4 |       1.2  |
| vibewar.lol        |             4 |       1.2  |
| toolify.ai         |             4 |       1.2  |
| claimrank.lol      |             2 |       0.6  |
| dontbid.lol        |             1 |       0.3  |
| growu.lol          |             1 |       0.3  |

### Category confidence distribution

|   category_confidence |   records |   sharePct |
|----------------------:|----------:|-----------:|
|                  0.17 |         4 |       1.2  |
|                  0.5  |       116 |      34.73 |
|                  0.67 |         1 |       0.3  |
|                  1    |       213 |      63.77 |

## Findings

- The AI agent index covers 334 records across 334 distinct domains.
- 0 of 334 records (0.0%) appear on the Harpd Rank board.
- Records were observed from 11 distinct discovery sources; the largest is 'uneed.best' with 267 records (79.94% of the slice).
- Automated category confidence is not uniform: 213 records (63.77%) are assigned at confidence 1.0, while 120 (35.93%) sit at 0.5 or below. Mean confidence is 0.8154.
- Observation window: 2026-09-09T05:32:39.445000+00:00 to 2026-09-09T05:58:27.151000+00:00.
- 334 of 334 records have an empty `profile_url`, so the slice cannot be joined to catalog profiles on that field.
- The dataset's own disclosure states it is a coverage view sliced from the Harpd Product Discovery Index and is not a ranking.

## Notes

- The dataset's own disclosure states: 'Coverage view sliced from the Harpd Product Discovery Index by product category. Not a ranking.'

## Limitations

- This is a **coverage** dataset, not a ranking. It records which agent products were observed, not which are best or most used.
- Category assignment is automated and low-confidence for a large share of records: 120 of 334 sit at 0.5 or below. Category membership should be treated as indicative only.
- 334 records are not on the rank board, which is expected: the discovery index is broader than the catalog.
- No usage, revenue, download or traffic metric is present, and none is estimated. Absence from the rank board does not indicate failure.
- A single observation window means no adoption trend can be measured.
- Descriptions and titles are supplied by the discovered sites themselves and are not independently verified by Harpd.

## Dataset link

- `data/research/ai-agent-index.json`
- <https://harpd.com/discovery/>
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
@misc{harpd-ai-datasets-agent-index,
  author       = {Harpd},
  title        = {Harpd AI Datasets — AI Agent Index},
  year         = {2026},
  howpublished = {\url{https://harpd.com/discovery/}},
  note         = {Open data, licensed CC BY 4.0}
  url          = {https://harpd.com/discovery/}
}
```

### APA

Harpd. (2026). *Harpd AI Datasets — AI Agent Index*. https://harpd.com/discovery/ (Accessed: 2026-09-09)

### Licence

Dataset content is published under CC BY 4.0. Attribution: Harpd (https://harpd.com).

Canonical data home: <https://harpd.com/data/>
