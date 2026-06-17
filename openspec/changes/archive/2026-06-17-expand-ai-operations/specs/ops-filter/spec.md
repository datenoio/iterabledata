## ADDED Requirements

### Requirement: AI-Assisted Filter Execution
The system SHALL accept filter abstract syntax trees produced by `ai.translate_filter()` and apply
them through the existing filter operation layer.

#### Scenario: Apply AI-produced AST
- **WHEN** a filter AST from `ai.translate_filter()` is passed to the filter executor
- **THEN** rows are filtered according to the AST semantics
- **AND** behavior matches equivalent hand-written `ops.filter` expressions for supported nodes

#### Scenario: Reject unsupported AST nodes
- **WHEN** a filter AST contains a node type not in the whitelist
- **THEN** the executor raises a clear validation error before processing rows
