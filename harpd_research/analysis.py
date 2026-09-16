"""Pandas computations over the Harpd open datasets.

Every function here is a pure transformation of loaded data. No function
invents, estimates or back-fills a value. Where the underlying data cannot
support a conclusion, the function returns that fact as data (a zero count, an
empty frame, an explicit ``False`` flag) rather than a plausible-looking number.

Domain rule enforced throughout: ``rankPoints`` measures **promotional
placement bought with Credits**. It is not a quality score, and no function here
labels a ``rankPoints`` ordering as quality or "best".
"""

from __future__ import annotations

import pandas as pd

__all__ = [
    "PLACEMENT_CAVEAT",
    "PLACEMENT_LABEL",
    "benchmark_efficiency",
    "category_boards",
    "cost_per_successful_task",
    "cross_index_overlap",
    "discovery_coverage",
    "evidence_audit",
    "market_composition",
    "placement_concentration",
    "ranking_board_comparison",
    "top_placement",
]

#: Reused verbatim wherever an ordering by rankPoints is shown.
PLACEMENT_CAVEAT = (
    "Rank Points are promotional placement bought with Credits — NOT an editorial "
    "quality score. Any ordering below is a promotional placement ordering, not a "
    "ranking of product quality."
)

#: Short label to attach to placement-ordered outputs.
PLACEMENT_LABEL = "promotional placement ordering"


# --------------------------------------------------------------------------
# product catalog / market composition
# --------------------------------------------------------------------------


def market_composition(products: pd.DataFrame, top_n: int | None = None) -> pd.DataFrame:
    """Product counts per category with share of the catalog.

    Columns: ``category``, ``categoryName``, ``productCount``, ``sharePct``.
    Sorted by ``productCount`` descending -- a *catalog size* ordering, which is
    a count of listings, not a quality measure.
    """
    required = {"category", "categoryName"}
    missing = required - set(products.columns)
    if missing:
        raise ValueError(f"market_composition: products missing columns {sorted(missing)}")
    if products.empty:
        return pd.DataFrame(columns=["category", "categoryName", "productCount", "sharePct"])

    grouped = (
        products.groupby(["category", "categoryName"], dropna=False)
        .size()
        .reset_index(name="productCount")
    )
    total = int(grouped["productCount"].sum())
    grouped["sharePct"] = (grouped["productCount"] / total * 100).round(2)
    grouped = grouped.sort_values(
        ["productCount", "category"], ascending=[False, True]
    ).reset_index(drop=True)
    if top_n is not None:
        grouped = grouped.head(top_n).reset_index(drop=True)
    return grouped


def placement_concentration(products: pd.DataFrame) -> dict[str, object]:
    """How much of the catalog carries paid placement, and how concentrated it is.

    This is the load-bearing honesty check for the whole repository. If almost no
    product has ``rankPoints > 0``, then no meaningful placement distribution
    exists, and the returned ``has_meaningful_placement`` is ``False`` so callers
    can say so instead of computing a misleading statistic.
    """
    if "rankPoints" not in products.columns:
        raise ValueError("placement_concentration: products missing 'rankPoints'")

    points = pd.to_numeric(products["rankPoints"], errors="coerce").fillna(0)
    total = int(len(points))
    funded = points[points > 0]
    funded_count = int(len(funded))
    total_points = float(points.sum())

    top_share = None
    if funded_count and total_points > 0:
        top_share = round(float(funded.max()) / total_points * 100, 2)

    return {
        "totalProducts": total,
        "productsWithPlacement": funded_count,
        "productsWithoutPlacement": total - funded_count,
        "placementCoveragePct": round(funded_count / total * 100, 4) if total else 0.0,
        "totalRankPoints": total_points,
        "maxRankPoints": float(points.max()) if total else 0.0,
        "largestPlacementSharePct": top_share,
        "distinctPlacementValues": int(points.nunique()),
        "has_meaningful_placement": funded_count >= 2,
        "caveat": PLACEMENT_CAVEAT,
    }


