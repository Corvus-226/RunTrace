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
