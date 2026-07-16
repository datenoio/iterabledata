# Change: Harden Release Artifacts and Publishing

## Why

The review found that wheel discovery includes unrelated top-level Python trees, ignored local files can leak into builds, two workflows duplicate release logic, publishing depends on a long-lived token, and CI references obsolete action/runtime versions. The exact artifact delivered to users is therefore broader and less reproducible than the source package intends.

## What Changes

- Restrict package discovery and wheel contents to the importable `iterable` package and distribution metadata.
- Build from a clean checkout and verify wheel contents plus fresh-environment imports before publishing.
- Consolidate release automation into one build-once workflow using PyPI Trusted Publishing/OIDC.
- Use supported action and Node runtime versions, explicit permissions, a protected release environment, and provenance/attestations.
- Modernize SPDX/license-file metadata without changing the MIT license.

## Impact

- Affected specs: `distribution-artifacts`, `release-automation`
- Affected files: `pyproject.toml`, build configuration, `.github/workflows/ci.yml`, security/release/publish workflows
- Compatibility: distribution contents become narrower; the importable package and public API do not change
