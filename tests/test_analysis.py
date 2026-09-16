"""Analysis tests: functions return the expected columns and honest edge cases."""

from __future__ import annotations

import pandas as pd
import pytest

from harpd_research import analysis, loader


@pytest.fixture
def products(offline: str) -> pd.DataFrame:
    return loader.load_products()


@pytest.fixture
def categories(offline: str) -> pd.DataFrame:
    return loader.load_categories()


@pytest.fixture
def agents(offline: str) -> pd.DataFrame:
    return loader.load_ai_agent_index()


# --------------------------------------------------------------------------
# market_composition
# --------------------------------------------------------------------------


def test_market_composition_columns(products: pd.DataFrame) -> None:
    frame = analysis.market_composition(products)
    assert list(frame.columns) == ["category", "categoryName", "productCount", "sharePct"]
    assert not frame.empty


def test_market_composition_counts_sum_to_catalog(products: pd.DataFrame) -> None:
    frame = analysis.market_composition(products)
    assert int(frame["productCount"].sum()) == len(products)


def test_market_composition_shares_sum_to_100(products: pd.DataFrame) -> None:
    frame = analysis.market_composition(products)
    assert frame["sharePct"].sum() == pytest.approx(100.0, abs=0.05)


def test_market_composition_sorted_descending(products: pd.DataFrame) -> None:
    frame = analysis.market_composition(products)
    counts = frame["productCount"].tolist()
    assert counts == sorted(counts, reverse=True)


def test_market_composition_top_n(products: pd.DataFrame) -> None:
    frame = analysis.market_composition(products, top_n=3)
    assert len(frame) == 3


def test_market_composition_empty_input_returns_empty_frame() -> None:
    frame = analysis.market_composition(
        pd.DataFrame(columns=["category", "categoryName"])
    )
    assert frame.empty
    assert "productCount" in frame.columns


def test_market_composition_missing_columns_raises() -> None:
    with pytest.raises(ValueError, match="missing columns"):
        analysis.market_composition(pd.DataFrame({"category": ["x"]}))


# --------------------------------------------------------------------------
# placement_concentration -- the load-bearing honesty check
# --------------------------------------------------------------------------


def test_placement_concentration_keys(products: pd.DataFrame) -> None:
    result = analysis.placement_concentration(products)
    expected = {
        "totalProducts", "productsWithPlacement", "productsWithoutPlacement",
        "placementCoveragePct", "totalRankPoints", "maxRankPoints",
        "largestPlacementSharePct", "distinctPlacementValues",
        "has_meaningful_placement", "caveat",
    }
    assert expected == set(result)


def test_placement_counts_are_consistent(products: pd.DataFrame) -> None:
    result = analysis.placement_concentration(products)
    assert (
        result["productsWithPlacement"] + result["productsWithoutPlacement"]
        == result["totalProducts"]
    )
    assert result["totalProducts"] == len(products)


def test_placement_caveat_is_present_and_correct(products: pd.DataFrame) -> None:
    """The promotional-placement caveat must always accompany these numbers."""
    result = analysis.placement_concentration(products)
    assert "promotional placement" in result["caveat"]
    assert "NOT an editorial quality score" in result["caveat"]


def test_placement_concentration_all_zero_is_not_meaningful() -> None:
    frame = pd.DataFrame({"rankPoints": [0, 0, 0]})
    result = analysis.placement_concentration(frame)
    assert result["productsWithPlacement"] == 0
    assert result["has_meaningful_placement"] is False
    assert result["largestPlacementSharePct"] is None


def test_placement_concentration_flags_single_funded_product() -> None:
    """One funded product is not a distribution; the flag must say so."""
    frame = pd.DataFrame({"rankPoints": [0, 233, 0]})
    result = analysis.placement_concentration(frame)
    assert result["productsWithPlacement"] == 1
    assert result["has_meaningful_placement"] is False
    assert result["largestPlacementSharePct"] == 100.0


def test_placement_concentration_meaningful_when_two_funded() -> None:
    frame = pd.DataFrame({"rankPoints": [10, 20, 0]})
    result = analysis.placement_concentration(frame)
    assert result["has_meaningful_placement"] is True


