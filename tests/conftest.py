"""Shared pytest configuration for the framework test suite.

Slim by design. AcqMSS's ``conftest.py`` centralized REAL-FM-7 ``bias`` /
``oracle`` fixtures that load conacq objects; those live in the *application*
repo and are intentionally NOT ported here — the framework repo has no conacq.

The ``slow`` marker is registered in ``pyproject.toml`` under
``[tool.pytest.ini_options]``. Resource paths live in
``tests/resource_paths.py`` (framework subset) and ``tests/diagnosis_helpers.py``
(per-algorithm suites). Nothing else is needed at collection time, so this file
holds no fixtures.
"""
