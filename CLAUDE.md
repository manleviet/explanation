# CLAUDE.md

Guidance for Claude Code working in the **`explanation`** repository.

> **Skeleton (Phase 0).** Pointer-map + install only. Code-tracking docs
> (`system-architecture`, `codebase-summary`, `code-standards`) and a full
> `init` pass are generated **after** the port re-greens on flamapy 2.6 — see
> `plans/260719-phase-0-port/impl-plan.md` (step 10). Do not describe package
> internals here until then.

## What this repo is

Canonical **explanation framework** for [flamapy](https://flamapy.org): conflict
detection + diagnosis over feature models (FastDiag, FastDiagP, KBDiag, HS-DAG,
QuickXPlain) on the PySAT backend. Working repos (AcqMSS, DiagEnergy, KBDiag)
consume it via editable/remote install instead of vendoring a copy. Also feeds
the public flamapy plugin `flamapy-sat` (`pysat_metamodel`).

## Packages (three-tier, one-directional deps — enforced by `tests/test_boundary_guard.py`)

- `explanation/` — framework (models, operations/algorithms, transformations,
  checker port). Public façade: `explanation.api`.
- `profiling/` — neutral leaf (timing/metrics). Depends on nothing above it.
- App tier (conacq/quacq/etc.) lives in the **consuming** repos, never here.

Layering rules (ADR-0002): `explanation → profiling` only via the `profiling`
façade; `profiling` imports neither tier above it; `explanation` never imports
any app. Rationale in `docs/adr/`.

## Requirements & install

- Python **>= 3.11**. Deps resolve automatically: `flamapy-fw/fm/sat~=2.6.0.dev4`,
  `python-sat~=0.1.7.dev1`.
- Editable (local dev alongside a consuming repo):
  `pip install -e /path/to/explanation` (or `uv pip install -e …`).
- Remote pin (new machine / CI): `pip install "git+https://…/explanation.git@<tag>"`.
- See `README.md` for the full install matrix and reproducibility note.

## Tests

`PYTHONPATH=. python -m pytest tests/ -q`. Run `tests/test_boundary_guard.py`
first after any structural change — a red layering rule means a misplaced import.
Read every skip: a skipped test on a missing fixture is a **missing resource**,
not a pass.

## Map

- `docs/adr/` — architecture decision records (WHY the shape is what it is).
- `plans/` — this repo's implementation plans (Phase 0 port under
  `260719-phase-0-port/`).
