"""Harpd research toolkit: load, analyse, and report on Harpd open data.

This package is the single source of truth for the logic used by both the
notebooks in ``notebooks/`` and the report generator in
``scripts/generate_reports.py``. Nothing is duplicated between the two, so a
number that appears in a report and a number that appears in a notebook come
from the same code path.

Example
-------
>>> from harpd_research import loader, analysis
>>> products = loader.load_products()
>>> analysis.placement_concentration(products)["totalProducts"]
1122

Domain rule: ``rankPoints`` is **promotional placement bought with Credits**, not
an editorial quality score. See :data:`harpd_research.analysis.PLACEMENT_CAVEAT`.
"""

from __future__ import annotations

from . import analysis, citation, loader, report

__all__ = ["analysis", "citation", "loader", "report", "__version__"]

__version__ = "1.0.0"
