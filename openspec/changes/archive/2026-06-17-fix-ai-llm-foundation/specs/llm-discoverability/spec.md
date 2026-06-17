## ADDED Requirements

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
