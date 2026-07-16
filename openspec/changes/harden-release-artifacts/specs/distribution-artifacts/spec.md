## ADDED Requirements

### Requirement: Minimal Python Distribution Contents

Built wheels SHALL contain only the importable `iterable` package, explicitly declared package data, and distribution metadata. Unrelated repository trees and ignored working-tree files SHALL NOT be included through implicit namespace discovery.

#### Scenario: Wheel top-level paths are checked

- **WHEN** CI builds a wheel from a clean checkout
- **THEN** every wheel entry SHALL be under `iterable/` or the wheel's distribution metadata directories
- **AND** top-level `dev/`, `examples/`, `docs/`, and tests SHALL NOT be present

#### Scenario: Ignored local Python file exists

- **WHEN** a developer has an ignored Python file outside `iterable/`
- **THEN** package discovery SHALL NOT include it in a wheel

### Requirement: Built Artifact Verification

The project SHALL validate the exact wheel and source distribution intended for publication for metadata correctness, content policy, installation, and representative imports.

#### Scenario: Fresh wheel installation

- **WHEN** a release candidate wheel is installed into a fresh environment
- **THEN** `import iterable` and the documented `open_iterable` import SHALL succeed
- **AND** a core CSV/JSONL smoke operation SHALL succeed without the source checkout on `sys.path`

#### Scenario: Artifact validation failure

- **WHEN** metadata, content, installation, or smoke validation fails
- **THEN** the release workflow SHALL stop before publication
- **AND** the failing artifact SHALL NOT be published

### Requirement: Modern License Metadata

Distribution metadata SHALL declare the MIT license using current SPDX-compatible project metadata and SHALL include the repository's license file.

#### Scenario: Build metadata inspection

- **WHEN** wheel and sdist metadata are inspected
- **THEN** they SHALL identify the MIT license without deprecated license-table/classifier usage
- **AND** the configured license file SHALL be present in the distribution
