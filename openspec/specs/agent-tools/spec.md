# agent-tools Specification

## Purpose
The agent-tools capability exposes JSON-serializable wrappers, machine-readable schemas,
optional LangChain and MCP integrations for LLM agents operating on IterableData datasets.
## Requirements
### Requirement: Agent Tool Wrappers
The system SHALL provide an `iterable.tools` module exposing JSON-serializable wrapper functions
for common agent operations over IterableData datasets.

#### Scenario: Read sample rows
- **WHEN** `tools.read_sample(path, n=5)` is called on a supported file
- **THEN** the function returns a dict with `ok=True` and `data` containing up to 5 row dictionaries
- **AND** the result is JSON-serializable

#### Scenario: Tool error handling
- **WHEN** a tool wrapper is called with an invalid path or unsupported format
- **THEN** the function returns a dict with `ok=False` and a clear `error` message
- **AND** does not raise unhandled exceptions to the agent runtime

#### Scenario: Infer schema via tool
- **WHEN** `tools.infer_schema(path)` is called
- **THEN** the function returns JSON-serializable schema metadata consistent with `ops.schema.infer()`

#### Scenario: Analyze dataset via tool
- **WHEN** `tools.analyze_dataset(path, autodoc=False)` is called
- **THEN** the function returns structure metadata consistent with `ops.inspect.analyze()`

#### Scenario: Generate documentation via tool
- **WHEN** `tools.generate_documentation(path, provider=..., format="json")` is called with AI deps available
- **THEN** the function returns documentation payload suitable for agent consumption

### Requirement: Tool Schema Export
The system SHALL export machine-readable tool schemas for OpenAI function calling, Anthropic tools,
and generic JSON Schema consumers.

#### Scenario: OpenAI function schemas
- **WHEN** `tools.schemas.to_openai_functions()` is called
- **THEN** the function returns a list of function definitions covering core tools
- **AND** each definition includes name, description, and parameters schema

#### Scenario: Anthropic tool schemas
- **WHEN** `tools.schemas.to_anthropic_tools()` is called
- **THEN** the function returns Anthropic-compatible tool definitions for the same core tools

#### Scenario: Schema stability tested
- **WHEN** CI runs tool schema snapshot tests
- **THEN** accidental breaking changes to tool names or required parameters fail the build

### Requirement: LangChain Tool Bundle
The system SHALL provide an optional LangChain integration that registers IterableData tools.

#### Scenario: Get LangChain tools
- **WHEN** `from iterable.tools.langchain import get_tools` is used with `langchain-core` installed
- **THEN** the function returns a list of LangChain `Tool` or `StructuredTool` instances
- **AND** each tool invokes the corresponding `iterable.tools` wrapper

#### Scenario: Missing LangChain dependency
- **WHEN** LangChain tools are imported without `langchain-core` installed
- **THEN** a clear `ImportError` is raised with install instructions

### Requirement: MCP Server
The system SHALL provide an optional Model Context Protocol server exposing IterableData read and
analysis operations for IDE agents.

#### Scenario: MCP server starts via stdio
- **WHEN** the MCP server is launched with `iterabledata[mcp]` installed
- **THEN** it registers tools for format detection, sampling, schema inference, analysis, and documentation generation
- **AND** communicates over stdio transport

#### Scenario: MCP read_sample tool
- **WHEN** an MCP client invokes `read_sample` with a valid file path
- **THEN** the server returns a JSON payload of sample rows
- **AND** supports optional redaction

#### Scenario: MCP destructive operations gated
- **WHEN** an MCP client invokes a write operation such as `convert_file`
- **THEN** the server requires an explicit confirmation flag before writing files

### Requirement: Validated JSON Documentation Output
The system SHALL support optional Pydantic validation of `ai.doc.generate()` JSON responses.

#### Scenario: Validate JSON output
- **WHEN** `doc.generate(..., format="json", validate_output=True)` completes successfully
- **THEN** the returned dict conforms to the `DocumentationResult` model

#### Scenario: Validation disabled by default
- **WHEN** `doc.generate()` is called without `validate_output`
- **THEN** behavior remains backward compatible with existing JSON dict responses

### Requirement: MCP Registry Manifest
The repository SHALL include a root-level `server.json` describing the
`iterable-mcp` stdio server for the official MCP Registry schema.

#### Scenario: server.json is present and version-aligned
- **WHEN** CI reads `server.json`
- **THEN** `$schema` is the MCP 2025-12-11 server schema
- **AND** `packages[0].registryType` is `pypi` with identifier `iterabledata`
- **AND** `version` equals `iterable.__version__`
- **AND** transport type is `stdio`

#### Scenario: MCP docs link the manifest
- **WHEN** a reader opens the MCP integration page
- **THEN** the page references `server.json` and `pip install iterabledata[mcp]`

