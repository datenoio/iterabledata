# Releasing

Releases are made from a version tag such as `v1.2.3`. The `Release` workflow
builds the wheel and source distribution once, checks their metadata and
contents, installs the wheel in a clean environment, and uploads those exact
artifacts for publication and the GitHub release.

PyPI publication runs in the protected `pypi` environment using GitHub OIDC
Trusted Publishing. No PyPI API token is stored in repository or organization
secrets. Configure the PyPI project publisher for this repository, workflow,
and protected environment before enabling a production release.

For a normal release:

1. Update `iterable/__init__.py` and the changelog, then merge to the release branch.
2. Create and push an annotated `v<version>` tag.
3. Review the build, wheel smoke test, provenance, and GitHub release jobs.

The manual workflow trigger accepts a tag for recovery or a pre-approved
release rerun. If PyPI publication is unavailable, keep the protected build
artifacts and resolve the environment or publisher configuration before a
rerun; do not add a long-lived token or rebuild a different artifact locally.
