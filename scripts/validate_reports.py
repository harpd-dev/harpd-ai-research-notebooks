#!/usr/bin/env python
"""Validate the committed reports in ``reports/``.

Checks that every expected report exists, carries all required sections, a
non-zero sample size, a real data timestamp, the promotional-placement caveat,
and a complete Citation block (BibTeX + APA).

Exit code is non-zero if any check fails, so this can gate CI.

Usage
-----
    python scripts/validate_reports.py
    python scripts/validate_reports.py --reports-dir reports
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from harpd_research.report import REQUIRED_SECTIONS, validate_report_text  # noqa: E402

EXPECTED_REPORTS = [
    "2026-09-ai-market-report.md",
    "2026-09-ai-ranking-report.md",
    "2026-09-ai-agent-report.md",
]

#: Phrases that would indicate a rankPoints ordering presented as quality.
#: Note: "editorial quality score" is deliberately absent here — it appears
#: legitimately inside the required caveat ("NOT an editorial quality score").
#: It is checked separately, line by line, below.
BANNED_PHRASES = [
    "best products",
    "highest quality",
    "top quality products",
    "quality ranking of products",
]

#: Phrases that would indicate a fabricated external endorsement.
FABRICATION_PHRASES = [
    "cited by",
    "used by researchers",
    "adopted by",
    "as used in",
    "peer reviewed",
]


def validate_report(path: Path) -> list[str]:
    """Return a list of problems with one report. Empty means valid."""
    problems: list[str] = []

    if not path.is_file():
        return [f"{path.name}: file is missing"]

    text = path.read_text(encoding="utf-8")

    for section in validate_report_text(text):
        problems.append(f"{path.name}: missing required section '{section}'")

    match = re.search(r"Records analysed: \*\*([\d,]+)\*\*", text)
    if not match:
        problems.append(f"{path.name}: no 'Records analysed' sample size line")
    elif int(match.group(1).replace(",", "")) <= 0:
        problems.append(f"{path.name}: sample size is zero — an empty report")

    if not re.search(r"Dataset `generatedAt`: `\d{4}-\d{2}-\d{2}T", text):
        problems.append(f"{path.name}: no real dataset timestamp")

    if not re.search(r"Snapshot date used for this report: `\d{4}-\d{2}-\d{2}`", text):
        problems.append(f"{path.name}: no snapshot date (idempotency anchor)")

    if "promotional placement bought with Credits" not in text:
        problems.append(f"{path.name}: missing the promotional-placement caveat")

    lowered = text.lower()
    for phrase in BANNED_PHRASES:
        if phrase in lowered:
            problems.append(f"{path.name}: contains quality-ranking phrasing '{phrase}'")

    for phrase in FABRICATION_PHRASES:
        if phrase in lowered:
            problems.append(f"{path.name}: contains unsupported endorsement '{phrase}'")

    # The caveat line legitimately contains "quality score", so only flag the
    # phrase when it appears outside that sentence.
    for line in text.splitlines():
        if "editorial quality score" in line.lower() and "NOT an editorial" not in line:
            problems.append(f"{path.name}: 'editorial quality score' used outside the caveat")

    return problems


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--reports-dir",
        default=str(ROOT / "reports"),
        help="directory containing the markdown reports",
    )
    args = parser.parse_args(argv)

    reports_dir = Path(args.reports_dir)
    if not reports_dir.is_dir():
        print(f"FAIL: reports directory not found: {reports_dir}", file=sys.stderr)
        return 1

    print(f"Validating reports in {reports_dir}")
    print(f"Required sections: {len(REQUIRED_SECTIONS)}")
    print()

    all_problems: list[str] = []
    for filename in EXPECTED_REPORTS:
        path = reports_dir / filename
        problems = validate_report(path)
        if problems:
            print(f"FAIL {filename}")
            for problem in problems:
                print(f"       {problem}")
        else:
            size = path.stat().st_size
            print(f"PASS {filename} ({size:,} bytes)")
        all_problems.extend(problems)

    # Any additional report present must also be valid.
    for path in sorted(reports_dir.glob("*.md")):
        if path.name in EXPECTED_REPORTS:
            continue
        problems = validate_report(path)
        if problems:
            print(f"FAIL {path.name} (unexpected report)")
            for problem in problems:
                print(f"       {problem}")
            all_problems.extend(problems)
        else:
            print(f"PASS {path.name} (additional report)")

    print()
    if all_problems:
        print(f"FAILED with {len(all_problems)} problem(s)", file=sys.stderr)
        return 1

    print(f"All {len(EXPECTED_REPORTS)} reports valid.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
