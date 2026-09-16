"""Dataset loading for Harpd open data.

Notebooks fetch from the public raw GitHub URL by default so a third party can
reproduce every number on a clean machine. Two escape hatches exist:

* ``HARPD_DATA_BASE``  -- point at any base URL *or* local directory.
* ``HARPD_CACHE_DIR``  -- where HTTP responses are cached (default ``.cache/``).

Nothing in this module invents data. If a file is missing, unreachable or
malformed, a :class:`DatasetError` is raised. Callers must decide whether to
stop; the default posture across this repository is to fail closed.
"""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
from typing import Any

import pandas as pd
import requests

__all__ = [
    "DEFAULT_DATA_BASE",
    "RAW_GITHUB_BASE",
    "DatasetError",
    "available_datasets",
    "fetch_json",
    "load_ai_agent_index",
    "load_ai_market_index",
    "load_ai_tools_index",
    "load_benchmark_results",
    "load_categories",
    "load_developer_tools_index",
    "load_evidence",
    "load_llm_pricing",
    "load_manifest",
    "load_products",
    "load_ranking",
    "load_research_index",
    "model_replacement_status",
    "resolved_data_base",
]

#: Canonical location of the published Harpd open datasets.
RAW_GITHUB_BASE = "https://raw.githubusercontent.com/harpd-dev/harpd-ai-datasets/main/"

#: Base used when ``HARPD_DATA_BASE`` is unset.
DEFAULT_DATA_BASE = RAW_GITHUB_BASE

#: Separate Harpd repositories that hold data this notebook set also reads.
LLM_COST_BENCHMARK_BASE = "https://raw.githubusercontent.com/harpd-dev/llm-cost-benchmark/main/"
MODEL_REPLACEMENT_BENCHMARK_BASE = (
    "https://raw.githubusercontent.com/harpd-dev/model-replacement-benchmark/main/"
)

_TIMEOUT_SECONDS = 30


class DatasetError(RuntimeError):
    """Raised when a dataset cannot be loaded or does not have the expected shape."""


# --------------------------------------------------------------------------
# low-level fetch
# --------------------------------------------------------------------------


def _data_base(base: str | None = None) -> str:
    """Resolve the base location, honouring the ``HARPD_DATA_BASE`` override."""
    resolved = base or os.environ.get("HARPD_DATA_BASE") or DEFAULT_DATA_BASE
    return resolved if resolved.endswith("/") else resolved + "/"


def _cache_dir() -> Path:
    raw = os.environ.get("HARPD_CACHE_DIR", ".cache")
    path = Path(raw)
    path.mkdir(parents=True, exist_ok=True)
    return path


def resolved_data_base(base: str | None = None) -> str:
    """The base location actually in use, after applying ``HARPD_DATA_BASE``.

    Exposed so notebooks and reports can print where their numbers came from.
    """
    return _data_base(base)


def _is_local(base: str) -> bool:
    return not base.startswith(("http://", "https://"))


def _cache_path(base: str, relative_path: str) -> Path:
    digest = hashlib.sha256(f"{base}{relative_path}".encode()).hexdigest()[:16]
    safe = relative_path.replace("/", "__")
    return _cache_dir() / f"{safe}.{digest}.json"


