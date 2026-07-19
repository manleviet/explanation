# Project Roadmap

Framework-scoped. Tracks work owned by **this** repo. Application-tier work
(conacq/quacq/congen, evaluation pipelines, paper tables) is tracked in the
consuming repos — see the scope note at the bottom.

Status legend: ✅ done · 🔜 next · ⏸ deferred (with the decision that deferred it)
· ❓ awaiting ratification

## ✅ Phase 0 — Port the framework out of AcqMSS

Completed 2026-07-19 (`92265be`, `1b5a924`).

| Item | Evidence |
|------|----------|
| 56 framework sources ported byte-matched to the AcqMSS redesign | `explanation/` (50 modules, 5,741 LOC) + `profiling/` (6 modules, 1,244 LOC) |
| Test suite ported + green | `PYTHONPATH=. python -m pytest tests/ -q` → **275 passed** |
| Layering enforced, not just documented | `tests/test_boundary_guard.py` (3 framework rules; ADR-0002) |
| Dependencies pinned exactly, clean-venv verified | `pyproject.toml` (`==2.6.0.dev4` ×3, `python-sat==0.1.8.dev17`) |
| 11 framework ADRs ported; app-scoped ADRs left in AcqMSS | `docs/adr/` + index note |
| Framework docs + README install matrix | `docs/`, `README.md` |

Plan and reports: `plans/260719-phase-0-port/`.

## 🔜 Phase 1 — Consumer rollout

Switch the working repos off their vendored copies and onto this one. No
framework code changes; this is a migration of consumers.

- **AcqMSS** — `pip install -e /path/to/explanation`, then delete the in-repo
  `explanation/` copy so it does not shadow the install. Imports stay
  `from explanation. …`.
- **DiagEnergy** — same, plus an import rewrite: `diagenergy.diagnosis.` →
  `explanation.`.
- **KBDiag** — same editable install.
- **Exit criteria** — each consumer's suite green against the installed package,
  with no in-repo `explanation/` directory remaining.

Install methods and the trade-offs between them: `README.md` § Installation.

## ⏸ Phase 2 — Parallel executor (ADR-0014)

The one substantial engineering item **explicitly deferred to this repo**. The
2026-06-22 canonical decision ruled it out of AcqMSS ("to be done AFTER
migration, not on the prototype"); Phase 0 is that migration, so this is now
unblocked.

Scope, per ADR-0014:

1. `ConsistencyExecutor` Protocol + `ProcessExecutor` (shared pool) +
   `MemoizingExecutor` (in-flight dedup).
2. Rewrite `FastDiagP` to consume an injected executor instead of a bare
   `mp.Pool`.
3. Fix the **FastDiagP speculative consistency-check double-count** — the
   lookahead submits a CC the main path may re-derive, and worker-process
   profiler increments are lost. Recorded in ADR-0014 as carried debt, not a
   live-path defect (FastDiagP is test-only today).
4. Node-level parallelism for HS-DAG and WipeOutR — the reason parallelism gets
   **one** home rather than a per-algorithm solution.

The scaffolding is already here and deliberately kept: `IHSLabelable.get_instance`
(0-caller — its driver is this work), `ProfilerMode.MULTI_PROCESS` + the
`Manager.dict` path, and `CopyableChecker.copy()` (which *does* run today).
`tests/test_parallel_scaffolding_guard.py` stops a tidy-up sweep from deleting
half a design. **Read ADR-0014 before touching any of the three.**

## ⏸ Phase 3 — Release

- **`v0.1.0` tag** — needed for reproducible pinning. Editable installs float on
  working-copy state, so freezing results for a paper requires tagging the
  framework and recording the tag in the experiment repo (`README.md` §
  Reproducibility note).
- **PyPI publish** — `README.md` documents this as case 4 ("once published:
  `pip install explanation`"). Until then, consumers use `git+https://…@<tag>`.

## ❓ Open questions

1. **`python-sat` pin — ratify.** Pinned `==0.1.8.dev17`: the prescribed
   `0.1.7.dev1` has no wheel on this platform and fails to build from source
   (`ld: library 'cadical' not found`), and `0.1.8.dev17` is what the
   reviewed-green suite actually ran on. Confirm, or require `0.1.7.dev1` plus a
   documented `cadical` source-build prerequisite — a one-line revert either way.
   Detail: `plans/260719-phase-0-port/phase-0-port-execution-report.md`.
2. **`TestSuiteReader` collection warnings** — 4 benign pytest warnings from a
   class whose name starts with `Test` but is not a test. Left as pre-existing
   framework naming. Rename (with the ripple through imports) or silence?

## Out of scope for this repo

The application tier is not here and is not this roadmap's business:
conacq/quacq/congen, oracle/bias builders, the evaluation pipeline, and paper
tables. The application-scoped ADRs (**0005**, **0006**, **0008**, **0015**,
**0016**, **0017**) live in AcqMSS, along with the work they track. This repo's
ADR set is the 11 framework decisions indexed in `docs/adr/README.md`.
