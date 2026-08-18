## ADDED Requirements

### Requirement: MCP Registry Manifest
The repository SHALL include a root-level `server.json` describing the
`iterable-mcp` stdio server for the official MCP Registry schema.

#### Scenario: server.json is present and version-aligned
- **WHEN** CI reads `server.json`
- **THEN** `$schema` is the MCP 2025-12-11 server schema
- **AND** `packages[0].registryType` is `pypi` with identifier `iterabledata`
- **AND** `version` equals `iterable.__version__`
- **AND** transport type is `stdio`

#### Scenario: MCP docs link the manifest
- **WHEN** a reader opens the MCP integration page
- **THEN** the page references `server.json` and `pip install iterabledata[mcp]`
