# Change: Publish IterableData to the MCP Registry on release

## Why

Phase 6 committed `server.json`, but the official MCP Registry will reject a
publish until PyPI proves ownership (`mcp-name` in the package README) and a
publisher authenticates. Interactive `mcp-publisher login github` cannot run in
CI. GitHub OIDC login can, after the next PyPI release that includes the
ownership marker.

## What Changes

- Add `<!-- mcp-name: io.github.datenoio/iterabledata -->` to `README.md` so the
  PyPI long description satisfies registry ownership checks.
- Publish `server.json` from the existing tag/release workflow using
  `mcp-publisher login github-oidc` after PyPI upload.
- Test that the README marker matches `server.json` `name`.
- Document in Agent discovery that registry listing happens on release, not from
  a laptop login.

No runtime API changes. No new CLI in this package. First successful registry
listing still requires the next `v*` PyPI release so the README marker is live.

## Impact

- Affected specs: `agent-tools`
- Affected files: `README.md`, `.github/workflows/release.yml`,
  `tests/test_mcp_server.py`, `docs/docs/integrations/DISCOVERY.md`
