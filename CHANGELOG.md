# Changelog

All notable changes to RunTrace will be documented in this file. The format is
based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and the
project follows [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.3.0] - 2026-08-21

### Added

- `ml-runtrace run` now exposes the newly saved snapshot ID to its child process
  as `RUNTRACE_RUN_ID`, making it possible to correlate logs, metrics, and
  observability spans with exact local provenance. A stale inherited value is
  replaced for the child without modifying the parent environment.
- Added a run-correlation guide with dependency-free structured logging and
  optional OpenTelemetry examples, including privacy and distributed-worker
  boundaries.

## [0.2.0] - 2026-08-17

### Added

- Added `ml-runtrace run -- COMMAND...`, an opt-in snapshot-before-execution
  wrapper that preserves exact arguments, does not invoke an implicit shell,
  keeps the snapshot when execution fails, and returns the child exit code.
- Added privacy-conscious PEP 610 provenance for packages installed from VCS,
  remote archives, or local directories, including resolved VCS commit IDs and
  archive hashes when available.

### Changed

- Snapshot schema v1 now accepts additive `command_argv` and
  `package_sources` fields while remaining compatible with existing v0.1.0
  YAML records. `show` and `diff` expose the new reproducibility metadata.

### Documentation

- Added an original experiment-fingerprint README hero that presents RunTrace
  as a local snapshot and diff tool without unsupported product claims.

## [0.1.0] - 2026-08-13

### Added

- Initial Python package and Typer CLI skeleton.
- Collision-free public names: PyPI distribution `ml-runtrace`, Python import
  `ml_runtrace`, console command `ml-runtrace`, and module entry point
  `python -m ml_runtrace`. The project and repository remain RunTrace, with no
  `runtrace` import or command alias.
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
- Idempotent `ml-runtrace init` support that locates the current Git root, creates
  `.runtrace/runs/` and a minimal `runtrace.toml`, and preserves existing
  configuration and stored runs.
- `ml-runtrace snapshot` capture for Git state, Python runtime, platform,
  dependencies, optional GPU/CUDA metadata, and optional run name, command,
  and validated YAML config values, path, and SHA-256 hash.
- Compact newest-first `ml-runtrace list` output for local run IDs, names, short
  commits, dirty states, and UTC creation times, including friendly empty-state
  and actionable corrupt-record handling.
- Sectioned `ml-runtrace show` output for complete stored snapshots selected by
  full or unique abbreviated run ID, with explicit missing-value display and
  deterministic JSON formatting for captured config values.
- Deterministic `ml-runtrace diff` output for two full or uniquely abbreviated run
  IDs, including recursive configuration, Git, runtime, platform, and Python
  dependency changes grouped into readable terminal sections.
- Complete README and Getting Started documentation for installation, the
  init-to-diff workflow, terminal output, local storage, privacy, project
  maturity, and RunTrace's scope relative to full tracking platforms.
- Credential-free, tag-triggered PyPI Trusted Publishing with a protected
  deployment environment, immutable GitHub Action pins, retained provenance,
  and SHA-256 verification across the artifact handoff.

[Unreleased]: https://github.com/Corvus-226/RunTrace/compare/v0.3.0...HEAD
[0.3.0]: https://github.com/Corvus-226/RunTrace/compare/v0.2.0...v0.3.0
[0.2.0]: https://github.com/Corvus-226/RunTrace/compare/v0.1.0...v0.2.0
[0.1.0]: https://github.com/Corvus-226/RunTrace/releases/tag/v0.1.0
