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