def top_placement(products: pd.DataFrame, n: int = 10) -> pd.DataFrame:
    """The ``n`` products with the most placement points.

    Output is a **promotional placement ordering** (see :data:`PLACEMENT_CAVEAT`),
    not a quality ranking. Ties are broken by ``rank`` then ``name`` for
    determinism.
    """
    if "rankPoints" not in products.columns:
        raise ValueError("top_placement: products missing 'rankPoints'")

    columns = [
        column
        for column in ["rank", "name", "categoryName", "rankPoints", "verified"]
        if column in products.columns
    ]
    frame = products.loc[:, columns].copy()
    frame["rankPoints"] = pd.to_numeric(frame["rankPoints"], errors="coerce").fillna(0)
    frame = frame[frame["rankPoints"] > 0]
    if frame.empty:
        return frame.reset_index(drop=True)

    sort_columns = ["rankPoints"]
    ascending = [False]
    if "rank" in frame.columns:
        sort_columns.append("rank")
        ascending.append(True)
    if "name" in frame.columns:
        sort_columns.append("name")
        ascending.append(True)

    frame = frame.sort_values(sort_columns, ascending=ascending)
    return frame.head(n).reset_index(drop=True)


# --------------------------------------------------------------------------
# category boards
# --------------------------------------------------------------------------


def category_boards(categories: pd.DataFrame) -> pd.DataFrame:
    """Category board state, listing counts and whether placement is open.

    ``state == "LISTED_NO_RP"`` means the category has listings but no paid
    placement sold; ``topRankOpen`` is the publisher's own flag that the top
    position is still available. Both are *supply* signals, not quality signals.
    """
    required = {"slug", "name", "productCount", "state"}
    missing = required - set(categories.columns)
    if missing:
        raise ValueError(f"category_boards: categories missing columns {sorted(missing)}")
    if categories.empty:
        return pd.DataFrame(columns=["slug", "name", "productCount", "rankedProductCount", "state"])

    frame = categories.copy()
    if "rankedProductCount" not in frame.columns:
        frame["rankedProductCount"] = 0
    frame["rankedProductCount"] = pd.to_numeric(
        frame["rankedProductCount"], errors="coerce"
    ).fillna(0)
    frame["productCount"] = pd.to_numeric(frame["productCount"], errors="coerce").fillna(0)

    keep = [
        column
        for column in [
            "slug",
            "name",
            "productCount",
            "rankedProductCount",
            "totalRankPoints",
            "state",
            "topRankOpen",
        ]
        if column in frame.columns
    ]
    frame = frame.loc[:, keep].sort_values(["productCount", "slug"], ascending=[False, True])
    return frame.reset_index(drop=True)


def ranking_board_comparison(
    overall: pd.DataFrame, monthly: pd.DataFrame, weekly: pd.DataFrame
) -> pd.DataFrame:
    """Compare the three published boards on size and placement totals.

    A board is a *view* over the same catalog, so differences here are about the
    published placement windows, not about product quality.
    """
    rows = []
    for label, frame in (("overall", overall), ("monthly", monthly), ("weekly", weekly)):
        points = (
            pd.to_numeric(frame["rankPoints"], errors="coerce").fillna(0)
            if "rankPoints" in frame.columns
            else pd.Series(dtype="float64")
        )
        rows.append(
            {
                "board": label,
                "records": int(len(frame)),
                "distinctProducts": int(frame["id"].nunique())
                if "id" in frame.columns
                else int(len(frame)),
                "productsWithPlacement": int((points > 0).sum()),
                "totalRankPoints": float(points.sum()),
                "categoriesRepresented": int(frame["category"].nunique())
                if "category" in frame.columns
                else 0,
            }
        )
    return pd.DataFrame(rows)


# --------------------------------------------------------------------------
# discovery indexes
# --------------------------------------------------------------------------


def discovery_coverage(records: pd.DataFrame, label: str) -> dict[str, object]:
    """Coverage summary for a discovery index slice.

    A discovery index is a *coverage* view, not a ranking. Reported fields:
    record count, distinct domains, how many appear on the rank board, and the
    confidence distribution of the automated category assignment.
    """
    if records.empty:
        return {
            "label": label,
            "records": 0,
            "distinctDomains": 0,
            "onRankBoard": 0,
            "onRankBoardPct": 0.0,
            "meanCategoryConfidence": None,
            "distinctDiscoverySources": 0,
            "observedAtMin": None,
            "observedAtMax": None,
            "hasData": False,
        }

    domains = records["domain"].dropna().nunique() if "domain" in records.columns else 0

    on_board = 0
    if "on_rank_board" in records.columns:
        on_board = int(_as_bool(records["on_rank_board"]).sum())

    confidence = None
    if "category_confidence" in records.columns:
        series = pd.to_numeric(records["category_confidence"], errors="coerce").dropna()
        if not series.empty:
            confidence = round(float(series.mean()), 4)

    sources = (
        int(records["discovered_from"].dropna().nunique())
        if "discovered_from" in records.columns
        else 0
    )

    observed_min = observed_max = None
    if "observed_at" in records.columns:
        stamps = pd.to_datetime(records["observed_at"], errors="coerce", utc=True).dropna()
        if not stamps.empty:
            observed_min = stamps.min().isoformat()
            observed_max = stamps.max().isoformat()

    return {
        "label": label,
        "records": int(len(records)),
        "distinctDomains": int(domains),
        "onRankBoard": on_board,
        "onRankBoardPct": round(on_board / len(records) * 100, 2),
        "meanCategoryConfidence": confidence,
        "distinctDiscoverySources": sources,
        "observedAtMin": observed_min,
        "observedAtMax": observed_max,
        "hasData": True,
    }


