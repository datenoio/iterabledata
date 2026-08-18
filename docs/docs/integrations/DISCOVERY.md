---
sidebar_position: 6
title: Agent discovery
description: MCP server.json, llms.txt, and the portable skill for directories and crawlers
---

# Agent discovery

Phase 5 taught coding models the public API. This page is the retrieval surface:
the files directories and crawlers ingest. Context7 and skill indexes still need a
maintainer submission; the MCP Registry is published from the tagged release
workflow after PyPI upload.

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

The release workflow publishes this file to the [MCP Registry](https://github.com/modelcontextprotocol/registry) after each tagged PyPI upload (`mcp-publisher login github-oidc`). Schema: `2025-12-11`. Server name: `io.github.datenoio/iterabledata`. PyPI ownership is the README marker `<!-- mcp-name: io.github.datenoio/iterabledata -->` (live after the next `v*` release). Setup docs: [MCP](/integrations/MCP).

## Portable skill

Copy [`skills/iterabledata/SKILL.md`](https://github.com/datenoio/iterabledata/blob/main/skills/iterabledata/SKILL.md) into another repository (Cursor/Claude Code skills directory). Optionally list it on [skills.sh](https://skills.sh) or similar skill indexes.

## Context7 / llms.txt directories

Point Context7, llmstxt.org, and similar indexes at the hosted `llms.txt` URL above and the GitHub repo `datenoio/iterabledata`. The site `robots.txt` allows those paths.

## Canonical imports (do not drift)

```python
from iterable import open_iterable
from iterable.convert import convert
```

PyPI package: `iterabledata`. Import package: `iterable`.