def test_placement_concentration_missing_column_raises() -> None:
    with pytest.raises(ValueError, match="rankPoints"):
        analysis.placement_concentration(pd.DataFrame({"rank": [1]}))


# --------------------------------------------------------------------------
# top_placement
# --------------------------------------------------------------------------


def test_top_placement_columns_and_order(products: pd.DataFrame) -> None:
    frame = analysis.top_placement(products, n=5)
    assert {"rank", "name", "categoryName", "rankPoints", "verified"}.issubset(
        frame.columns
    )
    assert frame["rankPoints"].tolist() == sorted(
        frame["rankPoints"].tolist(), reverse=True
    )


def test_top_placement_excludes_unfunded(products: pd.DataFrame) -> None:
    frame = analysis.top_placement(products, n=100)
    assert (frame["rankPoints"] > 0).all()


def test_top_placement_empty_when_no_placement() -> None:
    frame = analysis.top_placement(pd.DataFrame({"rankPoints": [0, 0], "name": ["a", "b"]}))
    assert frame.empty


# --------------------------------------------------------------------------
# category_boards / ranking_board_comparison
# --------------------------------------------------------------------------


def test_category_boards_columns(categories: pd.DataFrame) -> None:
    frame = analysis.category_boards(categories)
    assert {"slug", "name", "productCount", "rankedProductCount", "state"}.issubset(
        frame.columns
    )
    assert frame["productCount"].tolist() == sorted(
        frame["productCount"].tolist(), reverse=True
    )


def test_category_boards_missing_columns_raises() -> None:
    with pytest.raises(ValueError, match="missing columns"):
        analysis.category_boards(pd.DataFrame({"slug": ["a"]}))


def test_ranking_board_comparison_columns(offline: str) -> None:
    frame = analysis.ranking_board_comparison(
        loader.load_ranking("overall"),
        loader.load_ranking("monthly"),
        loader.load_ranking("weekly"),
    )
    assert list(frame["board"]) == ["overall", "monthly", "weekly"]
    assert {
        "records", "distinctProducts", "productsWithPlacement",
        "totalRankPoints", "categoriesRepresented",
    }.issubset(frame.columns)


# --------------------------------------------------------------------------
# discovery_coverage / sources / overlap
# --------------------------------------------------------------------------


def test_discovery_coverage_keys(agents: pd.DataFrame) -> None:
    result = analysis.discovery_coverage(agents, "agents")
    expected = {
        "label", "records", "distinctDomains", "onRankBoard", "onRankBoardPct",
        "meanCategoryConfidence", "distinctDiscoverySources",
        "observedAtMin", "observedAtMax", "hasData",
    }
    assert expected == set(result)
    assert result["hasData"] is True
    assert result["records"] == len(agents)


def test_discovery_coverage_empty_input() -> None:
    result = analysis.discovery_coverage(pd.DataFrame(), "empty")
    assert result["hasData"] is False
    assert result["records"] == 0
    assert result["meanCategoryConfidence"] is None


def test_discovery_coverage_handles_string_booleans() -> None:
    """on_rank_board arrives as a real bool in JSON and as a string in CSV."""
    frame = pd.DataFrame(
        {"domain": ["a.com", "b.com"], "on_rank_board": ["true", "false"]}
    )
    result = analysis.discovery_coverage(frame, "strings")
    assert result["onRankBoard"] == 1


def test_discovery_sources_columns(agents: pd.DataFrame) -> None:
    frame = analysis.discovery_sources(agents)
    assert list(frame.columns) == ["discovered_from", "recordCount", "sharePct"]
    assert frame["recordCount"].tolist() == sorted(
        frame["recordCount"].tolist(), reverse=True
    )


def test_discovery_sources_empty_input() -> None:
    frame = analysis.discovery_sources(pd.DataFrame())
    assert frame.empty
    assert "recordCount" in frame.columns


def test_cross_index_overlap_detects_shared_domains() -> None:
    left = pd.DataFrame({"domain": ["a.com", "b.com"]})
    right = pd.DataFrame({"domain": ["b.com", "c.com"]})
    frame = analysis.cross_index_overlap({"left": left, "right": right})
    assert list(frame["domain"]) == ["b.com"]
    assert frame.iloc[0]["indexCount"] == 2


