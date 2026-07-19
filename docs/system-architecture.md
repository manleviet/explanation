# System Architecture

Framework-scoped. Covers the two packages this repo ships — `explanation`
(framework) and `profiling` (leaf) — and their public contracts. The application
tier (conacq/quacq/congen) lives in consuming repos and is out of scope here.

## Tiers and dependency direction

```
application (conacq/quacq/…)   ── in CONSUMING repos ── uses ──▶ explanation.api, profiling
      │  (absent from this repo)
      ▼
explanation  (framework)       ── may use ──▶ profiling
      │
      ▼
profiling    (neutral leaf)    ── stdlib + itself only
```

One-directional, and each edge is narrow:

| From | To | Allowed surface |
|------|----|-----------------|
| application | `explanation` | **only** `explanation.api` (no deep paths, no `_private`) |
| application | `profiling` | **only** the `profiling` façade |
| `explanation` | `profiling` | **only** the `profiling` façade |
| `explanation` | application | **never** (framework is app-agnostic) |
| `profiling` | anything above | **never** (leaf) |

Enforced by `tests/test_boundary_guard.py` (AST, no imports): rule 3
(`explanation → profiling` façade-only), rule 4 (`explanation ⊥ application`),
rule 5 (`profiling` is a leaf). Rationale: ADR-0002. The two conacq-side rules of
the upstream guard are omitted here — they scan a `conacq/` tree that does not
exist in this repo and would pass vacuously.

## `explanation` — the framework

The public door is **`explanation.api`** (105 LOC, re-export only). It exposes
exactly what consumers use — the Task family, encoding free functions, the
checker port + `build_checker`, clause utilities, `QuickXPlain`, the operation
registry, and `FmToDiagPysat`. Nothing is re-exported "just in case".

Internal layers behind the façade:

