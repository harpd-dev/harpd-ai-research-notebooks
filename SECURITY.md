# Security Policy

## Scope

This repository contains analysis code, notebooks and generated markdown reports.
It has no server, no user accounts and no database. The realistic security surface
is therefore small, and is limited to:

1. **Remote data fetching.** `harpd_research.loader` fetches JSON over HTTPS from
   public GitHub raw URLs and writes a local cache under `.cache/`.
2. **Notebook execution.** Notebooks run arbitrary Python when executed. Never
   execute a notebook from an untrusted source without reading it first.
3. **CI workflows.** `.github/workflows/` runs on GitHub-hosted runners with a
   scoped `GITHUB_TOKEN`.

## Supported versions

Only the `main` branch is supported. Fixes are applied there.

## Reporting a vulnerability

Please report security issues privately rather than in a public issue.

- Email: **harpdsupport@gmail.com**
- Or use GitHub's private vulnerability reporting on this repository
  (Security → Report a vulnerability).

Please include:

- what the issue is and where it lives (file, line, workflow),
- how to reproduce it,
- what an attacker could achieve,
- any suggested fix.

We aim to acknowledge reports within a few days.

## Design notes relevant to security

- **No credentials are required to run this repository.** Every dataset is public
  and read over plain HTTPS with no authentication.
- **No untrusted input is executed.** The loader parses JSON only. It does not
  evaluate code, and it does not deserialise pickles.
- **The cache is keyed by a hash** of the base URL and path
  (`sha256(f"{base}{path}")[:16]`), so a crafted path cannot escape the cache
  directory by traversal.
- **Reports are generated, never executed.** Markdown reports are rendered from
  computed values; they contain no script content.
- **Workflows do not run on untrusted forks with secrets.** `sync-and-report.yml`
  runs only on `schedule` and `workflow_dispatch`, not on `pull_request`, so a
  fork cannot trigger it with repository write access.
- **The sync workflow commits only generated files** (`reports/`, `notebooks/`)
  and restores the previous reports if any step fails.

## What is explicitly out of scope

- The accuracy of the published datasets. Correctness questions belong in an
  issue on the relevant dataset repository.
- Vulnerabilities in third-party dependencies. Report those upstream; we will
  still bump a pinned version if it affects this repository.
- Anything requiring an attacker to already have write access to the repository.
