"""Core agent tool implementations."""

from __future__ import annotations

from typing import Any

from ..ai import doc as ai_doc
from ..ai.context import redact_for_llm, sample_for_llm
from ..ai.filter import translate_filter as ai_translate_filter
from ..ai.plan import plan_conversion as ai_plan_conversion
from ..ai.suggest import suggest_transform as ai_suggest_transform
from ..catalog import describe_format
from ..convert.core import convert
from ..helpers.detect import detect_file_type
from ..ops import inspect, schema, stats
from ..validate import core as validate_core
from ._result import tool_error, tool_success


def _class_id(cls: type | None) -> str | None:
    if cls is None:
        return None
    id_fn = getattr(cls, "id", None)
    if callable(id_fn):
        try:
            return str(id_fn())
        except Exception:
            return cls.__name__
    return cls.__name__


def _json_safe(value: Any) -> Any:
    if value is None or isinstance(value, (bool, int, float, str)):
        return value
    if isinstance(value, dict):
        return {str(k): _json_safe(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_safe(v) for v in value]
    if isinstance(value, type):
        return _class_id(value)
    return str(value)


def detect_format(path: str) -> dict[str, Any]:
    """Detect format and compression for a file path."""
    try:
        result = detect_file_type(path)
        data = {
            "filename": result.get("filename", path),
            "success": result.get("success", False),
            "format": _class_id(result.get("datatype")),
            "compression": _class_id(result.get("codec")),
            "confidence": result.get("confidence"),
            "detection_method": result.get("detection_method"),
        }
        return tool_success(data)
    except Exception as exc:
        return tool_error(str(exc), code="detect_failed")


def describe_capabilities(format_id: str) -> dict[str, Any]:
    """Describe format metadata and capabilities."""
    try:
        return tool_success(describe_format(format_id, include_capabilities=True))
    except ValueError as exc:
        return tool_error(str(exc), code="unknown_format")
    except Exception as exc:
        return tool_error(str(exc), code="describe_failed")


def read_sample(path: str, n: int = 10, redact: bool = False) -> dict[str, Any]:
    """Read a bounded sample of rows from a file."""
    try:
        rows = sample_for_llm(path, max_rows=n, strategy="head")
        if redact:
            rows = redact_for_llm(rows)
        return tool_success({"rows": _json_safe(rows), "count": len(rows)})
    except Exception as exc:
        return tool_error(str(exc), code="read_failed")


def infer_schema(path: str, **kwargs: Any) -> dict[str, Any]:
    """Infer schema for a dataset file."""
    try:
        schema_info = schema.infer(path, **kwargs)
        return tool_success(_json_safe(schema_info))
    except Exception as exc:
        return tool_error(str(exc), code="schema_failed")


def analyze_dataset(path: str, autodoc: bool = False, **kwargs: Any) -> dict[str, Any]:
    """Analyze dataset structure; optional AI documentation."""
    try:
        analysis = inspect.analyze(path, autodoc=autodoc, **kwargs)
        return tool_success(_json_safe(analysis))
    except ImportError as exc:
        return tool_error(str(exc), code="missing_dependencies")
    except Exception as exc:
        return tool_error(str(exc), code="analyze_failed")


def compute_stats(path: str, **kwargs: Any) -> dict[str, Any]:
    """Compute statistics for a dataset file."""
    try:
        stats_info = stats.compute(path, **kwargs)
        return tool_success(_json_safe(stats_info))
    except Exception as exc:
        return tool_error(str(exc), code="stats_failed")


def convert_file(
    input_path: str,
    output_path: str,
    *,
    confirm: bool = False,
    dry_run: bool = False,
    **kwargs: Any,
) -> dict[str, Any]:
    """Convert between formats; writes require confirm=True."""
    if dry_run:
        detection = detect_format(input_path)
        if not detection.get("ok"):
            return detection
        return tool_success(
            {
                "dry_run": True,
                "input_path": input_path,
                "output_path": output_path,
                "source_format": detection["data"].get("format"),
                "message": "Conversion not executed (dry_run=True).",
            }
        )
    if not confirm:
        return tool_error(
            "File conversion requires confirm=True to prevent accidental writes.",
            code="confirmation_required",
        )
    try:
        result = convert(input_path, output_path, **kwargs)
        return tool_success(_json_safe(result))
    except Exception as exc:
        return tool_error(str(exc), code="convert_failed")


def generate_documentation(path: str, **kwargs: Any) -> dict[str, Any]:
    """Generate AI documentation for a dataset."""
    try:
        output_format = kwargs.pop("format", kwargs.pop("doc_format", "json"))
        result = ai_doc.generate(path, format=output_format, **kwargs)
        if output_format == "json" and isinstance(result, dict):
            return tool_success(_json_safe(result))
        return tool_success({"documentation": result, "format": output_format})
    except ImportError as exc:
        return tool_error(str(exc), code="missing_dependencies")
    except Exception as exc:
        return tool_error(str(exc), code="doc_failed")


def validate_data(
    path: str,
    rules: dict[str, list[str]],
    *,
    mode: str = "stats",
    max_errors: int | None = None,
) -> dict[str, Any]:
    """Validate dataset rows against field rules."""
    try:
        result = validate_core.iterable(path, rules, mode=mode, max_errors=max_errors)
        if mode == "stats":
            return tool_success(_json_safe(result))
        errors = []
        for row, row_errors in result:
            if row_errors:
                errors.append({"row": _json_safe(row), "errors": row_errors})
            if max_errors is not None and len(errors) >= max_errors:
                break
        return tool_success({"invalid_rows": errors, "count": len(errors)})
    except Exception as exc:
        return tool_error(str(exc), code="validate_failed")


def plan_conversion(source: str, target: str, **kwargs: Any) -> dict[str, Any]:
    """Produce a declarative conversion plan (does not convert)."""
    try:
        plan = ai_plan_conversion(source, target, **kwargs)
        return tool_success(_json_safe(plan))
    except Exception as exc:
        return tool_error(str(exc), code="plan_failed")


def suggest_transform(path: str, goal: str, **kwargs: Any) -> dict[str, Any]:
    """Suggest a declarative transform spec for a dataset and goal."""
    try:
        spec = ai_suggest_transform(path, goal, **kwargs)
        return tool_success(_json_safe(spec))
    except Exception as exc:
        return tool_error(str(exc), code="suggest_failed")


def translate_filter_tool(
    expression: str,
    *,
    schema: dict[str, Any] | None = None,
    **kwargs: Any,
) -> dict[str, Any]:
    """Translate natural language or DSL into a validated filter AST."""
    try:
        result = ai_translate_filter(expression, schema=schema, **kwargs)
        return tool_success(_json_safe(result))
    except Exception as exc:
        return tool_error(str(exc), code="filter_failed")
