# RunTrace

[![CI](https://github.com/Corvus-226/RunTrace/actions/workflows/ci.yml/badge.svg)](https://github.com/Corvus-226/RunTrace/actions/workflows/ci.yml)
[![Python 3.10–3.12](https://img.shields.io/badge/python-3.10--3.12-blue.svg)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

RunTrace is a lightweight CLI for capturing and comparing the code,
configuration, environment, and metadata behind machine-learning experiments.
It stores transparent YAML snapshots in the current Git repository, without a
server or account.

> **Project status:** v0.1.0 release candidate. It has not been published to
> PyPI. The collision-free candidate is verified locally on Windows and by
> pull request CI on Linux with Python 3.10–3.12. The public names approved in
> [Issue #24](https://github.com/Corvus-226/RunTrace/issues/24) are now part of
> the candidate and remain subject to final release review.

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

### 1. Install the current candidate from source

Clone the repository and create an isolated environment:

```console
git clone https://github.com/Corvus-226/RunTrace.git
cd RunTrace
python -m venv .venv
```

Activate the environment using the command for your shell, then install the
reviewed source and verify the current command:

```console
python -m pip install .
ml-runtrace --version
python -m ml_runtrace --version
```

The planned PyPI distribution is `ml-runtrace`, but it is not available yet.
Its Python import is `ml_runtrace`, and its only console command is
`ml-runtrace`. No `runtrace` import or command alias is provided because an
unrelated PyPI project owns those names. Contributors should use the locked uv
environment described in [Development](#development).

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

## CLI reference

| Command | Purpose |
| --- | --- |
| `ml-runtrace init` | Initialize local RunTrace state at the containing Git root. |
| `ml-runtrace snapshot` | Capture the current reproducibility context. |
| `ml-runtrace list` | List recorded runs newest first. |
| `ml-runtrace show <run-id>` | Display one complete stored snapshot. |
| `ml-runtrace diff <run-a> <run-b>` | Compare reproducibility-relevant values. |

Run `ml-runtrace <command> --help` for command-specific arguments and options.

## Privacy and storage

RunTrace is local-only by default. It does not upload experiment data, source
code, credentials, environment variables, or artifacts. Snapshot capture does
not read those implicit secret sources.

When `--config` or `--command` is supplied, RunTrace intentionally stores the
parsed config values and command in local YAML. Do not put secrets in those
explicit inputs. Review `.runtrace/runs/*.yaml` before sharing or committing
it, just as you would review any experiment record.

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
