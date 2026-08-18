## 1. Ownership marker

- [x] 1.1 Add `<!-- mcp-name: io.github.datenoio/iterabledata -->` to `README.md`
- [x] 1.2 Assert the marker matches `server.json` `name` in tests

## 2. Release publish

- [x] 2.1 Add an `mcp-registry` job to `.github/workflows/release.yml` after PyPI publish
- [x] 2.2 Authenticate with `mcp-publisher login github-oidc` and `id-token: write`
- [x] 2.3 Update Agent discovery docs: listing is on the next tagged release

## 3. Validate

- [x] 3.1 `openspec validate publish-mcp-registry --strict`
- [x] 3.2 Run targeted pytest and ruff
