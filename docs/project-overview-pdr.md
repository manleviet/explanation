# Project Overview & Development Requirements

What this repo is for, who consumes it, what it must guarantee, and what it
deliberately refuses to do. For *how* it is shaped, see
`docs/system-architecture.md`; for *why* it is shaped that way, see `docs/adr/`.

## Problem

Conflict detection and diagnosis over feature models (FastDiag, KBDiag, HS-DAG,
QuickXPlain, WipeOutR) was implemented **inside** a research prototype (AcqMSS)
and then copied into every repo that needed it. Three vendored copies drifted:
a fix landed in one, a paper's numbers came from another, and nothing pinned
which copy produced which result.

## Purpose

Be the **single canonical source** of that framework. Working repos (AcqMSS,
DiagEnergy, KBDiag) install it instead of vendoring it. It also feeds the public
flamapy plugin `flamapy-sat` (`pysat_metamodel`).

## Consumers and what each needs

| Consumer | Needs |
|----------|-------|
| AcqMSS / DiagEnergy / KBDiag | Diagnosis + conflict operations, callable from an application tier the framework knows nothing about |
| `flamapy-sat` (`pysat_metamodel`) | Operations that fit flamapy's plugin shape |
| Paper / experiment reproduction | A pinnable version whose outputs are byte-stable across machines |

The third is the demanding one: a "small cleanup" that reorders SAT variable ids
silently changes every published diagnosis. That constraint drives most of the
requirements below.

## Scope

**In scope** — the framework tier only:

- **Operations** (registry names): `diagnosis`, `conflict`, `testcase`,
  `testcase_quickxplain`, `redundancy_constraints`, `redundancy_testcases`.
- **Algorithms**: FastDiag, FastDiagP, KBDiag, QuickXPlain (+ with-test-cases),
  HS-DAG with pluggable labelers, WipeOutR (FM and T variants).
- **Inputs**: UVL feature models, DIMACS CNF, test-suite files.
- **Solver backends**: PySAT incremental (default), PySAT non-incremental, SAT4J
  (external jar, needs a JVM).
- **`profiling`**: neutral timing/metrics infrastructure, shipped as a separate
  top-level leaf package (ADR-0003).

**Out of scope — deliberately.** The application tier: conacq / quacq / congen,
oracle and bias construction, the evaluation pipeline, result extraction, paper
tables. These live in consuming repos. This is not a layering preference; it is
enforced (see R2) because a framework that knows about `conacq` cannot be reused
by DiagEnergy.

## Requirements

**R1 — One public door.** Consumers import `explanation.api` and `profiling`,
nothing else. No deep paths (`explanation.models.*`, `explanation.operations.*`),
no `_underscore` names across a tier. A symbol is added to the façade when a
consumer needs it, never "just in case".

**R2 — One-directional layering.** `application → explanation → profiling`.
`explanation` never imports the application tier; `profiling` imports nothing
above it. *Verified by* `tests/test_boundary_guard.py` — an AST check, so it
catches a violating import without executing it (ADR-0002).

**R3 — Byte-stable outputs.** `FmToDiagPysat` assigns SAT variable ids in
flamapy's feature **tree-traversal order**, not alphabetically. Every diagnosis
is expressed in those ids, so the order is load-bearing. *Verified by*
`tests/test_transformations_characterization.py`, which pins the full 65-feature
id catalog for `arcade-game.uvl`.

**R4 — Reproducible dependency resolution.** Pins are exact (`==`), never `~=`.
`~=2.6.0.dev4` resolves to `==2.6.*` and floats onto flamapy 2.6.0 final, whose
`uvl_reader` breaks the suite; PEP 440 also orders `dev4 < 2.6.0`. See
`pyproject.toml` and `docs/code-standards.md` § Dependencies.

**R5 — Immutability at construction.** The `Task` family is frozen dataclasses,
deep-frozen in `__post_init__` (lists → tuples, mappings → `FrozenDict`).
`FrozenDict` rather than `MappingProxyType` because FastDiagP ships tasks to
worker processes and they must **pickle**. *Verified by*
`tests/test_task_immutability.py` (ADR-0012).

**R6 — Solver-agnostic algorithms.** Algorithms depend on the narrow checker
*port* (`ConsistencyChecker` → `TestCaseChecker` → `CopyableChecker`, widening by
capability); solver specifics live in adapters behind `build_checker`. The port
imports neither `pysat` nor `subprocess`. *Verified by*
`tests/test_solver_backend_port.py` (ADR-0004).

**R7 — Reasoning is recorded.** Every non-obvious structural choice gets an ADR
before the next person "tidies" it. ADRs are immutable once accepted — supersede,
never edit.

## Constraints

- Python **>= 3.11**.
- flamapy `2.6.0.dev4` (a dev build, not a release) — the framework is verified
  against it; the final 2.6.0 is known-broken for this suite.
- `python-sat==0.1.8.dev17` — pending ratification (see
  `docs/project-roadmap.md` § Open questions).
- SAT4J backend needs a JVM and `solver_apps/org.sat4j.core.jar` (344 KB),
  resolved relative to the working directory. The default PySAT path needs
  neither.
- `profiling` must remain **stdlib-only**.

## Quality gates

- `PYTHONPATH=. python -m pytest tests/ -q` — currently **275 passed**.
- Run `tests/test_boundary_guard.py` **first** after any structural change; it is
  the cheapest signal that a refactor broke the architecture.
- Behavior is pinned by characterization tests asserting exact literal outputs.
  When a dependency bump shifts an output, re-pin to the new **verified** value
  and cite the evidence — never relax the assertion.
- **Read every skip.** A skipped test on a missing fixture is a missing resource,
  not a pass.

## Success criteria

1. No consuming repo keeps a vendored `explanation/` copy (Phase 1 of the
   roadmap).
2. A published result can be reproduced from a recorded framework tag + the
   experiment repo.
3. A new algorithm or solver backend is added without editing the façade's
   existing exports or any consumer.
4. The boundary guard has never been weakened to make a change pass.
