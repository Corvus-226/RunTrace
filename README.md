# RunTrace

![RunTrace — Know exactly what changed. An experiment fingerprint formed by overlapping version traces](https://raw.githubusercontent.com/Corvus-226/RunTrace/main/docs/assets/runtrace-overview.png)

[![CI](https://github.com/Corvus-226/RunTrace/actions/workflows/ci.yml/badge.svg)](https://github.com/Corvus-226/RunTrace/actions/workflows/ci.yml)
[![PyPI](https://img.shields.io/pypi/v/ml-runtrace.svg)](https://pypi.org/project/ml-runtrace/)
[![GitHub Release](https://img.shields.io/github/v/release/Corvus-226/RunTrace.svg)](https://github.com/Corvus-226/RunTrace/releases/latest)
[![Python 3.10–3.12](https://img.shields.io/badge/python-3.10--3.12-blue.svg)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

RunTrace is a lightweight CLI for capturing and comparing the code,
configuration, environment, and metadata behind machine-learning experiments.
It stores transparent YAML snapshots in the current Git repository, without a
server or account.

> **Project status:** [v0.1.0](https://github.com/Corvus-226/RunTrace/releases/tag/v0.1.0)
> is the first published release. It is available from
> [PyPI](https://pypi.org/project/ml-runtrace/0.1.0/) and verified on Windows
> and Linux with Python 3.10–3.12.

## Why RunTrace?

Experiment folders named `final`, `final-2`, and `final-really` do not explain
which commit, config, Python environment, or command produced a result.
RunTrace records that reproducibility context at the moment you choose, then
lets you inspect and compare it later.

RunTrace deliberately has a smaller job than MLflow or Weights & Biases. It is
useful when you want:

- a local-first workflow with no service, database, or account;
- human-readable snapshot files that remain under your control;
- Git-aware records of committed and uncommitted code state;
- configuration and dependency comparisons from the terminal;
- an incremental reproducibility layer rather than a full tracking platform.

It does not track metrics, host dashboards, schedule experiments, upload
artifacts, or replace a full experiment-tracking platform.

## Quick Start

### 1. Install from PyPI

Create and activate an isolated environment using the command for your shell:

```console
python -m venv .venv
```

Then install RunTrace and verify both supported entry points:

```console
python -m pip install ml-runtrace
ml-runtrace --version
python -m ml_runtrace --version
```

The PyPI distribution is `ml-runtrace`, its Python import is `ml_runtrace`,
and its only console command is `ml-runtrace`. No `runtrace` import or command
alias is provided because an unrelated PyPI project owns those names.
Contributors should use the locked uv environment described in
[Development](#development).

### 2. Initialize an existing Git repository

RunTrace requires a Git repository with at least one commit:

```console
cd your-project
ml-runtrace init
```

This creates `runtrace.toml` and `.runtrace/runs/` at the Git root. Commit
`runtrace.toml` if it is part of the project configuration. Add `.runtrace/` to
your `.gitignore` when recorded runs should remain local and untracked.

### 3. Record an experiment

Create a repository-local YAML config such as `configs/train.yaml`:

```yaml
model: resnet18
optimizer:
  learning_rate: 0.001
  weight_decay: 0.01
batch_size: 32
seed: 42
```

Commit the code and config you want to identify, then record the experiment:

```console
git add runtrace.toml configs/train.yaml
git commit -m "add training baseline"
ml-runtrace snapshot --name baseline --config configs/train.yaml --command "python train.py --config configs/train.yaml"
```

`snapshot` records the supplied command; it does not execute that command. The
result prints a 12-character run ID and writes one YAML file beneath
`.runtrace/runs/`.

#### Preview on current `main`: snapshot, then run

The current development branch adds an opt-in wrapper planned for the next
release. It is not part of the PyPI v0.1.0 package:

```console
ml-runtrace run --name baseline --config configs/train.yaml -- python train.py --config configs/train.yaml
```

`run` writes the snapshot before starting the command after `--`, preserving
the exact argument vector as well as a readable command. If snapshot capture
fails, the experiment is not started. If the experiment fails, its snapshot is
kept and its exit code is returned.

The child process is started directly, without an implicit shell. Pipes,
redirection, shell variables, and other shell syntax are therefore not
interpreted unless you explicitly run a shell as the child command.

### 4. Inspect and compare runs

After recording another run, use either a full ID or a unique abbreviated ID:

```console
ml-runtrace list
ml-runtrace show <run-id>
ml-runtrace diff <baseline-id> <candidate-id>
```

A representative diff looks like this (IDs and values will differ):

```text
Comparing a31f82000001 -> b91de3000002
Configuration ────────────────────────────────────────────────────────────────
changed  config.values.optimizer.learning_rate
before  0.001
after   0.0005
Git ──────────────────────────────────────────────────────────────────────────
changed  commit
before  83ab2c1000000000000000000000000000000000
after   92dc113000000000000000000000000000000000
Environment ──────────────────────────────────────────────────────────────────
changed  torch
before  2.4.0
after   2.5.0
```

The detailed [Getting Started guide](docs/getting-started.md) walks through the
entire init → snapshot → list → show → diff workflow and explains each result.

## What a snapshot contains

- run ID, optional name, and UTC timestamp;
- Git commit, branch or detached-HEAD state, and dirty state;
- Python version, implementation, operating system, and architecture;
- installed Python distribution names and versions;
- optional NVIDIA GPU, driver, and CUDA metadata when detectable;
- an explicitly supplied command and YAML config path, SHA-256 hash, and
  parsed values.

On current `main`, snapshots also include the exact argument vector used by
`ml-runtrace run` and sanitized [PEP 610](https://peps.python.org/pep-0610/)
origins for direct VCS, archive, and local-directory package installations.
VCS and archive origins retain a safe relative package subdirectory when one
is declared.

## CLI reference

| Command | Purpose |
| --- | --- |
| `ml-runtrace init` | Initialize local RunTrace state at the containing Git root. |
| `ml-runtrace snapshot` | Capture the current reproducibility context. |
| `ml-runtrace run -- COMMAND...` | On current `main` (next release), snapshot first and then execute an argument vector. |
| `ml-runtrace list` | List recorded runs newest first. |
| `ml-runtrace show <run-id>` | Display one complete stored snapshot. |
| `ml-runtrace diff <run-a> <run-b>` | Compare reproducibility-relevant values. |

Run `ml-runtrace <command> --help` for command-specific arguments and options.

## Privacy and storage

RunTrace is local-only by default. It does not upload experiment data, source
code, credentials, environment variables, or artifacts. Snapshot capture does
not read those implicit secret sources.

When `--config`, `--command`, or the current-main `run` wrapper is used,
RunTrace intentionally stores the parsed config values, readable command, and
exact command arguments in local YAML. Do not put secrets in those explicit
inputs.

For packages installed from a direct source, current `main` reads standardized
`direct_url.json` metadata. URL usernames/passwords, queries, fragments, and
local absolute directory paths are omitted. A remote URL's host and repository
path, requested revision, and safe relative subdirectory can still reveal
private project names; review `.runtrace/runs/*.yaml` before sharing or
committing it, just as you would review any experiment record.

## Development

RunTrace requires Python 3.10 or newer and uses
[uv](https://docs.astral.sh/uv/) for its reproducible development environment:

```console
git clone https://github.com/Corvus-226/RunTrace.git
cd RunTrace
uv sync --all-groups --locked
uv run ml-runtrace --help
uv run pytest
uv run ruff check .
uv run ruff format --check .
```

CI runs the same quality gates on Linux with Python 3.10, 3.11, and 3.12.

## Contributing and security

Focused bug reports, design feedback, and contributions are welcome. Read
[CONTRIBUTING.md](CONTRIBUTING.md) before opening a pull request. Report
vulnerabilities privately using the instructions in [SECURITY.md](SECURITY.md),
not a public issue.

## License

RunTrace is released under the [MIT License](LICENSE).
