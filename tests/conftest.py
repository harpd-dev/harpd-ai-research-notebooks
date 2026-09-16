"""Shared pytest fixtures.

The suite is hermetic: it never touches the network. Fixtures under
``tests/fixtures/`` are real *subsets* of the published Harpd datasets, so the
loader is still exercised against the real schema.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

FIXTURES = Path(__file__).resolve().parent / "fixtures"


@pytest.fixture(scope="session")
def datasets_base() -> str:
    """Base directory for the subsetted Harpd dataset fixtures."""
    base = FIXTURES / "datasets"
    assert base.is_dir(), f"missing fixtures at {base}"
    return str(base) + "/"


@pytest.fixture(scope="session")
def benchmark_base() -> str:
    """Base directory for the llm-cost-benchmark fixtures."""
    base = FIXTURES / "benchmark"
    assert base.is_dir(), f"missing fixtures at {base}"
    return str(base) + "/"


@pytest.fixture
def offline(monkeypatch: pytest.MonkeyPatch, datasets_base: str) -> str:
    """Point ``HARPD_DATA_BASE`` at the fixture datasets."""
    monkeypatch.setenv("HARPD_DATA_BASE", datasets_base)
    monkeypatch.setenv("HARPD_CACHE_DIR", str(FIXTURES / ".cache"))
    return datasets_base


@pytest.fixture
def empty_base(tmp_path: Path) -> str:
    """A base directory containing an empty products dataset."""
    target = tmp_path / "data/products/products.json"
    target.parent.mkdir(parents=True)
    target.write_text(
        json.dumps(
            {
                "schemaVersion": "1.0",
                "generatedAt": "2026-09-16T00:00:00.000Z",
                "lastUpdated": "2026-09-15T00:00:00.000Z",
                "count": 0,
                "products": [],
            }
        ),
        encoding="utf-8",
    )
    return str(tmp_path) + "/"


@pytest.fixture
def missing_base(tmp_path: Path) -> str:
    """A base directory with no dataset files at all."""
    (tmp_path / "empty-dir").mkdir()
    return str(tmp_path / "empty-dir") + "/"


@pytest.fixture(scope="session")
def reports_dir() -> Path:
    return REPO_ROOT / "reports"


@pytest.fixture(scope="session")
def notebooks_dir() -> Path:
    return REPO_ROOT / "notebooks"
