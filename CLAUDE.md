# CLAUDE.md

Guidance for Claude Code working in the **`explanation`** repository.

## What this repo is

Canonical **explanation framework** for [flamapy](https://flamapy.org): conflict
detection + diagnosis over feature models (FastDiag, FastDiagP, KBDiag, HS-DAG,
QuickXPlain, WipeOutR) on the PySAT backend, plus a SAT4J backend. Working repos
(AcqMSS, DiagEnergy, KBDiag) **consume** it via editable/remote install instead
of vendoring a copy. It also feeds the public flamapy plugin `flamapy-sat`
(`pysat_metamodel`).

This repo ships **framework code only**. The application tier (conacq / quacq /
congen, oracle, bias, evaluation) lives in the consuming repos and is *not*
present here — docs and code must not describe it as in-repo.

## Architecture (three tiers, one-directional deps)

```
application (conacq/quacq/…)   ── in CONSUMING repos ── uses ──▶ explanation.api, profiling
      │  (not in this repo)
      ▼
explanation  (framework)       ── may use ──▶ profiling
      │
      ▼
profiling    (neutral leaf)    ── stdlib + itself only
```

- **Single public door:** `explanation.api` (façade). Consumers must not reach
  into `explanation.models.*` / `.operations.*` / `.transformations.*`, nor
  import underscore-private names.
- **Leaf:** `profiling` imports neither tier above it.
- Rules are enforced as an AST test — `tests/test_boundary_guard.py` (rules
  3/4/5: `explanation → profiling` façade-only, `explanation ⊥ app`, `profiling`
  is a leaf). Run it first after any structural change. Rationale: `docs/adr/`
  (ADR-0002).

## Package map

`explanation/` (framework)
- `api.py` — the public façade (only import surface for consumers).
- `models/` — pure data + builders: `task_preparation` (frozen `Task` family,
  `TaskInput`, `PreparedTask`, prepare_* helpers), `diagnosis_model_builder`,
  `pysat_diagnosis_model`, `encoding` (name↔id free functions), `frozen_dict`,
  `kb_protocol`, `assumption_id_allocator`, `assignment_assumption_map`,
  `testsuite`, `abstract_model_builder`.
- `operations/` — diagnosis/conflict/testcase/redundancy operations + the
  `registry` (name→op plugin seam); `algorithms/` (fastdiag, fastdiagp, kbdiag,
  quickxplain(+_with_testcases), wipeoutr_fm/_t, utils) and `algorithms/hsdag/`
  (hsdag, node, `labeler/`).
- `checker/` — the consistency-checker **port**: `protocols` (ConsistencyChecker
  / TestCaseChecker / CopyableChecker) + `backend` (PySAT incremental /
  non-incremental / SAT4J adapters, `SolverBackend`, `build_checker`). ADR-0004.
- `transformations/` — `fm_to_diag_pysat` (FeatureModel→DiagnosisModel),
  `dimacs_to_diag_pysat`, `dimacs_to_configuration`, `testsuite_reader`.

`profiling/` (leaf) — `Profiler`/`ProfilerProtocol`, `ProfilerMode`,
`NullProfiler`, decorators, `ProfilerPreset`, global-profiler registry +
`profiler_session`. Consumed via `from profiling import X`.

## Requirements & install

- Python **>= 3.11**. Exact-pinned deps (see `pyproject.toml`):
  `flamapy-fw/fm/sat==2.6.0.dev4`, `python-sat==0.1.8.dev17`.
  Pins are `==`, not `~=`: `~=2.6.0.dev4` floats onto flamapy **2.6.0 final**,
  whose uvl_reader breaks the suite; and PEP 440 orders dev4 < 2.6.0.
- Editable (dev alongside a consuming repo): `pip install -e /path/to/explanation`
  (or `uv pip install -e …`). Then delete the consuming repo's old in-repo
  `explanation/` copy so it doesn't shadow the install.
- Remote pin (new machine / CI): `pip install "git+https://…/explanation.git@<tag>"`.
- Full install matrix + reproducibility note: `README.md`.

## Tests

`PYTHONPATH=. python -m pytest tests/ -q` (275 tests). Layout:
`tests/test_diagnosis_*` (per-algorithm, share `diagnosis_helpers.py`),
`test_transformations_characterization` (pins the FM→SAT-var-id **traversal
order** — the invariant every diagnosis depends on), `test_solver_backend_port`,
`test_encoding`, `test_task_immutability`, `test_profiler`, `test_boundary_guard`,
+ fixtures under `tests/resources/`.

- Run `test_boundary_guard.py` first after structural changes.
- **Read every skip:** a skip on a missing fixture is a missing resource, not a
  pass.
- Behavior is pinned by characterization tests (exact literal outputs). When a
  dependency bump shifts output, re-pin to the new *verified* value — never relax
  an assertion.

## Map

- `docs/system-architecture.md` — tiers, dependency rules, request flows.
- `docs/codebase-summary.md` — package/module inventory + entry points.
- `docs/code-standards.md` — conventions the code follows.
- `docs/adr/` — architecture decision records (WHY the shape is what it is).
- `plans/` — this repo's implementation plans (Phase 0 port under
  `260719-phase-0-port/`).

## Working here

- Framework source (`explanation/`, `profiling/`) is byte-matched to its upstream
  redesign; keep changes minimal and test-pinned.
- Do not introduce application-tier concepts (conacq/oracle/bias) into the
  framework — the boundary guard will fail, and it is protecting a real invariant
  (ADR-0002).
- ADRs are immutable once accepted; supersede, don't edit.
