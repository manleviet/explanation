"""Framework test-resource paths (reduced from AcqMSS).

AcqMSS's ``resource_paths`` mixed two sources: a repo-root ``data/`` block
(REAL feature models / bias / examples / results — conacq application data) and
a ``tests/resources/`` block (diagnosis fixtures). Only the latter is framework
scope; the ``data/`` constants (``DATA_DIR``/``FM_PATH``/``BIAS_PATH``/
``EXAMPLES_*``/``RESULT_PATH``/``MODELS``) stay in AcqMSS.

Kept here: the ``tests/resources/``-based constants the framework suite uses.
"""
from pathlib import Path

# tests/resources/ — diagnosis + transform fixtures (.fide, .cnf, .uvl, .testcases).
RESOURCES_DIR = Path(__file__).resolve().parent / "resources"
FM_INCONSISTENT = RESOURCES_DIR / "smartwatch_inconsistent.fide"
# Real product-line FM as DIMACS CNF (~6.5k clauses) — a large KB for
# exercising FastDiagP's deep recursion / speculative lookahead.
CNF_PROD = RESOURCES_DIR / "prod_1_1.cnf"