- **models/** — pure data and its builders.
  - `task_preparation` — the immutable `Task` family (`Task` ABC → `DiagnosisTask`,
    `TestCaseTask`), `TaskInput` (validated, mutually-exclusive input factories),
    `PreparedTask` (task + `DescriptionProvider` + assignment map), and the
    `prepare_*` strategies that turn a model + input into a `PreparedTask`.
    Tasks are frozen dataclasses, deep-frozen at construction (list fields →
    tuples, `negation_map` → `FrozenDict`) — ADR-0012.
  - `diagnosis_model_builder` / `pysat_diagnosis_model` — build and hold a
    `DiagnosisModel`: the SAT-variable catalog (name↔id), constraint clause maps,
    and the next free assumption id.
  - `encoding` — free functions translating config↔literals and
    config→assumptions, given the KB's name↔id maps as parameters (the catalog
    lives in one place — the KB — not duplicated; ADR-0007).
  - `kb_protocol` — `KBProtocol`, the `@runtime_checkable` read-only name↔id
    contract every KB satisfies.
  - `frozen_dict`, `assumption_id_allocator`, `assignment_assumption_map`,
    `testsuite`, `abstract_model_builder` — supporting data types.
- **operations/** — the diagnosis/conflict/testcase/redundancy operations plus
  `algorithms/` (the reusable solvers) and `algorithms/hsdag/` (HS-DAG + its
  labelers). `registry` is an additive name→operation-class seam; built-ins
  register at import (`diagnosis`, `conflict`, `testcase`, `testcase_quickxplain`,
  `redundancy_constraints`, `redundancy_testcases`).
- **checker/** — the consistency-checker **port** (ADR-0004): `protocols`
  declares the narrow contracts; `backend` holds the solver adapters.
- **transformations/** — readers/converters that produce framework models from
  external formats (UVL feature model, DIMACS CNF, test-suite files).

### The checker port (ADR-0004, ADR-0013)

`checker/protocols.py` declares three `@runtime_checkable` Protocols, widening by
capability:

- `ConsistencyChecker` — `is_consistent(set_c)` (SAT/UNSAT only; drops disabled
  assumptions, safe under the one-way guard encoding), `find_model(set_c)` (a
  fully-pinned model, keeping disabled assumptions — ADR-0013), `cleanup()`.
- `TestCaseChecker` — adds `is_consistent_test_cases(...)` (KBDiag,
  QuickXPlainWithTestCases).
- `CopyableChecker` — adds `copy()` for parallel fan-out (FastDiagP).

`checker/backend.py` supplies the adapters — incremental PySAT, non-incremental
PySAT, and SAT4J (external jar at `solver_apps/org.sat4j.core.jar`) — behind one
construction door, `build_checker(task, backend=SolverBackend.…)`. The port
imports neither `pysat` nor `subprocess`; only the adapters do. Pinned by
`tests/test_solver_backend_port.py`.

### The traversal-order invariant

`FmToDiagPysat` assigns each feature a SAT variable id from flamapy's feature
**tree-traversal order** (not alphabetical). Every diagnosis is expressed in
those ids, so the order is load-bearing. It is pinned exactly — inline 65-feature
catalog for `arcade-game.uvl` — by
`tests/test_transformations_characterization.py`. A dependency bump that shifts
this order shifts every diagnosis; that test is the guard.

## `profiling` — the leaf

Neutral timing/metrics infrastructure, consumed via `from profiling import X`:
`Profiler` (concrete) / `ProfilerProtocol` (`@runtime_checkable`), `ProfilerMode`,
`NullProfiler`, `MetricType`, `measure_time`/`count_calls` decorators,
`ProfilerPreset`/`create_profiler`, and a global-profiler registry with
`profiler_session`. It depends on nothing above it (rule 5) and is pinned by
`tests/test_profiler.py`. Parallel-mode scaffolding (`ProfilerMode.MULTI_PROCESS`,
FastDiagP fan-out) is deferred to the canonical repo (ADR-0014), guarded by
`tests/test_parallel_scaffolding_guard.py`.

## Request flow — a diagnosis run (representative)

1. **Build model** — `DiagnosisModelBuilder.from_uvl(fm).with_positive_testcases(…)`
   → `DiagnosisModel` (via `FmToDiagPysat`: variable catalog + constraint maps +
   next assumption id).
2. **Prepare** — a `prepare_*` strategy turns model + `TaskInput` into a
   `PreparedTask` (frozen `Task` with `set_c`/`set_b`/… + a `DescriptionProvider`
   for human-readable output).
3. **Check** — `build_checker(task, backend=…)` yields a `ConsistencyChecker`
   adapter.
4. **Solve** — an algorithm (FastDiag / KBDiag / QuickXPlain / HS-DAG / WipeOutR)
   consumes the checker + task sets and returns the diagnosis/conflict in
   assumption ids.
5. **Describe** — the `DescriptionProvider` maps ids back to constraint names for
   display. Pinned end-to-end by `tests/test_diagnosis_*.py`.

## Invariants (with their pinning tests)

| Invariant | Pinned by |
|-----------|-----------|
| Package layering (façade-only, app-free leaf) | `test_boundary_guard.py` |
| FM→SAT-var-id traversal order | `test_transformations_characterization.py` |
| Task deep-immutability (tuples + FrozenDict) — ADR-0012 | `test_task_immutability.py` |
| Encoding round-trips / deterministic ordering | `test_encoding.py` |
| Checker port satisfied by all backends; `is_consistent`≠`find_model` (ADR-0013) | `test_solver_backend_port.py` |
| Per-algorithm diagnosis outputs | `test_diagnosis_{fastdiag,kbdiag,quickxplain,quickxplain_wtc,hsdag}.py` |
| Redundancy (WipeOutR) outputs | `test_diagnosis_redundancy.py` |
| Assumption-id allocation | `test_assumption_id_allocator.py` |
| Profiler behavior; parallel scaffolding present (ADR-0014) | `test_profiler.py`, `test_parallel_scaffolding_guard.py` |
