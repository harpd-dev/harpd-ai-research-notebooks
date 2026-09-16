"""Citation formatting: BibTeX, APA 7 and CITATION.cff entries.

Only real, resolvable resources are described here -- the Harpd open datasets
and the notebooks/reports in this repository. No third-party citations are
invented, and nothing claims that an external party has used this work.
"""

from __future__ import annotations

from typing import Any

__all__ = [
    "CITATION_YEAR",
    "DATASETS_REPO",
    "HARPD_HOME",
    "HARPD_DATA_HOME",
    "NOTEBOOKS_REPO",
    "apa",
    "bibtex",
    "citation_cff_entry",
    "citation_block",
    "dataset_citation",
]

CITATION_YEAR = "2026"

HARPD_HOME = "https://harpd.com"
HARPD_DATA_HOME = "https://harpd.com/data/"
DATASETS_REPO = "https://github.com/harpd-dev/harpd-ai-datasets"
NOTEBOOKS_REPO = "https://github.com/harpd-dev/harpd-ai-research-notebooks"

_PUBLISHER = "Harpd"


def _clean(text: str) -> str:
    return " ".join(str(text).split())


def bibtex(
    key: str,
    title: str,
    url: str,
    year: str = CITATION_YEAR,
    author: str = _PUBLISHER,
    note: str | None = None,
) -> str:
    """Render a BibTeX ``@misc`` entry."""
    lines = [
        f"@misc{{{key},",
        f"  author       = {{{author}}},",
        f"  title        = {{{_clean(title)}}},",
        f"  year         = {{{year}}},",
        f"  howpublished = {{\\url{{{url}}}}},",
        "  note         = {Open data, licensed CC BY 4.0}"
        if note is None
        else f"  note         = {{{_clean(note)}}}",
        f"  url          = {{{url}}}",
        "}",
    ]
    return "\n".join(lines)


def apa(
    title: str,
    url: str,
    year: str = CITATION_YEAR,
    author: str = _PUBLISHER,
    accessed: str | None = None,
) -> str:
    """Render an APA 7 reference string."""
    reference = f"{author}. ({year}). *{_clean(title)}*. {url}"
    if accessed:
        reference += f" (Accessed: {accessed})"
    return reference


def dataset_citation(
    dataset_name: str,
    dataset_url: str,
    accessed: str,
    key: str,
) -> dict[str, str]:
    """Convenience wrapper producing both BibTeX and APA for one dataset."""
    title = f"Harpd AI Datasets: {dataset_name}"
    return {
        "key": key,
        "title": title,
        "url": dataset_url,
        "bibtex": bibtex(key=key, title=title, url=dataset_url),
        "apa": apa(title=title, url=dataset_url, accessed=accessed),
    }


def citation_cff_entry(
    title: str,
    url: str,
    year: str = CITATION_YEAR,
    author: str = _PUBLISHER,
) -> dict[str, Any]:
    """A CITATION.cff-shaped ``preferred-citation`` mapping."""
    return {
        "type": "dataset",
        "title": _clean(title),
        "authors": [{"name": author}],
        "year": int(year),
        "url": url,
        "license": "CC-BY-4.0",
    }


def citation_block(
    title: str,
    url: str,
    accessed: str,
    key: str,
    year: str = CITATION_YEAR,
) -> str:
    """A complete markdown Citation section: BibTeX + APA + licence note.

    This is the block appended to the end of every generated report.
    """
    return "\n".join(
        [
            "## Citation",
            "",
            "If you use this report, cite the underlying datasets:",
            "",
            "### BibTeX",
            "",
            "```bibtex",
            bibtex(key=key, title=title, url=url, year=year),
            "```",
            "",
            "### APA",
            "",
            apa(title=title, url=url, year=year, accessed=accessed),
            "",
            "### Licence",
            "",
            "Dataset content is published under CC BY 4.0. Attribution: "
            f"{_PUBLISHER} ({HARPD_HOME}).",
            "",
            f"Canonical data home: <{HARPD_DATA_HOME}>",
            "",
        ]
    )
