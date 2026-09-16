"""Tests over the committed artefacts: reports and notebooks.

These run against the files in the repository, so they catch a report or notebook
that was committed in a broken state.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

import pytest

from harpd_research.report import validate_report_text

EXPECTED_REPORTS = [
    "2026-09-ai-market-report.md",
    "2026-09-ai-ranking-report.md",
    "2026-09-ai-agent-report.md",
]

NOTEBOOK_SECTIONS = [
    "Question",
    "Dataset",
    "Method",
    "Analysis",
    "Visualization",
    "Findings",
    "Limitations",
    "Reproducibility",
    "Sources",
]


# --------------------------------------------------------------------------
# reports
# --------------------------------------------------------------------------


@pytest.mark.parametrize("filename", EXPECTED_REPORTS)
def test_expected_report_exists(reports_dir: Path, filename: str) -> None:
    assert (reports_dir / filename).is_file(), f"missing committed report {filename}"


@pytest.mark.parametrize("filename", EXPECTED_REPORTS)
def test_committed_report_has_all_required_sections(reports_dir: Path, filename: str) -> None:
    text = (reports_dir / filename).read_text(encoding="utf-8")
    missing = validate_report_text(text)
    assert missing == [], f"{filename} is missing {missing}"


@pytest.mark.parametrize("filename", EXPECTED_REPORTS)
def test_committed_report_has_citation_block(reports_dir: Path, filename: str) -> None:
    text = (reports_dir / filename).read_text(encoding="utf-8")
    assert "## Citation" in text
    assert "```bibtex" in text
    assert "@misc{" in text
    assert "### APA" in text
    assert "Harpd. (2026)." in text


@pytest.mark.parametrize("filename", EXPECTED_REPORTS)
def test_committed_report_has_nonzero_sample_size(reports_dir: Path, filename: str) -> None:
    text = (reports_dir / filename).read_text(encoding="utf-8")
    match = re.search(r"Records analysed: \*\*([\d,]+)\*\*", text)
    assert match, f"{filename} has no sample size line"
    assert int(match.group(1).replace(",", "")) > 0


@pytest.mark.parametrize("filename", EXPECTED_REPORTS)
def test_committed_report_has_a_data_timestamp(reports_dir: Path, filename: str) -> None:
    text = (reports_dir / filename).read_text(encoding="utf-8")
    assert re.search(r"Dataset `generatedAt`: `\d{4}-\d{2}-\d{2}T", text), (
        f"{filename} has no real data timestamp"
    )


@pytest.mark.parametrize("filename", EXPECTED_REPORTS)
def test_committed_report_states_the_placement_caveat(reports_dir: Path, filename: str) -> None:
    text = (reports_dir / filename).read_text(encoding="utf-8")
    assert "promotional placement bought with Credits" in text
    assert "NOT an editorial quality score" in text


@pytest.mark.parametrize("filename", EXPECTED_REPORTS)
def test_committed_report_never_claims_quality_ranking(reports_dir: Path, filename: str) -> None:
    """No report may describe a rankPoints ordering as a quality ranking."""
    text = (reports_dir / filename).read_text(encoding="utf-8").lower()
    for banned in (
        "best products",
        "top quality products",
        "highest quality",
        "quality ranking of products",
    ):
        assert banned not in text, f"{filename} contains banned phrase: {banned}"


@pytest.mark.parametrize("filename", EXPECTED_REPORTS)
def test_committed_report_links_the_dataset(reports_dir: Path, filename: str) -> None:
    text = (reports_dir / filename).read_text(encoding="utf-8")
    assert "harpd-ai-datasets" in text
    assert "harpd.com/data/" in text
    assert "CC BY 4.0" in text


# --------------------------------------------------------------------------
# notebooks
# --------------------------------------------------------------------------


def notebook_files(notebooks_dir: Path) -> list[Path]:
    return sorted(notebooks_dir.glob("*.ipynb"))


def test_seven_notebooks_exist(notebooks_dir: Path) -> None:
    files = notebook_files(notebooks_dir)
    assert len(files) == 7, f"expected 7 notebooks, found {len(files)}: {[f.name for f in files]}"


def test_notebook_filenames(notebooks_dir: Path) -> None:
    expected = {
        "01-ai-market-overview.ipynb",
        "02-ai-product-ranking-trends.ipynb",
        "03-ai-agent-market.ipynb",
        "04-ai-developer-tools.ipynb",
        "05-ai-tools-landscape.ipynb",
        "06-model-replacement-analysis.ipynb",
        "07-cost-per-successful-task.ipynb",
    }
    assert {f.name for f in notebook_files(notebooks_dir)} == expected


@pytest.mark.parametrize("path", notebook_files(Path(__file__).resolve().parents[1] / "notebooks"))
def test_notebook_has_required_sections_in_order(path: Path) -> None:
    notebook = json.loads(path.read_text(encoding="utf-8"))
    headings = []
    for cell in notebook["cells"]:
        if cell["cell_type"] != "markdown":
            continue
        for line in "".join(cell["source"]).splitlines():
            match = re.match(r"^##\s+(.+?)\s*$", line)
            if match:
                headings.append(match.group(1).strip())

    positions = []
    for section in NOTEBOOK_SECTIONS:
        assert section in headings, f"{path.name} is missing the '{section}' section"
        positions.append(headings.index(section))
    assert positions == sorted(positions), f"{path.name} sections are out of order: {headings}"


@pytest.mark.parametrize("path", notebook_files(Path(__file__).resolve().parents[1] / "notebooks"))
def test_notebook_has_code_cells(path: Path) -> None:
    notebook = json.loads(path.read_text(encoding="utf-8"))
    code_cells = [c for c in notebook["cells"] if c["cell_type"] == "code"]
    assert len(code_cells) >= 4, f"{path.name} has too few code cells"


@pytest.mark.parametrize("path", notebook_files(Path(__file__).resolve().parents[1] / "notebooks"))
def test_notebook_uses_the_shared_package(path: Path) -> None:
    """Logic must not be duplicated: notebooks import harpd_research."""
    notebook = json.loads(path.read_text(encoding="utf-8"))
    source = "\n".join("".join(c["source"]) for c in notebook["cells"] if c["cell_type"] == "code")
    assert "from harpd_research import" in source, f"{path.name} does not import harpd_research"


@pytest.mark.parametrize("path", notebook_files(Path(__file__).resolve().parents[1] / "notebooks"))
def test_notebook_states_the_placement_caveat(path: Path) -> None:
    notebook = json.loads(path.read_text(encoding="utf-8"))
    source = "\n".join("".join(c["source"]) for c in notebook["cells"])
    assert "PLACEMENT_CAVEAT" in source or "promotional placement" in source.lower(), (
        f"{path.name} does not state the promotional-placement caveat"
    )


def test_notebook_06_declares_the_missing_dataset(notebooks_dir: Path) -> None:
    """The model-replacement notebook must state the dataset is absent."""
    notebook = json.loads(
        (notebooks_dir / "06-model-replacement-analysis.ipynb").read_text(encoding="utf-8")
    )
    source = "\n".join("".join(c["source"]) for c in notebook["cells"])
    assert "not published" in source.lower() or "NOT published" in source
    assert "stub" in source.lower()
    assert "notClaimed" in source


def test_notebook_07_labels_the_data_as_modeled(notebooks_dir: Path) -> None:
    """The cost benchmark is a MODELED estimate and must be labelled as such."""
    notebook = json.loads(
        (notebooks_dir / "07-cost-per-successful-task.ipynb").read_text(encoding="utf-8")
    )
    source = "\n".join("".join(c["source"]) for c in notebook["cells"])
    assert "isModeled" in source
    assert "MODELED" in source


@pytest.mark.parametrize("path", notebook_files(Path(__file__).resolve().parents[1] / "notebooks"))
def test_notebook_has_executed_outputs(path: Path) -> None:
    """Notebooks are committed executed so GitHub renders real numbers."""
    notebook = json.loads(path.read_text(encoding="utf-8"))
    executed = [c for c in notebook["cells"] if c["cell_type"] == "code" and c.get("outputs")]
    assert executed, f"{path.name} has no executed outputs"
    assert any(c.get("execution_count") for c in executed), (
        f"{path.name} outputs are not from a real execution"
    )
