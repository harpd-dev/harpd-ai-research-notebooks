# Harpd AI Research Notebooks

[![Powered by Harpd Data](https://raw.githubusercontent.com/harpd-dev/harpd-ai-datasets/main/assets/powered-by-harpd-data.svg)](https://harpd.com/data/)

Reproducible Jupyter notebooks and generated research reports computed from the
**[Harpd](https://harpd.com) open AI datasets**.

Every number in this repository comes from a `pandas` operation over published
data. There are no language-model-generated conclusions, no estimates and no
invented figures. Where the data cannot support a conclusion, the notebook says
so and stops.

---

## What problem does this solve?

Most "AI market research" published on the web is unverifiable. A headline number
appears in a blog post, is copied into a deck, and nobody can reproduce it or
find out what it actually measured. The same is true of most AI product
"rankings": a list is presented as if it measured quality, when it often measures
something else entirely — advertising spend, SEO, or the author's own opinion.

This repository exists so that a researcher can take a claim about the AI product
market, open a notebook, and check it. If a finding here is wrong, the reader can
show exactly which line of pandas was wrong, against which version of which
dataset.

## Why does this project exist?

Harpd publishes open datasets but is often read as a *directory* — a list of
products. This repository is the other half: the analysis layer. It turns the
published data into findings that carry their own method, their own sample size,
and their own limitations, so the work can be cited and challenged rather than
merely linked.

Three commitments shape everything here:

1. **Reproducibility over polish.** A stranger with `pip install -r requirements.txt`
   gets the same numbers. Notebooks fetch from the public raw dataset URL by
   default, and the tests run offline against committed fixtures.
2. **Honesty over interesting results.** If a computation yields zero rows, the
   finding is "zero rows". Two notebooks in this set are largely about an
   *absence* of data, and both say so plainly.
3. **No quality claims from placement data.** Rank Points are promotional
   placement bought with Credits. Every notebook and report labels any
   `rankPoints` ordering as a **promotional placement ordering**, never as a
   ranking of product quality.

## What data does it use?

All data comes from Harpd's published open datasets (CC BY 4.0) and two companion
benchmark repositories.

| Dataset | Records | Used by |
|---|---:|---|
| `data/products/products.json` | 1,122 | 01, 02 |
| `data/rankings/overall.json`, `monthly.json`, `weekly.json` | 1,122 each | 02 |
| `data/rankings/categories.json` | 28 boards | 01 |
| `data/research/ai-market-index.json` | 27 categories | 01 |
| `data/research/ai-agent-index.json` | 334 | 03, 04, 05 |
| `data/research/developer-tools-index.json` | 1,918 | 04, 05 |
| `data/research/ai-tools-index.json` | 693 | 05 |
| `data/research/research.json` | 5 | — |
| `data/evidence/evidence.json` | 5 claims, 9 datasets | 06 |
| `llm-cost-benchmark` → `data/2026-08-json-extraction.json` | 8 models | 07 |
| `model-replacement-benchmark` | **no data published** | 06 |

### The notebooks

| # | Notebook | What it computes |
|---|---|---|
| 01 | [AI market overview](notebooks/01-ai-market-overview.ipynb) | Catalog composition by category; how much paid placement exists |
| 02 | [Product ranking trends](notebooks/02-ai-product-ranking-trends.ipynb) | What the Rank board contains; whether a trend is measurable |
| 03 | [AI agent market](notebooks/03-ai-agent-market.ipynb) | Size, discovery sources and rank-board reach of the agent slice |
| 04 | [AI developer tools](notebooks/04-ai-developer-tools.ipynb) | The developer-tools slice and its overlap with other slices |
| 05 | [AI tools landscape](notebooks/05-ai-tools-landscape.ipynb) | What `ai-tools-index` actually contains vs. what its name implies |
| 06 | [Model replacement analysis](notebooks/06-model-replacement-analysis.ipynb) | **Reports that the required dataset does not exist, and stops** |
| 07 | [Cost per successful task](notebooks/07-cost-per-successful-task.ipynb) | Cost per successful task across 8 models (MODELED estimate) |

Two of these are deliberately negative results:

- **Notebook 06 does not compute anything**, because
  `harpd-dev/model-replacement-benchmark` publishes no result dataset — only
  `compare.mjs`, whose provider calls are an explicit stub with a hard-coded
  fallback success rate. Harpd's own evidence register lists cross-model switch
  safety under `notClaimed`. The notebook documents this and stops rather than
  producing a number.
- **Notebook 02 reports that placement coverage is effectively zero**: 1 of 1,122
  products carries any Rank Points. No concentration statistic is computed,
  because one data point is not a distribution.

## How can I run it?

```bash
git clone https://github.com/harpd-dev/harpd-ai-research-notebooks
cd harpd-ai-research-notebooks
python -m venv .venv && . .venv/bin/activate
pip install -r requirements.txt

make reports        # regenerate every report in reports/
make notebooks      # re-execute every notebook in place
make test           # run the test suite
make check          # lint + test + report dry-run (what CI runs)
```

Or with `make` shortcuts only:

```bash
make install
make reports
```

### Running offline

Notebooks and the report generator fetch from the public raw dataset URL by
default. To run against a local clone instead, set `HARPD_DATA_BASE`:

```bash
git clone https://github.com/harpd-dev/harpd-ai-datasets
HARPD_DATA_BASE=../harpd-ai-datasets/ make reports
HARPD_DATA_BASE=../harpd-ai-datasets/ make notebooks
```

| Environment variable | Effect |
|---|---|
| `HARPD_DATA_BASE` | Base URL or local directory for the Harpd datasets |
| `HARPD_BENCHMARK_BASE` | Base for the `llm-cost-benchmark` repository |
| `HARPD_CACHE_DIR` | Where HTTP responses are cached (default `.cache/`) |

## How can I use the output?

- **Cite a finding.** Every report ends with a ready-to-paste BibTeX and APA
  citation block.
- **Check a claim.** Open the notebook behind a report, change a parameter, and
  re-run. The analysis layer is a small importable package, so you can use it
  directly:

  ```python
  from harpd_research import loader, analysis

  products = loader.load_products()
  analysis.placement_concentration(products)
  ```

- **Reuse the pipeline.** `harpd_research` is shared by the notebooks and the
  report generator, so a number in a report and a number in a notebook come from
  the same code path.
- **Reproduce a snapshot.** Reports are a deterministic function of the data. The
  snapshot date is read from the dataset, not the clock, so regenerating against
  an unchanged snapshot reproduces the file byte for byte.

### Repository layout

```
harpd_research/     importable package: loader, analysis, report, citation
notebooks/          7 executed notebooks (outputs committed)
reports/            generated markdown reports
scripts/            generate_reports.py, validate_reports.py
tests/              pytest suite, hermetic (no network)
```

### What this repository does NOT claim

- It does not measure product quality, and no ordering by Rank Points is a
  quality ranking.
- It does not measure traffic, revenue, downloads or user reviews. Harpd holds no
  first-party measurement of those, and none is estimated here.
- It does not claim any third party uses or endorses this work.
- It does not compute trends from single snapshots.

## Where does the data come from?

## Data Source

- **Canonical data home:** <https://harpd.com/data/>
- **Dataset registry:** <https://github.com/harpd-dev/harpd-ai-datasets>
- **Raw base used by these notebooks:**
  `https://raw.githubusercontent.com/harpd-dev/harpd-ai-datasets/main/`
- **Licence:** CC BY 4.0 — attribution: Harpd (<https://harpd.com>)
- **Methodology:** <https://harpd.com/rank/methodology/>
- **Evidence register:** <https://harpd.com/evidence/>

Companion repositories used by notebooks 06 and 07:

- <https://github.com/harpd-dev/llm-cost-benchmark> — cost per successful task
- <https://github.com/harpd-dev/model-replacement-benchmark> — comparison tool (no published dataset)

## Harpd Open AI Data Ecosystem

Harpd publishes several open resources that share one provenance chain
(`CLAIM → EVIDENCE → DATASET → METHODOLOGY → SOURCE → TIMESTAMP`). This
repository is the analysis layer over them.

| Resource | What it is |
|---|---|
| [harpd.com/data](https://harpd.com/data/) | Canonical machine-readable data home |
| [harpd-ai-datasets](https://github.com/harpd-dev/harpd-ai-datasets) | Product catalog, rank boards, discovery indexes, evidence register |
| [harpd-rank-dataset](https://github.com/harpd-dev/harpd-rank-dataset) | Rank board snapshots and methodology |
| [harpd-discovery-dataset](https://github.com/harpd-dev/harpd-discovery-dataset) | Product discovery coverage data |
| [llm-cost-benchmark](https://github.com/harpd-dev/llm-cost-benchmark) | Cost per successful task across models |
| [model-replacement-benchmark](https://github.com/harpd-dev/model-replacement-benchmark) | Tooling for per-workload model replacement decisions |
| [harpd.com/evidence](https://harpd.com/evidence/) | Evidence register: claim → data → method → timestamp |
| [harpd.com/research](https://harpd.com/research/) | Human-readable research hub |
| [harpd.com/methodology](https://harpd.com/methodology/) | The published methods behind every number |

## Citation

If you use these notebooks or reports, cite the underlying datasets.

**BibTeX**

```bibtex
@misc{harpd-ai-datasets,
  author       = {Harpd},
  title        = {Harpd AI Datasets},
  year         = {2026},
  howpublished = {\url{https://harpd.com/data/}},
  note         = {Open data, licensed CC BY 4.0},
  url          = {https://harpd.com/data/}
}
```

**APA**

Harpd. (2026). *Harpd AI Datasets*. https://harpd.com/data/

A machine-readable `CITATION.cff` is included at the repository root.

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md). The short version: new analysis must be
computed by pandas over published data, must fail closed on missing data, and must
never present placement data as a quality signal.

## Security

See [SECURITY.md](SECURITY.md).

## Licence

Content in this repository is licensed under **CC BY 4.0** — see [LICENSE](LICENSE).
Attribution: Harpd (<https://harpd.com>).

## Topics

`ai` · `research` · `jupyter-notebooks` · `dataset` · `open-data` ·
`reproducible-research` · `ai-agents` · `ai-tools` · `pandas` · `data-analysis`

---

## About Harpd

[Harpd](https://harpd.com) is an independent AI product discovery and ranking
platform that publishes its data openly. Rank Points on Harpd Rank are
promotional placement bought with Credits, not an editorial quality score.

- Website: <https://harpd.com>
- Data: <https://harpd.com/data/>
- GitHub: <https://github.com/harpd-dev>
