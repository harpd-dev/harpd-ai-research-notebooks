# Contributing

Thanks for considering a contribution. This repository makes specific promises to
its readers, and contributions are held to those promises.

## The three hard rules

Every contribution must respect these. A pull request that breaks one will be
declined regardless of how interesting the result is.

### 1. Never invent data

Every number must come from a `pandas` operation over a published dataset. No
estimates, no interpolation, no back-filling, no "reasonable" placeholder values,
and no figures produced by a language model.

If a computation yields zero rows, the finding is "zero rows". Write it down.

### 2. Never present placement as quality

Rank Points are **promotional placement bought with Credits**, not an editorial
quality score. Any ordering by `rankPoints` must be labelled a *promotional
placement ordering*. The constant to reuse is
`harpd_research.analysis.PLACEMENT_CAVEAT`.

Do not write "best", "top-quality", "leading" or similar about a `rankPoints`
ordering.

### 3. Fail closed

If a dataset is missing, unreachable or empty, the code must stop — not degrade
into an empty-but-plausible output. `scripts/generate_reports.py` must exit
non-zero and must not overwrite the last valid report.

## Adding a notebook

1. Name it `NN-short-title.ipynb`, continuing the existing numbering.
2. Include these markdown sections, in this order:

   `Question` · `Dataset` · `Method` · `Analysis` · `Visualization` ·
   `Findings` · `Limitations` · `Reproducibility` · `Sources`

3. Import the shared package rather than duplicating logic:

   ```python
   from harpd_research import analysis, loader
   ```

   If you need a new computation, add it to `harpd_research/analysis.py` so the
   report generator can use it too.

4. Put the dataset-loading boilerplate in the first code cell, and print the
   resolved data base so a reader can see where the numbers came from.
5. Compute findings from variables rather than typing numbers into markdown:

   ```python
   findings = [
       f"The catalog contains {placement['totalProducts']:,} products.",
   ]
   for i, line in enumerate(findings, 1):
       print(f"{i}. {line}")
   ```

6. Execute the notebook and commit the outputs, so GitHub renders real numbers:

   ```bash
   make notebooks
   ```

7. State the limitations honestly. Every dataset here has real gaps; name them.

## Adding a report

Reports are generated, not hand-written. Add a builder to
`scripts/generate_reports.py` and register it in `BUILDERS`. It must supply a
non-zero `sample_size`, a real dataset timestamp, and a `accessed` snapshot date
derived from the data (not `datetime.now()` — that would break idempotency).

## Development setup

```bash
python -m venv .venv && . .venv/bin/activate
pip install -r requirements.txt

make lint      # ruff check + format check
make test      # pytest
make check     # what CI runs
```

Run the suite before opening a pull request. `make check` should be clean.

## Tests

The suite is hermetic — it never touches the network. Fixtures under
`tests/fixtures/` are real *subsets* of the published datasets, so the loader is
exercised against the real schema. Regenerate them only if the upstream schema
changes, and keep them schema-faithful.

If you add an analysis function, add a test that pins its output columns and its
behaviour on empty input.

## Domain vocabulary

Use these terms consistently:

| Term | Meaning |
|---|---|
| **Rank Points** | Promotional placement bought with Credits. Not quality. |
| **Placement coverage** | Share of products carrying `rankPoints > 0`. |
| **Discovery index** | A coverage view of observed products. Not a ranking. |
| **Catalog** | The product records Harpd publishes. |
| **MODELED** | An estimate, per the evidence register's claim types. Must be labelled wherever it appears. |

## Reporting a problem with a number

If a figure here looks wrong, please open an issue naming the notebook or report,
the cell or section, and the dataset version. Being able to check a number is the
entire point of this repository, so corrections are welcome.

## Licence

By contributing, you agree that your contribution is licensed under CC BY 4.0.
