## ADDED Requirements

### Requirement: Optional agent skill documentation block
The system SHALL provide an LLM-backed documentation block named `agent_skill`
that produces structured skill data and a neutral agent-skill Markdown document
(YAML frontmatter with at least `name` and `description`, plus a Markdown body).
The block MUST be registered and available for explicit selection, and MUST NOT
be included in the default block set used when `blocks` is omitted.

#### Scenario: Opt-in generation
- **WHEN** `ai.doc.generate_blocks()` is called with `blocks` including `agent_skill`
- **THEN** the result contains an `agent_skill` block entry with `markdown` and `data`
- **AND** the markdown begins with YAML frontmatter containing `name` and `description`

#### Scenario: Not in default block set
- **WHEN** `ai.doc.generate_blocks()` is called without an explicit `blocks` list
- **THEN** the default blocks are generated without `agent_skill`

#### Scenario: Skill language follows block context
- **WHEN** `agent_skill` is generated with a non-English `language` on the block context
- **THEN** skill prose fields in the structured data and rendered markdown use that language

#### Scenario: Structured schema is available
- **WHEN** a caller requests the JSON Schema for the `agent_skill` block
- **THEN** a schema describing the structured skill payload is returned
