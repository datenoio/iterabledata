---
sidebar_position: 6
title: Agent discovery
description: MCP server.json, llms.txt, and the portable skill for directories and crawlers
---

# Agent discovery

Phase 5 taught coding models the public API. This page is the retrieval surface:
the files directories and crawlers ingest. External directory submissions (Context7,
llmstxt.site, skills.sh) still need a maintainer — see [Directory submissions](/integrations/DIRECTORY_SUBMISSIONS)
for copy-paste payloads. The MCP Registry listing is live from tagged releases.

## Hosted machine indexes

| File | URL |
|------|-----|
| Short index | https://datenoio.github.io/iterabledata/llms.txt |
| Copy-paste recipes | https://datenoio.github.io/iterabledata/llms-full.txt |
| Well-known copy | https://datenoio.github.io/iterabledata/.well-known/llms.txt |

Regenerate committed copies with `python dev/scripts/generate_llms_txt.py`.

## MCP Registry

Root [`server.json`](https://github.com/datenoio/iterabledata/blob/main/server.json) describes the stdio server:

```bash
pip install iterabledata[mcp]
iterable-mcp
```

The release workflow publishes this file to the [MCP Registry](https://registry.modelcontextprotocol.io) after each tagged PyPI upload (`mcp-publisher login github-oidc`), retrying until PyPI indexes the new version. Schema: `2025-12-11`. Server name: `io.github.datenoio/iterabledata` (listed as of 1.0.23). PyPI ownership is the README marker `<!-- mcp-name: io.github.datenoio/iterabledata -->`. Setup docs: [MCP](/integrations/MCP).

## Portable skill

Copy [`skills/iterabledata/SKILL.md`](https://github.com/datenoio/iterabledata/blob/main/skills/iterabledata/SKILL.md) into another repository (Cursor/Claude Code skills directory). Optionally list it on [skills.sh](https://skills.sh) or similar skill indexes.

## Context7 / llms.txt directories

Point Context7, llmstxt.org, and similar indexes at the hosted `llms.txt` URL above and the GitHub repo `datenoio/iterabledata`. The site `robots.txt` allows those paths. Copy-paste submission payloads: [Directory submissions](/integrations/DIRECTORY_SUBMISSIONS).

## Portable skill in llms.txt

Root `llms.txt` includes a `## Skills` section linking the hosted portable skill at
`https://datenoio.github.io/iterabledata/skills/iterabledata/SKILL.md` (generated from
`skills/iterabledata/SKILL.md` by `dev/scripts/generate_llms_txt.py`).

## Canonical imports (do not drift)

```python
from iterable import open_iterable
from iterable.convert import convert
```

PyPI package: `iterabledata`. Import package: `iterable`.
