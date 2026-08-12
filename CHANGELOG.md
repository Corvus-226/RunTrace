# Changelog

All notable changes to RunTrace will be documented in this file. The format is
based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and the
project follows [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- Initial Python package and Typer CLI skeleton.
- PyPI distribution name set to `ml-runtrace`; the project and CLI remain
  RunTrace and `runtrace`.
- Local development workflow using uv, pytest, and Ruff.
- Linux CI matrix for Python 3.10, 3.11, and 3.12.
- Repository contribution, security, issue, and pull request guidance.
- Git metadata capture for the full commit SHA, branch or detached-HEAD state,
  and dirty working trees, including untracked files.
- Deterministic capture of the Python runtime, operating system, installed
  distribution versions, and optional NVIDIA GPU/CUDA metadata.
- Versioned Pydantic snapshot models and readable local YAML persistence with
  atomic saves, duplicate-ID protection, newest-first listing, and full or
  unique abbreviated run-ID lookup.

[Unreleased]: https://github.com/Corvus-226/RunTrace/compare/v0.1.0...HEAD
