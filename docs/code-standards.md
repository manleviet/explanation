# Code Standards

Conventions the `explanation` and `profiling` packages actually follow. Derived
from the current code; when in doubt, match the nearest existing module.

## Language & typing
- Python **>= 3.11**. Type hints on public functions/classes; `typing.Protocol`
  for structural contracts.
- Structural contracts are `@runtime_checkable` Protocols
  (`ConsistencyChecker`/`TestCaseChecker`/`CopyableChecker` in `checker/protocols.py`,
  `KBProtocol`, `ProfilerProtocol`). Consumers depend on the narrowest role they
  need — capability widening is expressed by Protocol inheritance, not flags.
- Docstrings on every module and public class/function, explaining *why*, not
  just *what* (see any module header).

## Immutability
- Pure-data units are **frozen dataclasses** (`@dataclass(frozen=True)`), and
  deep-frozen at construction: list fields → tuples, mapping fields → `FrozenDict`
  in `__post_init__` (`Task` family, ADR-0012). Rebinding *or* in-place mutation
  raises. Pinned by `test_task_immutability.py`.
- Use `FrozenDict` (not `MappingProxyType`) for immutable mapping fields — it is a
  read-only `dict` subclass that still **pickles**, required because FastDiagP
  ships tasks to worker processes.
- Derived quantities are **free functions** (e.g. `cf(task)`), not methods on the
  data class — the data stays pure (no behavior).

## Boundaries (the load-bearing rule)
- Consumers reach the framework **only** through `explanation.api`; the framework
  reaches the leaf **only** through the `profiling` façade. No deep submodule
  imports across a tier, no `_underscore` privates across a tier.
- The framework never imports the application tier. `profiling` imports nothing
  above it.
- Add a symbol to `explanation.api` only when a consumer needs it — never "just in
  case". Enforced by `test_boundary_guard.py` (ADR-0002).
- The name↔id catalog lives in **one** place (the KB/model) and is passed to the
  encoding free functions as parameters — never duplicated (ADR-0007).

## Naming & layout
- Modules: `snake_case.py`; packages lowercase, no hyphens. Classes `PascalCase`;
  functions/vars `snake_case`; module-private helpers `_leading_underscore`.
- One concern per module; keep modules focused (most are < 200 LOC; the few large
  ones — `task_preparation`, `core`, `pysat_explanation_builder` — are cohesive
  single-responsibility units).
- A package `__init__` re-exports its internal surface for intra-framework use; it
  is **not** a second public door (only `explanation.api` is).
- Extension seams are additive: the operation `registry` maps a stable name → op
  class; built-ins self-register at import.

## Tests
- Behavior is pinned by **characterization tests** asserting exact literal outputs
  (diagnosis strings, id catalogs). Do not relax an assertion to make a bump pass:
  re-pin to the new *verified* value only after confirming the change is
  intended/whitespace-only, and cite the evidence.
- New behavior gets a test that fails without the change (prove teeth: a mechanism
  test builds inputs that only pass if the mechanism actually runs — e.g. build a
  `Task` from a plain `list`/`dict` and assert the coerced tuple/`FrozenDict`, not
  the annotation).
- Run `tests/test_boundary_guard.py` first after any structural change.
- Read every skip — a skipped test on a missing fixture is a missing resource, not
  a pass. The `slow` marker is registered in `pyproject.toml`
  (`[tool.pytest.ini_options]`), not `conftest.py`.

## Dependencies
- Pinned **exactly** (`==`) in `pyproject.toml`: `flamapy-fw/fm/sat==2.6.0.dev4`,
  `python-sat==0.1.8.dev17`. Do not loosen to `~=` — `~=2.6.0.dev4` floats onto
  flamapy 2.6.0 final (breaks the uvl_reader path), and PEP 440 orders dev4 <
  2.6.0. `python-sat` is pinned to `0.1.8.dev17` (the version with a wheel that
  greens the suite; `0.1.7.dev1` has no wheel and fails to build).
- `profiling` must remain a stdlib-only leaf.

## Architecture decisions
- Every non-obvious structural choice is recorded in `docs/adr/`. Read the
  relevant ADR before "tidying" something that looks misplaced. ADRs are immutable
  once accepted — supersede with a new one, never edit.
