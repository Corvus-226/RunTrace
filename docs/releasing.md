# Releasing RunTrace

This runbook prepares a release and defines the approval boundary for
publishing without a PyPI password or API token. Publication is always an
explicit maintainer action; merging a release-preparation pull request alone
does not authorize a tag or upload.

## Release invariants

- The release tag points to the reviewed `main` commit.
- `pyproject.toml`, `runtrace.__version__`, the tag, changelog, and release notes
  contain the same version.
- The sdist and wheel uploaded to PyPI are the exact files attached to the
  GitHub Release.
- CI, package checks, and a fresh Windows install pass before tagging.
- No password, API token, or long-lived publishing credential enters GitHub.
- Published files are never overwritten; a correction uses a new patch
  version.

## One-time trusted publishing setup

The `ml-runtrace` PyPI JSON and Simple API endpoints returned HTTP 404 during
the 2026-08-12 release audit. Repeat that check immediately before publication:

```console
curl --fail https://pypi.org/pypi/ml-runtrace/json
curl --fail https://pypi.org/simple/ml-runtrace/
```

For an unregistered name, both commands should fail with HTTP 404. This only
checks current availability. PyPI explicitly states that a pending trusted
publisher does not create a project or reserve its name until first use.

Before enabling publishing or pushing a release tag:

1. Create a protected GitHub Actions environment named `pypi` and require the
   maintainer's approval for deployments.
2. In the maintainer's PyPI account, add a pending GitHub publisher with:
   - PyPI project name: `ml-runtrace`
   - owner: `Corvus-226`
   - repository: `RunTrace`
   - workflow: `release.yml`
   - environment: `pypi`
3. Confirm two-factor authentication and recovery details for both GitHub and
   PyPI.

The official references are
[PyPI's pending-publisher guide](https://docs.pypi.org/trusted-publishers/creating-a-project-through-oidc/),
[PyPI's publishing guide](https://docs.pypi.org/trusted-publishers/using-a-publisher/),
and
[GitHub's PyPI OIDC guide](https://docs.github.com/en/actions/how-tos/secure-your-work/security-harden-deployments/oidc-in-pypi).

## Prepare the source

1. Start from an up-to-date `main` branch and a scoped release issue.
2. Set the final version in `pyproject.toml` and `src/runtrace/__init__.py`.
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
```

Install the wheel into a newly created Windows virtual environment and run the
documented init → snapshot → list → show → diff workflow. Record test counts,
artifact names, SHA-256 values, and the smoke result in `docs/development-log.md`.

## Build the reviewed candidate

The checked-in `release.yml` is deliberately non-publishing. In GitHub Actions,
open **Release candidate**, choose **Run workflow**, and provide the reviewed
commit or tag plus the exact expected version. The workflow has read-only
repository permissions and no OIDC permission. It:

1. verifies the source version and versioned release-notes file;
2. reruns tests, lint, format, and package metadata checks;
3. builds the sdist and wheel once;
4. records SHA-256 values; and
5. retains the files as a seven-day workflow artifact for review.

Download that artifact, verify its hashes and contents, and record the Actions
run before requesting publication approval.

## Approve publication

The repository intentionally has no active PyPI or GitHub Release publishing
job at this stage. Pushing a tag currently does not upload a package. Enabling
or executing publication requires a separate, explicit maintainer approval and
a reviewed change that grants only the publish job `id-token: write` through
the protected `pypi` environment.

Only after the release-preparation pull request is merged and its `main` CI is
green—and after that separate approval—choose the exact audited commit. Prefer
a signed tag when signing is configured; otherwise create an annotated tag:

```console
git switch main
git pull --ff-only origin main
git tag -s v0.1.0 -m "RunTrace v0.1.0"
git push origin v0.1.0
```

If signing is unavailable, replace `-s` with `-a` and record that decision.
The approved publishing path must verify the tag/version match, build once,
publish the exact same files through PyPI trusted publishing, and attach those
files plus `SHA256SUMS` to the GitHub Release. Do not add token-based fallback
credentials.

## Post-publication verification

Wait for PyPI's index to expose the files, then use another new environment:

```console
python -m venv .venv-release-check
python -m pip install --no-cache-dir ml-runtrace==0.1.0
runtrace --version
runtrace --help
```

Repeat the documented workflow and compare the SHA-256 digests of the PyPI and
GitHub Release artifacts. Confirm that the GitHub Release points to the audited
tag and that the PyPI page identifies trusted publishing and attestations.

If publication reveals a serious issue, do not replace files. Yank the affected
release when appropriate, document the reason, fix forward, and publish a new
patch version.
