# explanation

Explanation framework for [flamapy](https://flamapy.org) — conflict detection and
diagnosis over feature models (FastDiag, KBDiag, HS-DAG, QuickXPlain), built on the
PySAT backend.

This is the **canonical source**. Working repos (AcqMSS, DiagEnergy, KBDiag) consume
it instead of keeping their own copy. It also feeds the public flamapy plugin
`flamapy-sat` (`pysat_metamodel`).

## Requirements

- Python **>= 3.11**
- Dependencies (resolved automatically): `flamapy-fw~=2.6.0.dev4`,
  `flamapy-fm~=2.6.0.dev4`, `flamapy-sat~=2.6.0.dev4`, `python-sat~=0.1.7.dev1`

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
