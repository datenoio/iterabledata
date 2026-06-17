"""Machine-readable tool schemas for LLM function calling."""

from __future__ import annotations

import copy
import json
from typing import Any

from . import (
    analyze_dataset,
    compute_stats,
    convert_file,
    describe_capabilities,
    detect_format,
    generate_documentation,
    infer_schema,
    plan_conversion,
    read_sample,
    suggest_transform,
    translate_filter_tool,
    validate_data,
)

TOOL_HANDLERS: dict[str, Any] = {
    "detect_format": detect_format,
    "describe_capabilities": describe_capabilities,
    "read_sample": read_sample,
    "infer_schema": infer_schema,
    "analyze_dataset": analyze_dataset,
    "compute_stats": compute_stats,
    "convert_file": convert_file,
    "generate_documentation": generate_documentation,
    "validate_data": validate_data,
    "plan_conversion": plan_conversion,
    "suggest_transform": suggest_transform,
    "translate_filter": translate_filter_tool,
}

TOOL_DEFINITIONS: list[dict[str, Any]] = [
    {
        "name": "detect_format",
        "description": "Detect data format and compression for a file path.",
        "parameters": {
            "type": "object",
            "properties": {"path": {"type": "string", "description": "Path to the data file"}},
            "required": ["path"],
        },
    },
    {
        "name": "describe_capabilities",
        "description": "Describe format metadata, example args, and capabilities by format id or alias.",
        "parameters": {
            "type": "object",
            "properties": {
                "format_id": {"type": "string", "description": "Format id or alias (e.g. csv, tsv, xml)"},
            },
            "required": ["format_id"],
        },
    },
    {
        "name": "read_sample",
        "description": "Read a bounded sample of rows from a data file.",
        "parameters": {
            "type": "object",
            "properties": {
                "path": {"type": "string"},
                "n": {"type": "integer", "default": 10},
                "redact": {"type": "boolean", "default": False},
            },
            "required": ["path"],
        },
    },
    {
        "name": "infer_schema",
        "description": "Infer schema (field types and constraints) for a data file.",
        "parameters": {
            "type": "object",
            "properties": {"path": {"type": "string"}},
            "required": ["path"],
        },
    },
    {
        "name": "analyze_dataset",
        "description": "Analyze dataset structure; optionally include AI-generated documentation.",
        "parameters": {
            "type": "object",
            "properties": {
                "path": {"type": "string"},
                "autodoc": {"type": "boolean", "default": False},
            },
            "required": ["path"],
        },
    },
    {
        "name": "compute_stats",
        "description": "Compute column statistics for a data file.",
        "parameters": {
            "type": "object",
            "properties": {"path": {"type": "string"}},
            "required": ["path"],
        },
    },
    {
        "name": "convert_file",
        "description": "Convert a file to another format. Writes require confirm=true; use dry_run to plan only.",
        "parameters": {
            "type": "object",
            "properties": {
                "input_path": {"type": "string"},
                "output_path": {"type": "string"},
                "confirm": {"type": "boolean", "default": False},
                "dry_run": {"type": "boolean", "default": False},
            },
            "required": ["input_path", "output_path"],
        },
    },
    {
        "name": "generate_documentation",
        "description": "Generate AI-powered dataset documentation (requires iterabledata[ai]).",
        "parameters": {
            "type": "object",
            "properties": {
                "path": {"type": "string"},
                "provider": {"type": "string", "default": "openai"},
                "doc_format": {
                    "type": "string",
                    "default": "json",
                    "enum": ["json", "markdown", "html", "yaml", "text"],
                },
            },
            "required": ["path"],
        },
    },
    {
        "name": "validate_data",
        "description": "Validate rows against field rules; returns stats by default.",
        "parameters": {
            "type": "object",
            "properties": {
                "path": {"type": "string"},
                "rules": {
                    "type": "object",
                    "additionalProperties": {
                        "type": "array",
                        "items": {"type": "string"},
                    },
                    "description": "Map of field name to rule names (e.g. email: [common.email])",
                },
                "mode": {"type": "string", "default": "stats"},
            },
            "required": ["path", "rules"],
        },
    },
    {
        "name": "plan_conversion",
        "description": "Produce a declarative conversion plan between source and target paths (does not convert).",
        "parameters": {
            "type": "object",
            "properties": {
                "source": {"type": "string"},
                "target": {"type": "string"},
                "use_llm": {"type": "boolean", "default": False},
                "provider": {"type": "string", "default": "openai"},
            },
            "required": ["source", "target"],
        },
    },
    {
        "name": "suggest_transform",
        "description": "Suggest a declarative transform spec for a dataset and goal (requires iterabledata[ai]).",
        "parameters": {
            "type": "object",
            "properties": {
                "path": {"type": "string"},
                "goal": {"type": "string"},
                "provider": {"type": "string", "default": "openai"},
            },
            "required": ["path", "goal"],
        },
    },
    {
        "name": "translate_filter",
        "description": "Translate natural language or DSL into a validated filter AST.",
        "parameters": {
            "type": "object",
            "properties": {
                "expression": {"type": "string"},
                "provider": {"type": "string", "description": "Optional LLM provider for NL translation"},
            },
            "required": ["expression"],
        },
    },
]


def to_openai_functions() -> list[dict[str, Any]]:
    """Export tool definitions in OpenAI function-calling format."""
    return [
        {
            "type": "function",
            "function": {
                "name": tool["name"],
                "description": tool["description"],
                "parameters": copy.deepcopy(tool["parameters"]),
            },
        }
        for tool in TOOL_DEFINITIONS
    ]


def to_anthropic_tools() -> list[dict[str, Any]]:
    """Export tool definitions in Anthropic tools format."""
    return [
        {
            "name": tool["name"],
            "description": tool["description"],
            "input_schema": copy.deepcopy(tool["parameters"]),
        }
        for tool in TOOL_DEFINITIONS
    ]


def to_json_schema() -> dict[str, Any]:
    """Export all tool parameter schemas as a JSON Schema document."""
    return {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "title": "IterableData Agent Tools",
        "type": "object",
        "properties": {
            tool["name"]: {
                "type": "object",
                "description": tool["description"],
                **tool["parameters"],
            }
            for tool in TOOL_DEFINITIONS
        },
    }


def call_tool(name: str, arguments: dict[str, Any] | str) -> dict[str, Any]:
    """Invoke a tool by name with JSON arguments (for agent runtimes)."""
    if name not in TOOL_HANDLERS:
        return {"ok": False, "error": f"Unknown tool: {name}", "code": "unknown_tool"}
    if isinstance(arguments, str):
        arguments = json.loads(arguments)
    handler = TOOL_HANDLERS[name]
    # Map schema param names to function kwargs where they differ
    if name == "describe_capabilities":
        arguments = {"format_id": arguments.get("format_id")}
    if name == "generate_documentation" and "doc_format" in arguments:
        arguments = {**arguments, "format": arguments.pop("doc_format")}
    if name == "suggest_transform" and "path" in arguments:
        arguments = {"iterable": arguments.pop("path"), **arguments}
    return handler(**arguments)


def export_schema_snapshot() -> str:
    """Serialize OpenAI function schemas for snapshot testing."""
    return json.dumps(to_openai_functions(), indent=2, sort_keys=True)
