"""Characterization tests pinning the T1 Task-family invariants.

Tasks are immutable pure-data units-of-work: frozen dataclasses with only
intrinsic solve fields, no methods (derived quantities are free functions),
and TaskInput validates mutually-exclusive input combinations.
"""
import dataclasses

import pytest
from flamapy.metamodels.configuration_metamodel.models import Configuration

from explanation.models.task_preparation import (
    Task,
    DiagnosisTask,
    TaskInput,
    cf,
)
# Aliased with leading underscore so pytest does not try to collect these
# "Test*"-named data classes as test cases.
from explanation.models.task_preparation import TestCaseTask as _TestCaseTask
from explanation.models.testsuite import TestSuite as _TestSuite


# --- Deep-frozen contract: rebinding a field raises (shallow), AND the list-valued
#     fields coerce to tuples + negation_map to FrozenDict so mutating their contents
#     raises too (deep). The deep mechanism is pinned by test_task_is_deeply_frozen
#     below (ADR-0012). ---

@pytest.mark.parametrize("task_cls", [DiagnosisTask, _TestCaseTask])
def test_task_rebind_raises(task_cls):
    task = task_cls()
    with pytest.raises(dataclasses.FrozenInstanceError):
        task.set_c = [1, 2, 3]


@pytest.mark.parametrize("task_cls", [DiagnosisTask, _TestCaseTask])
def test_task_is_deeply_frozen(task_cls):
    """Deep immutability (ADR-0012): list-valued solve fields coerce to tuples that
    reject in-place mutation, and ``negation_map`` coerces to a ``FrozenDict`` (a
    read-only dict subclass that still pickles — FastDiagP ships tasks to workers).
    Built with a plain ``list``/``dict`` so it passes only if ``__post_init__``
    actually coerces, not merely if the annotation changed — the mechanism, not the
    label. Both the identity type AND the mutate-block are pinned (one alone is not
    enough: a plain dict has the wrong type; a MappingProxy blocks mutation but does
    not pickle).
    """
    task = task_cls(set_c=[1], negation_map={1: 2})
    # list-valued solve field → tuple (rejects in-place mutation)
    with pytest.raises((TypeError, AttributeError)):
        task.set_c.append(999)  # a tuple rejects this; a list would not
    # mapping-valued field → FrozenDict: pin the identity type ...
    assert type(task.negation_map).__name__ == "FrozenDict"
    # ... AND the mutate-block mechanism (a plain dict would accept this).
    with pytest.raises(TypeError):
        task.negation_map[3] = 4


def test_task_input_is_frozen():
    ti = TaskInput()
    with pytest.raises(dataclasses.FrozenInstanceError):
        ti.for_redundancy = True


# --- Hierarchy: every task is a Task; test-case tasks are TestCaseTask ---

def test_hierarchy():
    assert issubclass(DiagnosisTask, Task)
    assert issubclass(_TestCaseTask, Task)
    # The conacq ConGenTask ⊂ _TestCaseTask and QuAcqTask ⊂ DiagnosisTask
    # assertions are cross-repo (conacq subclasses framework tasks) and live in
    # AcqMSS, where conacq is present. The framework repo pins only its own
    # internal hierarchy above.


# --- Pure data: no residual get_cf method; cf() is a free function ---

def test_no_get_cf_method_on_task():
    assert not hasattr(DiagnosisTask(), "get_cf")


def test_cf_free_function():
    task = DiagnosisTask(set_c=[3, 4], set_b=[1, 2])
    assert cf(task) == (1, 2, 3, 4)  # set_b + set_c (frozen tuples -> tuple)


# NOTE: QuAcqTask's ``constraint_clauses`` deep-freeze test is conacq-specific
# (QuAcqTask lives in conacq) and stays in AcqMSS. The framework's own deep-freeze
# mechanism is pinned by test_task_is_deeply_frozen above.


# --- TaskInput factories map to the documented use cases ---

def test_taskinput_factories():
    assert TaskInput.fm_diagnosis() == TaskInput()
    assert TaskInput.redundancy_fm().for_redundancy is True

    cfg = Configuration({})
    assert TaskInput.config(cfg).configuration is cfg
    assert TaskInput.config_with_cf(cfg).with_cf_in_c is True
    assert TaskInput.error(cfg).test_case is cfg

    pos = _TestSuite([])
    ti = TaskInput.testcases(pos)
    assert ti.positive_test_cases is pos and ti.is_testcase_task()
    assert TaskInput.redundancy_t(pos).for_redundancy is True


# --- TaskInput validates mutually-exclusive inputs ---

def test_taskinput_rejects_config_with_testcases():
    with pytest.raises(ValueError):
        TaskInput(configuration=Configuration({}), positive_test_cases=_TestSuite([]))


def test_taskinput_rejects_testcase_with_error():
    with pytest.raises(ValueError):
        TaskInput(test_case=Configuration({}), positive_test_cases=_TestSuite([]))
