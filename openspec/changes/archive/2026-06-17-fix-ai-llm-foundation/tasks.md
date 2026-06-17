## 1. Wire autodoc integration

- [x] 1.1 Implement `inspect.analyze(autodoc=True)` calling `ai.doc.generate()` with analysis context
- [x] 1.2 Add `documentation` and `documentation_meta` keys to analyze result when `autodoc=True`
- [x] 1.3 Raise clear `ImportError` when `[ai]` extra missing (remove silent `pass`)
- [x] 1.4 Support `autodoc` provider/model kwargs forwarded to `doc.generate()`
- [x] 1.5 Update `inspect.analyze()` docstring and `docs/docs/api/` cross-links

## 2. Spec and Purpose updates

- [x] 2.1 Write Purpose for `openspec/specs/ai/spec.md` (via delta archive or direct update on merge)
- [x] 2.2 Write Purpose for `openspec/specs/ops-inspect/spec.md`
- [x] 2.3 Expand autodoc scenario in ops-inspect delta to match implementation

## 3. llms.txt and contributor onboarding

- [x] 3.1 Add `dev/scripts/generate_llms_txt.py` to emit root `llms.txt`
- [x] 3.2 Commit initial `llms.txt` (entry points, extras map, top examples, OpenSpec link)
- [x] 3.3 Add `tests/test_llms_txt.py` asserting required sections exist
- [x] 3.4 Add `CONTRIBUTING.md` linking `AGENTS.md`, OpenSpec workflow, Cursor skills

## 4. Docs site deployment

- [x] 4.1 Fix `docs/docusaurus.config.js` `url` / `baseUrl` / `organizationName` / `projectName`
- [x] 4.2 Verify `.github/workflows/deploy-docs.yml` publishes successfully
- [x] 4.3 Update `README.md`, `pyproject.toml` project URLs to working docs URL
- [x] 4.4 Document setup in `docs/GITHUB_PAGES_SETUP.md`

## 5. Integration guide security hardening

- [x] 5.1 Remove or replace `exec()` patterns in `docs/integrations/CLAUDE.md`
- [x] 5.2 Remove or replace `exec()` patterns in `docs/integrations/OPENAI.md` and `GEMINI.md`
- [x] 5.3 Add "Data privacy" section to each integration guide (residency, sampling, redaction)
- [x] 5.4 Update `docs/integrations/AI_FRAMEWORKS.md` with declarative transform examples

## 6. AI conformance tests

- [x] 6.1 Add `tests/test_ai_conformance.py` parametrized from OpenSpec scenario names
- [x] 6.2 Cover autodoc integration in `tests/test_inspect.py`
- [x] 6.3 Add `@pytest.mark.ai` marker in `pyproject.toml` for AI-related tests

## 7. README and discoverability

- [x] 7.1 Add "AI Quick Start" section to `README.md` (local provider first)
- [x] 7.2 Link `llms.txt` from README for agent consumers

## 8. Verification

- [x] 8.1 `pytest tests/test_inspect.py tests/test_ai.py tests/test_ai_conformance.py tests/test_llms_txt.py -v`
- [x] 8.2 `ruff check iterable tests && ruff format --check iterable tests`
- [x] 8.3 `openspec validate fix-ai-llm-foundation --strict`
