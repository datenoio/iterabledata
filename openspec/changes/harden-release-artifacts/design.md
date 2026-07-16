## Context

Setuptools namespace discovery currently includes Python files under unrelated top-level directories. Release workflows duplicate build and publish behavior and use a stored PyPI token. Some workflow actions and Node versions are beyond support.

## Goals / Non-Goals

- Goals:
  - Produce a minimal, reproducible wheel and source distribution.
  - Test the exact built artifacts before publication.
  - Publish with short-lived identity credentials and least privilege.
  - Maintain one authoritative release path.
- Non-Goals:
  - Change package name, public imports, or versioning semantics.
  - Add a CLI.
  - Lock all runtime dependencies.

## Decisions

### Explicit package discovery

Setuptools discovery will include only `iterable` and `iterable.*`. Wheel verification will assert allowed top-level paths rather than depending only on ignore rules.

### Build once, promote the same artifacts

The release workflow will create wheel and sdist once, run metadata/content/install smoke checks against them, upload them as immutable workflow artifacts, and publish those same files.

### Trusted Publishing

PyPI publication will use GitHub OIDC with `id-token: write` only in the protected publish job. Ordinary test/build jobs will have read-only permissions and no publishing credentials.

### Supported toolchain policy

Actions and Node runtimes must be on supported major versions. Dependabot/Renovate or a scheduled audit may propose updates, but release changes remain reviewed.

## Risks / Trade-offs

- A file unintentionally relied on from `examples/` or `dev/` will no longer ship. Mitigation: install and import tests plus explicit package-data declarations.
- OIDC setup requires PyPI project configuration. Mitigation: document one-time setup and retain a manual, protected recovery procedure that does not become a second normal workflow.
- Consolidating workflows can alter tag/manual behavior. Mitigation: preserve supported triggers and test a non-publishing build path first.

## Migration Plan

1. Restrict discovery and add artifact assertions.
2. Modernize metadata and validate wheel/sdist locally and in CI.
3. Consolidate build/release jobs without enabling publication.
4. Configure PyPI Trusted Publisher and enable the protected publish job.
5. Remove obsolete duplicate workflow and token secret after a successful release.

## Open Questions

- Which release environment approvers should be mandatory?
- Should provenance be generated through PyPI's publishing action, GitHub attestations, or both?
