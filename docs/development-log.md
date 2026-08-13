# RunTrace Development Log

This log records implementation decisions and verification results. It is not a
substitute for issues, pull requests, commit history, or `CHANGELOG.md`.

## Daily delivery checklist

This checklist expands the dated plan into verifiable daily outcomes. A struck
item has been implemented and locally verified; open items remain planned. The
board reports progress but does not override issue scope, dependency order,
review, CI, or release safety.

### Day 1 — 2026-08-12 — Repository foundation

- ~~Create and verify the public GitHub repository and product scope.~~
- ~~Add the MIT license and initial README positioning.~~
- ~~Create `pyproject.toml`, the collision-free `src/ml_runtrace` package
  layout, and CLI entry point.~~
- ~~Configure uv, pytest, Ruff, and the committed dependency lockfile.~~
- ~~Add Linux CI for Python 3.10, 3.11, and 3.12.~~
- ~~Add `AGENTS.md`, `CONTRIBUTING.md`, `SECURITY.md`, and GitHub issue and pull
  request templates.~~
- ~~Create the v0.1.0 milestone and scoped Issues #1–#12.~~

### Day 2 — 2026-08-13 — Snapshot core

- ~~Capture Git commit, branch, detached-HEAD state, and dirty state.~~
- ~~Capture Python version, implementation, operating system, architecture,
  and machine.~~
- ~~Capture installed Python distribution versions deterministically.~~
- ~~Capture optional NVIDIA GPU, driver, and CUDA metadata without requiring a
  GPU.~~
- ~~Define strict versioned snapshot models, 12-character run IDs, and UTC
  timestamps.~~
- ~~Persist readable YAML atomically with collision protection and schema
  validation.~~
- ~~Parse repository-local UTF-8 YAML configs safely and record their path,
  SHA-256 hash, values, and optional experiment command.~~
- ~~Implement `ml-runtrace snapshot` with actionable success and error output.~~

### Day 3 — 2026-08-14 — CLI and storage

- ~~Implement idempotent `ml-runtrace init` at the containing Git root.~~
- ~~Create and validate `runtrace.toml` and `.runtrace/runs/` without replacing
  existing user data.~~
- ~~Support validated newest-first storage listing and full or unique-prefix
  run lookup.~~
- ~~Implement compact, literal-safe `ml-runtrace list` output and its empty
  state.~~
- ~~Implement complete, sectioned `ml-runtrace show <run-id>` output.~~
- ~~Handle uninitialized projects, corrupt snapshots, and missing or ambiguous
  IDs without avoidable tracebacks.~~
- ~~Cover the complete init → snapshot → list → show workflow with unit and
  real CLI tests.~~

### Day 4 — 2026-08-15 — Experiment diff

- ~~Recursively compare nested configuration mappings and arrays with stable
  dotted and indexed paths.~~
- ~~Report configuration additions, removals, and changes, including command,
  path, and content hash.~~
- ~~Compare Git commit, branch, detached state, and dirty state.~~
- ~~Compare Python runtime, platform fields, and dependency additions,
  removals, and version changes.~~
- ~~Render deterministic Configuration, Git, Runtime, and Environment sections
  with literal-safe Rich output.~~
- ~~Support full and unique abbreviated IDs plus clear identical, missing, and
  ambiguous results.~~
- ~~Verify focused tests, the full suite, lint, formatting, lockfile, package
  builds, command help, and a real two-snapshot CLI smoke test.~~

### Day 5 — 2026-08-16 — Release readiness

- ~~Expand the README into the complete user guide.~~
- ~~Add a copy-paste Quick Start covering the full local workflow.~~
- ~~Add verified terminal output or a screenshot of the core workflow.~~
- ~~Maintain contributor guidance in `CONTRIBUTING.md`.~~
- ~~Maintain private vulnerability reporting guidance in `SECURITY.md`.~~
- ~~Maintain user-visible changes under `CHANGELOG.md` Unreleased.~~
- ~~Verify installation and the full workflow in a clean isolated
  environment.~~
- ~~Run the full test and quality suite on Windows.~~
- ~~Run CI on Linux with Python 3.10, 3.11, and 3.12.~~
- ~~Perform the final scope, packaging metadata, and release-readiness audit.~~

### Day 6 — 2026-08-17 — v0.1.0 release

- ~~Recheck `ml-runtrace` availability through PyPI's JSON and Simple API
  endpoints.~~
- ~~Record maintainer approval for strategy A in Issue #24: distribution
  `ml-runtrace`, import `ml_runtrace`, command `ml-runtrace`, module
  `python -m ml_runtrace`, and no aliases.~~
- ~~Rename the source package, internal imports, console entry point, module
  entry point, user-facing command guidance, and focused tests.~~
- ~~Add a network-free two-order install/uninstall coexistence audit using a
  synthetic distribution that owns the `runtrace` import and command.~~
- ~~Repeat the two-order and both-uninstall audit against the real PyPI
  `runtrace==0.3.2` wheel.~~
- ~~Obtain green Linux CI for the migrated package on Python 3.10–3.12 and
  the packaging smoke job.~~
- [ ] Configure the protected `pypi` environment and pending trusted publisher
  with maintainer-controlled deployment approval.
- ~~Freeze the v0.1.0 feature scope and keep publication outside automatic
  release-preparation work.~~
- ~~Change the development version to `0.1.0` and finalize changelog and release
  notes.~~
- ~~Add the release runbook, immutable action pins, Linux packaging smoke job,
  and read-only candidate workflow.~~
- ~~Build and inspect the final source distribution and wheel, including
  metadata and file-content checks.~~
- ~~Install the exact wheel in a fresh environment and run the complete
  acceptance workflow.~~
- ~~Rebuild, inspect, and smoke-test the replacement candidate after the
  public-name migration; prior candidate hashes are invalidated.~~
- [ ] Run the candidate workflow for the reviewed commit and compare recorded
  artifact hashes.
- [ ] Create and push the signed or annotated `v0.1.0` tag.
- [ ] Publish the distribution to PyPI.
- [ ] Publish the GitHub Release and attach final release notes.
- [ ] Replace source-development installation guidance with the verified PyPI
  installation command.

## 2026-08-12 — Day 1 repository bootstrap

### Scope

- Confirm the RunTrace product name and public repository.
- Establish a Python package and CLI skeleton for Issue #1.
- Add the minimum OSS governance, test, lint, and CI files required by the
  project plan.
- Keep snapshot, storage, show, list, and diff behavior out of this change so
  each can be implemented and reviewed through its own issue.

### Decisions

- Package layout: `src/runtrace` with Python 3.10+ support.
- PyPI already contains an unrelated `runtrace` distribution. Use
  `ml-runtrace` as the planned distribution name while retaining RunTrace as
  the project name and `runtrace` as the CLI command. Availability must be
  rechecked immediately before the first release.
- Development environment: uv with a committed lockfile.
- CLI framework: Typer; current public behavior is limited to help and version.
- Runtime dependencies are restricted to the planned stack: Typer, Rich,
  PyYAML, and Pydantic.
- Persistence remains local-only; `.runtrace/` is ignored until storage policy
  is implemented deliberately.
- CI targets Linux on Python 3.10, 3.11, and 3.12.

### Implemented

- [x] README project positioning and source-development instructions
- [x] MIT license
- [x] `pyproject.toml` and `src` package layout
- [x] `runtrace --help` and `runtrace --version`
- [x] Initial CLI tests
- [x] Ruff and pytest configuration
- [x] GitHub Actions CI workflow
- [x] Contributor, security, agent, issue, and pull request guidance

### Verification

- `uv sync --all-groups`: passed; lockfile resolved 22 packages and installed
  `ml-runtrace==0.1.0.dev0`.
- `uv lock --check`: passed.
- `uv run pytest -p no:cacheprovider`: 3 tests passed on Windows with Python
  3.12.7 and pytest 8.4.2.
- `uv run ruff check . --no-cache`: passed.
- `uv run ruff format --check . --no-cache`: 13 files already formatted.
- GitHub YAML parse: 4 workflow/template files parsed successfully with
  PyYAML.
