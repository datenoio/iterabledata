## ADDED Requirements

### Requirement: Well-Known LLM Index
The documentation site SHALL serve a `.well-known/llms.txt` copy of the root
machine index so crawlers that look under well-known paths can retrieve the
canonical public API without cloning the repository.

#### Scenario: well-known llms.txt matches root
- **WHEN** CI compares `docs/static/.well-known/llms.txt` to root `llms.txt`
- **THEN** the files are identical
- **AND** `docs/static/robots.txt` allows `/llms.txt` and `/llms-full.txt`

### Requirement: Heuristic Prompt Coverage
The test suite SHALL include a heuristic prompt-eval that checks the public
generation corpus (portable skill, `llms-full.txt`, cookbook scripts) for
canonical snippets matching common coding-model prompts. The eval SHALL NOT
call paid LLM APIs.

#### Scenario: Common prompts hit canonical imports
- **WHEN** CI runs the prompt-eval
- **THEN** prompts for reading, converting, writing JSONL, XML `tagname`, and
  schema inference each match required substrings in the public corpus
- **AND** every matched snippet uses `from iterable import open_iterable` or
  `from iterable.convert import convert` rather than internal module paths

### Requirement: External Directory Submission Guide
Getting-started / integration docs SHALL describe how a maintainer submits
IterableData to MCP, skill, and llms.txt directories, without requiring those
submissions to succeed in CI.

#### Scenario: Discovery page lists submission targets
- **WHEN** a maintainer opens the agent discovery integration page
- **THEN** it lists the MCP Registry `server.json`, the portable skill path,
  and the hosted `llms.txt` / `llms-full.txt` URLs
- **AND** it states that CI does not publish to those directories
