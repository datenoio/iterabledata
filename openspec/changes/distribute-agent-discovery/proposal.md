# Change: Distribute agent discovery indexes

## Why

Phase 5 taught coding models the public IterableData API, but crawlers and MCP
clients still have to find the repo by luck. The docs site now serves `llms.txt`
and `llms-full.txt`; MCP is an extra with no registry manifest; the portable
skill has nowhere to be discovered except GitHub browse. The remaining product
work is retrieval: put the same canonical snippets on the surfaces directories
and IDEs actually index.

## What Changes

- Commit an MCP Registry `server.json` for `iterable-mcp` (`pip install iterabledata[mcp]`).
- Serve `/.well-known/llms.txt` and `robots.txt` from the docs site next to the
  existing `/llms.txt` and `/llms-full.txt`.
- Expand the cookbook with gzip-read, JSONL-write, and `read_sample` scripts.
- Add a heuristic prompt-eval (no paid APIs) that fails if the public corpus no
  longer answers common generation prompts with canonical imports.
- Document how to submit the skill / MCP server / llms.txt to external
  directories (Context7, skills.sh, MCP registry) without requiring those
  submissions in CI.
- Fix the archived `llm-discoverability` spec Purpose (left as TBD) and point
  the LLM readiness roadmap at Phase 6.

No breaking API changes. No CLI. No `exec()` of model-generated code. External
directory *accounts* stay out of CI; this change ships the files those
directories ingest.

## Impact

- Affected specs: `llm-discoverability`, `examples`, `agent-tools`
- Affected code/docs: `server.json`, `docs/static/`, `examples/cookbook/`,
  `docs/docs/integrations/`, `tests/test_llm_prompt_eval.py`,
  `openspec/changes/LLM_READINESS_ROADMAP.md`, `openspec/specs/llm-discoverability/spec.md`
