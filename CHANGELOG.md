# Changelog

All notable changes to this repository are documented here.

The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and
this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

Dataset versions refer to the `version` field in
[`harpd-ai-datasets`](https://github.com/harpd-dev/harpd-ai-datasets)
`data/manifest.json`.

## [Unreleased]

### Added

- `scripts/validate_reports.py` — standalone report validator used by CI and the
  validate workflow. Checks required sections, sample size, data timestamps, the
  placement caveat, and rejects quality-ranking or fabricated-endorsement phrasing.

### Changed

- CI no longer requires committed reports to byte-match a fresh generation.
  Upstream datasets update on their own schedule, so that check failed for reasons
  unrelated to this repository. CI now validates that reports *can* be generated
  and that the committed ones are structurally valid; keeping them current is
  `sync-and-report.yml`'s job.

## [1.0.0] — 2026-09-16

Initial release, built against dataset version `2026.9`.

### Added

- **Seven notebooks**, each with Question / Dataset / Method / Analysis /
  Visualization / Findings / Limitations / Reproducibility / Sources sections,
  committed with executed outputs:
  - `01-ai-market-overview.ipynb`
  - `02-ai-product-ranking-trends.ipynb`
  - `03-ai-agent-market.ipynb`
  - `04-ai-developer-tools.ipynb`
  - `05-ai-tools-landscape.ipynb`
  - `06-model-replacement-analysis.ipynb`
  - `07-cost-per-successful-task.ipynb`
- **`harpd_research/`** — shared package so logic is not duplicated between the
  notebooks and the report generator:
  - `loader.py` — fetch, parse and cache datasets; `HARPD_DATA_BASE` offline override
  - `analysis.py` — the pandas computations
  - `report.py` — deterministic markdown rendering with fail-closed guards
  - `citation.py` — BibTeX, APA and CITATION.cff formatting
- **Three generated reports** in `reports/`, each with a data timestamp, sample
  size, methodology, limitations, dataset link, source, reproduction instructions
  and a BibTeX + APA citation block:
  - `2026-09-ai-market-report.md` (sample size 1,122)
  - `2026-09-ai-ranking-report.md` (sample size 1,122)
  - `2026-09-ai-agent-report.md` (sample size 334)
- **`scripts/generate_reports.py`** — idempotent, fail-closed report generator.
  Refuses to write when a dataset is missing or empty, and exits non-zero.
- **`tests/`** — hermetic pytest suite covering dataset shapes, analysis output
  columns, report sections, citation formatting, and the fail-closed guarantees.
- **Workflows**: `ci.yml` (lint, test, execute notebooks), `sync-and-report.yml`
  (scheduled sync, rollback on failure, commit only if changed, monthly release),
  `validate.yml` (required sections and citation block).
- Repository hygiene: `README.md`, `LICENSE` (CC BY 4.0), `CITATION.cff`,
  `CONTRIBUTING.md`, `SECURITY.md`, `Makefile`, `pyproject.toml`, `.gitignore`.

### Findings recorded in this release

These are results, not features. They are listed because they shape what the
repository can and cannot claim.

- **Placement coverage is effectively zero.** 1 of 1,122 products carries any
  Rank Points (233 points, in the AI Media board). 1,121 carry zero. No placement
  distribution, concentration curve or top-N share is computed, because one data
  point is not a distribution.
- **No trend is measurable from the published boards.** `overall`, `monthly` and
  `weekly` are three views of the same period window, not three points in time.
- **`ai-tools-index` is narrower than its name.** Its declared slice is
  `['agents', 'ai-media']`; it is not a general AI tools census.
- **No discovery-index record reaches the rank board.** All three slices report
  `on_rank_board` false for every record.
- **The model-replacement dataset does not exist.** Notebook 06 documents this and
  stops rather than computing an answer. `model-replacement-benchmark` ships
  `compare.mjs`, whose provider calls are an explicit stub with a hard-coded
  fallback success rate of 0.9.
- **The cost benchmark is a MODELED estimate.** `llm-cost-benchmark` sets
  `"isModeled": true`. Notebook 07 recomputes and labels it accordingly, and
  reports that only 5 of its 8 models appear in the companion price snapshot.

### Notes

- Rank Points are promotional placement bought with Credits. Nothing in this
  repository presents them as a measure of product quality, and the test suite
  enforces that.
