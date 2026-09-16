"""Citation formatter tests."""

from __future__ import annotations

from harpd_research import citation


def test_bibtex_has_required_fields() -> None:
    entry = citation.bibtex(
        key="harpd-ai-datasets",
        title="Harpd AI Datasets",
        url="https://harpd.com/data/",
    )
    assert entry.startswith("@misc{harpd-ai-datasets,")
    assert "author" in entry
    assert "title" in entry
    assert "year       = {2026}" in entry
    assert "https://harpd.com/data/" in entry
    assert entry.rstrip().endswith("}")


def test_bibtex_braces_are_balanced() -> None:
    entry = citation.bibtex(key="k", title="T", url="https://example.org/")
    assert entry.count("{") == entry.count("}")


def test_bibtex_custom_note() -> None:
    entry = citation.bibtex(key="k", title="T", url="u", note="Custom note")
    assert "Custom note" in entry


def test_apa_structure() -> None:
    reference = citation.apa(title="Harpd AI Datasets", url="https://harpd.com/data/")
    assert reference.startswith("Harpd. (2026).")
    assert "*Harpd AI Datasets*" in reference
    assert "https://harpd.com/data/" in reference


def test_apa_with_accessed_date() -> None:
    reference = citation.apa(title="T", url="u", accessed="2026-09-16")
    assert "(Accessed: 2026-09-16)" in reference


def test_apa_without_accessed_has_no_access_note() -> None:
    reference = citation.apa(title="T", url="u")
    assert "Accessed" not in reference


def test_whitespace_is_normalised() -> None:
    entry = citation.bibtex(key="k", title="A   very\n  spaced   title", url="u")
    assert "A very spaced title" in entry
    reference = citation.apa(title="A   very\n  spaced   title", url="u")
    assert "A very spaced title" in reference


def test_dataset_citation_returns_both_formats() -> None:
    result = citation.dataset_citation(
        dataset_name="Products",
        dataset_url="https://harpd.com/data/",
        accessed="2026-09-16",
        key="harpd-products",
    )
    assert set(result) == {"key", "title", "url", "bibtex", "apa"}
    assert result["key"] == "harpd-products"
    assert "Harpd AI Datasets: Products" in result["title"]
    assert result["bibtex"].startswith("@misc{harpd-products,")
    assert "Harpd AI Datasets: Products" in result["apa"]


def test_citation_cff_entry_shape() -> None:
    entry = citation.citation_cff_entry(
        title="Harpd AI Datasets", url="https://harpd.com/data/"
    )
    assert entry["type"] == "dataset"
    assert entry["year"] == 2026
    assert entry["license"] == "CC-BY-4.0"
    assert entry["authors"] == [{"name": "Harpd"}]
    assert entry["url"] == "https://harpd.com/data/"


def test_citation_block_contains_both_formats() -> None:
    block = citation.citation_block(
        title="Harpd AI Datasets",
        url="https://harpd.com/data/",
        accessed="2026-09-16",
        key="harpd-ai-datasets",
    )
    assert "## Citation" in block
    assert "### BibTeX" in block
    assert "```bibtex" in block
    assert "@misc{harpd-ai-datasets," in block
    assert "### APA" in block
    assert "Harpd. (2026)." in block
    assert "### Licence" in block
    assert "CC BY 4.0" in block
    assert citation.HARPD_DATA_HOME in block


def test_citation_block_bibtex_fence_is_closed() -> None:
    block = citation.citation_block(title="T", url="u", accessed="d", key="k")
    assert block.count("```") % 2 == 0


def test_no_third_party_usage_claim_is_made() -> None:
    """The repo must never assert that an external party uses this work."""
    block = citation.citation_block(title="T", url="u", accessed="d", key="k").lower()
    for phrase in ("cited by", "used by researchers", "adopted by", "as used in"):
        assert phrase not in block
