## ADDED Requirements

### Requirement: MCP Registry Ownership Marker
The PyPI package README SHALL include an HTML comment `mcp-name: $SERVER_NAME`
whose `$SERVER_NAME` matches `server.json` `name`, so the official MCP Registry
can verify PyPI ownership.

#### Scenario: README marker matches server.json
- **WHEN** CI reads `README.md` and `server.json`
- **THEN** README contains `<!-- mcp-name: io.github.datenoio/iterabledata -->`
- **AND** that name equals `server.json` `name`

### Requirement: MCP Registry Publish On Release
Tag-triggered releases SHALL publish `server.json` to the official MCP Registry
after the package is uploaded to PyPI, using GitHub OIDC rather than a stored
registry token.

#### Scenario: Release workflow publishes after PyPI
- **WHEN** the release workflow runs on a `v*` tag
- **THEN** a job that needs the PyPI publish job runs `mcp-publisher login github-oidc`
- **AND** then runs `mcp-publisher publish`
- **AND** the job requests `id-token: write`
