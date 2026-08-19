---
sidebar_position: 7
title: Directory submissions
description: Copy-paste payloads for Context7, llms.txt directories, and skills.sh
---

# Directory submissions

IterableData discovery indexes are committed in this repository and deployed to GitHub Pages.
Some directories require a maintainer submission. **Do not commit API keys.** Run these steps
locally with your own credentials.

**Status (2026-08-19)**

| Directory | Status | Action |
|-----------|--------|--------|
| MCP Registry (`io.github.datenoio/iterabledata`) | Live since 1.0.23 | None — OIDC publish runs on tagged releases |
| GitHub Pages `llms.txt` / `llms-full.txt` | Live | Regenerate with `python dev/scripts/generate_llms_txt.py` |
| Context7 | Pending maintainer | Submit repo or hosted `llms.txt` (below) |
| llmstxt.site directory | Pending maintainer | Submit form (below) |
| skills.sh | Pending telemetry | Install skill from repo once (below) |

Canonical URLs to cite in every submission:

```
https://datenoio.github.io/iterabledata/llms.txt
https://datenoio.github.io/iterabledata/llms-full.txt
https://datenoio.github.io/iterabledata/.well-known/llms.txt
https://datenoio.github.io/iterabledata/skills/iterabledata/SKILL.md
https://github.com/datenoio/iterabledata
https://pypi.org/project/iterabledata/
```

## Context7

Submit the GitHub repository (preferred — indexes docs + source) or the hosted `llms.txt`.

**Web UI:** [context7.com/add-library](https://context7.com/add-library)

**GitHub repository payload**

```json
{
  "docsRepoUrl": "https://github.com/datenoio/iterabledata"
}
```

**Hosted llms.txt payload**

```json
{
  "llmstxtUrl": "https://datenoio.github.io/iterabledata/llms-full.txt"
}
```

**API (requires a Context7 API key — create at context7.com)**

```bash
# GitHub repo
curl -sS -X POST 'https://context7.com/api/v2/add/repo/github' \
  -H 'Authorization: Bearer ctx7sk-REPLACE_ME' \
  -H 'Content-Type: application/json' \
  -d '{"docsRepoUrl":"https://github.com/datenoio/iterabledata"}'

# Or llms.txt only
curl -sS -X POST 'https://context7.com/api/v2/add/llmstxt' \
  -H 'Authorization: Bearer ctx7sk-REPLACE_ME' \
  -H 'Content-Type: application/json' \
  -d '{"llmstxtUrl":"https://datenoio.github.io/iterabledata/llms-full.txt"}'
```

After approval, agents can resolve the library as `/datenoio/iterabledata` (exact ID is assigned by Context7).

## llmstxt.site directory

**Form:** [llmstxt.site/submit](https://llmstxt.site/submit)

Suggested fields:

| Field | Value |
|-------|-------|
| Site name | IterableData |
| llms.txt URL | `https://datenoio.github.io/iterabledata/llms.txt` |
| llms-full.txt URL | `https://datenoio.github.io/iterabledata/llms-full.txt` |
| Repository | `https://github.com/datenoio/iterabledata` |
| PyPI | `https://pypi.org/project/iterabledata/` |

**Alternate explorer:** [llms-text.ai/request](https://llms-text.ai/request) (GitHub issue workflow).

Note: GitHub Pages serves under `/iterabledata/` (project site), not the org root. Submit the full URLs above, not `datenoio.github.io/llms.txt`.

## skills.sh

skills.sh indexes skills after the Skills CLI records installs from a public GitHub repository.
There is no manual listing form for new skills.

```bash
npx skills add datenoio/iterabledata --skill iterabledata
```

The skill file lives at `skills/iterabledata/SKILL.md` in this repository. It is also hosted at
`https://datenoio.github.io/iterabledata/skills/iterabledata/SKILL.md` and linked from the
`## Skills` section of `llms.txt`.

Optional: add a `skills.sh.json` in the repo root after telemetry has seen the repository
(see [skills.sh](https://skills.sh/) documentation).

## Verification checklist

After submitting, confirm:

1. [MCP Registry search](https://registry.modelcontextprotocol.io/v0/servers?search=io.github.datenoio/iterabledata) returns `io.github.datenoio/iterabledata`.
2. `curl -sS https://datenoio.github.io/iterabledata/llms.txt | head` returns the machine index.
3. `curl -sS https://datenoio.github.io/iterabledata/skills/iterabledata/SKILL.md | head` returns YAML frontmatter with `name: iterabledata`.
4. Context7 / llmstxt.site listings appear after their review queue (may take days).

## Related

- [Agent discovery](/integrations/DISCOVERY) — hosted indexes and MCP manifest
- [Cookbook](/getting-started/cookbook) — fifteen prompt-shaped scripts
- [MCP setup](/integrations/MCP) — `pip install iterabledata[mcp]` then `iterable-mcp`