- `uv run runtrace --version`: returned `runtrace 0.1.0.dev0`.
- `uv run --locked python -m runtrace --help`: passed.
- `uv build`: produced both `ml_runtrace-0.1.0.dev0.tar.gz` and the universal
  `ml_runtrace-0.1.0.dev0-py3-none-any.whl` in a temporary verification
  directory.
- `git diff --check`: passed.

### GitHub coordination

- Public repository and maintainer access verified. The repository started with
  zero issues and zero milestones.
- Created the [`v0.1.0` milestone](https://github.com/Corvus-226/RunTrace/milestone/1)
  with a due date of 2026-08-17.
- Created and assigned all twelve scoped backlog items:
  - [#1 Initialize Python package and CLI skeleton](https://github.com/Corvus-226/RunTrace/issues/1)
  - [#2 Capture Git repository metadata](https://github.com/Corvus-226/RunTrace/issues/2)
  - [#3 Capture Python runtime and installed dependencies](https://github.com/Corvus-226/RunTrace/issues/3)
  - [#4 Implement snapshot persistence](https://github.com/Corvus-226/RunTrace/issues/4)
  - [#5 Implement `runtrace init`](https://github.com/Corvus-226/RunTrace/issues/5)
  - [#6 Implement `runtrace snapshot`](https://github.com/Corvus-226/RunTrace/issues/6)
  - [#7 Implement `runtrace list`](https://github.com/Corvus-226/RunTrace/issues/7)
  - [#8 Implement `runtrace show`](https://github.com/Corvus-226/RunTrace/issues/8)
  - [#9 Implement experiment diff](https://github.com/Corvus-226/RunTrace/issues/9)
  - [#10 Add GitHub Actions test matrix](https://github.com/Corvus-226/RunTrace/issues/10)
  - [#11 Write Quick Start documentation](https://github.com/Corvus-226/RunTrace/issues/11)
  - [#12 Prepare v0.1.0 release](https://github.com/Corvus-226/RunTrace/issues/12)
- Verified the milestone contains exactly 12 open issues. Implementation issues
  use the `enhancement` label; documentation work uses `documentation`.

### Maintainer review handoff

- The staged Day 1 / Issue #1 diff was handed to the maintainer with the
  original planning document explicitly excluded.
- On 2026-08-12, the maintainer authorized commit, push, and pull request
  submission for `codex/issue-1-cli-skeleton`.

### Submission record

- Created commit `76218b3` (`feat: initialize package and CLI skeleton`) and
  pushed `codex/issue-1-cli-skeleton` to `origin`.
- Opened [pull request #13](https://github.com/Corvus-226/RunTrace/pull/13)
  against `main`. The pull request closes #1, references #10, uses the
  `enhancement` label, and belongs to the `v0.1.0` milestone.
- GitHub Actions run `31570794406` passed on Python 3.10, 3.11, and 3.12.
- The original planning document remains excluded from the branch.

### Next scoped work

1. Complete the maintainer's final GitHub review of pull request #13.
2. Merge Issue #1 only after the final CI run passes.
3. Record how the CI work in #10 is resolved, then start Git metadata work in
   #2 on a new branch.

## 2026-08-12 — Issue #2 Git metadata

### Coordination

- The maintainer authorized continued implementation after the final Issue #1
  CI run passed.
- Merged [pull request #13](https://github.com/Corvus-226/RunTrace/pull/13)
  into `main` as `0eb9da6`; Issue #1 closed automatically.
- Recorded the implementation and successful Python 3.10–3.12 CI runs on
  [Issue #10](https://github.com/Corvus-226/RunTrace/issues/10), then closed
  that issue as completed.
- Started Issue #2 from the updated `main` branch on
  `codex/issue-2-git-metadata`.

### Scope

- Capture the full commit SHA, current branch, detached-HEAD state, and dirty
  working-tree state.
- Count tracked modifications and untracked files as dirty.
- Keep the implementation read-only and based on the installed Git CLI.
- Do not inspect or retain remotes, patches, source contents, credentials, or
  environment-variable values.

### Decisions

- Use a frozen, slotted `GitMetadata` dataclass with explicit `branch: None`
  and `detached: true` values for detached HEADs.
- Invoke Git with argument lists and `git -C <path>` rather than a shell, so
  repository paths containing spaces work on Windows and Linux.
- Disable optional Git locks and terminal prompts, and bound each local Git
  command to ten seconds.
- Raise `GitMetadataError` with concise recovery guidance for missing paths,
  non-repositories, repositories without a readable commit, missing Git, and
  failed metadata commands.
- Keep Git fixture identity local to each commit command and disable global and
  system Git configuration in tests; no contributor Git identity is required.

### Implemented

- [x] Focused `runtrace.git` metadata module with no new dependency
- [x] Clean branch and full commit SHA capture
- [x] Tracked and untracked dirty-tree detection
- [x] Explicit detached-HEAD representation
- [x] Paths-with-spaces coverage
- [x] Actionable non-repository and command-failure errors
- [x] Changelog entry for the new capture capability

### Verification

- `uv run pytest -p no:cacheprovider`: 11 tests passed on Windows with Python
  3.12.7, including 8 focused Git tests.
- `uv run ruff check . --no-cache`: passed.
- `uv run ruff format --check . --no-cache`: 15 files already formatted.
- An initial non-repository test exposed that the system temporary directory
  sits below another Git working tree. The fixture now sets a Git ceiling for
  that case, preserving intentional support for collecting metadata from a
  repository subdirectory while making the failure test isolated.

### Submission record

- Created commit `5d16004` (`feat: capture Git repository metadata`) and
  pushed `codex/issue-2-git-metadata` to `origin`.
- Opened [pull request #14](https://github.com/Corvus-226/RunTrace/pull/14)
  against `main`. The pull request closes #2, uses the `enhancement` label, and
  belongs to the `v0.1.0` milestone.
- GitHub Actions run `31572928468` passed on Python 3.10, 3.11, and 3.12.
- The original planning document remains untracked and excluded.

## 2026-08-12 — Issue #3 environment metadata

### Coordination

- The maintainer authorized continued implementation after reviewing the
  one-issue-per-branch workflow.
- Merged [pull request #14](https://github.com/Corvus-226/RunTrace/pull/14)
  into `main` as `404ad5b`; Issue #2 closed automatically.
- Started Issue #3 from the updated `main` branch on
  `codex/issue-3-environment-metadata`.

### Scope

- Capture Python version and implementation.
- Capture operating system, release, architecture, and machine information.
- Capture installed distribution names and versions with normalized names and
  stable ordering.
- Detect NVIDIA GPU names, driver versions, and CUDA version when available.
- Never capture environment variables, tokens, credentials, package source
  URLs, installer details, or package contents.

### Decisions

- Use frozen, slotted dataclasses for runtime, platform, GPU, and aggregate
  environment metadata.
- Use only the standard library; no new runtime dependency is required.
- Normalize distribution names using the PEP 503 separator rule and sort the
  resulting mapping. If malformed environments expose duplicate metadata for
  one normalized name, select deterministically from sorted versions.
- Read only the standard distribution `Name` and `Version` fields; direct URL
  and installer metadata are deliberately ignored.
- Treat `nvidia-smi` as an optional, five-second best-effort probe. Missing
  commands, timeouts, non-zero exits, empty results, and a failed CUDA summary
  probe do not prevent environment capture.
- Invoke `nvidia-smi` without a shell and capture no environment-variable
  values.

### Implemented

- [x] Python interpreter version and implementation capture
- [x] Operating system, release, architecture, and machine capture
- [x] Normalized, deduplicated, stably ordered package mapping
- [x] Optional GPU names, driver versions, and CUDA version capture
- [x] Graceful GPU detection fallback without hardware or `nvidia-smi`
- [x] Tests proving package source URLs are excluded
- [x] Changelog entry for the new environment capability

### Verification

- `uv run pytest -p no:cacheprovider`: 20 tests passed on Windows with Python
  3.12.7, including 9 focused environment tests.
- `uv run ruff check . --no-cache`: passed.
- `uv run ruff format --check . --no-cache`: 17 files already formatted.
- `uv lock --check`: passed with the existing 22-package lock graph.
- `git diff --check`: passed.
- A real local capture reported CPython 3.12.7 on 64-bit Windows, produced a
  sorted 20-distribution mapping, and detected optional GPU metadata without
  exposing device details in the verification output.

### Submission record

- Created commit `a19c610` (`feat: capture Python environment metadata`) and
  pushed `codex/issue-3-environment-metadata` to `origin`.
- Opened [pull request #15](https://github.com/Corvus-226/RunTrace/pull/15)
  against `main`. The pull request closes #3, uses the `enhancement` label, and
  belongs to the `v0.1.0` milestone.
- GitHub Actions run `31578268151` passed on Python 3.10, 3.11, and 3.12.
- The original planning document remains untracked and excluded.

## 2026-08-12 — Issue #4 snapshot persistence

### Coordination

- Merged [pull request #15](https://github.com/Corvus-226/RunTrace/pull/15)
  into `main` as `d59f848`; Issue #3 closed automatically.
- Started Issue #4 from the updated `main` branch on
  `codex/issue-4-snapshot-persistence`.

### Scope

- Define a versioned, validated snapshot schema for Git, runtime, environment,
  hardware, and experiment metadata.
- Generate short run IDs and aware UTC timestamps.
- Persist human-readable YAML beneath `.runtrace/runs/` without silently
  replacing an existing snapshot.
- Load, validate, list, and resolve snapshots by full or unique abbreviated
  run ID.
- Keep storage local-only and reject paths that escape the initialized project.

### Decisions

- Use strict, frozen Pydantic models that reject unknown fields. Normalize
  timestamps to UTC and persist a schema version so incompatible future
  changes can be detected deliberately.
- Generate 12-character lowercase hexadecimal IDs from 48 bits of
  cryptographic randomness. Short prefixes are accepted only when they match
  exactly one stored snapshot.
- Require an existing `.runtrace/` directory rather than letting storage
  implicitly initialize a project; Issue #5 remains responsible for `init`.
- Write each YAML document to a same-directory temporary file, flush and sync
  it, then publish it with an atomic replacement. An exclusive per-run lock
  and a pre-existing destination check prevent RunTrace writers from silently
  replacing duplicate IDs.
- Resolve metadata, run directories, and snapshot files before use. Reject
  symlinks or files that escape the project storage boundary.
- Parse with PyYAML's safe loader, validate the complete Pydantic schema, and
  verify that the declared run ID matches the filename before returning data.
- Persist only the planned reproducibility metadata. Environment variables,
  credentials, package source URLs, source code, and remote services remain
  outside the storage model.

### Implemented

- [x] Pydantic schema for snapshot, Git, runtime, platform, environment,
  hardware, GPU, and experiment metadata
- [x] Collision-resistant run ID and aware UTC timestamp defaults
- [x] Readable, versioned YAML serialization beneath `.runtrace/runs/`
- [x] Atomic saves with temporary-file cleanup and duplicate-ID protection
- [x] Validated loading and filename/run-ID consistency checks
- [x] Newest-first listing and full or unique abbreviated ID resolution
- [x] Actionable errors for missing, ambiguous, locked, invalid, or corrupt runs
- [x] Storage-boundary and path-traversal protection
- [x] Focused success, conflict, failure, corruption, and symlink tests

### Verification

- `uv run pytest -p no:cacheprovider`: 37 tests passed on Windows with Python
  3.12.7, including 17 focused snapshot storage tests.
- `uv run ruff check . --no-cache`: passed.
- `uv run ruff format --check . --no-cache`: 20 files already formatted.
- `uv lock --check`: passed with the existing 22-package lock graph; no new
  dependency was introduced.
- `uv build`: produced both `ml_runtrace-0.1.0.dev0.tar.gz` and the universal
  `ml_runtrace-0.1.0.dev0-py3-none-any.whl` in a temporary verification
  directory.
- `git diff --check`: passed.

### Submission record

- Created commit `b320dd1` (`feat: persist validated experiment snapshots`)
  and pushed `codex/issue-4-snapshot-persistence` to `origin`.
- Opened [pull request #16](https://github.com/Corvus-226/RunTrace/pull/16)
  against `main`. The pull request closes #4, uses the `enhancement` label, is
  assigned to the maintainer, and belongs to the `v0.1.0` milestone.
- GitHub Actions run `31588934022` passed on Python 3.10, 3.11, and 3.12.
- The original planning document remains untracked and excluded.

## 2026-08-12 — Issue #5 project initialization

### Coordination

- Merged [pull request #16](https://github.com/Corvus-226/RunTrace/pull/16)
  into `main` as `41aba97`; Issue #4 closed automatically.
- Assigned Issue #5 to the maintainer and started from the updated `main`
  branch on `codex/issue-5-init-command`.

### Scope

- Add the `runtrace init` command.
- Locate the Git work-tree root even when invoked from a nested directory or
  an empty repository without a commit.
- Create `.runtrace/runs/` and a minimal `runtrace.toml` at the repository root.
- Preserve existing configuration and stored runs on repeated invocation.
- Fail without writing files when the current directory is not in a Git
  repository or an initialization path is unsafe.

### Decisions

- Keep Git discovery in `runtrace.git` and project initialization in a focused
  `runtrace.project` module; the CLI only translates domain results into output
  and exit codes.
- Use `git rev-parse --show-toplevel` through the existing bounded, non-shell
  Git runner. Unlike snapshot Git capture, initialization does not require an
  existing commit.
- Always initialize the resolved work-tree root rather than the process's
  nested working directory. Print both the required success sentence and the
  resolved project location.
- Create a minimal, stable `[runtrace]` configuration with schema version 1.
  Use exclusive file creation and never parse, replace, or normalize a user's
  existing `runtrace.toml` during initialization.
- Treat existing directories and files as state to preserve. Validate their
  types and resolved locations, rejecting metadata, run, or configuration
  paths that escape their allowed project boundary.
- Keep initialization local-only. It reads only Git's work-tree location and
  does not capture metadata, environment values, credentials, source code, or
  network state.

### Implemented

- [x] `runtrace init` CLI command and concise non-zero error handling
- [x] Git-root discovery from repository roots and nested directories
- [x] Support for empty Git repositories without a commit
- [x] `.runtrace/runs/` creation using `pathlib.Path`
- [x] Minimal `runtrace.toml` creation with an explicit schema version
- [x] Idempotent preservation of custom configuration and stored runs
- [x] File-type, symlink, and project-boundary validation
- [x] Updated snapshot-storage guidance to recommend `runtrace init`
- [x] CLI coverage for first use, repeated use, non-Git paths, invalid paths,
  and escaped run directories

### Verification

- Focused `uv run pytest` coverage for CLI, Git, and storage: 33 tests passed
  on Windows with Python 3.12.7.
- `uv run ruff check` on the changed Python files: passed.
- `uv run ruff format --check` on the changed Python files: all 6 files were
  already formatted.
- A real console-script smoke test initialized an empty Git repository twice,
  printed the resolved project path both times, preserved the generated
  configuration, and kept `.runtrace/runs/` intact.
- `uv run pytest -p no:cacheprovider`: 43 tests passed on Windows with Python
  3.12.7.
- `uv run ruff check . --no-cache`: passed.
- `uv run ruff format --check . --no-cache`: 21 files already formatted.
- `uv lock --check`: passed with the existing 22-package lock graph; no new
  dependency was introduced.
- `uv build`: produced both `ml_runtrace-0.1.0.dev0.tar.gz` and the universal
  `ml_runtrace-0.1.0.dev0-py3-none-any.whl` in a temporary verification
  directory, which was removed after validation.
- `uv run runtrace --help`: listed `init` with its Git-repository description.
- `git diff --check`: passed.

### Submission record

- Created commit `ac8720e` (`feat: add idempotent project initialization`)
  and pushed `codex/issue-5-init-command` to `origin`.
- Opened [pull request #17](https://github.com/Corvus-226/RunTrace/pull/17)
  against `main`. The pull request closes #5, uses the `enhancement` label, is
  assigned to the maintainer, and belongs to the `v0.1.0` milestone.
- GitHub Actions run `31590157309` passed on Python 3.10, 3.11, and 3.12.
- The original planning document remains untracked and excluded.

## 2026-08-12 — Issue #6 experiment snapshot command

### Coordination

- Merged [pull request #17](https://github.com/Corvus-226/RunTrace/pull/17)
  into `main` as `9ce4cd8`; Issue #5 closed automatically.
- Assigned Issue #6 to the maintainer and started from the updated `main`
  branch on `codex/issue-6-snapshot-command`.

### Scope

- Add `runtrace snapshot` with optional `--name`, `--config`, and `--command`.
- Capture and assemble the existing Git, Python runtime, dependency, platform,
  and optional hardware metadata into the versioned snapshot schema.
- Safely load a YAML config, record its portable path, raw SHA-256 digest, and
  parsed values, then persist the complete snapshot.
- Require an initialized RunTrace project and fail before writing when config
  input is missing, unreadable, unsafe, or unsupported.
- Print the generated run ID and local YAML path.

### Decisions

- Keep config loading in `runtrace.config`, orchestration and model conversion
  in `runtrace.snapshot`, metadata capture in its existing modules, and CLI
  presentation in `runtrace.cli`.
- Require `runtrace.toml`, `.runtrace/`, and `.runtrace/runs/` before capture;
  missing project state directs the user to `runtrace init` without creating
  files implicitly.
- Resolve user config paths relative to the invocation directory, require the
  resolved file to remain inside the Git repository, and persist only its
  POSIX-style repository-relative path.
- Hash the original config bytes with SHA-256, decode UTF-8 YAML with the safe
  loader, and accept only finite JSON-compatible values. Reject YAML dates,
  sets, non-string map keys, non-finite numbers, unsafe tags, invalid encoding,
  and cyclic or otherwise unsupported structures with concise guidance.
- Exclude only `.runtrace`'s generated local data from the snapshot dirty-tree
  check so a prior snapshot does not make the next run dirty. All other tracked
  and untracked changes, including `runtrace.toml` until committed, still count.
- Convert existing frozen metadata dataclasses into strict Pydantic snapshot
  models explicitly. Missing GPU/CUDA data remains a normal `null` hardware
  value rather than an error.
- Persist explicitly supplied config values and commands locally. Continue to
  exclude environment-variable values, credentials, package source URLs,
  source contents, remotes, patches, and automatic uploads.

### Implemented

- [x] `runtrace snapshot` command and optional name/config/command arguments
- [x] Initialized-project validation before metadata capture
- [x] Safe UTF-8 YAML loading and raw SHA-256 hashing
- [x] Repository-relative config path normalization and boundary protection
- [x] Strict JSON-compatible config validation
- [x] Git/runtime/platform/dependency/GPU model assembly
- [x] Atomic persistence through the existing snapshot store
- [x] Run-ID and local-path success output
- [x] Minimal, full, dirty-tree, prior-snapshot, no-GPU, config, and failure tests
- [x] README privacy disclosure for explicit config and command capture

### Verification

- `uv run pytest -p no:cacheprovider`: 62 tests passed on Windows with Python
  3.12.7.
- `uv run ruff check . --no-cache`: passed.
- `uv run ruff format --check . --no-cache`: 25 files already formatted.
- `uv lock --check`: passed with the existing 22-package lock graph; no new
  dependency was introduced.
- A real console-script smoke test completed `init`, committed a clean baseline,
  and ran `snapshot` with name, config, and command options. The resulting local
  YAML contained a 12-character run ID, aware UTC timestamp, full commit,
  `main` branch, `dirty: false`, relative config path, and SHA-256 hash. The
  temporary repository was removed after validation.
- `uv build`: produced both `ml_runtrace-0.1.0.dev0.tar.gz` and the universal
  `ml_runtrace-0.1.0.dev0-py3-none-any.whl` in a temporary verification
  directory, which was removed after validation.
- `uv run runtrace snapshot --help`: listed the name, config, and command
  options with their expected types.
- `git diff --check`: passed.

### Submission record

- Created commit `37a6c5a` (`feat: capture experiment snapshots from CLI`)
  and pushed `codex/issue-6-snapshot-command` to `origin`.
- Opened [pull request #18](https://github.com/Corvus-226/RunTrace/pull/18)
  against `main`. The pull request closes #6, uses the `enhancement` label, is
  assigned to the maintainer, and belongs to the `v0.1.0` milestone.
- GitHub Actions run `31591666159` passed on Python 3.10, 3.11, and 3.12.
- The original planning document remains untracked and excluded.

## 2026-08-12 — Issue #7 local run listing

### Coordination

- Merged [pull request #18](https://github.com/Corvus-226/RunTrace/pull/18)
  into `main` as `ec5e476`; Issue #6 closed automatically.
- Assigned Issue #7 to the maintainer and started from the updated `main`
  branch on `codex/issue-7-list-command`.

### Scope

- Add `runtrace list` for a fast local summary without a service.
- Display run ID, optional name, short commit, dirty state, and creation time.
- Preserve the storage layer's deterministic newest-first ordering.
- Provide a friendly success state when no snapshots exist and actionable
  errors when stored records are corrupt.

### Decisions

- Keep snapshot reading and validation in `SnapshotStore`; add a focused
  `runtrace.presentation` module for terminal rendering and keep the CLI layer
  responsible only for project lookup, error translation, and orchestration.
- Display the full 12-character run ID so every row can be copied without
  relying on prefix uniqueness. Display seven commit characters, `yes`/`no`
  dirty values, and UTC times in `YYYY-MM-DD HH:MM UTC` form.
- Render missing names as an em dash. Collapse whitespace and constrain names
  to 24 terminal columns for a compact table, while preserving stored values.
- Construct user-supplied names as Rich `Text` rather than markup so names such
  as `[bold]...[/bold]` remain literal and cannot affect terminal styling.
- Return success with guidance to run `runtrace snapshot` when storage is empty.
  Let existing schema and YAML validation errors identify the corrupt filename
  and recommend repair or removal without exposing a traceback.

### Implemented

- [x] `runtrace list` command and initialized-project validation
- [x] Compact Rich table with run ID, name, commit, dirty, and created columns
- [x] Deterministic newest-first output from validated storage records
- [x] Clear em-dash fallback for missing names
- [x] Literal, single-line, width-bounded user-name rendering
- [x] Friendly empty state with next-command guidance
- [x] Actionable corrupt-record and uninitialized-project failures
- [x] Empty, single-run, multiple-run, literal-name, and corruption CLI tests

### Verification

- `uv run pytest -p no:cacheprovider`: 67 tests passed on Windows with Python
  3.12.7.
- `uv run ruff check . --no-cache`: passed.
- `uv run ruff format --check . --no-cache`: 27 files already formatted.
- `uv lock --check`: passed with the existing 22-package lock graph; no new
  dependency was introduced.
- A real console-script smoke test initialized and committed a temporary Git
  project, recorded a clean snapshot, modified a tracked file, recorded a dirty
  snapshot, and listed both. The dirty run appeared first with `yes`; the clean
  run appeared second with `no`. The temporary repository was removed.
- `uv build`: produced both `ml_runtrace-0.1.0.dev0.tar.gz` and the universal
  `ml_runtrace-0.1.0.dev0-py3-none-any.whl` in a temporary verification
  directory, which was removed after validation.
- `uv run runtrace list --help`: described newest-first local run listing.
- `git diff --check`: passed.

### Submission record

- Created commit `e74d3eb` (`feat: list local experiment snapshots`) and
  pushed `codex/issue-7-list-command` to `origin`.
- Opened [pull request #19](https://github.com/Corvus-226/RunTrace/pull/19)
  against `main`. The pull request closes #7, uses the `enhancement` label, is
  assigned to the maintainer, and belongs to the `v0.1.0` milestone.
- GitHub Actions run `31592402274` passed on Python 3.10, 3.11, and 3.12.
- The original planning document remains untracked and excluded.

## 2026-08-12 — Issue #8 complete run display

### Coordination

- Merged [pull request #19](https://github.com/Corvus-226/RunTrace/pull/19)
  into `main` as `5f27010`; Issue #7 closed automatically.
- Assigned Issue #8 to the maintainer and started from the updated `main`
  branch on `codex/issue-8-show-command`.

### Scope

- Add `runtrace show <run-id>` for a complete stored reproducibility record.
- Accept a full run ID or a unique abbreviated ID.
- Present overview, Git, runtime, environment, hardware, and experiment values
  in labeled terminal sections.
- Represent optional values clearly and preserve every stored value while
  formatting output.
- Return actionable errors for unknown and ambiguous ID prefixes.

### Decisions

- Reuse `SnapshotStore.load` for full/unique-prefix resolution and complete
  schema validation; the command never reads the live Git repository,
  environment, hardware, or config file to supplement historical data.
- Extend the focused presentation module with Overview, Git, Runtime,
  Environment, Hardware, and Experiment sections. Show full commit and run IDs,
  complete UTC timestamps, all recorded packages, and yes/no booleans.
- Use an em dash for missing optional scalar values and an explicit
  `No packages recorded.` state for an empty package mapping.
- Format captured config values as sorted, indented JSON so nested stored data
  remains deterministic and distinguishable from terminal labels. A config
  file whose stored value is JSON `null` remains distinct from no config path.
- Render stored names, commands, paths, packages, GPU names, and versions as
  Rich `Text`, not markup. Long fields use folding rather than ellipsis; a
  regression test specifically verifies the complete 64-character config hash.
- Do not infer or expose anything that was not present in the validated YAML
  snapshot.

### Implemented

- [x] `runtrace show <run-id>` command and initialized-project validation
- [x] Full and unique abbreviated run-ID lookup
- [x] Six labeled sections covering every persisted snapshot component
- [x] Full-length commit, timestamp, config hash, package, and config display
- [x] Explicit optional-value, empty-package, and no-config states
- [x] Deterministic JSON rendering for nested captured config values
- [x] Literal user-text rendering and fold-without-truncation behavior
- [x] Actionable missing and ambiguous ID errors without tracebacks
- [x] Full, abbreviated, optional, missing, ambiguous, and literal-text tests

### Verification

- `uv run pytest -p no:cacheprovider`: 73 tests passed on Windows with Python
  3.12.7.
- `uv run ruff check . --no-cache`: passed.
- `uv run ruff format --check . --no-cache`: 28 files already formatted.
- `uv lock --check`: passed with the existing 22-package lock graph; no new
  dependency was introduced.
- A real console-script smoke test initialized and committed a temporary Git
  project, captured a named run with a YAML config and command, then used the
  generated ID's six-character prefix with `show`. All six sections, relative
  config path, and complete 64-character SHA-256 hash were verified. The
  temporary repository was removed.
- `uv build`: produced both `ml_runtrace-0.1.0.dev0.tar.gz` and the universal
  `ml_runtrace-0.1.0.dev0-py3-none-any.whl` in a temporary verification
  directory, which was removed after validation.
- `uv run runtrace show --help`: described the required full or unique
  abbreviated run-ID argument.
- `git diff --check`: passed.

### Submission record

- Created commit `4a4210c` (`feat: show complete experiment snapshots`) and
  pushed `codex/issue-8-show-command` to `origin`.
- Opened [pull request #20](https://github.com/Corvus-226/RunTrace/pull/20)
  against `main`. The pull request closes #8, uses the `enhancement` label, is
  assigned to the maintainer, and belongs to the `v0.1.0` milestone.
- GitHub Actions run `31593293257` passed on Python 3.10, 3.11, and 3.12.
- The original planning document remains untracked and excluded.

## 2026-08-12 — Issue #9 experiment diff

### Coordination

- Merged [pull request #20](https://github.com/Corvus-226/RunTrace/pull/20)
  into `main` as `6469973`; Issue #8 closed automatically.
- Assigned Issue #9 to the maintainer and started from the updated `main`
  branch on `codex/issue-9-experiment-diff`.

### Scope

- Add `runtrace diff <run-a> <run-b>` for reproducibility-focused comparison of
  two persisted experiment snapshots.
- Compare nested configuration values, Git state, Python runtime and platform,
  and installed dependency versions.
- Distinguish added, removed, and changed values in deterministic section and
  path order.
- Accept full or unique abbreviated run IDs and preserve storage-layer error
  behavior.

### Decisions

- Keep comparison logic in a deterministic `runtrace.diff` module with frozen
  result models. The function accepts two validated snapshots and has no
  filesystem, terminal, or process-state dependencies.
- Treat run ID, run name, and timestamp as snapshot identity rather than
  reproducibility differences. Display both IDs in the comparison heading but
  do not report those identity fields as changes.
- Compare experiment command, config path, config SHA-256, and config values.
  Recurse through JSON mappings and arrays with dotted, bracket-quoted, and
  indexed paths so leaf-level changes remain stable and actionable.
- Compare Git commit, branch, detached state, and dirty state; compare Python
  version, implementation, platform fields, and every installed distribution
  version. Sort mapping keys and package names for deterministic output.
- Represent missing values internally with a private sentinel so an absent
  field remains distinct from an explicit JSON `null` value.
- Render Configuration, Git, Runtime, and Environment in fixed order. Give
  every change its own path line and folded before/after rows so long paths and
  hashes remain complete at narrow terminal widths.
- Construct all stored values as Rich `Text` rather than markup, preserving
  literal brackets and preventing stored content from affecting presentation.

### Implemented

- [x] Pure structured snapshot comparison with fixed sections and change kinds
- [x] Recursive mapping and array paths with special-key escaping
- [x] Configuration command, path, hash, and value comparison
- [x] Git commit, branch, detached-state, and dirty-state comparison
- [x] Python, implementation, platform, and dependency comparison
- [x] Deterministic added, removed, and changed classification
- [x] Sectioned, fold-without-truncation, literal-safe Rich presentation
- [x] Full and unique abbreviated ID support through validated storage lookup
- [x] Friendly identical, missing, ambiguous, corrupt, and uninitialized states
- [x] Focused model, CLI, ordering, nested-array, and rendering regression tests
- [x] README status, changelog entry, and detailed daily delivery checklist

### Verification

- `uv run pytest -p no:cacheprovider`: 85 tests passed on Windows with Python
  3.12.7.
- `uv run ruff check . --no-cache`: passed.
- `uv run ruff format --check . --no-cache`: 30 files already formatted.
- `uv lock --check`: passed with the existing 22-package lock graph; no new
  dependency was introduced.
- A real console-script smoke test initialized and committed a temporary Git
  project, captured two runs from different nested YAML configs and commands
  across two commits, then compared them with six-character IDs. Configuration
  and Git sections, recursive array paths, and all three change kinds were
  verified. The temporary repository was removed.
- `uv build`: produced both `ml_runtrace-0.1.0.dev0.tar.gz` and the universal
  `ml_runtrace-0.1.0.dev0-py3-none-any.whl` in a temporary verification
  directory, which was removed after validation.
- `uv run runtrace diff --help`: described both required full or unique
  abbreviated run-ID arguments.
- `git diff --check`: passed.

### Submission record

- Created commit `bdaca0a` (`feat: compare experiment snapshots`) and pushed
  `codex/issue-9-experiment-diff` to `origin`.
- Opened [pull request #21](https://github.com/Corvus-226/RunTrace/pull/21)
  against `main`. The pull request closes #9, uses the `enhancement` label, is
  assigned to the maintainer, and belongs to the `v0.1.0` milestone.
- GitHub Actions run `31594849751` passed on Python 3.10, 3.11, and 3.12.
- The original planning document remains untracked and excluded.

## 2026-08-12 — Issue #11 Quick Start documentation

### Coordination

- Merged [pull request #21](https://github.com/Corvus-226/RunTrace/pull/21)
  into `main` as `5b92f1b`; Issue #9 closed automatically.
- Assigned Issue #11 to the maintainer and started from the updated `main`
  branch on `codex/issue-11-quick-start-docs`.

### Scope

- Complete the README first screen and a copyable Quick Start.
- Add `docs/getting-started.md` for the complete init → snapshot → list → show
  → diff workflow.
- Explain current source installation and the planned `ml-runtrace` PyPI
  distribution without presenting an unpublished release as available.
- Explain local-first positioning, privacy behavior, storage, supported
  platforms, and current project maturity.
- Verify the documented workflow in a clean environment before release.

### Decisions

- Lead with the user problem, local/server-free position, pre-release status,
  and a four-step first experiment. Keep contributor setup in a separate
  Development section rather than making it the first user path.
- Clearly label `python -m pip install ml-runtrace` as the post-v0.1.0 command.
  For the current pre-release, document installation from a cloned source tree
  inside an isolated environment.
- Use one-line CLI examples that work across PowerShell, Command Prompt, and
  POSIX shells. Avoid machine-specific absolute paths, shell-only environment
  variables, and secret-like sample data.
- State that `--command` records but does not execute a command, that config
  values are intentionally persisted, and that users should review snapshot
  YAML before sharing it.
- Explain the Git preconditions and the difference between `runtrace.toml` and
  local `.runtrace/` data, including the user's choice to ignore or version run
  records.
- Use representative text output instead of a platform-specific image so IDs,
  paths, terminal widths, and colors are visibly illustrative rather than
  claimed to be invariant.
- Keep the detailed guide task-oriented, then add diff interpretation, common
  errors, privacy, and a concise comparison with full tracking platforms.

### Implemented

- [x] Complete README first screen, positioning, maturity, and support matrix
- [x] Source and planned PyPI installation guidance with release distinction
- [x] Four-step README Quick Start and representative diff output
- [x] Detailed `docs/getting-started.md` full-workflow guide
- [x] Copyable init, snapshot, list, show, and diff commands
- [x] Config example and Git/dirty-state guidance
- [x] CLI reference, snapshot contents, storage, and privacy documentation
- [x] RunTrace versus full tracking platform scope explanation
- [x] Common error resolutions and project-maturity statement
- [x] Changelog and daily delivery checklist updates

### Verification

- Built `ml_runtrace-0.1.0.dev0.tar.gz` and the universal
  `ml_runtrace-0.1.0.dev0-py3-none-any.whl` in an isolated temporary directory.
- Created a clean Python 3.12.7 virtual environment and installed the wheel
  with all 15 resolved runtime packages. Resolution exercised currently
  available compatible releases including Pydantic 2.13.4 and Typer 0.27.1.
- In a separate temporary Git repository, the installed console script ran
  `init`, captured baseline and candidate configs across two commits, listed
  both runs, showed a run by six-character ID, and diffed both runs by unique
  prefixes. Every documented output section and change kind was verified.
- A preliminary offline-only installation correctly stopped because some
  dependency wheels were not cached. The network-backed clean install then
  passed; both validated temporary roots were removed.
- Documentation checks confirmed balanced code fences, all five command names,
  the unpublished-PyPI warning, valid local targets, and no machine-specific
  user paths.
- `uv run pytest -p no:cacheprovider`: 85 tests passed on Windows with Python
  3.12.7.
- `uv run ruff check . --no-cache`: passed.
- `uv run ruff format --check . --no-cache`: 31 files already formatted.
- `uv lock --check`: passed with the existing 22-package development lock
  graph; no dependency was introduced.
- Package-content inspection confirmed the README, license, Getting Started
  guide, and source modules in the sdist, plus CLI/diff modules, metadata, and
  license in the wheel. The temporary artifacts were removed.
- GitHub's rendered branch views displayed the README badges, headings, local
  links, Quick Start, and every Getting Started section correctly.
- `git diff --check`: passed.

### Submission record

- Created commit `7c35bd4` (`docs: add complete Quick Start`) and pushed
  `codex/issue-11-quick-start-docs` to `origin`.
- Opened [pull request #22](https://github.com/Corvus-226/RunTrace/pull/22)
  against `main`. The pull request closes #11, uses the `documentation` label,
  is assigned to the maintainer, and belongs to the `v0.1.0` milestone.
- GitHub Actions run `31596299684` passed on Python 3.10, 3.11, and 3.12.
- The original planning document remains untracked and excluded.

## 2026-08-12 — Issue #12 v0.1.0 release preparation

### Coordination

- Merged [pull request #22](https://github.com/Corvus-226/RunTrace/pull/22)
  into `main` as `c3134c8`; Issue #11 closed automatically.
- Assigned Issue #12 to the maintainer and started from that updated `main`
  commit on `codex/issue-12-release-preparation`.
- Kept tag creation, PyPI publication, and GitHub Release creation outside this
  branch because Issue #12 requires a separate explicit maintainer approval
  for publication.

### Scope

- Freeze the first-release scope and change the package version to `0.1.0`.
- Finalize changelog, release notes, release-candidate installation guidance,
  support status, and an auditable maintainer runbook.
- Harden CI action references and add Linux package-build and clean-wheel smoke
  coverage.
- Add a manually dispatched, read-only candidate workflow that builds and
  retains artifacts without tagging or publishing them.
- Recheck distribution-name availability, build and inspect both artifacts,
  and run a clean Windows acceptance workflow.

### Decisions

- Treat the PyPI JSON and Simple API HTTP 404 responses on 2026-08-12 as an
  availability observation, not a reservation. PyPI documents that a pending
  publisher creates the project only on first use and does not reserve the
  name beforehand.
- Require a protected GitHub `pypi` environment and a PyPI pending trusted
  publisher before any publication workflow is enabled. Do not add a password,
  API token, or long-lived fallback credential.
- Keep `.github/workflows/release.yml` non-publishing and manually dispatched.
  It has `contents: read`, no OIDC permission, no tag trigger, and no GitHub or
  PyPI write step. Candidate artifacts expire after seven days.
- Pin every third-party action reference to a complete commit SHA, while
  retaining the corresponding release name in a comment for maintainability.
- Add Twine to the locked development tools so local and CI package metadata
  validation use the same reviewed major version.
- Bound Hatchling to `>=1.27,<1.30`: Hatchling 1.30+ emitted Core Metadata 2.5,
  which Twine 6.2 rejected, while the compatible range emits supported Core
  Metadata 2.4. Do not bypass the metadata check.
- Explicitly exclude the untracked original planning document from Hatch
  source distributions. This makes local and clean-clone artifact contents
  consistent and keeps the planning file outside release artifacts.
- Use the release-preparation pull request as the approval boundary: it may be
  reviewed and tested normally, but it must not imply authorization to create
  a tag or publish irreversible artifacts.

### Implemented

- [x] Package and runtime version changed from `0.1.0.dev0` to `0.1.0`
- [x] Alpha classifier, documentation URL, changelog release, and v0.1.0 notes
- [x] Truthful release-candidate install, maturity, contributor, and support
  documentation that does not claim PyPI publication
- [x] Maintainer release runbook with one-time trusted-publisher prerequisites
- [x] Read-only manual release-candidate workflow with SHA-pinned actions
- [x] SHA-pinned CI actions and separate Linux package smoke job
- [x] Locked Twine release tooling and compatible Hatchling metadata boundary
- [x] Release metadata/workflow guardrail tests compatible with Python 3.10+
- [x] Explicit source-distribution exclusion for the private planning document
- [x] Final wheel and sdist metadata, contents, hashes, and Windows wheel smoke
- [x] Release-preparation pull request and first green Linux matrix/package CI
- [ ] Explicit maintainer approval of the release-preparation pull request
- [ ] Protected environment, pending publisher, signed or annotated tag,
  trusted publication, and post-publication verification

### Verification

- PyPI returned HTTP 404 for both `https://pypi.org/pypi/ml-runtrace/json` and
  `https://pypi.org/simple/ml-runtrace/` on 2026-08-12. The name appeared
  unregistered at check time but remains unreserved until publication.
- The first package check exposed Core Metadata 2.5 incompatibility with Twine
  6.2. After bounding Hatchling, `twine check` passed for both distributions
  and each reports Core Metadata 2.4.
- Package-content inspection found and then eliminated the untracked planning
  document from the local sdist. The corrected wheel contains 18 files; the
  corrected sdist contains 45 files with package source, tests, license,
  README, release documentation, and no planning document.
- Pre-commit local audit artifact SHA-256 values (the reviewed commit is built
  again by CI and its hashes supersede these values):
  - `ml_runtrace-0.1.0-py3-none-any.whl`:
    `5ea659cc0c253dbdf7d7c94fb043f6ab3541317058c954474aa694855188cbd6`
  - `ml_runtrace-0.1.0.tar.gz`:
    `71c1a3c150e2db7ec5f40517c3da02f66c51c3f0eda6d270985050dda65c976f`
- The exact corrected wheel hash matched the wheel already installed into a
  clean Python 3.12.7 Windows virtual environment. Pip resolved 15 runtime
  packages, `pip check` found no broken requirements, and `runtrace --version`
  returned `runtrace 0.1.0`.
- In a new temporary Git repository, that installed console script completed
  `init`, two named `snapshot` operations, `list`, `show`, and `diff`; the
  outputs contained both IDs, the candidate details, and the before/after
  command change. The temporary environment and repository were removed.
- `uv run pytest -p no:cacheprovider`: 88 tests passed on Windows with Python
  3.12.7, including three release metadata and workflow guardrail tests.
- `uv run ruff check . --no-cache`: passed.
- `uv run ruff format --check . --no-cache`: 34 files already formatted.
- `uv lock --check`: passed with the 48-package locked graph, including Twine
  and its release-checking dependencies.
- Both GitHub Actions YAML files parsed successfully and `git diff --check`
  passed.
- [Pull request #23](https://github.com/Corvus-226/RunTrace/pull/23) opened
  against `main`, references Issue #12 without closing it, is assigned to the
  maintainer, carries the `enhancement` label, and belongs to the `v0.1.0`
  milestone.
- GitHub Actions run `31599053386` passed all four checks: the Linux Python
  3.10, 3.11, and 3.12 matrix plus the new package smoke job. The package job
  built commit `0895cf7`, passed Twine and clean-wheel installation, and
  recorded these first-review hashes:
  - wheel: `28519f89c21658b0fe0a55dc3aae67fd708b064ec97cb7a8bb249ddd788d189b`
  - sdist: `407ea4fd632dc257609f33ef520a527e101881f195a1f5fdd634a61e32bfef6f`
- The first package job reported a non-failing cache-save warning because it
  raced the Python 3.12 job for the same uv cache key. Distinct `package` and
  `release-candidate` cache suffixes now prevent cross-job cache contention;
  this follows setup-uv's documented guidance for jobs with different roles.

### Submission record

- Created commit `0895cf7` (`chore: prepare v0.1.0 release`) and pushed
  `codex/issue-12-release-preparation` to `origin`.
- Opened [pull request #23](https://github.com/Corvus-226/RunTrace/pull/23)
  with an explicit publication boundary. The PR remains open and Issue #12
  remains open; neither a merge nor any release action has been performed.

## 2026-08-13 — Gate 0 public-name coexistence audit

### Coordination

- Used the v0.1.0 release-progress guide to start at Gate 0 before any PR
  approval, trusted-publisher configuration, merge, tag, or publication.
- Confirmed through PyPI's JSON and Simple APIs that the unrelated `runtrace`
  distribution is currently published at version 0.3.2 and requires Python
  3.11 or newer; `ml-runtrace` still returned HTTP 404 on both endpoints.
- Opened [Issue #24](https://github.com/Corvus-226/RunTrace/issues/24) as the
  release-blocking public-name decision, assigned it to the maintainer, added
  the `bug` label, and placed it in the `v0.1.0` milestone.
- Added the evidence and stop condition to
  [pull request #23](https://github.com/Corvus-226/RunTrace/pull/23), then
  converted that pull request to draft.

### Scope

- Test the published `runtrace==0.3.2` distribution and the local
  `ml_runtrace-0.1.0` candidate wheel in both installation orders.
- Compare import resolution, console-command behavior, distribution RECORD
  ownership, and `pip check` results.
- Uninstall one distribution from each combined environment and verify whether
  the remaining distribution still imports and runs.
- Stop release work on any package or command collision; do not choose or
  implement a new public name without maintainer review.

### Decisions

- Treat distribution names, Python import packages, and console scripts as
  separate public namespaces. The available `ml-runtrace` distribution name
  does not mitigate collisions in the other two namespaces.
- Treat this as a release blocker rather than a documentation caveat. A warning
  cannot prevent pip from overwriting or deleting files owned by another
  distribution.
- Keep the current package and command unchanged until Issue #24 records a
  maintainer-approved naming decision. Do not start Trusted Publishing setup
  while the publishable artifact identity remains unresolved.
- Correct release-preparation documentation immediately so an open or merged
  candidate never claims that v0.1.0 is already available from PyPI.
- Exclude both untracked maintainer reference documents from local sdists so a
  developer-machine build matches a clean-clone build more closely.

### Experiment

- Environment A installed `runtrace==0.3.2` first. Its import reported version
  0.3.2 and its `runtrace --help` identified an unrelated AI-agent black-box
  tool. Installing the candidate second changed the same import and executable
  to RunTrace v0.1.0.
- Environment B installed the candidate first. Its import and executable
  reported RunTrace v0.1.0. Installing `runtrace==0.3.2` second changed both to
  the unrelated project.
- The two distribution RECORD files claim the same six paths:
  - `Scripts/runtrace.exe`
  - `runtrace/__init__.py`
  - `runtrace/__main__.py`
  - `runtrace/cli.py`
  - `runtrace/config.py`
  - `runtrace/models.py`
- In Environment A, uninstalling `runtrace` left `ml-runtrace==0.1.0` metadata
  installed but removed the `runtrace` import and executable.
- In Environment B, uninstalling `ml-runtrace` left `runtrace==0.3.2` metadata
  installed but removed the `runtrace` import and executable.
- `pip check` returned success at every checkpoint, demonstrating that normal
  dependency validation does not detect cross-distribution file ownership.
- Both temporary environments and the candidate wheel directory were removed
  after the audit.
- After the documentation and packaging corrections, all 88 tests passed on
  Windows with Python 3.12.7. Ruff lint passed, 35 files were already
  formatted, `uv lock --check` passed, and both Actions YAML files parsed.
- Three focused release guardrail tests passed. Both candidate distributions
  passed Twine; the sdist contained 45 files and excluded both untracked
  maintainer reference documents.
- Tracked-file audits found no machine-specific user paths, private-key blocks,
  PyPI tokens, or API-key assignments. `runtrace --version` and `--help`
  continued to pass for the unchanged source candidate.

### Result

- [x] Both installation orders tested in clean Python 3.12 environments
- [x] Python import ownership collision reproduced
- [x] Console-script ownership collision reproduced
- [x] Six shared RECORD paths identified
- [x] Both uninstall directions shown to break the remaining distribution
- [x] False-negative `pip check` behavior recorded
- [x] Blocking Issue #24 and PR #23 comment created
- [x] PR #23 converted to draft and release progression stopped
- [x] Collision-free import and command names approved by the maintainer
- [x] Naming decision implemented with regression tests and documentation
- [x] Both-order installation and uninstall acceptance criteria pass

### Submission record

- Created commit `26170b0` (`docs: block release on public name collision`)
  on the existing `codex/issue-12-release-preparation` branch and pushed it to
  draft pull request #23. Both local maintainer reference documents remained
  untracked.
- GitHub Actions run `31622202758` passed all four checks for commit `26170b0`:
  Linux Python 3.10, 3.11, and 3.12 plus the package smoke job.
- Static release review confirmed consistent candidate version `0.1.0`,
  full-SHA action pins, read-only workflow permissions, a manual-only
  seven-day candidate artifact, no OIDC permission, and no tag, PyPI, or
  GitHub Release write path.
- Review recommendation: keep PR #23 in draft and request changes until Issue
  #24 resolves the shared `runtrace` package and command at `pyproject.toml`
  lines 45 and 61. All other checked release-preparation gates passed.

### Risks and next scoped work

- The original candidate names could silently replace an unrelated tool and
  must never be published. Strategy A supersedes that artifact.
- The approved naming change invalidates every earlier candidate hash; only a
  rebuilt and re-reviewed artifact can become v0.1.0.
- Trusted Publishing work remains deferred until the migrated package passes
  CI and PR #23 is re-reviewed.

## 2026-08-13 — Strategy A public namespace migration

### Coordination

- The maintainer explicitly approved strategy A on 2026-08-13.
- Continued on the existing `codex/issue-12-release-preparation` branch and
  draft pull request #23; no new branch was created.
- Kept Issue #24 open as the acceptance record. No merge, trusted-publisher
  setup, tag, PyPI upload, or GitHub Release was performed.

### Scope

- Keep the project and repository name RunTrace and the distribution name
  `ml-runtrace`.
- Rename the Python package to `ml_runtrace`, the console command to
  `ml-runtrace`, and the module entry point to `python -m ml_runtrace`.
- Provide no `runtrace` import, command alias, or secondary console script.
- Preserve the existing `.runtrace/` local data directory, `runtrace.toml`
  configuration file, `[runtrace]` configuration table, and snapshot schema;
  these persisted project names do not collide with Python installation
  namespaces.

### Implementation

- Renamed `src/runtrace` to `src/ml_runtrace` and migrated all internal and
  test imports.
- Changed the sole package entry point to
  `ml-runtrace = "ml_runtrace.cli:main"`; version output now identifies
  `ml-runtrace`, and `python -m ml_runtrace` invokes the same application.
- Updated actionable CLI errors, README, Getting Started guide, changelog,
  draft release notes, release runbook, issue template, CI, release-candidate
  workflow, and packaging guardrail tests.
- Added `scripts/check_public_name_coexistence.py`. It constructs a valid
  local `runtrace` wheel without contacting a package index, installs it and
  the actual candidate wheel in both orders, checks distribution metadata,
  import paths, entry points, RECORD ownership, and generated scripts, then
  uninstalls one distribution in each environment and verifies that the other
  remains intact.
- Added an optional `--runtrace-wheel` input so the same audit can verify a
  downloaded real public wheel without weakening the network-free default.

### Verification

- `uv sync --all-groups --locked` resolved the existing 48-package graph and
  rebuilt the editable project under the approved package name.
- The pre-documentation full suite passed all 88 tests on Windows with Python
  3.12.7. After adding the final public-name guardrail, all 89 tests passed.
- Ruff lint passed, all 36 Python files were formatted, `uv lock --check`
  resolved the locked 48-package graph, and both Actions workflow files parsed
  as YAML.
- A freshly built `ml_runtrace-0.1.0-py3-none-any.whl` passed the synthetic
  offline audit in both installation orders and both uninstall directions.
- The same candidate passed against the downloaded real
  `runtrace-0.3.2-py3-none-any.whl` under the same four lifecycle checks.
  Both imports and both commands remained independently installed, and the
  two distributions had no shared RECORD paths.
- All build roots and virtual environments created for these audits were
  confined to the system temporary directory and removed after validation.
- Twine accepted both replacement artifacts. The wheel RECORD contained 18
  files and only the `ml_runtrace` package; the sdist contained 46 files, only
  `src/ml_runtrace`, and neither untracked maintainer reference document.
- A fresh Windows environment installed the exact wheel and returned
  `ml-runtrace 0.1.0` from both `ml-runtrace --version` and
  `python -m ml_runtrace --version`. Neither a `runtrace` executable nor a
  `runtrace` import was present.
- The clean wheel then passed the complete init → two snapshots → list → show
  → diff workflow in an isolated Git repository. The assertions confirmed
  both run labels, complete baseline data, and the changed learning rate.
- The final privacy audit covered 37 repository files and found no local user
  paths, private-key blocks, PyPI tokens, GitHub tokens, or credential
  assignments. The two untracked maintainer references were explicitly
  excluded and remained outside the candidate.
- GitHub Actions run
  [`31624906406`](https://github.com/Corvus-226/RunTrace/actions/runs/31624906406)
  passed all four jobs for implementation commit `2005035`: Linux Python
  3.10, 3.11, and 3.12 plus the package smoke job.
- The package job completed in 26 seconds. It built both artifacts, passed the
  offline two-order/both-uninstall audit, passed Twine, and installed the
  exact wheel in a clean environment with the approved command, module, and
  no legacy `runtrace` import or executable.
- CI recorded these implementation-candidate hashes:
  - wheel: `53b292f3ba08f4b5b26cd6a233e55aff75d357d0ada87a9378253fb565745d82`
  - sdist: `6d28f2b2405fb3cbeeefcd6dcedc10f8b759a0e83d730e2ba0f8509049e00370`

### Result

- [x] Maintainer decision recorded
- [x] Python package and internal imports migrated
- [x] Sole console and module entry points migrated
- [x] `runtrace` compatibility aliases intentionally absent
- [x] User documentation and workflow commands migrated
- [x] Focused metadata and documentation guardrails added
- [x] Synthetic offline two-order and both-uninstall audit passed
- [x] Real `runtrace==0.3.2` two-order and both-uninstall audit passed
- [x] Final full quality, artifact, clean-install, and privacy validation
- [x] Commit, push, and Linux CI evidence

### Submission record

- Created commit `2005035` (`fix: resolve public name collision`) and pushed
  it to the existing `codex/issue-12-release-preparation` branch and draft PR
  #23. Both local maintainer reference documents remained untracked.
- Posted the explicit strategy A decision, implementation details, local
  evidence, and unchanged publication boundary to Issue #24.
- PR #23 remained Draft while the implementation CI ran. No merge, trusted
  publisher, tag, PyPI upload, or GitHub Release action was performed.

## 2026-08-13 — Release status reconciliation

### Coordination

- Confirmed that the public PyPI project page for `ml-runtrace` still returns
  HTTP 404. The distribution has not been published and the name remains
  unreserved until a trusted publication succeeds.
- Confirmed that pull request #23 is open, out of Draft, conflict-free, and
  reports all four required checks as successful for reviewed head `7557d00`.
- Confirmed that all eight acceptance criteria in Issue #24 are checked, the
  final evidence comment is present, and the collision blocker is closed.

### Current usability boundary

- RunTrace is usable from the reviewed source branch or its validated local
  wheel with the `ml-runtrace` command and `ml_runtrace` import package.
- RunTrace is not yet a public release: there is no merged release commit on
  `main`, `v0.1.0` tag, PyPI project, trusted deployment, or GitHub Release.
- The published installation command must not replace source-development
  guidance until a clean install from PyPI has passed post-publication
  acceptance.

### Verification

- The reviewed strategy A implementation and validation record resolves to
  `7557d0069de3743d2578e3ff03dd9aa590502dbc`; subsequent documentation-only
  reconciliation does not change package code or public names.
- GitHub Actions run
  [`31625355238`](https://github.com/Corvus-226/RunTrace/actions/runs/31625355238)
  passed Python 3.10, 3.11, 3.12, and the package smoke job.
- The final-head package job recorded:
  - wheel SHA-256:
    `ebed8b75fec1ecda3e2e341278d54197b95cb86f88049ca52dd76885d14931c2`
  - sdist SHA-256:
    `8e3eef39fe86fbb46ca56a6702f5ae318f33379c512a905d227d7cdcaaf056b1`
- The package smoke job passed the offline coexistence audit, Twine, and a
  clean-wheel install using only `ml-runtrace` and `python -m ml_runtrace`.

### Gate status

- [x] Gate 0 public-name collision resolved and independently regression-tested
- [x] Gate 1 technical re-review complete; PR #23 is ready for maintainer merge
- [ ] Maintainer authorization to merge PR #23
- [ ] Protected `pypi` environment and pending trusted publisher
- [ ] Reviewed tag-triggered Trusted Publishing workflow
- [ ] Final candidate built from the merged and reviewed `main` commit
- [ ] Annotated or signed `v0.1.0` tag and trusted PyPI publication
- [ ] GitHub Release and clean PyPI post-publication acceptance

### Next scoped work

1. Record explicit maintainer authorization before merging PR #23.
2. After merge, create a new scoped Trusted Publishing issue and branch; Issue
   #24 is already used by the resolved public-name collision.
3. Keep build and publish jobs separate, grant OIDC only to the protected
   publish job, and stop before any tag or real deployment.
