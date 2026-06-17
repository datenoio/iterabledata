"""AI-assisted natural language and DSL filter translation."""

from __future__ import annotations

import json
import re
from typing import Any

from .prompts import load_prompt
from .providers import get_provider

_FORBIDDEN_SQL = re.compile(
    r"(--|\bDROP\b|\bDELETE\b|\bINSERT\b|\bUPDATE\b|\bUNION\b|\bEXEC\b|\bSELECT\s+\*)",
    re.IGNORECASE,
)

_COMPARISON_OPS = {
    "==": "eq",
    "=": "eq",
    "!=": "ne",
    "<>": "ne",
    "<": "lt",
    "<=": "le",
    ">": "gt",
    ">=": "ge",
}

_LOGICAL_SPLIT = re.compile(r"\s+(and|or)\s+", re.IGNORECASE)


def _validate_filter_input(expression: str) -> None:
    if not expression or not expression.strip():
        raise ValueError("Filter expression cannot be empty")
    if _FORBIDDEN_SQL.search(expression):
        raise ValueError("Filter expression contains disallowed SQL keywords or patterns")
    if ";" in expression:
        raise ValueError("Multi-statement filter expressions are not allowed")


def _parse_value(raw: str) -> Any:
    raw = raw.strip()
    if (raw.startswith("'") and raw.endswith("'")) or (raw.startswith('"') and raw.endswith('"')):
        return raw[1:-1]
    if raw.lower() in ("true", "false"):
        return raw.lower() == "true"
    if raw.lower() == "null":
        return None
    try:
        if "." in raw:
            return float(raw)
        return int(raw)
    except ValueError:
        return raw


def _parse_atom(expr: str) -> dict[str, Any]:
    expr = expr.strip()
    in_match = re.match(
        r"^`?([A-Za-z_][A-Za-z0-9_]*)`?\s+in\s+\((.+)\)\s*$",
        expr,
        re.IGNORECASE,
    )
    if in_match:
        field = in_match.group(1)
        values = [_parse_value(v.strip()) for v in in_match.group(2).split(",") if v.strip()]
        return {"op": "in", "field": field, "values": values}

    for op_token, ast_op in sorted(_COMPARISON_OPS.items(), key=lambda x: -len(x[0])):
        pattern = rf"^`?([A-Za-z_][A-Za-z0-9_]*)`?\s+{re.escape(op_token)}\s+(.+)$"
        match = re.match(pattern, expr)
        if match:
            return {"op": ast_op, "field": match.group(1), "value": _parse_value(match.group(2))}

    raise ValueError(f"Unable to parse filter atom: {expr!r}")


def _parse_expression(expression: str) -> dict[str, Any]:
    expression = expression.strip()
    if expression.startswith("(") and expression.endswith(")"):
        expression = expression[1:-1].strip()

    parts = _LOGICAL_SPLIT.split(expression)
    if len(parts) == 1:
        return _parse_atom(expression)

    nodes: list[Any] = []
    for i, part in enumerate(parts):
        if i % 2 == 0:
            nodes.append(_parse_expression(part))
        else:
            nodes.append(part.lower())

    result = nodes[0]
    idx = 1
    while idx < len(nodes):
        logical_op = nodes[idx]
        right = nodes[idx + 1]
        result = {"op": logical_op, "left": result, "right": right}
        idx += 2
    return result


def ast_to_filter_expr(node: dict[str, Any]) -> str:
    """Convert a filter AST node to an ``ops.filter`` expression string."""
    op = node.get("op")
    if op in ("eq", "ne", "lt", "le", "gt", "ge"):
        py_ops = {"eq": "==", "ne": "!=", "lt": "<", "le": "<=", "gt": ">", "ge": ">="}
        value = node["value"]
        if isinstance(value, str):
            value_repr = json.dumps(value)
        else:
            value_repr = repr(value)
        return f"`{node['field']}` {py_ops[op]} {value_repr}"
    if op == "in":
        values = ", ".join(json.dumps(v) if isinstance(v, str) else repr(v) for v in node["values"])
        return f"`{node['field']}` in ({values})"
    if op == "regex":
        flags = ", ignore_case=True" if node.get("ignore_case") else ""
        return f"search(`{node['field']}`, {json.dumps(node['pattern'])}{flags})"
    if op == "not":
        return f"not ({ast_to_filter_expr(node['child'])})"
    if op in ("and", "or"):
        left = ast_to_filter_expr(node["left"])
        right = ast_to_filter_expr(node["right"])
        return f"({left}) {op} ({right})"
    raise ValueError(f"Unknown filter AST op: {op!r}")


def validate_filter_ast(node: dict[str, Any]) -> None:
    """Validate a filter AST node; raises ValueError on unknown ops."""
    op = node.get("op")
    allowed = {"eq", "ne", "lt", "le", "gt", "ge", "and", "or", "not", "in", "regex"}
    if op not in allowed:
        raise ValueError(f"Unknown filter AST op: {op!r}")
    if op in ("eq", "ne", "lt", "le", "gt", "ge", "in", "regex"):
        if "field" not in node:
            raise ValueError(f"Filter AST node {op!r} requires 'field'")
    if op == "in" and not isinstance(node.get("values"), list):
        raise ValueError("Filter 'in' node requires 'values' list")
    if op == "not":
        validate_filter_ast(node["child"])
    if op in ("and", "or"):
        validate_filter_ast(node["left"])
        validate_filter_ast(node["right"])


def apply_ast(iterable: Any, ast: dict[str, Any]) -> Any:
    """Apply a filter AST using ``ops.filter.filter_expr``."""
    from ..ops.filter import filter_expr

    validate_filter_ast(ast)
    expression = ast_to_filter_expr(ast)
    return filter_expr(iterable, expression)


def translate_filter(
    expression: str,
    schema: dict[str, Any] | None = None,
    *,
    provider: str | None = None,
    model: str | None = None,
    api_key: str | None = None,
    base_url: str | None = None,
    **kwargs: Any,
) -> dict[str, Any]:
    """
      Translate natural language or simple DSL into a validated filter AST.

    Does not apply the filter; call ``apply_ast`` or ``ops.filter.filter_expr`` explicitly.
    """
    _validate_filter_input(expression)
    fields: list[str] = []
    if schema and isinstance(schema.get("fields"), dict):
        fields = list(schema["fields"].keys())

    try:
        ast = _parse_expression(expression)
        validate_filter_ast(ast)
        return {
            "ast": ast,
            "expression": ast_to_filter_expr(ast),
            "source": "dsl",
            "explanation": "Parsed simple filter DSL into AST.",
        }
    except ValueError:
        if provider is None:
            raise ValueError(
                "Could not parse filter as DSL. Provide provider=... for natural language translation."
            ) from None

    prompt = load_prompt(
        "translate_filter",
        expression=expression,
        fields=json.dumps(fields),
    )
    llm = get_provider(provider, api_key=api_key, base_url=base_url)
    raw = llm.generate(prompt=prompt, model=model, temperature=0.1, **kwargs)
    try:
        ast = json.loads(raw)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", raw, re.DOTALL)
        if not match:
            raise ValueError("LLM did not return valid filter AST JSON") from None
        ast = json.loads(match.group(0))
    validate_filter_ast(ast)
    return {
        "ast": ast,
        "expression": ast_to_filter_expr(ast),
        "source": "llm",
        "explanation": "Translated natural language filter via LLM.",
    }
