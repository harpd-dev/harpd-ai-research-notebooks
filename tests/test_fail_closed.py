"""Fail-closed guarantees.

These are the most important tests in the suite. The scheduled workflow depends
on the generator refusing to produce output when the data is missing or empty,
and on it leaving the last valid report untouched when it does.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest

from harpd_research import loader
from harpd_research.report import ReportData, ReportError, render_report

REPO_ROOT = Path(__file__).resolve().parents[1]


def load_generator():
    """Import scripts/generate_reports.py as a module."""
    path = REPO_ROOT / "scripts" / "generate_reports.py"
    spec = importlib.util.spec_from_file_location("generate_reports", path)
    module = importlib.util.module_from_spec(spec)
    sys.modules["generate_reports"] = module
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def generator():
    return load_generator()


def make_report(**overrides) -> ReportData:
    base = {
        "slug": "t",
        "title": "T",
        "question": "Q?",
        "dataset_name": "D",
        "dataset_path": "p",
        "dataset_url": "https://harpd.com/data/",
        "generated_at": "2026-09-16T00:00:00.000Z",
        "last_updated": "2026-09-16T00:00:00.000Z",
        "sample_size": 10,
        "methodology": ["m"],
        "limitations": ["l"],
        "findings": ["f"],
        "citation_key": "k",
        "accessed": "2026-09-16",
    }
    base.update(overrides)
    return ReportData(**base)


# --------------------------------------------------------------------------
# render_report must refuse invalid inputs
# --------------------------------------------------------------------------


def test_render_refuses_zero_sample_size() -> None:
    with pytest.raises(ReportError, match="refusing to render a report with sample_size"):
        render_report(make_report(sample_size=0))


def test_render_refuses_negative_sample_size() -> None:
    with pytest.raises(ReportError):
        render_report(make_report(sample_size=-5))


def test_render_refuses_none_sample_size() -> None:
    with pytest.raises(ReportError):
        render_report(make_report(sample_size=None))


def test_render_refuses_missing_generated_at() -> None:
    with pytest.raises(ReportError, match="without a data timestamp"):
        render_report(make_report(generated_at=""))


def test_render_refuses_missing_last_updated() -> None:
    with pytest.raises(ReportError, match="without lastUpdated"):
        render_report(make_report(last_updated=""))


def test_render_refuses_missing_snapshot_date() -> None:
    """A wall-clock fallback would break idempotency, so a blank must raise."""
    with pytest.raises(ReportError, match="snapshot date"):
        render_report(make_report(accessed=""))


def test_render_succeeds_at_sample_size_one() -> None:
    assert render_report(make_report(sample_size=1))


# --------------------------------------------------------------------------
# loader must refuse empty datasets
# --------------------------------------------------------------------------


def test_loader_refuses_empty_products(empty_base: str) -> None:
    with pytest.raises(loader.DatasetError, match="empty"):
        loader.load_products(base=empty_base)


def test_loader_refuses_missing_products(missing_base: str) -> None:
    with pytest.raises(loader.DatasetError):
        loader.load_products(base=missing_base)


# --------------------------------------------------------------------------
# the generator as a whole must exit non-zero and write nothing
# --------------------------------------------------------------------------


def test_generate_returns_nonzero_on_empty_data(
    generator, empty_base, tmp_path, monkeypatch
) -> None:
    monkeypatch.setenv("HARPD_DATA_BASE", empty_base)
    monkeypatch.setattr(generator, "REPORTS_DIR", tmp_path)
    assert generator.generate() == 1
    # The fixture dataset lives inside tmp_path, so assert on reports, not on
    # tmp_path being empty: the guarantee is that no report file is emitted.
    assert list(tmp_path.glob("*.md")) == [], "no report may be written on empty data"


def test_generate_returns_nonzero_on_missing_data(
    generator, missing_base, tmp_path, monkeypatch
) -> None:
    monkeypatch.setenv("HARPD_DATA_BASE", missing_base)
    monkeypatch.setattr(generator, "REPORTS_DIR", tmp_path)
    assert generator.generate() == 1
    assert list(tmp_path.glob("*.md")) == [], "no report may be written on missing data"


def test_generate_does_not_overwrite_last_valid_report(
    generator, empty_base, tmp_path, monkeypatch
) -> None:
    """The core guarantee: a failed run must leave the previous report intact."""
    existing = tmp_path / "2026-09-ai-market-report.md"
    sentinel = "# Last known good report\n\nDo not lose me.\n"
    existing.write_text(sentinel, encoding="utf-8")

    monkeypatch.setenv("HARPD_DATA_BASE", empty_base)
    monkeypatch.setattr(generator, "REPORTS_DIR", tmp_path)

    assert generator.generate() == 1
    assert existing.read_text(encoding="utf-8") == sentinel


def test_generate_check_mode_writes_nothing(
    generator, tmp_path, monkeypatch, datasets_base
) -> None:
    monkeypatch.setenv("HARPD_DATA_BASE", datasets_base)
    monkeypatch.setattr(generator, "REPORTS_DIR", tmp_path)
    assert generator.generate(check_only=True) == 0
    assert list(tmp_path.iterdir()) == []


def test_generate_fails_when_a_builder_raises(generator, tmp_path, monkeypatch) -> None:
    """If any builder raises, nothing at all is written."""

    def exploding_builder():
        raise generator.GenerationFailed("simulated failure")

    monkeypatch.setattr(generator, "BUILDERS", {"2026-09-ai-market-report.md": exploding_builder})
    monkeypatch.setattr(generator, "REPORTS_DIR", tmp_path)
    assert generator.generate() == 1
    assert list(tmp_path.iterdir()) == []


def test_generate_rejects_a_report_missing_sections(generator, tmp_path, monkeypatch) -> None:
    """A rendered report that lost a required section must not be written."""
    good = generator.build_agent_report()

    def stripped_builder():
        return good

    monkeypatch.setattr(generator, "BUILDERS", {"x.md": stripped_builder})
    monkeypatch.setattr(generator, "REPORTS_DIR", tmp_path)
    # First confirm the good report validates, then simulate a broken renderer.
    assert generator.validate_report_text(generator.render_report(good)) == []

    def broken_render(_data):
        return "# Title only\n"

    monkeypatch.setattr(generator, "render_report", broken_render)
    assert generator.generate() == 1
    assert list(tmp_path.iterdir()) == []
