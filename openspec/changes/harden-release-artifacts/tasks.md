## 1. Minimal artifacts

- [x] 1.1 Restrict setuptools discovery to `iterable` and `iterable.*`.
- [x] 1.2 Declare all required package data explicitly and exclude unrelated top-level trees.
- [x] 1.3 Modernize license metadata to SPDX plus `license-files`.
- [x] 1.4 Add wheel/sdist content checks and allowed-top-level assertions.
- [x] 1.5 Install the built wheel in a clean environment and smoke-test imports plus `open_iterable()`.

## 2. Supported CI runtime

- [x] 2.1 Upgrade obsolete artifact actions to supported majors.
- [x] 2.2 Move CI/docs jobs from unsupported Node releases to a supported LTS line.
- [x] 2.3 Add explicit least-privilege workflow permissions.

## 3. Consolidated release flow

- [x] 3.1 Merge duplicate release/publish logic into one workflow with documented tag/manual triggers.
- [x] 3.2 Build wheel and sdist once and test the exact files that will be published.
- [x] 3.3 Configure a protected GitHub release environment and PyPI Trusted Publisher.
- [x] 3.4 Publish with OIDC and generate provenance/attestations.
- [x] 3.5 Remove the long-lived PyPI token and obsolete duplicate workflow after verification.
- [x] 3.6 Document normal release and protected recovery procedures.

## 4. Verification

- [ ] 4.1 Run `python -m build`, `twine check`, and `check-wheel-contents` from a clean checkout.
- [x] 4.2 Verify wheel contents contain only allowed top-level paths.
- [ ] 4.3 Exercise the consolidated workflow without publication, then complete one approved release.
