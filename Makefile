# Harpd AI Research Notebooks
#
#   make install     create .venv and install dependencies
#   make notebooks   execute every notebook in place
#   make reports     regenerate reports/ from live data
#   make test        run the test suite
#   make lint        run ruff
#   make check       lint + test + report dry-run (what CI runs)
#   make clean       remove caches and execution artefacts

PYTHON ?= python3
VENV   := .venv
BIN    := $(VENV)/bin
NOTEBOOKS := $(wildcard notebooks/*.ipynb)

# Point at a local clone of the datasets to run fully offline, e.g.
#   make reports HARPD_DATA_BASE=../harpd-ai-datasets/
HARPD_DATA_BASE ?=
export HARPD_DATA_BASE

.PHONY: help install notebooks reports reports-check test lint lint-fix check clean

help:
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) \
		| awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-16s\033[0m %s\n", $$1, $$2}'

$(BIN)/python:
	$(PYTHON) -m venv $(VENV)
	$(BIN)/pip install --upgrade pip
	$(BIN)/pip install -r requirements.txt

install: $(BIN)/python ## Create the virtualenv and install dependencies

notebooks: install ## Execute every notebook in place
	@for nb in $(NOTEBOOKS); do \
		echo "executing $$nb"; \
		$(BIN)/jupyter nbconvert --to notebook --execute --inplace \
			--ExecutePreprocessor.timeout=600 "$$nb" || exit 1; \
	done
	@echo "all notebooks executed"

reports: install ## Regenerate every report in reports/
	$(BIN)/python scripts/generate_reports.py

reports-check: install ## Validate reports can be produced, without writing
	$(BIN)/python scripts/generate_reports.py --check

test: install ## Run the test suite
	$(BIN)/pytest

lint: install ## Lint with ruff
	$(BIN)/ruff check .
	$(BIN)/ruff format --check .

lint-fix: install ## Lint and apply safe fixes
	$(BIN)/ruff check --fix .
	$(BIN)/ruff format .

check: lint test reports-check ## Lint, test and validate reports (CI parity)

clean: ## Remove caches and execution artefacts
	rm -rf .pytest_cache .ruff_cache .cache
	find . -name '__pycache__' -type d -prune -exec rm -rf {} +
	find . -name '.ipynb_checkpoints' -type d -prune -exec rm -rf {} +
