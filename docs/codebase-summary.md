# Codebase Summary

Framework-scoped inventory of the `explanation` repo. Two shipped packages —
`explanation` (5,741 LOC, 50 modules) and `profiling` (1,244 LOC, 6 modules) —
plus the test suite and fixtures. The application tier (conacq/quacq/congen) is
not in this repo.

## `explanation/` (framework)

### Public façade
- `api.py` (105) — the single import surface for consumers. Re-exports the Task
  family + prepare helpers, encoding free functions, `AssignmentAssumptionMap`,
  `KBProtocol`, `AbstractModelBuilder`, the checker port (`ConsistencyChecker`,
  `TestCaseChecker`, `CopyableChecker`, `SolverBackend`, `build_checker`,
  `SolverTimeoutError`), clause utils (`split`, `diff`, `negate_cnf_tseitin`),
  `QuickXPlain`, the operation registry, and `FmToDiagPysat`.

### `models/` — data + builders
| Module | LOC | Responsibility |
|--------|-----|----------------|
| `task_preparation.py` | 714 | frozen `Task` family, `TaskInput`, `PreparedTask`, `DescriptionProvider`, `prepare_*` strategies + factory |
| `diagnosis_model_builder.py` | 381 | fluent `DiagnosisModelBuilder` (`from_uvl` / `from_dimacs` / `with_*_testcases`) |
| `pysat_diagnosis_model.py` | 115 | `DiagnosisModel` — variable catalog + constraint maps + next assumption id |
| `testsuite.py` | 92 | `TestSuite`, `TestCase`, `Assignment` |
| `encoding.py` | 58 | config↔literal / config→assumption free functions |
| `abstract_model_builder.py` | 46 | builder base (consumers' oracle/bias builders inherit) |
| `assumption_id_allocator.py` | 44 | assumption-id allocation |
| `frozen_dict.py` | 30 | `FrozenDict` — immutable, picklable dict for deep-freeze |
| `assignment_assumption_map.py` | 28 | assignment↔assumption mapping |
| `kb_protocol.py` | 27 | `KBProtocol` structural contract |
| `__init__.py` | 31 | internal package exports |

### `operations/` — operations, algorithms, registry
| Module | LOC | Responsibility |
|--------|-----|----------------|
| `pysat_explanation_builder.py` | 437 | assembles explanation operations |
| `pysat_abstract_hsdag_explanation.py` | 269 | HS-DAG-based explanation base + `_format_results` |
| `registry.py` | 56 | name→operation-class seam; built-ins register at import |
| `pysat_redundancy_constraints.py` / `_testcases.py` | 89 / 83 | redundancy operations (first-class `execute()`) |
| `pysat_testcase.py` / `_testcase_quickxplain.py` | 86 / 64 | test-case operations |
| `pysat_conflict.py` / `pysat_diagnosis.py` | 74 / 73 | conflict / diagnosis operations |
| `pysat_abstract_explanation.py` | 52 | operation base class |

`operations/algorithms/` — reusable solvers: `fastdiagp.py` (236, parallel),
`quickxplain_with_testcases.py` (194), `kbdiag.py` (142), `wipeoutr_t.py` (135),
`utils.py` (127, clause helpers), `wipeoutr_fm.py` (116), `fastdiag.py` (110),
`quickxplain.py` (104).
`operations/algorithms/hsdag/` — `hsdag.py` (349), `node.py` (85), and
`labeler/` (`quickxplain_with_testcases_labeler.py` 201, `kbdiag_labeler.py` 83,
`fastdiag_labeler.py` 67, `quickxplain_labeler.py` 65, `labeler.py` 58).

### `checker/` — consistency-checker port + adapters
| Module | LOC | Responsibility |
|--------|-----|----------------|
| `backend.py` | 326 | PySAT (incremental / non-incremental) + SAT4J adapters, `SolverBackend`, `build_checker` |
| `protocols.py` | 71 | `ConsistencyChecker` / `TestCaseChecker` / `CopyableChecker` Protocols |
| `__init__.py` | 22 | internal facade (not a second public door) |

### `transformations/`
`fm_to_diag_pysat.py` (112, FeatureModel→DiagnosisModel), `dimacs_to_diag_pysat.py`
(85), `dimacs_to_configuration.py` (58), `testsuite_reader.py` (42).

## `profiling/` (leaf)
| Module | LOC | Responsibility |
|--------|-----|----------------|
| `core.py` | 614 | `Profiler` concrete class, `ProfilerMode` |
| `protocol.py` | 319 | `Profiler` Protocol, `AbstractProfiler`, `NullProfiler`, `MetricType`, `ProfilerError` |
| `decorators.py` | 113 | `measure_time`, `count_calls` |
| `registry.py` | 92 | global-profiler get/set/use + `profiler_session` |
| `presets.py` | 57 | `ProfilerPreset`, `create_profiler` |
| `__init__.py` | 49 | public surface (`from profiling import X`) |

## Tests (`tests/`, 275 passing)
- Per-algorithm diagnosis: `test_diagnosis_{fastdiag,hsdag,kbdiag,quickxplain,
  quickxplain_wtc,redundancy}.py`, sharing `diagnosis_helpers.py` (config,
  resource paths, checker wiring).
- Characterization / contract: `test_transformations_characterization.py`
  (traversal-order id catalog), `test_encoding.py`, `test_task_immutability.py`,
  `test_solver_backend_port.py`, `test_assumption_id_allocator.py`,
  `test_utils.py`, `test_profiler.py`.
- Guards: `test_boundary_guard.py` (layering, AST), `test_parallel_scaffolding_guard.py`.
- Infra: `conftest.py` (slim — marker registration is in `pyproject.toml`),
  `resource_paths.py` (framework subset), fixtures in `tests/resources/`
  (`.uvl`, `.cnf`, `.fide`, `.testcases`, `.csvconf` + `arcade-game.uvl`).

## Entry points (consumer's view)
```python
from explanation.api import (
    DiagnosisModelBuilder,  # build a model from UVL/DIMACS  ← via models/operations
    TaskInput, build_checker, SolverBackend, QuickXPlain, FmToDiagPysat,
)
from profiling import ProfilerPreset, profiler_session
```
Typical run: build model → prepare task → `build_checker` → run algorithm →
describe result (see `docs/system-architecture.md` § request flow).

## Runtime dependency
`solver_apps/org.sat4j.core.jar` (344 KB) — required by the SAT4J backend;
resolved relative to the working directory (`SAT4JChecker`).
