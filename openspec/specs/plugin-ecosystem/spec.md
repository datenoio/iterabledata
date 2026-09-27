# plugin-ecosystem Specification

## Purpose
TBD - created by archiving change add-reference-plugin. Update Purpose after archive.
## Requirements
### Requirement: Published reference plugin

The repository SHALL ship a minimal, installable example plugin demonstrating
the documented discovery mechanism.

#### Scenario: Install and discover

- **WHEN** the example plugin is pip-installed into an environment with
  iterabledata
- **THEN** the plugin's format/codec is discovered through the documented
  loader and usable via `open_iterable()`

#### Scenario: No core changes required

- **WHEN** the example plugin is exercised end-to-end
- **THEN** it works against the unmodified installed library, proving the
  loader contract is sufficient

