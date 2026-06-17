"""Agent tool wrappers returning JSON-serializable results."""

from __future__ import annotations

from ._core import (
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
from ._result import tool_error, tool_success

__all__ = [
    "analyze_dataset",
    "compute_stats",
    "convert_file",
    "describe_capabilities",
    "detect_format",
    "generate_documentation",
    "infer_schema",
    "plan_conversion",
    "read_sample",
    "suggest_transform",
    "tool_error",
    "tool_success",
    "translate_filter_tool",
    "validate_data",
]
