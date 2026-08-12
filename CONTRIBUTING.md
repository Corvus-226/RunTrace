# Contributing to RunTrace

Thank you for helping make ML experiments easier to reproduce. RunTrace is in
early development, so focused feedback and small, well-tested changes are the
most useful contributions.

## Before starting

1. Search existing issues and pull requests.
2. Open or comment on an issue before beginning a non-trivial change.
3. Keep proposals within the local-first reproducibility scope described in
   `README.md` and `AGENTS.md`.

Security reports must follow `SECURITY.md` and must not be posted in public
issues.

## Development environment

Install Python 3.10 or newer and [uv](https://docs.astral.sh/uv/), then run:

```console
git clone https://github.com/Corvus-226/RunTrace.git
cd RunTrace
uv sync --all-groups
uv run pytest
uv run ruff check .
uv run ruff format --check .
```

## Pull requests

- Link a scoped issue using `Closes #<number>` when appropriate.
- Add or update tests for behavior changes.
- Update documentation and `CHANGELOG.md` for user-visible changes.
- Keep unrelated edits out of the pull request.
- Call out any compatibility, privacy, or data-format impact.

A maintainer will review scope, tests, compatibility, and documentation before
merge. CI must pass on all supported Python versions.
