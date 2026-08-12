# AGENTS.md

This file defines the repository-wide expectations for coding agents and human
contributors working on RunTrace.

## Product goal

RunTrace is a lightweight, local-first CLI that records and compares the code,
configuration, environment, and metadata behind machine-learning experiments.
Every v0.x feature must directly help users record, inspect, compare, or check
experiment reproducibility information.

## Architecture boundaries

- Keep persisted run data in readable local files under `.runtrace/`.
- Do not add a server, cloud account, database service, web dashboard, auth
  system, scheduler, model host, or automatic upload path in v0.x.
- Do not capture environment variables, tokens, credentials, SSH material, or
  source-code contents.
- Keep Git, runtime, configuration, storage, and diff concerns in separate
  modules as they are implemented.
- Prefer deterministic functions with explicit inputs over hidden process-wide
  state.
- Windows and Linux are both supported platforms.

## Python conventions

- Support Python 3.10, 3.11, and 3.12.
- Use type hints for public functions and important internal boundaries.
- Use `pathlib.Path` for filesystem paths.
- Keep user-facing errors concise and actionable; do not expose an avoidable
  traceback for ordinary CLI mistakes.
- Use Ruff for linting and formatting. Do not introduce a second formatter or
  overlapping lint stack.
- Prefer the standard library. Add a dependency only when it materially reduces
  complexity and fits the approved stack: Typer, Rich, PyYAML, and Pydantic.
  Discuss other runtime dependencies in an issue first.

## Tests

- Every behavior change requires focused tests.
- Test success paths and user-facing error paths.
- Filesystem and Git tests must use temporary directories and must not depend on
  the contributor's global Git configuration.
- Tests must not require network access, a GPU, or external services.
- Before requesting review, run:

  ```console
  uv run pytest
  uv run ruff check .
  uv run ruff format --check .
  ```

## Issues, pull requests, and releases

- Start non-trivial work from a scoped issue and keep pull requests focused.
- Link the pull request to its issue and explain how the change was validated.
- Do not mix refactors or formatting sweeps into a feature or bug fix.
- Document CLI breaking changes explicitly before implementation.
- Update `CHANGELOG.md` for user-visible changes, including public API and CLI
  changes.
- Never fabricate users, feedback, issues, contributions, download counts, or
  maintenance activity.

## Documentation

- Keep examples executable and synchronized with actual behavior.
- Mark planned commands as planned; do not document unreleased behavior as
  available.
- Explain privacy implications whenever captured metadata changes.