def fetch_json(relative_path: str, base: str | None = None, use_cache: bool = True) -> Any:
    """Load a JSON document from the dataset base.

    Works against the public raw URL, an alternate URL, or a local directory.
    Raises :class:`DatasetError` on any failure -- never returns a placeholder.
    """
    resolved = _data_base(base)

    if _is_local(resolved):
        target = Path(resolved) / relative_path
        if not target.is_file():
            raise DatasetError(f"Dataset not found on disk: {target}")
        try:
            return json.loads(target.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            raise DatasetError(f"Malformed JSON in {target}: {exc}") from exc

    cache_file = _cache_path(resolved, relative_path)
    if use_cache and cache_file.is_file():
        try:
            return json.loads(cache_file.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            cache_file.unlink(missing_ok=True)

    url = resolved + relative_path
    try:
        response = requests.get(url, timeout=_TIMEOUT_SECONDS)
        response.raise_for_status()
    except requests.RequestException as exc:
        if cache_file.is_file():
            return json.loads(cache_file.read_text(encoding="utf-8"))
        raise DatasetError(f"Could not fetch {url}: {exc}") from exc

    try:
        payload = response.json()
    except ValueError as exc:
        raise DatasetError(f"Response from {url} was not JSON: {exc}") from exc

    if use_cache:
        cache_file.write_text(json.dumps(payload), encoding="utf-8")
    return payload


# --------------------------------------------------------------------------
# shape helpers
# --------------------------------------------------------------------------


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise DatasetError(message)


def _records_frame(payload: Any, list_key: str, source: str) -> pd.DataFrame:
    """Pull a list of records out of a payload that may or may not be wrapped."""
    if isinstance(payload, list):
        records = payload
    elif isinstance(payload, dict):
        _require(
            list_key in payload,
            f"{source}: expected key {list_key!r}; found {sorted(payload)[:8]}",
        )
        records = payload[list_key]
    else:
        raise DatasetError(f"{source}: expected object or list, got {type(payload).__name__}")

    _require(isinstance(records, list), f"{source}: {list_key!r} is not a list")
    frame = pd.DataFrame(records)
    _require(not frame.empty, f"{source}: dataset is empty (0 records)")
    return frame


def _coerce_numeric(frame: pd.DataFrame, columns: list[str]) -> pd.DataFrame:
    for column in columns:
        if column in frame.columns:
            frame[column] = pd.to_numeric(frame[column], errors="coerce")
    return frame


def _attach_meta(frame: pd.DataFrame, payload: Any) -> pd.DataFrame:
    """Copy real dataset timestamps onto ``frame.attrs``.

    Reports must be able to print the timestamp that came *from the data*. When
    the payload carries none, nothing is attached -- a blank timestamp is
    reported as blank rather than defaulted to today's date.
    """
    if not isinstance(payload, dict):
        return frame

    meta = payload.get("meta") if isinstance(payload.get("meta"), dict) else payload

    for key in ("generatedAt", "lastUpdated", "updatedAt", "source", "license"):
        value = meta.get(key) if key in meta else payload.get(key)
        if value:
            frame.attrs[key] = value

    for key in ("periods", "scope", "methodology", "note", "disclosure"):
        if key in payload:
            frame.attrs[key] = payload[key]
        elif key in meta:
            frame.attrs[key] = meta[key]

    if isinstance(payload.get("meta"), dict):
        for key in ("datasetId", "periodKey", "sliceDefinition"):
            if key in payload["meta"]:
                frame.attrs[key] = payload["meta"][key]

    return frame


# --------------------------------------------------------------------------
# dataset loaders
# --------------------------------------------------------------------------


def load_manifest(base: str | None = None) -> dict[str, Any]:
    """Load ``data/manifest.json`` -- the dataset registry."""
    payload = fetch_json("data/manifest.json", base=base)
    _require(isinstance(payload, dict), "manifest: expected an object")
    _require("datasets" in payload, "manifest: missing 'datasets'")
    return payload


def available_datasets(base: str | None = None) -> pd.DataFrame:
    """Return the manifest registry as a DataFrame (one row per dataset)."""
    manifest = load_manifest(base=base)
    frame = pd.DataFrame(manifest["datasets"])
    _require(not frame.empty, "manifest: 'datasets' is empty")
    return frame


def load_products(base: str | None = None) -> pd.DataFrame:
    """Load the product catalog (1122 records at the 2026-09 snapshot)."""
    payload = fetch_json("data/products/products.json", base=base)
    frame = _records_frame(payload, "products", "products")
    frame = _coerce_numeric(frame, ["rank", "rankPoints"])
    return _attach_meta(frame, payload)


def load_ranking(period: str = "overall", base: str | None = None) -> pd.DataFrame:
    """Load a ranking board: ``overall``, ``monthly`` or ``weekly``."""
    _require(
        period in {"overall", "monthly", "weekly"},
        f"ranking: period must be overall/monthly/weekly, got {period!r}",
    )
    payload = fetch_json(f"data/rankings/{period}.json", base=base)
    frame = _records_frame(payload, "products", f"rankings/{period}")
    frame = _coerce_numeric(frame, ["rank", "rankPoints"])
    return _attach_meta(frame, payload)


def load_categories(base: str | None = None) -> pd.DataFrame:
    """Load the 28 category boards with product counts and placement state."""
    payload = fetch_json("data/rankings/categories.json", base=base)
    frame = _records_frame(payload, "categories", "rankings/categories")
    frame = _coerce_numeric(frame, ["productCount", "rankedProductCount", "totalRankPoints"])
    return _attach_meta(frame, payload)


def load_ai_market_index(base: str | None = None) -> pd.DataFrame:
    """Load the AI market index (one row per category, 27 rows)."""
    payload = fetch_json("data/research/ai-market-index.json", base=base)
    frame = _records_frame(payload, "categories", "research/ai-market-index")
    frame = _coerce_numeric(
        frame, ["productCount", "totalRankPoints", "productShare", "pointsShare"]
    )
    if "topProduct" in frame.columns:
        frame["topProductName"] = frame["topProduct"].apply(
            lambda value: (value or {}).get("name") if isinstance(value, dict) else None
        )
        frame["topProductRankPoints"] = frame["topProduct"].apply(
            lambda value: (value or {}).get("rankPoints") if isinstance(value, dict) else None
        )
    return _attach_meta(frame, payload)


def _load_discovery_index(filename: str, base: str | None = None) -> pd.DataFrame:
    payload = fetch_json(f"data/research/{filename}", base=base)
    frame = _records_frame(payload, "records", f"research/{filename}")
    frame = _coerce_numeric(frame, ["category_confidence"])
    return _attach_meta(frame, payload)


def load_ai_agent_index(base: str | None = None) -> pd.DataFrame:
    """Load the AI agent discovery index (334 records at the 2026-09 snapshot)."""
    return _load_discovery_index("ai-agent-index.json", base=base)


def load_developer_tools_index(base: str | None = None) -> pd.DataFrame:
    """Load the developer tools discovery index (1918 records)."""
    return _load_discovery_index("developer-tools-index.json", base=base)


def load_ai_tools_index(base: str | None = None) -> pd.DataFrame:
    """Load the AI tools discovery index (693 records)."""
    return _load_discovery_index("ai-tools-index.json", base=base)


def load_research_index(base: str | None = None) -> pd.DataFrame:
    """Load the monthly research publication index (5 rows)."""
    payload = fetch_json("data/research/research.json", base=base)
    frame = _records_frame(payload, "research", "research/research")
    frame = _coerce_numeric(frame, ["listingCount"])
    return _attach_meta(frame, payload)


def load_evidence(base: str | None = None) -> dict[str, Any]:
    """Load the evidence register (claims, datasets, graph, rules)."""
    payload = fetch_json("data/evidence/evidence.json", base=base)
    _require(isinstance(payload, dict), "evidence: expected an object")
    _require("claims" in payload, "evidence: missing 'claims'")
    return payload


def load_benchmark_results(base: str | None = None) -> tuple[pd.DataFrame, dict[str, Any]]:
    """Load the llm-cost-benchmark JSON-extraction results.

    Returns ``(frame, meta)``. ``meta`` carries the ``isModeled`` flag and the
    publisher's own methodology note, which callers MUST surface -- the published
    figures are a MODELED estimate, not a live measurement.
    """
    payload = fetch_json("data/2026-08-json-extraction.json", base=base or LLM_COST_BENCHMARK_BASE)
    _require(isinstance(payload, dict), "benchmark: expected an object")
    frame = _records_frame(payload, "results", "benchmark/json-extraction")
    frame = _coerce_numeric(
        frame,
        [
            "successRate",
            "p50LatencyMs",
            "p95LatencyMs",
            "avgInputTokens",
            "avgOutputTokens",
            "costPerTask",
            "costPerSuccessfulTask",
        ],
    )
    meta = {key: value for key, value in payload.items() if key != "results"}
    return frame, meta


def load_llm_pricing(base: str | None = None) -> pd.DataFrame:
    """Load the llm-cost-benchmark list-price snapshot."""
    payload = fetch_json("pricing/llm-pricing.json", base=base or LLM_COST_BENCHMARK_BASE)
    frame = _records_frame(payload, "models", "benchmark/llm-pricing")
    return _coerce_numeric(
        frame,
        [
            "input_per_million",
            "cached_input_per_million",
            "output_per_million",
            "context_window",
        ],
    )


def model_replacement_status(
    base: str | None = None,
) -> dict[str, Any]:
    """Probe whether a real model-replacement dataset exists.

    The repository ``harpd-dev/model-replacement-benchmark`` ships a comparison
    script whose model calls are an explicit stub. This helper reports that
    honestly instead of fabricating a result set. It never raises for a missing
    dataset -- the caller is expected to render the finding.
    """
    resolved = base or MODEL_REPLACEMENT_BENCHMARK_BASE
    result: dict[str, Any] = {
        "repo": "https://github.com/harpd-dev/model-replacement-benchmark",
        "data_files": [],
        "dataset_available": False,
        "reason": "",
    }

    candidates = [
        "data/model-replacement.json",
        "data/results.json",
        "data/tasks.json",
        "data/model-replacement.csv",
        "data/results.csv",
    ]

    if _is_local(_data_base(resolved)):
        root = Path(_data_base(resolved))
        if root.is_dir():
            result["data_files"] = sorted(
                str(p.relative_to(root)) for p in root.rglob("*") if p.is_file()
            )
    else:
        for candidate in candidates:
            try:
                response = requests.head(
                    _data_base(resolved) + candidate, timeout=10, allow_redirects=True
                )
            except requests.RequestException:
                continue
            if response.status_code == 200:
                result["data_files"].append(candidate)

    if result["data_files"]:
        result["dataset_available"] = True
        result["reason"] = "A model-replacement result file was located."
    else:
        result["reason"] = (
            "No model-replacement result dataset is published. The repository ships "
            "compare.mjs, whose provider calls are an explicit stub, and Harpd's own "
            "evidence register lists cross-model switch safety as notClaimed."
        )
    return result