def test_cross_index_overlap_empty_when_disjoint() -> None:
    left = pd.DataFrame({"domain": ["a.com"]})
    right = pd.DataFrame({"domain": ["b.com"]})
    frame = analysis.cross_index_overlap({"left": left, "right": right})
    assert frame.empty


def test_cross_index_overlap_empty_input() -> None:
    frame = analysis.cross_index_overlap({})
    assert frame.empty
    assert "domain" in frame.columns


# --------------------------------------------------------------------------
# benchmark analysis
# --------------------------------------------------------------------------


@pytest.fixture
def benchmark(benchmark_base: str) -> tuple[pd.DataFrame, dict]:
    return loader.load_benchmark_results(base=benchmark_base)


def test_cost_per_successful_task_columns(benchmark) -> None:
    results, meta = benchmark
    frame = analysis.cost_per_successful_task(results, meta)
    assert {
        "efficiencyOrder", "model", "successRate", "costPerTask",
        "costPerSuccessfulTask", "publishedCostPerSuccessfulTask",
        "recomputedDeltaPct", "isModeled",
    }.issubset(frame.columns)


def test_cost_per_successful_task_is_the_quotient(benchmark) -> None:
    results, meta = benchmark
    frame = analysis.cost_per_successful_task(results, meta)
    for _, row in frame.iterrows():
        assert row["costPerSuccessfulTask"] == pytest.approx(
            row["costPerTask"] / row["successRate"], rel=1e-3
        )


def test_cost_per_successful_task_propagates_modeled_flag(benchmark) -> None:
    """The MODELED disclosure must ride along with every row."""
    results, meta = benchmark
    frame = analysis.cost_per_successful_task(results, meta)
    assert frame["isModeled"].all()


def test_cost_per_successful_task_sorted_ascending(benchmark) -> None:
    results, meta = benchmark
    frame = analysis.cost_per_successful_task(results, meta)
    costs = frame["costPerSuccessfulTask"].tolist()
    assert costs == sorted(costs)
    assert frame["efficiencyOrder"].tolist() == list(range(1, len(frame) + 1))


def test_cost_per_successful_task_empty_input() -> None:
    frame = analysis.cost_per_successful_task(
        pd.DataFrame(columns=["model", "successRate", "costPerTask"])
    )
    assert frame.empty
    assert "costPerSuccessfulTask" in frame.columns


def test_cost_per_successful_task_missing_columns_raises() -> None:
    with pytest.raises(ValueError, match="missing columns"):
        analysis.cost_per_successful_task(pd.DataFrame({"model": ["m"]}))


def test_benchmark_efficiency_keys(benchmark) -> None:
    results, meta = benchmark
    table = analysis.cost_per_successful_task(results, meta)
    summary = analysis.benchmark_efficiency(table)
    assert summary["hasData"] is True
    assert summary["models"] == len(results)
    assert summary["costSpreadRatio"] is not None
    assert summary["cheapestCostPerSuccessfulTask"] <= summary["mostExpensiveCostPerSuccessfulTask"]


def test_benchmark_efficiency_empty_input() -> None:
    summary = analysis.benchmark_efficiency(pd.DataFrame())
    assert summary["hasData"] is False
    assert summary["costSpreadRatio"] is None


# --------------------------------------------------------------------------
# evidence_audit
# --------------------------------------------------------------------------


def test_evidence_audit_columns(offline: str) -> None:
    frame = analysis.evidence_audit(loader.load_evidence())
    assert list(frame.columns) == ["claimType", "claims", "supported", "withSource"]
    assert not frame.empty
    assert frame["claims"].sum() > 0


def test_evidence_audit_empty_input() -> None:
    frame = analysis.evidence_audit({"claims": []})
    assert frame.empty


# --------------------------------------------------------------------------
# domain-rule guard
# --------------------------------------------------------------------------


def test_placement_caveat_forbids_quality_framing() -> None:
    caveat = analysis.PLACEMENT_CAVEAT.lower()
    assert "promotional placement" in caveat
    assert "not an editorial quality score" in caveat
    assert analysis.PLACEMENT_LABEL == "promotional placement ordering"
