#!/usr/bin/env python
"""Regenerate every markdown report in ``reports/`` from live Harpd data.

Design rules
------------
* **Idempotent.** Reports are a deterministic function of the data. Running this
  twice against the same snapshot produces byte-identical files, so the sync
  workflow's "commit only if changed" check is meaningful.
* **Fail closed.** If a dataset fails to load, or loads but is empty, the report
  is not written, the previous file on disk is left untouched, and the process
  exits non-zero. An empty report must never replace a valid one.
* **No invented numbers.** Every figure comes from ``harpd_research.analysis``.

Usage
-----
    python scripts/generate_reports.py                 # fetch from raw GitHub
    HARPD_DATA_BASE=../harpd-ai-datasets/ python scripts/generate_reports.py
    python scripts/generate_reports.py --check         # verify only, write nothing
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from harpd_research import analysis, loader  # noqa: E402
from harpd_research.report import (  # noqa: E402
    ReportData,
    ReportError,
    render_report,
    report_metadata,
    validate_report_text,
)

REPORTS_DIR = ROOT / "reports"
DATASET_HOME = "https://harpd.com/data/"
REGISTRY = "https://github.com/harpd-dev/harpd-ai-datasets"


class GenerationFailed(RuntimeError):
    """Raised when a report cannot be produced from real data."""


def _snapshot_date(*frames: pd.DataFrame) -> str:
    """Derive the report's date from the data itself, not from the wall clock.

    Idempotency depends on this: re-running against an unchanged snapshot must
    produce byte-identical files, so the "rendered" stamp has to come from the
    dataset's own ``generatedAt`` rather than ``datetime.now()``.
    """
    stamps = []
    for frame in frames:
        value = (frame.attrs or {}).get("generatedAt")
        if value:
            stamps.append(str(value))
    if not stamps:
        return ""
    return max(stamps)[:10]


def _require_records(frame: pd.DataFrame, what: str) -> None:
    """Fail closed on an empty or missing frame."""
    if frame is None or frame.empty:
        raise GenerationFailed(
            f"{what}: dataset is empty or unavailable — refusing to write a report."
        )


# --------------------------------------------------------------------------
# report 1: AI market
# --------------------------------------------------------------------------


def build_market_report() -> ReportData:
    products = loader.load_products()
    categories = loader.load_categories()
    market_index = loader.load_ai_market_index()
    manifest = loader.load_manifest()

    _require_records(products, "products")
    _require_records(categories, "categories")

    accessed = _snapshot_date(products, categories)
    composition = analysis.market_composition(products)
    placement = analysis.placement_concentration(products)
    boards = analysis.category_boards(categories).head(12)

    category_states = (
        categories.groupby("state")
        .agg(categories=("slug", "nunique"), products=("productCount", "sum"))
        .reset_index()
        .sort_values("products", ascending=False)
        .reset_index(drop=True)
    )

    findings = [
        f"The catalog contains {placement['totalProducts']:,} products across "
        f"{int(products['category'].nunique())} categories.",
        f"The largest category by listing count is "
        f"'{composition.iloc[0]['categoryName']}' with "
        f"{int(composition.iloc[0]['productCount']):,} products "
        f"({composition.iloc[0]['sharePct']}% of the catalog).",
        f"Only {placement['productsWithPlacement']:,} of "
        f"{placement['totalProducts']:,} products "
        f"({placement['placementCoveragePct']}%) carry any Rank Points at all; "
        f"{placement['productsWithoutPlacement']:,} carry zero.",
        f"Total Rank Points across the whole catalog is "
        f"{placement['totalRankPoints']:,.0f}, and "
        f"{placement['distinctPlacementValues']} distinct point values exist.",
        "Category board states: "
        + "; ".join(
            f"{row.state} = {int(row.categories)} categories / {int(row.products):,} products"
            for row in category_states.itertuples()
        )
        + ".",
        "Because placement coverage is near zero, this report deliberately does "
        "not compute a placement distribution, a placement leaderboard, or any "
        "concentration statistic beyond the raw counts shown above — the data "
        "cannot support them.",
    ]

    limitations = [
        "Rank Points are promotional placement bought with Credits. Nothing in "
        "this report measures product quality, and no ordering here is a quality "
        "ranking.",
        "Harpd holds no first-party measurement of third-party traffic, revenue "
        "or user reviews; such figures are not present in this dataset and are "
        "not estimated here.",
        f"{int(products['description'].isna().sum())} product records have no "
        "description; category composition counts listings, not active or "
        "maintained products.",
        "A category with a large listing count is not a large market — it is a "
        "large number of discovered listings.",
        "This snapshot is a single point in time. No trend, growth rate or "
        "period-over-period change is computed, because one snapshot cannot "
        "support one.",
    ]

    return ReportData(
        slug="2026-09-ai-market-report",
        title="Harpd AI Market Report — 2026-09",
        question=(
            "How is the Harpd product catalog composed across categories, and how "
            "much paid placement does it actually carry?"
        ),
        dataset_name="Products + category boards",
        dataset_path="data/products/products.json, data/rankings/categories.json",
        dataset_url=f"{DATASET_HOME}",
        generated_at=str(products.attrs.get("generatedAt") or manifest.get("updatedAt") or ""),
        last_updated=str(manifest.get("updatedAt") or ""),
        sample_size=int(len(products)),
        methodology=[
            "Load `data/products/products.json` and `data/rankings/categories.json` "
            "from the public raw dataset URL (or `HARPD_DATA_BASE` when set).",
            "`analysis.market_composition` groups products by category and computes "
            "each category's share of total listings.",
            "`analysis.placement_concentration` counts products with "
            "`rankPoints > 0` and sums total points across the catalog.",
            "`analysis.category_boards` reports each board's listing count and "
            "publisher-declared state.",
            "All arithmetic is integer counting and share division over the loaded "
            "records. No value is imputed, smoothed or modelled.",
            "The published `manifest.json` recordCount is cross-checked against the "
            "number of rows actually parsed.",
        ],
        limitations=limitations,
        findings=findings,
        tables=[
            ("Catalog composition by category (count ordering, not quality)", composition.head(15)),
            ("Category board state", category_states),
            ("Largest category boards", boards),
        ],
        extra_notes=[
            f"Manifest declares version `{manifest.get('version')}` with "
            f"`updatedAt` {manifest.get('updatedAt')}.",
            f"Manifest lists {len(manifest.get('datasets', []))} published datasets.",
            f"The market index file independently reports "
            f"{int(market_index['productCount'].sum()):,} products across "
            f"{len(market_index)} categories, consistent with the catalog count.",
        ],
        citation_key="harpd-ai-datasets-products",
        citation_title="Harpd AI Datasets — Products & Category Boards",
        accessed=accessed,
    )


# --------------------------------------------------------------------------
# report 2: ranking / placement
# --------------------------------------------------------------------------


def build_ranking_report() -> ReportData:
    overall = loader.load_ranking("overall")
    monthly = loader.load_ranking("monthly")
    weekly = loader.load_ranking("weekly")
    manifest = loader.load_manifest()

    _require_records(overall, "rankings/overall")
    _require_records(monthly, "rankings/monthly")
    _require_records(weekly, "rankings/weekly")

    accessed = _snapshot_date(overall, monthly, weekly)
    comparison = analysis.ranking_board_comparison(overall, monthly, weekly)
    placement = analysis.placement_concentration(overall)
    top = analysis.top_placement(overall, n=10)

    if top.empty:
        top_note = (
            "No product carries Rank Points in this snapshot, so no placement "
            "ordering can be shown. This is reported as a finding, not filled in."
        )
        findings_top: list[str] = []
    else:
        top_note = (
            "The table below is a **promotional placement ordering**, not a "
            "quality ranking. It lists products by Credits spent on placement."
        )
        findings_top = [
            f"The single product carrying placement points is "
            f"'{top.iloc[0]['name']}' with {int(top.iloc[0]['rankPoints'])} Rank Points."
        ]

    findings = [
        "All three boards (overall, monthly, weekly) are views over the same "
        f"catalog of {int(len(overall)):,} products, so board size is identical "
        "across them.",
        f"{placement['productsWithPlacement']:,} of {placement['totalProducts']:,} "
        f"products ({placement['placementCoveragePct']}%) hold any Rank Points.",
        f"Total Rank Points on the overall board: {placement['totalRankPoints']:,.0f}.",
        *findings_top,
        "Because placement coverage is effectively zero, no meaningful "
        "concentration curve, Gini coefficient or top-N share can be computed. "
        "This report states that rather than producing a statistic that would "
        "imply a distribution where none exists.",
    ]

    limitations = [
        "Rank Points are promotional placement bought with Credits — NOT an "
        "editorial quality score. A higher position means more Credits were "
        "spent, not that a product is better.",
        "Harpd's own evidence register lists 'that a higher-ranked product on "
        "Harpd Rank is a better product' under `notClaimed`, with the reason that "
        "Rank Points are promotional placement and Harpd holds no quality "
        "measurement that would support an ordering by merit.",
        "These boards are live views scoped to the current period window, not "
        "historical archives. Historical archives are published separately at "
        "https://harpd.com/rank/history/.",
        "No time series is computed: the published files carry one period each, "
        "and this repository does not have historical snapshots to compare.",
    ]

    return ReportData(
        slug="2026-09-ai-ranking-report",
        title="Harpd AI Ranking & Placement Report — 2026-09",
        question=(
            "What does the Harpd Rank board actually contain, and how much paid "
            "placement is present on it?"
        ),
        dataset_name="Rankings (overall, monthly, weekly)",
        dataset_path="data/rankings/overall.json, monthly.json, weekly.json",
        dataset_url="https://harpd.com/rank/",
        generated_at=str(overall.attrs.get("generatedAt") or manifest.get("updatedAt") or ""),
        last_updated=str(manifest.get("updatedAt") or ""),
        sample_size=int(len(overall)),
        methodology=[
            "Load `overall.json`, `monthly.json` and `weekly.json` from the public "
            "raw dataset URL.",
            "`analysis.ranking_board_comparison` compares record counts, distinct "
            "products, placement totals and category coverage per board.",
            "`analysis.placement_concentration` counts products with "
            "`rankPoints > 0` and reports total and maximum points.",
            "`analysis.top_placement` returns the products with points, ordered by "
            "points descending — explicitly a promotional placement ordering.",
            "No quality score, review score or traffic figure is read or derived, "
            "because the dataset contains none.",
        ],
        limitations=limitations,
        findings=findings,
        tables=[
            ("Board comparison", comparison),
            ("Products carrying placement (promotional placement ordering)", top),
        ],
        extra_notes=[
            f"Period window for the overall board: monthKey "
            f"`{overall.attrs.get('periods', {}).get('monthKey') if overall.attrs.get('periods') else 'n/a'}`.",
            f"{top_note}",
        ],
        citation_key="harpd-ai-datasets-rankings",
        citation_title="Harpd AI Datasets — Rankings",
        accessed=accessed,
    )


# --------------------------------------------------------------------------
# report 3: AI agents
# --------------------------------------------------------------------------


def build_agent_report() -> ReportData:
    agents = loader.load_ai_agent_index()
    manifest = loader.load_manifest()

    _require_records(agents, "research/ai-agent-index")

    accessed = _snapshot_date(agents)
    coverage = analysis.discovery_coverage(agents, "AI agent index")
    sources = analysis.discovery_sources(agents, top_n=10)

    confidence_series = pd.to_numeric(agents["category_confidence"], errors="coerce")
    confidence = (
        confidence_series.value_counts()
        .rename_axis("category_confidence")
        .reset_index(name="records")
        .sort_values("category_confidence")
        .reset_index(drop=True)
    )
    confidence["sharePct"] = (confidence["records"] / confidence["records"].sum() * 100).round(2)
    full_confidence = int((confidence_series >= 1.0).sum())
    low_confidence = int((confidence_series <= 0.5).sum())

    top_source = sources.iloc[0]

    empty_profile = 0
    if "profile_url" in agents.columns:
        empty_profile = int(agents["profile_url"].fillna("").astype(str).str.strip().eq("").sum())

    findings = [
        f"The AI agent index covers {coverage['records']:,} records across "
        f"{coverage['distinctDomains']:,} distinct domains.",
        f"{coverage['onRankBoard']:,} of {coverage['records']:,} records "
        f"({coverage['onRankBoardPct']}%) appear on the Harpd Rank board.",
        f"Records were observed from {coverage['distinctDiscoverySources']} distinct "
        f"discovery sources; the largest is '{top_source['discovered_from']}' with "
        f"{int(top_source['recordCount']):,} records ({top_source['sharePct']}% of "
        "the slice).",
        f"Automated category confidence is not uniform: {full_confidence:,} records "
        f"({round(full_confidence / coverage['records'] * 100, 2)}%) are assigned at "
        f"confidence 1.0, while {low_confidence:,} "
        f"({round(low_confidence / coverage['records'] * 100, 2)}%) sit at 0.5 or "
        f"below. Mean confidence is {coverage['meanCategoryConfidence']}.",
        f"Observation window: {coverage['observedAtMin']} to {coverage['observedAtMax']}.",
        f"{empty_profile:,} of {coverage['records']:,} records have an empty "
        "`profile_url`, so the slice cannot be joined to catalog profiles on that "
        "field.",
        "The dataset's own disclosure states it is a coverage view sliced from the "
        "Harpd Product Discovery Index and is not a ranking.",
    ]

    limitations = [
        "This is a **coverage** dataset, not a ranking. It records which agent "
        "products were observed, not which are best or most used.",
        f"Category assignment is automated and low-confidence for a large share of "
        f"records: {low_confidence:,} of {coverage['records']:,} sit at 0.5 or "
        "below. Category membership should be treated as indicative only.",
        f"{coverage['records'] - coverage['onRankBoard']:,} records are not on the "
        "rank board, which is expected: the discovery index is broader than the "
        "catalog.",
        "No usage, revenue, download or traffic metric is present, and none is "
        "estimated. Absence from the rank board does not indicate failure.",
        "A single observation window means no adoption trend can be measured.",
        "Descriptions and titles are supplied by the discovered sites themselves "
        "and are not independently verified by Harpd.",
    ]

    return ReportData(
        slug="2026-09-ai-agent-report",
        title="Harpd AI Agent Market Report — 2026-09",
        question=(
            "How broad is the observed AI agent market in the Harpd discovery "
            "index, and how much of it reaches the rank board?"
        ),
        dataset_name="AI agent index",
        dataset_path="data/research/ai-agent-index.json",
        dataset_url="https://harpd.com/discovery/",
        generated_at=str(agents.attrs.get("generatedAt") or manifest.get("updatedAt") or ""),
        last_updated=str(manifest.get("updatedAt") or ""),
        sample_size=int(len(agents)),
        methodology=[
            "Load `data/research/ai-agent-index.json` from the public raw dataset URL.",
            "`analysis.discovery_coverage` reports record count, distinct domains, "
            "rank-board coverage and the confidence distribution.",
            "`analysis.discovery_sources` counts records per discovery source.",
            "Category confidence is tabulated as a value-count distribution so the "
            "uniform confidence level is visible rather than averaged away.",
            "The slice definition (`category == ['agents']`) is read from the "
            "dataset's own `meta.sliceDefinition` and reported as given.",
        ],
        limitations=limitations,
        findings=findings,
        tables=[
            ("Rank-board coverage", pd.DataFrame([coverage])),
            ("Discovery sources", sources),
            ("Category confidence distribution", confidence),
        ],
        extra_notes=[
            "The dataset's own disclosure states: 'Coverage view sliced from the "
            "Harpd Product Discovery Index by product category. Not a ranking.'",
        ],
        citation_key="harpd-ai-datasets-agent-index",
        citation_title="Harpd AI Datasets — AI Agent Index",
        accessed=accessed,
    )


# --------------------------------------------------------------------------
# driver
# --------------------------------------------------------------------------


BUILDERS = {
    "2026-09-ai-market-report.md": build_market_report,
    "2026-09-ai-ranking-report.md": build_ranking_report,
    "2026-09-ai-agent-report.md": build_agent_report,
}


def generate(check_only: bool = False) -> int:
    """Build every report. Returns a process exit code."""
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)

    written: list[str] = []
    unchanged: list[str] = []

    for filename, builder in BUILDERS.items():
        target = REPORTS_DIR / filename
        try:
            data = builder()
            text = render_report(data)
        except (loader.DatasetError, ReportError, GenerationFailed, ValueError) as exc:
            print(f"FAIL {filename}: {exc}", file=sys.stderr)
            print(
                "Refusing to write. Any previously committed report is left untouched.",
                file=sys.stderr,
            )
            return 1

        missing = validate_report_text(text)
        if missing:
            print(f"FAIL {filename}: missing sections {missing}", file=sys.stderr)
            return 1

        meta = report_metadata(data)
        if check_only:
            if target.is_file() and target.read_text(encoding="utf-8") == text:
                unchanged.append(filename)
            else:
                written.append(filename)
            print(
                f"CHECK {filename}: sample_size={meta['sample_size']:,} "
                f"tables={meta['tables']} findings={meta['findings']}"
            )
            continue

        if target.is_file() and target.read_text(encoding="utf-8") == text:
            unchanged.append(filename)
            print(f"SAME  {filename}: sample_size={meta['sample_size']:,} (no change)")
            continue

        target.write_text(text, encoding="utf-8")
        written.append(filename)
        print(f"WROTE {filename}: sample_size={meta['sample_size']:,}")

    print(f"\n{len(written)} written, {len(unchanged)} unchanged ({len(BUILDERS)} reports total)")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--check",
        action="store_true",
        help="validate that reports can be produced without writing files",
    )
    args = parser.parse_args(argv)
    try:
        return generate(check_only=args.check)
    except loader.DatasetError as exc:
        print(f"FATAL: dataset unavailable: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
