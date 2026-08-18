## 1. Spec and roadmap

- [x] 1.1 Write proposal, design, and delta specs; `openspec validate distribute-agent-discovery --strict`
- [x] 1.2 Replace `llm-discoverability` Purpose TBD with a real purpose statement
- [x] 1.3 Add Phase 6 to `openspec/changes/LLM_READINESS_ROADMAP.md` and fix the archived Phase 5 link

## 2. MCP and crawler indexes

- [x] 2.1 Add root `server.json` matching `iterable.__version__` and the MCP 2025-12-11 schema
- [x] 2.2 Generate `docs/static/.well-known/llms.txt` and `docs/static/robots.txt` from `dev/scripts/generate_llms_txt.py`
- [x] 2.3 Document MCP registry / skill / Context7 submission in `docs/docs/integrations/DISCOVERY.md` and link from MCP.md and the AI sidebar

## 3. Cookbook and prompt-eval

- [x] 3.1 Add cookbook scripts for gzip read, JSONL write, and `read_sample`
- [x] 3.2 Update cookbook README and getting-started cookbook page
- [x] 3.3 Add `tests/test_llm_prompt_eval.py` and `server.json` / well-known tests
- [x] 3.4 Run ruff and targeted pytest
