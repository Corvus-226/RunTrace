# Releasing RunTrace

This runbook prepares a release and defines the approval boundary for
publishing without a PyPI password or API token. Publication is always an
explicit maintainer action; merging a release-preparation pull request alone
does not authorize a tag or upload.

## Release invariants

- The release tag points to the reviewed `main` commit.
- `pyproject.toml`, `ml_runtrace.__version__`, the tag, changelog, and release notes
  contain the same version.
- The sdist and wheel uploaded to PyPI are the exact files attached to the
  GitHub Release.
- CI, package checks, and a fresh Windows install pass before tagging.
- No password, API token, or long-lived publishing credential enters GitHub.
- Published files are never overwritten; a correction uses a new patch
  version.

## Public-name collision gate

[Issue #24](https://github.com/Corvus-226/RunTrace/issues/24) records the
original conflict: the unrelated PyPI `runtrace==0.3.2` distribution and the
old candidate both owned the `runtrace` Python package and console script.
Install-order testing showed that either distribution could overwrite and
later uninstall the other's files; `pip check` did not detect the conflict.

The maintainer approved strategy A on 2026-08-13:

- project and repository: RunTrace;
- PyPI distribution: `ml-runtrace`;
- Python import: `ml_runtrace`;
- console command: `ml-runtrace`; and
- module entry point: `python -m ml_runtrace`.

Do not add a `runtrace` import, console alias, or secondary script. The
checked-in offline coexistence audit and a repeat audit against the real
`runtrace==0.3.2` wheel must pass in both installation orders, including
uninstall independence. Issue #24 closed after all acceptance criteria passed,
and PR #23 merged the reviewed migration into `main` as `01fb15d`.

## One-time trusted publishing setup

The `ml-runtrace` PyPI JSON and Simple API endpoints returned HTTP 404 during
the first-release audit on 2026-08-12. For later releases, query the project
immediately before publication and confirm that the target version is absent:

```console
curl --fail https://pypi.org/pypi/ml-runtrace/json
curl --fail https://pypi.org/simple/ml-runtrace/
```

Before the first release, both commands were expected to fail with HTTP 404.
After a project exists, inspect the JSON response and verify that the target
version does not appear under `releases`. This check does not reserve a version.

Before enabling publishing or pushing a release tag:

1. Create a protected GitHub Actions environment named `pypi` and require the
   maintainer's approval for deployments.
2. In the maintainer's PyPI account, add a pending GitHub publisher with:
   - PyPI project name: `ml-runtrace`
   - owner: `Corvus-226`
   - repository: `RunTrace`
   - workflow: `publish.yml`
   - environment: `pypi`
3. Confirm two-factor authentication and recovery details for both GitHub and
   PyPI.

For the current single-maintainer repository, the `pypi` environment uses
`Corvus-226` as the required reviewer, leaves **Prevent self-review** disabled,
allows only matching `v*` tags to deploy, and contains no environment secrets.
Revisit the self-review setting when another trusted maintainer is available.

The official references are
[PyPI's pending-publisher guide](https://docs.pypi.org/trusted-publishers/creating-a-project-through-oidc/),
[PyPI's publishing guide](https://docs.pypi.org/trusted-publishers/using-a-publisher/),
and
[GitHub's PyPI OIDC guide](https://docs.github.com/en/actions/how-tos/secure-your-work/security-harden-deployments/oidc-in-pypi).

## Prepare the source

1. Start from an up-to-date `main` branch and a scoped release issue.
2. Set the final version in `pyproject.toml` and `src/ml_runtrace/__init__.py`.
3. Move user-visible entries from Unreleased into the dated changelog release.
4. Add `docs/releases/v<version>.md` and update install/status documentation.
5. Run the full release validation described below.
6. Open a release-preparation pull request and require green Linux CI.

## Local release validation

Run the normal quality gates:

```console
uv sync --all-groups --locked
uv run pytest -p no:cacheprovider
uv run ruff check . --no-cache
uv run ruff format --check . --no-cache
uv lock --check
```

Build into a clean directory and inspect both artifacts:

```console
uv build
uv run twine check dist/*
uv run python scripts/check_public_name_coexistence.py --dist-dir dist
```

Immediately before publication, download the current real public wheel into a
temporary directory and rerun the same audit against it. For the collision
known at v0.1.0 preparation time:

```console
python -m pip download --no-deps --only-binary=:all: --dest <temporary-directory> runtrace==0.3.2
uv run python scripts/check_public_name_coexistence.py --dist-dir dist --runtrace-wheel <temporary-directory>/runtrace-0.3.2-py3-none-any.whl
```

The default audit is network-free; only the explicit `pip download` step
contacts PyPI.

Install the wheel into a newly created Windows virtual environment and run the
documented init → snapshot → list → show → diff workflow. Record test counts,
artifact names, SHA-256 values, and the smoke result in `docs/development-log.md`.

## Build the reviewed candidate

The checked-in `release.yml` is deliberately non-publishing. In GitHub Actions,
open **Release candidate**, choose **Run workflow**, and provide the reviewed
commit or tag plus the exact expected version. The workflow has read-only
repository permissions and no OIDC permission. It:

1. verifies the source version and versioned release-notes file;
2. reruns tests, lint, and format checks;
3. builds the sdist and wheel once;
4. runs the offline two-order public-name coexistence audit;
5. checks package metadata and records SHA-256 values; and
6. retains the files as a 7-day workflow artifact for review.

Download that artifact, verify its hashes and contents, and record the Actions
run before requesting publication approval.

## Approve publication

The formal `.github/workflows/publish.yml` workflow was enabled after its
scoped Issue #25 and pull request passed review. A matching version tag starts a
build job with read-only repository permission. That job verifies the
tag/version pair, runs quality and coexistence checks, builds once, records
provenance and SHA-256 values, and uploads the reviewed artifacts. A separate
publish job downloads those files, verifies their hashes, and receives
`id-token: write` only while using the protected `pypi` environment. It does
not check out source or rebuild distributions, and no password or API token is
configured.

Only after the release-preparation pull request is merged and its `main` CI is
green—and after that separate approval—choose the exact audited commit. Prefer
a signed tag when signing is configured; otherwise create an annotated tag:

```console
git switch main
git pull --ff-only origin main
git tag -s v0.2.0 -m "RunTrace v0.2.0"
git push origin v0.2.0
```

If signing is unavailable, replace `-s` with `-a` and record that decision.
The approved publishing path verifies the tag/version match, builds once, and
publishes the exact same files through PyPI Trusted Publishing. Download the
retained tag-workflow artifact and attach those distributions plus
`SHA256SUMS` and `RELEASE_PROVENANCE` to the GitHub Release. Do not add
token-based fallback credentials.

## Post-publication verification

Wait for PyPI's index to expose the files, then use another new environment:

```console
python -m venv .venv-release-check
python -m pip install --no-cache-dir ml-runtrace==0.2.0
ml-runtrace --version
ml-runtrace --help
python -m ml_runtrace --version
```

Repeat the documented workflow and compare the SHA-256 digests of the PyPI and
GitHub Release artifacts. Confirm that the GitHub Release points to the audited
tag and that the PyPI page identifies trusted publishing and attestations.

If publication reveals a serious issue, do not replace files. Yank the affected
release when appropriate, document the reason, fix forward, and publish a new
patch version.
