"""Loader tests: every published dataset shape parses into the expected frame."""

from __future__ import annotations

import pandas as pd
import pytest

from harpd_research import loader

# --------------------------------------------------------------------------
# shape tests, one per published dataset
# --------------------------------------------------------------------------


def test_load_products_shape(offline: str) -> None:
    frame = loader.load_products()
    assert isinstance(frame, pd.DataFrame)
    assert not frame.empty
    expected = {
        "id", "name", "slug", "url", "category", "categoryName",
        "rank", "rankPoints", "verified", "updatedAt", "website",
        "description", "productType",
    }
    assert expected.issubset(set(frame.columns))
    assert pd.api.types.is_numeric_dtype(frame["rank"])
    assert pd.api.types.is_numeric_dtype(frame["rankPoints"])


def test_load_products_carries_data_timestamp(offline: str) -> None:
    frame = loader.load_products()
    assert frame.attrs.get("generatedAt"), "generatedAt must come from the data"
    assert frame.attrs.get("lastUpdated")


@pytest.mark.parametrize("period", ["overall", "monthly", "weekly"])
def test_load_ranking_shape(offline: str, period: str) -> None:
    frame = loader.load_ranking(period)
    assert not frame.empty
    assert {"id", "name", "slug", "rank", "rankPoints", "category"}.issubset(frame.columns)
    assert pd.api.types.is_numeric_dtype(frame["rankPoints"])


def test_load_ranking_rejects_unknown_period(offline: str) -> None:
    with pytest.raises(loader.DatasetError, match="period must be"):
        loader.load_ranking("yearly")


def test_load_categories_shape(offline: str) -> None:
    frame = loader.load_categories()
    assert not frame.empty
    assert {"slug", "name", "productCount", "state"}.issubset(frame.columns)
    assert pd.api.types.is_numeric_dtype(frame["productCount"])


def test_load_ai_market_index_shape(offline: str) -> None:
    frame = loader.load_ai_market_index()
    assert not frame.empty
    assert {"category", "categoryName", "productCount", "totalRankPoints"}.issubset(
        frame.columns
    )
    # The nested topProduct object must be flattened, not left as a dict.
    assert "topProductName" in frame.columns
    assert not frame["topProductName"].isna().all()


def test_load_discovery_index_shapes(offline: str) -> None:
    for name, loader_fn in (
        ("agent", loader.load_ai_agent_index),
        ("developer", loader.load_developer_tools_index),
        ("ai-tools", loader.load_ai_tools_index),
    ):
        frame = loader_fn()
        assert not frame.empty, f"{name} index should not be empty"
        expected = {
            "id", "name", "domain", "url", "category", "category_confidence",
            "discovered_from", "observed_at", "on_rank_board", "profile_url",
        }
        assert expected.issubset(set(frame.columns)), f"{name} index columns"


def test_load_research_index_shape(offline: str) -> None:
    frame = loader.load_research_index()
    assert not frame.empty
    assert {"family", "familyTitle", "monthKey", "url", "listingCount"}.issubset(
        frame.columns
    )


def test_load_evidence_shape(offline: str) -> None:
    evidence = loader.load_evidence()
    assert "claims" in evidence
    assert "rules" in evidence
    assert "notClaimed" in evidence
    assert "chain" in evidence
    assert len(evidence["chain"]) >= 1
    for claim in evidence["claims"]:
        assert {"id", "claim", "claimType", "supported"}.issubset(claim)


def test_load_manifest_shape(offline: str) -> None:
    manifest = loader.load_manifest()
    assert {"name", "version", "updatedAt", "datasets"}.issubset(manifest)
    assert manifest["datasets"], "manifest must list at least one dataset"


def test_available_datasets_returns_registry(offline: str) -> None:
    frame = loader.available_datasets()
    assert not frame.empty
    assert {"id", "name", "json", "recordCount"}.issubset(frame.columns)


# --------------------------------------------------------------------------
# benchmark repository loaders
# --------------------------------------------------------------------------


def test_load_benchmark_results_carries_modeled_flag(benchmark_base: str) -> None:
    frame, meta = loader.load_benchmark_results(base=benchmark_base)
    assert not frame.empty
    assert {"model", "successRate", "costPerTask", "costPerSuccessfulTask"}.issubset(
        frame.columns
    )
    # The MODELED disclosure must survive loading; callers depend on it.
    assert meta.get("isModeled") is True
    assert meta.get("methodologyNote")


def test_load_llm_pricing_shape(benchmark_base: str) -> None:
    frame = loader.load_llm_pricing(base=benchmark_base)
    assert not frame.empty
    assert {
        "id", "provider", "input_per_million", "output_per_million"
    }.issubset(frame.columns)


# --------------------------------------------------------------------------
# failure behaviour
# --------------------------------------------------------------------------


def test_missing_dataset_raises(missing_base: str) -> None:
    with pytest.raises(loader.DatasetError):
        loader.load_products(base=missing_base)


def test_empty_dataset_raises(empty_base: str) -> None:
    """An empty dataset must raise, never return a zero-row frame."""
    with pytest.raises(loader.DatasetError, match="empty"):
        loader.load_products(base=empty_base)


def test_malformed_json_raises(tmp_path) -> None:
    target = tmp_path / "data/products/products.json"
    target.parent.mkdir(parents=True)
    target.write_text("{ not valid json", encoding="utf-8")
    with pytest.raises(loader.DatasetError, match="Malformed JSON"):
        loader.load_products(base=str(tmp_path) + "/")


def test_resolved_data_base_honours_env(offline: str) -> None:
    assert loader.resolved_data_base() == offline


def test_model_replacement_status_reports_absence(missing_base: str) -> None:
    """With no local benchmark clone, the probe must report 'not available'."""
    status = loader.model_replacement_status(base=missing_base)
    assert status["dataset_available"] is False
    assert status["data_files"] == []
    assert status["reason"]
    assert "stub" in status["reason"].lower() or "not" in status["reason"].lower()


def test_model_replacement_status_detects_a_file(tmp_path) -> None:
    """If a result file genuinely appears, the probe flips to available."""
    target = tmp_path / "data/model-replacement.json"
    target.parent.mkdir(parents=True)
    target.write_text("{}", encoding="utf-8")
    status = loader.model_replacement_status(base=str(tmp_path) + "/")
    assert status["dataset_available"] is True
    assert "data/model-replacement.json" in status["data_files"]
