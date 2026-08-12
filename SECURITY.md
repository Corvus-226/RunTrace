# Security Policy

## Supported versions

RunTrace has not made its first stable release. Security fixes currently target
the latest development branch and will be documented in release notes.

## Reporting a vulnerability

Do not open a public issue containing exploit details, credentials, private
paths, or other sensitive data. Use the repository's private
[security advisory form](https://github.com/Corvus-226/RunTrace/security/advisories/new)
to report a vulnerability. If private reporting is unavailable, contact the
maintainer through the GitHub profile before sharing details.

Include a concise impact description, affected version or commit, reproduction
steps, and any suggested mitigation. Remove unrelated sensitive information.

## Data-handling principles

RunTrace is local-only by default. It must not automatically upload experiment
data or capture environment variables, credentials, API keys, tokens, or SSH
keys. Changes that expand captured metadata require explicit privacy review.