def _as_bool(series: pd.Series) -> pd.Series:
    """Normalise a column that may be bool, 0/1 or 'true'/'false' strings."""
    if series.dtype == bool:
        return series
    return series.astype(str).str.strip().str.lower().isin({"true", "1", "yes", "t"})


def discovery_sources(records: pd.DataFrame, top_n: int = 10) -> pd.DataFrame:
    """Where discovery records were observed from, by count.

    A *coverage* ordering over observation sources -- not a quality signal about
    the products themselves.
    """
    if records.empty or "discovered_from" not in records.columns:
        return pd.DataFrame(columns=["discovered_from", "recordCount", "sharePct"])

    grouped = (
        records["discovered_from"]
        .fillna("(unspecified)")
        .replace("", "(unspecified)")
        .value_counts()
        .rename_axis("discovered_from")
        .reset_index(name="recordCount")
    )
    total = int(grouped["recordCount"].sum())
    grouped["sharePct"] = (grouped["recordCount"] / total * 100).round(2)
    return grouped.head(top_n).reset_index(drop=True)


def cross_index_overlap(indexes: dict[str, pd.DataFrame], min_indexes: int = 2) -> pd.DataFrame:
    """Domains observed in more than one discovery index.

    Overlap is a coverage observation. It does not imply a product is better.
    """
    frames = []
    for label, records in indexes.items():
        if records.empty or "domain" not in records.columns:
            continue
        subset = records.loc[:, ["domain"]].dropna().copy()
        subset["domain"] = subset["domain"].astype(str).str.strip().str.lower()
        subset = subset[subset["domain"] != ""]
        subset["index"] = label
        frames.append(subset)

    if not frames:
        return pd.DataFrame(columns=["domain", "indexCount", "indexes"])

    combined = pd.concat(frames, ignore_index=True).drop_duplicates()
    grouped = (
        combined.groupby("domain")["index"]
        .agg(indexCount="nunique", indexes=lambda values: ", ".join(sorted(set(values))))
        .reset_index()
    )
    grouped = grouped[grouped["indexCount"] >= min_indexes]
    return grouped.sort_values(["indexCount", "domain"], ascending=[False, True]).reset_index(
        drop=True
    )


# --------------------------------------------------------------------------
# benchmark (separate repository)
# --------------------------------------------------------------------------


def cost_per_successful_task(
    results: pd.DataFrame, meta: dict[str, object] | None = None
) -> pd.DataFrame:
    """Per-model cost of one *successful* task, recomputed from the raw fields.

    ``costPerSuccessfulTask`` is recomputed as ``costPerTask / successRate`` so
    the published figure is verified rather than trusted. The source's own
    ``isModeled`` disclosure is carried into the ``isModeled`` column so no
    downstream consumer can mistake a modeled estimate for a measurement.
    """
    required = {"model", "successRate", "costPerTask"}
    missing = required - set(results.columns)
    if missing:
        raise ValueError(f"cost_per_successful_task: missing columns {sorted(missing)}")
    if results.empty:
        return pd.DataFrame(
            columns=[
                "model",
                "successRate",
                "costPerTask",
                "costPerSuccessfulTask",
                "publishedCostPerSuccessfulTask",
                "recomputedDeltaPct",
                "isModeled",
            ]
        )

    frame = results.copy()
    frame["successRate"] = pd.to_numeric(frame["successRate"], errors="coerce")
    frame["costPerTask"] = pd.to_numeric(frame["costPerTask"], errors="coerce")

    published = (
        pd.to_numeric(frame["costPerSuccessfulTask"], errors="coerce")
        if "costPerSuccessfulTask" in frame.columns
        else pd.Series([float("nan")] * len(frame), index=frame.index)
    )
    frame["publishedCostPerSuccessfulTask"] = published

    valid = frame["successRate"] > 0
    frame["costPerSuccessfulTask"] = float("nan")
    frame.loc[valid, "costPerSuccessfulTask"] = (
        frame.loc[valid, "costPerTask"] / frame.loc[valid, "successRate"]
    )
    frame["costPerSuccessfulTask"] = frame["costPerSuccessfulTask"].round(6)

    frame["recomputedDeltaPct"] = (
        (frame["costPerSuccessfulTask"] - frame["publishedCostPerSuccessfulTask"]).abs()
        / frame["publishedCostPerSuccessfulTask"]
        * 100
    ).round(3)

    frame["isModeled"] = bool((meta or {}).get("isModeled", False))

    frame = frame.sort_values("costPerSuccessfulTask").reset_index(drop=True)
    frame.insert(0, "efficiencyOrder", range(1, len(frame) + 1))
    return frame


