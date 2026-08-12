# Changelog

All notable changes to RunTrace will be documented in this file. The format is
based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and the
project follows [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.1.0] - 2026-08-12

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
- Idempotent `runtrace init` support that locates the current Git root, creates
  `.runtrace/runs/` and a minimal `runtrace.toml`, and preserves existing
  configuration and stored runs.
- `runtrace snapshot` capture for Git state, Python runtime, platform,
  dependencies, optional GPU/CUDA metadata, and optional run name, command,
  and validated YAML config values, path, and SHA-256 hash.
- Compact newest-first `runtrace list` output for local run IDs, names, short
  commits, dirty states, and UTC creation times, including friendly empty-state
  and actionable corrupt-record handling.
- Sectioned `runtrace show` output for complete stored snapshots selected by
  full or unique abbreviated run ID, with explicit missing-value display and
  deterministic JSON formatting for captured config values.
- Deterministic `runtrace diff` output for two full or uniquely abbreviated run
  IDs, including recursive configuration, Git, runtime, platform, and Python
  dependency changes grouped into readable terminal sections.
- Complete README and Getting Started documentation for installation, the
  init-to-diff workflow, terminal output, local storage, privacy, project
  maturity, and RunTrace's scope relative to full tracking platforms.

[Unreleased]: https://github.com/Corvus-226/RunTrace/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/Corvus-226/RunTrace/releases/tag/v0.1.0
