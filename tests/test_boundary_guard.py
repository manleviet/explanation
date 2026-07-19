"""Architectural boundary guard — keep the packages cleanly layered.

Framework-repo variant. The full stack is three tiers with strictly
one-directional dependencies::

    (application: conacq/quacq/…)  ── lives in the CONSUMING repos, not here
      │
      ▼
    explanation   (framework)     ── may use ──▶ profiling
      │
      ▼
    profiling     (neutral leaf)  ── uses nothing but stdlib + itself

This repo ships only the bottom two tiers, so the guard pins exactly the rules
that have real files to scan here:

  (3) explanation → profiling : only the ``profiling`` façade (no deep paths)
  (4) explanation ⊥ app       : the framework never imports any application
                                (locked: confirms the framework is app-free)
  (5) profiling is a leaf      : it never imports explanation or any application

The AcqMSS suite also enforces conacq-side rules (1/2/6). Those scan a
``conacq/`` tree that does not exist here; ported verbatim they would pass
vacuously (an empty ``rglob`` yields no breaches) — a green light that means
"absent", not "clean". They stay in AcqMSS, where conacq is present.

Imports are parsed with ``ast``. A red test is a real breach (an import cycle
or a leaked internal), not a false alarm — report it rather than loosening it.
"""
import ast
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
EXPLANATION_DIR = REPO_ROOT / "explanation"
PROFILING_DIR = REPO_ROOT / "profiling"

# The sole façade module of the leaf tier that the tier above may import from.
PROFILING_FACADE = frozenset({"profiling"})

# Application top-level packages the framework must never import. The framework
# is app-agnostic; these live only in consuming repos.
APP_TOP_PACKAGES = ("conacq",)


def _iter_source_files(root: Path):
    """Yield every ``.py`` file under ``root`` (skipping bytecode caches)."""
    for path in sorted(root.rglob("*.py")):
        if "__pycache__" in path.parts:
            continue
        yield path


def _iter_imports(path: Path):
    """Yield ``(module, imported_name, lineno)`` for each absolute import.

    ``import a.b.c``        -> ("a.b.c", None, lineno)
    ``from a.b import c``   -> ("a.b", "c", lineno)

    Relative imports (``from . import x``) stay within their own package and can
    never cross a tier boundary, so they are skipped.
    """
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                yield alias.name, None, node.lineno
        elif isinstance(node, ast.ImportFrom):
            if node.level != 0:  # relative import — intra-package
                continue
            module = node.module or ""
            for alias in node.names:
                yield module, alias.name, node.lineno


def _top_package(module: str) -> str:
    return module.split(".", 1)[0]


def _facade_breaches(root: Path, target_top: str, facade: frozenset) -> list:
    """Imports of ``target_top`` from ``root`` that bypass the façade.

    A breach is a deep submodule path (anything under ``target_top`` other than
    the blessed façade module) or an underscore-private symbol name.
    """
    allowed = " / ".join(sorted(facade))
    breaches = []
    for path in _iter_source_files(root):
        rel = path.relative_to(REPO_ROOT)
        for module, name, lineno in _iter_imports(path):
            if _top_package(module) != target_top:
                continue
            if module not in facade:
                breaches.append(f"{rel}:{lineno}: deep import `{module}` (route through {allowed})")
                continue
            if name is not None and name.startswith("_"):
                breaches.append(f"{rel}:{lineno}: private symbol `{name}` from `{module}`")
    return breaches


def _dependency_breaches(root: Path, forbidden_top: str) -> list:
    """Any import of ``forbidden_top`` from files under ``root``."""
    breaches = []
    for path in _iter_source_files(root):
        rel = path.relative_to(REPO_ROOT)
        for module, _name, lineno in _iter_imports(path):
            if _top_package(module) == forbidden_top:
                breaches.append(f"{rel}:{lineno}: imports `{module}`")
    return breaches


def test_explanation_imports_profiling_only_through_facade():
    """(3) Framework reaches the profiling leaf solely via the ``profiling`` façade."""
    breaches = _facade_breaches(EXPLANATION_DIR, "profiling", PROFILING_FACADE)
    assert not breaches, "explanation → profiling breaches:\n  " + "\n  ".join(breaches)


def test_explanation_never_imports_an_application():
    """(4) The framework has zero knowledge of any application tier."""
    breaches = []
    for app_top in APP_TOP_PACKAGES:
        breaches += _dependency_breaches(EXPLANATION_DIR, app_top)
    assert not breaches, (
        "explanation → application breaches (framework must not know the app):\n  "
        + "\n  ".join(breaches)
    )


def test_profiling_is_a_leaf():
    """(5) The profiling leaf depends on neither the framework nor any application."""
    breaches = _dependency_breaches(PROFILING_DIR, "explanation")
    for app_top in APP_TOP_PACKAGES:
        breaches += _dependency_breaches(PROFILING_DIR, app_top)
    assert not breaches, (
        "profiling is not a leaf (must not import explanation/application):\n  "
        + "\n  ".join(breaches)
    )
