# Getting Started with RunTrace

This guide takes a Git-based project from installing the RunTrace v0.1.0
release candidate to its first experiment comparison.

## Before you start

You need:

- Python 3.10, 3.11, or 3.12;
- Git available on `PATH`;
- an existing Git repository with at least one commit;
- a UTF-8 YAML experiment config if you want config-level comparisons.

RunTrace supports Windows and Linux. The one-line RunTrace commands below work
in PowerShell, Command Prompt, and common POSIX shells.

## Install RunTrace

The first PyPI release has not been published. Clone the repository and create
an isolated environment:

```console
git clone https://github.com/Corvus-226/RunTrace.git
cd RunTrace
python -m venv .venv
```

Activate the environment using the command for your shell, then install the
current candidate from source:

```console
python -m pip install .
ml-runtrace --version
python -m ml_runtrace --version
```

The planned distribution name is `ml-runtrace`, but it is not available on
PyPI. The approved Python import is `ml_runtrace`, and the only console command
is `ml-runtrace`. [Issue #24](https://github.com/Corvus-226/RunTrace/issues/24)
records why no `runtrace` import or command alias is provided: an unrelated
PyPI project already owns both names.

## 1. Initialize your project

Change to an existing Git repository, then initialize RunTrace:

```console
cd your-project
ml-runtrace init
```

Expected output includes:

```text
Initialized RunTrace in current repository.
Project: <absolute-path-to-your-project>
```

RunTrace finds the containing Git root even when you invoke it from a nested
directory. Initialization is idempotent and creates:

```text
your-project/
├── runtrace.toml
└── .runtrace/
    └── runs/
```

It preserves existing config and run files. Commit `runtrace.toml` when it is
part of the project configuration. Add `.runtrace/` to `.gitignore` if the run
records should remain local rather than being reviewed and committed.

## 2. Prepare a reproducible baseline

Create `configs/train.yaml` inside the repository:

```yaml
model: resnet18
optimizer:
  learning_rate: 0.001
  weight_decay: 0.01
batch_size: 32
seed: 42
```

Commit the code and configuration. A snapshot requires the repository to have
a commit; its dirty flag then tells you whether tracked or untracked project
content differed from that commit.

```console
git add runtrace.toml configs/train.yaml
git commit -m "add training baseline"
```

RunTrace excludes its own `.runtrace/` storage from the captured dirty-state
calculation, so recording one run does not make every later run dirty.

## 3. Record the baseline

Capture the current Git, runtime, dependency, hardware, config, and command
context:

```console
ml-runtrace snapshot --name baseline --config configs/train.yaml --command "python train.py --config configs/train.yaml"
```

The command prints output in this form:

```text
Created snapshot a31f82000001.
Path: <project>/.runtrace/runs/a31f82000001.yaml
```

Your generated ID will be different. Save it for later comparison.

Important: `ml-runtrace snapshot --command ...` records the command string; it
does not start the training process. Run the experiment yourself before or
after recording, according to your workflow.

The optional snapshot inputs are:

| Option | Stored value |
| --- | --- |
| `--name` | A human-readable run label. |
| `--config` | Repository-relative path, raw SHA-256, and parsed YAML values. |
| `--command` | The literal command supplied by the user. |

Without these options, RunTrace still records Git, Python, platform,
dependencies, and optional GPU/CUDA metadata.

## 4. Inspect recorded runs

List snapshots newest first:

```console
ml-runtrace list
```

Representative output:

```text
RUN ID        NAME      COMMIT   DIRTY  CREATED
a31f82000001  baseline  83ab2c1  no     2026-08-13 06:31 UTC
```

Show the complete stored record using the full ID or a unique prefix:

```console
ml-runtrace show a31f82
```

`show` reads the historical YAML record. It does not replace stored values
with the current repository, environment, hardware, or config file.

## 5. Record a candidate

Change `optimizer.learning_rate` in `configs/train.yaml` to `0.0005`, then
commit the candidate if it should represent a new code/config revision:

```console
git add configs/train.yaml
git commit -m "try lower learning rate"
ml-runtrace snapshot --name candidate --config configs/train.yaml --command "python train.py --config configs/train.yaml"
```

Copy the new run ID from the output. Leaving changes uncommitted is also valid;
the snapshot will record `dirty: true` so that difference remains visible.

## 6. Compare the experiments

Pass the baseline first and the candidate second. Full IDs and unique prefixes
are both accepted, case-insensitively:

```console
ml-runtrace diff a31f82 b91de3
```

Representative output:

```text
Comparing a31f82000001 -> b91de3000002
Configuration ────────────────────────────────────────────────────────────────
changed  config.sha256
before  <baseline-sha256>
after   <candidate-sha256>
changed  config.values.optimizer.learning_rate
before  0.001
after   0.0005
Git ──────────────────────────────────────────────────────────────────────────
changed  commit
before  83ab2c1000000000000000000000000000000000
after   92dc113000000000000000000000000000000000
```

Differences are grouped in a fixed order:

1. **Configuration** — command, config path/hash, and recursively compared YAML
   mappings and arrays.
2. **Git** — commit, branch, detached state, and dirty state.
3. **Runtime** — Python implementation/version and platform fields.
4. **Environment** — installed distribution additions, removals, and version
   changes.

Each leaf is classified as `added`, `removed`, or `changed`. Run name,
timestamp, and run ID identify snapshots but are not reported as
reproducibility differences. If relevant values are identical, RunTrace prints
`No relevant differences found.`

## Storage and privacy

Every snapshot is a readable YAML file under `.runtrace/runs/`. RunTrace does
not start a service, create an account, or automatically upload anything. It
does not capture source contents, environment variables, tokens, credentials,
or experiment artifacts.

RunTrace does store values you explicitly pass with `--config` and `--command`.
Keep secrets out of those inputs, and review snapshot YAML before sharing or
committing it.

## RunTrace and full tracking platforms

| | RunTrace | Full tracking platforms |
| --- | --- | --- |
| Primary job | Capture and compare reproducibility context | Manage metrics, artifacts, dashboards, and experiment lifecycles |
| Required infrastructure | Local CLI and Git repository | Commonly a service, server, or database |
| Default storage | Local readable YAML | Platform-managed stores or databases |
| Account required | No | Often |

The tools can be complementary: RunTrace can provide a small local record even
when a team also uses a larger tracking system.

## Common errors

| Message or situation | Resolution |
| --- | --- |
| `Not inside a Git work tree` | Change into a Git repository or run `git init`. |
| `Repository has no commits yet` | Create the first Git commit before taking a snapshot. |
| `RunTrace is not initialized` | Run `ml-runtrace init` in the repository. |
| Config must be inside the repository | Move the YAML file under the Git root. |
| Run ID is ambiguous | Supply more characters or the complete 12-character ID. |
| Stored snapshot is invalid | Repair or remove the named YAML file after reviewing it. |

Run `ml-runtrace <command> --help` for the exact CLI arguments available in your
installed version.

## Current maturity

RunTrace v0.1.0 is a release candidate, not a published PyPI release. The core
local workflow and collision-free public names are tested on Windows and
covered by an offline two-order install/uninstall audit. Pull request CI also
passes on supported Python versions on Linux. Final release review is still
required before publication. After publication, snapshot schemas and CLI
behavior may still evolve during the 0.x series. Track changes in the repository's
[issues](https://github.com/Corvus-226/RunTrace/issues) and
[changelog](../CHANGELOG.md).
