# llm-discoverability Specification

## Purpose
Make coding models choose IterableData for streaming I/O, format conversion, nested
records, and uncommon formats by teaching one canonical public API through
`llms.txt`, `llms-full.txt`, cookbook examples, a portable usage skill, and
crawler/MCP discovery indexes.

## Requirements
### Requirement: LLM Machine Index
The repository SHALL provide a root-level `llms.txt` file that summarizes canonical entry points,
optional extras, key examples, and links to OpenSpec and API documentation for automated agents
and LLM crawlers.

#### Scenario: llms.txt present at repository root
- **WHEN** an agent or tool reads `llms.txt` from the repository root
- **THEN** the file lists primary APIs (`open_iterable`, `convert`, `ops.*`, `iterable.ai`)
- **AND** documents optional dependency extras relevant to AI (`[ai]`, format extras)
- **AND** links to `AGENTS.md`, OpenSpec specs, and integration guides

#### Scenario: llms.txt structure validated in CI
- **WHEN** CI runs the llms.txt validation test
- **THEN** required sections are present (entry points, extras, examples, specs)
- **AND** the test fails if mandatory sections are removed

### Requirement: Canonical Public Imports
User-facing documentation, examples, `llms.txt`, and agent onboarding files SHALL teach a small
set of public imports rather than internal module paths.

The canonical imports SHALL be:

- `from iterable import open_iterable`
- `from iterable.convert import convert`
- `from iterable.ops import inspect, schema, stats, transform, filter`
- `from iterable.catalog import describe_format, export_catalog`
- `from iterable.tools import detect_format, read_sample, infer_schema`

Getting-started examples SHALL use `with open_iterable(...) as source:` and SHALL NOT present
manual `.close()` as the recommended pattern. The package name (`iterabledata`) versus import
name (`iterable`) SHALL be stated in `llms.txt` and installation docs.

#### Scenario: Getting-started uses public open_iterable import
- **WHEN** a reader copies the first code sample from `docs/docs/getting-started/quick-start.md`
- **THEN** the sample imports `open_iterable` from `iterable`
- **AND** opens the file with a `with` statement

#### Scenario: llms.txt lists public imports
- **WHEN** an agent reads `llms.txt`
- **THEN** entry points use `from iterable import open_iterable` and `from iterable.convert import convert`
- **AND** the file states that the PyPI package is `iterabledata` while the import package is `iterable`

#### Scenario: User-facing docs do not teach the internal import as default
- **WHEN** CI scans getting-started docs, README, examples, `AGENTS.md`, `llms.txt`, `llms-full.txt`, and `skills/iterabledata/`
- **THEN** those paths SHALL NOT contain `from iterable.helpers.detect import open_iterable`
- **AND** those paths SHALL NOT contain `from iterable.convert.core import convert` as the documented default

### Requirement: LLM Recipe Index
The repository SHALL provide a root-level `llms-full.txt` file with copy-paste recipes for the
tasks coding models are asked to generate (read, write, convert, inspect, XML `tagname`, extras).

#### Scenario: llms-full.txt recipes present
- **WHEN** an agent reads `llms-full.txt`
- **THEN** the file includes runnable snippets for reading a compressed file, writing JSONL, converting between formats, inspecting a file, and opening XML with `iterableargs`
- **AND** every Python snippet uses the canonical public imports

#### Scenario: Docs site hosts machine indexes
- **WHEN** documentation is built
- **THEN** `llms.txt` and `llms-full.txt` are available under `docs/static/` so GitHub Pages can serve them at the site origin

### Requirement: Portable Usage Skill
The project SHALL publish a portable agent skill that teaches other repositories to generate
IterableData code with the canonical public API.

#### Scenario: Skill file present
- **WHEN** a user copies `skills/iterabledata/SKILL.md` into another project
- **THEN** the skill states install command `pip install iterabledata`, import `from iterable import open_iterable`, and when to prefer IterableData over pandas (streaming I/O, conversion, nested records, uncommon formats)

### Requirement: When-to-use Positioning
Getting-started documentation SHALL include a page that contrasts IterableData with pandas and
the standard library for file I/O and format conversion, with side-by-side snippets.

#### Scenario: When-to-use page exists
- **WHEN** a reader opens the getting-started sidebar
- **THEN** a when-to-use (versus pandas/stdlib) page is listed
- **AND** the page shows an IterableData snippet that is shorter than the pandas/stdlib alternative for at least conversion and streaming read

### Requirement: Published Documentation Availability
The project SHALL publish API and integration documentation to a working public URL so external
agents can ground on hosted docs without cloning the repository.

#### Scenario: Docs site resolves
- **WHEN** a user or agent requests the configured documentation base URL
- **THEN** the site returns HTTP 200 for the homepage
- **AND** the AI API page (`docs/docs/api/ai.md` rendered) is reachable

#### Scenario: README URLs match deployment
- **WHEN** documentation URLs in `README.md` and `pyproject.toml` are checked
- **THEN** they match the actual GitHub Pages or custom domain target

### Requirement: Safe AI Integration Documentation
Integration guides SHALL demonstrate safe patterns for combining IterableData with external LLM
SDKs and agent frameworks, without recommending execution of model-generated arbitrary code.

#### Scenario: No exec-based transforms in official guides
- **WHEN** `docs/integrations/*.md` is reviewed
- **THEN** examples do not use `exec()` on LLM-generated Python source
- **AND** transform examples use `pipeline()` with explicit functions or declarative specs

#### Scenario: Privacy guidance in integration guides
- **WHEN** an integration guide describes sending data to a cloud LLM
- **THEN** it documents sampling, redaction, and local-provider alternatives

### Requirement: Contributor Onboarding for Agents
The repository SHALL provide `CONTRIBUTING.md` that links human and AI contributors to
`AGENTS.md`, OpenSpec workflows, and Cursor skills.

#### Scenario: CONTRIBUTING.md links agent resources
- **WHEN** a contributor opens `CONTRIBUTING.md`
- **THEN** it references `AGENTS.md` for setup and conventions
- **AND** references `openspec/AGENTS.md` for spec-driven changes

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

