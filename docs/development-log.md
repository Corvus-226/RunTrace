# RunTrace Development Log

This log records implementation decisions and verification results. It is not a
substitute for issues, pull requests, commit history, or `CHANGELOG.md`.

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
