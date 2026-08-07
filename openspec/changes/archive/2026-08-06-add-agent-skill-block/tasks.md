## 1. Model and schema

- [x] 1.1 Add `AgentSkillBlock` (and nested fields) Pydantic model in `iterable/ai/models.py`
- [x] 1.2 Register `agent_skill` in `_BLOCK_MODELS` so JSON Schema is available

## 2. Generator and registry

- [x] 2.1 Implement `generate_agent_skill` and neutral skill markdown renderer in `iterable/ai/blocks.py`
- [x] 2.2 Register `agent_skill` in `BLOCK_REGISTRY` with `requires_llm=True`
- [x] 2.3 Keep `agent_skill` out of `DEFAULT_BLOCKS`

## 3. Tests

- [x] 3.1 Extend FakeProvider / `tests/test_ai_blocks.py` for `agent_skill` structured output
- [x] 3.2 Assert opt-in generation, default-set exclusion, language, and frontmatter shape
