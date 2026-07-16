## ADDED Requirements

### Requirement: Single Build-Once Release Workflow

The repository SHALL maintain one authoritative release workflow that builds artifacts once, verifies them, and publishes those same immutable artifacts after approval.

#### Scenario: Release candidate succeeds

- **WHEN** an authorized release trigger runs
- **THEN** one wheel and source distribution set SHALL be built
- **AND** verification and publication SHALL use that same set
- **AND** no second workflow SHALL rebuild a different publish candidate

#### Scenario: Verification fails

- **WHEN** any artifact or test gate fails
- **THEN** the publish job SHALL not run

### Requirement: Trusted and Least-Privilege Publishing

Normal publication SHALL use PyPI Trusted Publishing with short-lived OIDC credentials from a protected environment. Long-lived PyPI API tokens SHALL NOT be required by the normal workflow.

#### Scenario: Publish job requests identity

- **WHEN** the approved publish job starts
- **THEN** only that job SHALL receive `id-token: write`
- **AND** PyPI SHALL accept the configured trusted publisher identity

#### Scenario: Ordinary CI job runs

- **WHEN** tests, lint, or artifact verification run
- **THEN** those jobs SHALL have read-only repository permissions unless a narrower additional permission is required
- **AND** they SHALL NOT receive publishing credentials

### Requirement: Supported Release Toolchain and Provenance

Release and CI workflows SHALL use supported action major versions and supported Node runtimes, and published artifacts SHALL carry available provenance or attestations tied to the source revision and workflow.

#### Scenario: Workflow dependency audit

- **WHEN** workflow action and runtime versions are checked
- **THEN** no configured major/runtime SHALL be past its upstream support cutoff

#### Scenario: Successful publication

- **WHEN** artifacts are published
- **THEN** provenance or attestations SHALL identify the source revision and release workflow that produced them
