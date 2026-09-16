"""Markdown report rendering.

Reports are a deterministic projection of the analysis layer: the same inputs
always produce byte-identical output, which is what makes
``scripts/generate_reports.py`` idempotent.

Fail-closed rule: :func:`render_report` refuses to emit a report whose sample
size is zero or whose dataset timestamp is missing. A missing dataset must never
degrade into an empty-but-plausible report.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any

import pandas as pd

from . import citation
from .analysis import PLACEMENT_CAVEAT

__all__ = [
    "REQUIRED_SECTIONS",
    "ReportData",
    "ReportError",
    "render_report",
    "validate_report_text",
]

#: Every generated report must contain each of these headings.
REQUIRED_SECTIONS = [
    "Data timestamp",
    "Sample size",
    "Methodology",
    "Limitations",
    "Dataset link",
    "Source",
    "Reproduction instructions",
    "Citation",
]


class ReportError(RuntimeError):
    """Raised when a report cannot be produced from the supplied data."""


@dataclass
class ReportData:
    """Everything needed to render one report."""

    slug: str
    title: str
    question: str
    dataset_name: str
    dataset_path: str
    dataset_url: str
    generated_at: str
    last_updated: str
    sample_size: int
    methodology: list[str]
    limitations: list[str]
    findings: list[str]
    tables: list[tuple[str, pd.DataFrame]] = field(default_factory=list)
    extra_notes: list[str] = field(default_factory=list)
    citation_key: str = "harpd-ai-datasets"
    citation_title: str = "Harpd AI Datasets"
    accessed: str = ""

    def __post_init__(self) -> None:
        if not self.slug:
            raise ReportError("ReportData.slug is required")
        if not self.citation_key:
            raise ReportError("ReportData.citation_key is required")


def _table_to_markdown(frame: pd.DataFrame, index: bool = False) -> str:
    if frame is None or frame.empty:
        return "_No rows returned by this computation._"
    try:
        return frame.to_markdown(index=index)
    except ImportError:  # tabulate is optional; fall back to a plain grid.
        header = "| " + " | ".join(str(c) for c in frame.columns) + " |"
        divider = "| " + " | ".join("---" for _ in frame.columns) + " |"
        rows = [
            "| " + " | ".join("" if pd.isna(v) else str(v) for v in row) + " |"
            for row in frame.itertuples(index=False)
        ]
        return "\n".join([header, divider, *rows])


def _bullets(items: list[str]) -> str:
    if not items:
        return "_None recorded._"
    return "\n".join(f"- {item}" for item in items)


def render_report(data: ReportData) -> str:
    """Render a report to markdown, or raise :class:`ReportError`.

    Refuses to render when the sample size is zero or the data timestamp is
    blank -- the fail-closed guarantee the scheduled workflow depends on.
    """
    if data.sample_size is None or data.sample_size <= 0:
        raise ReportError(
            f"{data.slug}: refusing to render a report with sample_size="
            f"{data.sample_size!r}. No data means no report."
        )
    if not str(data.generated_at or "").strip():
        raise ReportError(f"{data.slug}: refusing to render without a data timestamp.")
    if not str(data.last_updated or "").strip():
        raise ReportError(f"{data.slug}: refusing to render without lastUpdated.")
    if not str(data.accessed or "").strip():
        raise ReportError(
            f"{data.slug}: refusing to render without a snapshot date derived from "
            "the data. A wall-clock fallback would break idempotency."
        )

    parts: list[str] = [
        f"# {data.title}",
        "",
        f"**Question.** {data.question}",
        "",
        f"> **Domain caveat.** {PLACEMENT_CAVEAT}",
        "",
        "## Data timestamp",
        "",
        f"- Dataset `generatedAt`: `{data.generated_at}`",
        f"- Dataset `lastUpdated`: `{data.last_updated}`",
        f"- Snapshot date used for this report: `{data.accessed}`",
        "",
        "The snapshot date is taken from the dataset itself, not from the clock at",
        "render time. Re-running the generator against an unchanged snapshot",
        "reproduces this file byte for byte.",
        "",
        "## Sample size",
        "",
        f"- Records analysed: **{data.sample_size:,}**",
        "",
        "## Methodology",
        "",
        _bullets(data.methodology),
        "",
    ]

    if data.tables:
        parts.append("## Analysis")
        parts.append("")
        for caption, frame in data.tables:
            parts.append(f"### {caption}")
            parts.append("")
            parts.append(_table_to_markdown(frame))
            parts.append("")

    parts.extend(["## Findings", "", _bullets(data.findings), ""])

    if data.extra_notes:
        parts.append("## Notes")
        parts.append("")
        parts.append(_bullets(data.extra_notes))
        parts.append("")

    parts.extend(
        [
            "## Limitations",
            "",
            _bullets(data.limitations),
            "",
            "## Dataset link",
            "",
            f"- `{data.dataset_path}`",
            f"- <{data.dataset_url}>",
            f"- Registry: <{citation.DATASETS_REPO}>",
            "",
            "## Source",
            "",
            f"- Publisher: {citation.HARPD_HOME}",
            f"- Data home: <{citation.HARPD_DATA_HOME}>",
            f"- Raw base: `{citation.DATASETS_REPO}` (branch `main`)",
            "- Licence: CC BY 4.0",
            "",
            "## Reproduction instructions",
            "",
            "```bash",
            "git clone https://github.com/harpd-dev/harpd-ai-research-notebooks",
            "cd harpd-ai-research-notebooks",
            "python -m venv .venv && . .venv/bin/activate",
            "pip install -r requirements.txt",
            "python scripts/generate_reports.py",
            "```",
            "",
            "To reproduce offline against a local clone of the datasets:",
            "",
            "```bash",
            "HARPD_DATA_BASE=/path/to/harpd-ai-datasets/ python scripts/generate_reports.py",
            "```",
            "",
        ]
    )

    parts.append(
        citation.citation_block(
            title=data.citation_title,
            url=data.dataset_url,
            accessed=data.accessed,
            key=data.citation_key,
        )
    )
    return "\n".join(parts)


def validate_report_text(text: str) -> list[str]:
    """Return the list of required sections missing from a report body."""
    missing = []
    for section in REQUIRED_SECTIONS:
        if not re.search(rf"^#+\s*{re.escape(section)}\s*$", text, flags=re.MULTILINE):
            missing.append(section)
    if "```bibtex" not in text:
        missing.append("BibTeX citation block")
    if not re.search(r"^###\s+APA\s*$", text, flags=re.MULTILINE):
        missing.append("APA citation block")
    return missing


def report_metadata(data: ReportData) -> dict[str, Any]:
    """Small machine-readable summary used by tests and the sync workflow."""
    return {
        "slug": data.slug,
        "title": data.title,
        "sample_size": data.sample_size,
        "generated_at": data.generated_at,
        "last_updated": data.last_updated,
        "dataset_path": data.dataset_path,
        "tables": len(data.tables),
        "findings": len(data.findings),
    }
