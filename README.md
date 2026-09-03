# explanation

Explanation framework for [flamapy](https://flamapy.org) — conflict detection and
diagnosis over feature models (FastDiag, KBDiag, HS-DAG, QuickXPlain), built on the
PySAT backend.

This is the **canonical source**. Working repos (AcqMSS, DiagEnergy, KBDiag) consume
it instead of keeping their own copy. It also feeds the public flamapy plugin
`flamapy-sat` (`pysat_metamodel`).

## Requirements

- Python **>= 3.11**
- Dependencies (resolved automatically), pinned **exactly** in `pyproject.toml`:
  `flamapy-fw==2.6.0.dev4`, `flamapy-fm==2.6.0.dev4`, `flamapy-sat==2.6.0.dev4`,
  `python-sat==0.1.8.dev17`
- Java runtime — only for the optional SAT4J backend
  (`solver_apps/org.sat4j.core.jar`). The default PySAT backend needs no JVM.

> **The jar does not travel with a `pip` install.** `solver_apps/` sits outside
> the packaged modules (`include = ["explanation*", "profiling*"]`), so a remote
> git install delivers the code without the jar. The SAT4J backend therefore
> works only from a repo checkout, invoked with the repo root as the working
> directory — the default jar path is relative. Anywhere else it raises
> `FileNotFoundError`, which reads like a botched install but is not one: use a
> PySAT backend, or pass an absolute path via
> `build_checker(..., sat4j_jar_path=...)`.

> **Do not loosen the pins to `~=`.** `~=2.6.0.dev4` resolves to `==2.6.*`, which
> floats onto flamapy **2.6.0 final** — whose `uvl_reader` breaks the test suite.
> PEP 440 also orders `dev4 < 2.6.0`, so a `<2.6.0` bound would exclude the very
> build the framework is verified against. Only `==` locks it.

## Installation

### 1. Editable install — recommended (local development)

Use this for projects on the same machine that are developed alongside the framework
(AcqMSS / DiagEnergy / KBDiag). One physical source of truth; edits are picked up
immediately, no re-install needed.

```bash
# in the consuming project's virtualenv
pip install -e /path/to/explanation
# or, if the project uses uv:
uv pip install -e /path/to/explanation
```

After switching to this, **delete the old in-repo `explanation/` copy** in the
consuming repo so it doesn't shadow the installed package. Imports stay
`from explanation. ...` (DiagEnergy must rewrite `diagenergy.diagnosis.` →
`explanation.`).

### 2. Remote git install — no local clone needed

Use this for a new project, another machine, or CI. `pip` clones the repo into a
temporary directory, builds, installs, and discards it — you never keep a local copy.
Requires the repo to be pushed to a remote, and `git` on the machine.

```bash
# pin a tag (recommended), or use @main / @<commit-sha>
pip install "git+https://github.com/<user>/explanation.git@v0.1.0"
```

Private repo works too, with authentication:

```bash
# via SSH key
pip install "git+ssh://git@github.com/<user>/explanation.git@v0.1.0"
```

Put the same line in the project's `requirements.txt` or in `dependencies` of its
`pyproject.toml` for a reproducible, portable pin.

### 3. From a local path or local git (niche)

```bash
pip install /path/to/explanation                       # plain local path
pip install "git+file:///path/to/explanation@v0.1.0"   # local git, pinned
```

`git+file://` gives a pinned snapshot but only on this machine (not portable) — prefer
editable (case 1) for dev or remote git (case 2) for sharing.

### 4. From PyPI (future)

Once published: `pip install explanation`.

## Verify the install

```bash
python -c "import explanation.api, profiling"   # both packages importable
PYTHONPATH=. python -m pytest tests/ -q         # 275 tests (from a clone)
```

Consumers import through the single public façade — `from explanation.api import …`
and `from profiling import …`. Deep imports (`explanation.models.*`,
`explanation.operations.*`) are not a supported surface; see
`docs/system-architecture.md`.

## Which method to use

| Situation | Method |
|---|---|
| Developing the framework alongside a project, same machine | `pip install -e <path>` (case 1) |
| New project / other machine / CI / no local clone | `git+https://...@tag` (case 2) |
| Reproducing published numbers | git tag the framework + pin the tag |
| Anyone installs without git/auth | PyPI (case 4) |

### Reproducibility note

Editable installs float on the working-copy state. When freezing results for a paper,
`git tag` the framework and record the commit/tag in the experiment repo.