def benchmark_efficiency(results: pd.DataFrame) -> dict[str, object]:
    """Spread between the cheapest and most expensive successful task.

    Returns ``None`` for the ratio when fewer than two usable rows exist, so a
    caller cannot report a spread that the data does not support.
    """
    if results.empty:
        return {
            "models": 0,
            "cheapestModel": None,
            "cheapestCostPerSuccessfulTask": None,
            "mostExpensiveModel": None,
            "mostExpensiveCostPerSuccessfulTask": None,
            "costSpreadRatio": None,
            "maxSuccessRate": None,
            "minSuccessRate": None,
            "hasData": False,
        }

    frame = results.dropna(subset=["costPerSuccessfulTask"])
    if frame.empty:
        return {
            "models": 0,
            "cheapestModel": None,
            "cheapestCostPerSuccessfulTask": None,
            "mostExpensiveModel": None,
            "mostExpensiveCostPerSuccessfulTask": None,
            "costSpreadRatio": None,
            "maxSuccessRate": None,
            "minSuccessRate": None,
            "hasData": False,
        }

    cheapest = frame.loc[frame["costPerSuccessfulTask"].idxmin()]
    dearest = frame.loc[frame["costPerSuccessfulTask"].idxmax()]
    ratio = None
    if cheapest["costPerSuccessfulTask"] and cheapest["costPerSuccessfulTask"] > 0:
        ratio = round(
            float(dearest["costPerSuccessfulTask"] / cheapest["costPerSuccessfulTask"]), 2
        )

    success = pd.to_numeric(results["successRate"], errors="coerce").dropna()
    return {
        "models": int(len(results)),
        "cheapestModel": str(cheapest["model"]),
        "cheapestCostPerSuccessfulTask": float(cheapest["costPerSuccessfulTask"]),
        "mostExpensiveModel": str(dearest["model"]),
        "mostExpensiveCostPerSuccessfulTask": float(dearest["costPerSuccessfulTask"]),
        "costSpreadRatio": ratio,
        "maxSuccessRate": round(float(success.max()), 4) if not success.empty else None,
        "minSuccessRate": round(float(success.min()), 4) if not success.empty else None,
        "hasData": True,
    }


# --------------------------------------------------------------------------
# evidence register
# --------------------------------------------------------------------------


def evidence_audit(evidence: dict[str, object]) -> pd.DataFrame:
    """Claim counts by type, with how many are marked supported.

    Harpd's own register: a claim is publishable only when it resolves to a
    registered dataset, a methodology URL and a real timestamp.
    """
    claims = (evidence or {}).get("claims") or []
    if not claims:
        return pd.DataFrame(columns=["claimType", "claims", "supported", "withSource"])

    frame = pd.DataFrame(claims)
    if "claimType" not in frame.columns:
        raise ValueError("evidence_audit: claims missing 'claimType'")

    frame["_supported"] = _as_bool(frame.get("supported", pd.Series(dtype=bool)))
    frame["_withSource"] = frame.get("source", pd.Series([None] * len(frame))).notna()

    grouped = (
        frame.groupby("claimType")
        .agg(
            claims=("claimType", "size"),
            supported=("_supported", "sum"),
            withSource=("_withSource", "sum"),
        )
        .reset_index()
    )
    grouped["supported"] = grouped["supported"].astype(int)
    grouped["withSource"] = grouped["withSource"].astype(int)
    return grouped.sort_values(["claims", "claimType"], ascending=[False, True]).reset_index(
        drop=True
    )
