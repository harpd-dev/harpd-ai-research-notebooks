"""Report rendering tests: required sections, determinism, and citations."""

from __future__ import annotations

import pytest

from harpd_research import report
from harpd_research.report import ReportData, ReportError, render_report, validate_report_text


def make_report(**overrides) -> ReportData:
    """A minimal but complete ReportData for rendering tests."""
    base = {
        "slug": "test-report",
        "title": "Test Report",
        "question": "What does the data show?",
        "dataset_name": "Products",
        "dataset_path": "data/products/products.json",
        "dataset_url": "https://harpd.com/data/",
        "generated_at": "2026-09-16T10:37:21.210Z",
        "last_updated": "2026-09-16T10:37:21.880Z",
        "sample_size": 1122,
        "methodology": ["Load the dataset.", "Count the records."],
        "limitations": ["Rank Points are promotional placement, not quality."],
        "findings": ["The catalog holds 1,122 products."],
        "citation_key": "harpd-ai-datasets",
        "citation_title": "Harpd AI Datasets",
        "accessed": "2026-09-16",
    }
    base.update(overrides)
    return ReportData(**base)


def test_required_sections_constant() -> None:
    expected = {
        "Data timestamp",
        "Sample size",
        "Methodology",
        "Limitations",
        "Dataset link",
        "Source",
        "Reproduction instructions",
        "Citation",
    }
    assert set(report.REQUIRED_SECTIONS) == expected


def test_render_contains_every_required_section() -> None:
    text = render_report(make_report())
    missing = validate_report_text(text)
    assert missing == [], f"missing sections: {missing}"


def test_render_includes_citation_block() -> None:
    text = render_report(make_report())
    assert "## Citation" in text
    assert "### BibTeX" in text
    assert "```bibtex" in text
    assert "@misc{harpd-ai-datasets," in text
    assert "### APA" in text
    assert "Harpd. (2026)." in text


def test_render_includes_data_timestamp_and_sample_size() -> None:
    text = render_report(make_report())
    assert "2026-09-16T10:37:21.210Z" in text
    assert "1,122" in text


def test_render_includes_dataset_link_and_source() -> None:
    text = render_report(make_report())
    assert "data/products/products.json" in text
    assert "https://harpd.com/data/" in text
    assert "CC BY 4.0" in text


def test_render_includes_reproduction_instructions() -> None:
    text = render_report(make_report())
    assert "git clone" in text
    assert "pip install -r requirements.txt" in text
    assert "scripts/generate_reports.py" in text
    assert "HARPD_DATA_BASE" in text


def test_render_carries_the_placement_caveat() -> None:
    text = render_report(make_report())
    assert "promotional placement bought with Credits" in text
    assert "NOT an editorial quality score" in text


def test_render_is_deterministic() -> None:
    """Same input must produce byte-identical output, twice."""
    data = make_report()
    assert render_report(data) == render_report(data)


def test_render_is_deterministic_across_instances() -> None:
    assert render_report(make_report()) == render_report(make_report())


def test_render_renders_tables() -> None:
    import pandas as pd

    data = make_report(tables=[("Counts", pd.DataFrame({"a": [1, 2], "b": ["x", "y"]}))])
    text = render_report(data)
    assert "### Counts" in text
    assert "| a | b |" in text or "|   a |" in text


def test_render_handles_empty_table_gracefully() -> None:
    import pandas as pd

    data = make_report(tables=[("Nothing", pd.DataFrame())])
    text = render_report(data)
    assert "No rows returned by this computation." in text


def test_render_includes_extra_notes() -> None:
    text = render_report(make_report(extra_notes=["A note."]))
    assert "## Notes" in text
    assert "A note." in text


def test_validate_report_text_reports_missing_sections() -> None:
    missing = validate_report_text("# Just a title\n\nNothing else.")
    assert "Methodology" in missing
    assert "Citation" in missing
    assert "BibTeX citation block" in missing


def test_validate_report_text_detects_missing_apa() -> None:
    text = render_report(make_report()).replace("### APA", "### References")
    assert "APA citation block" in validate_report_text(text)


def test_report_metadata_shape() -> None:
    meta = report.report_metadata(make_report())
    assert meta["slug"] == "test-report"
    assert meta["sample_size"] == 1122
    assert meta["tables"] == 0
    assert meta["findings"] == 1


# --------------------------------------------------------------------------
# construction guards
# --------------------------------------------------------------------------


def test_report_data_requires_slug() -> None:
    with pytest.raises(ReportError, match="slug is required"):
        make_report(slug="")


def test_report_data_requires_citation_key() -> None:
    with pytest.raises(ReportError, match="citation_key is required"):
        make_report(citation_key="")
