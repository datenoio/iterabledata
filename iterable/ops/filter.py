"""
Filtering and search operations.

Provides functions for filtering rows using expressions, regex patterns, and queries.
"""

from __future__ import annotations

import ast
import collections.abc
import re
from collections.abc import Iterator

from ..helpers.detect import open_iterable
from ..types import Row

# AST node types permitted in filter expressions. Anything else (attribute
# access, subscripts, comprehensions, lambdas, f-strings, imports, ...) is
# rejected before evaluation, so hostile expressions cannot escape the
# comparison/boolean subset that filter_expr documents.
_ALLOWED_AST_NODES: tuple[type[ast.AST], ...] = (
    ast.Expression,
    ast.BoolOp,
    ast.And,
    ast.Or,
    ast.UnaryOp,
    ast.Not,
    ast.USub,
    ast.UAdd,
    ast.Compare,
    ast.Eq,
    ast.NotEq,
    ast.Lt,
    ast.LtE,
    ast.Gt,
    ast.GtE,
    ast.In,
    ast.NotIn,
    ast.Is,
    ast.IsNot,
    ast.BinOp,
    ast.Add,
    ast.Sub,
    ast.Mult,
    ast.Div,
    ast.Mod,
    ast.Constant,
    ast.Name,
    ast.Load,
    ast.Call,
    ast.Attribute,
    ast.List,
    ast.Tuple,
    ast.Set,
)


def _check_filter_ast(processed_expr: str) -> ast.Expression:
    """Parse a processed filter expression and enforce the AST whitelist.

    Only ``row.get(...)`` calls, string-literal placeholders, constants,
    comparisons, boolean logic, and basic arithmetic are permitted.

    Raises:
        ValueError: If the expression contains disallowed syntax.
    """
    try:
        tree = ast.parse(processed_expr, mode="eval")
    except SyntaxError as e:
        raise ValueError(f"Invalid filter expression syntax: {e}") from e

    for node in ast.walk(tree):
        if not isinstance(node, _ALLOWED_AST_NODES):
            raise ValueError(f"Disallowed syntax in filter expression: {type(node).__name__}")
        if isinstance(node, ast.Attribute):
            if not (node.attr == "get" and isinstance(node.value, ast.Name) and node.value.id == "row"):
                raise ValueError("Attribute access is not allowed in filter expressions")
        elif isinstance(node, ast.Call):
            func = node.func
            if not (isinstance(func, ast.Attribute) and func.attr == "get"):
                raise ValueError("Only field access is allowed in filter expressions (no function calls)")
            if node.keywords:
                raise ValueError("Keyword arguments are not allowed in filter expressions")
        elif isinstance(node, ast.Name):
            if node.id != "row" and not node.id.startswith("__STRING_"):
                raise ValueError(f"Unknown name {node.id!r} in filter expression (use backticks for fields)")
    return tree


def _process_expr(expr: str) -> tuple[str, list[str]]:
    """Translate a filter expression into a Python-evaluable string.

    Protects string literals, rewrites backtick field access into ``row.get``
    calls, and returns the processed expression alongside the extracted string
    literals (in placeholder order).
    """
    string_literals: list[str] = []
    string_pattern = r"(['\"])((?:\\.|(?!\1).)*)\1"

    def replace_string(match):
        content = match.group(2)
        content = content.replace("\\'", "'").replace('\\"', '"')
        idx = len(string_literals)
        string_literals.append(content)
        return f"__STRING_{idx}__"

    processed_expr = re.sub(string_pattern, replace_string, expr)

    def replace_field(match):
        field_name = match.group(1).strip()
        field_name_escaped = field_name.replace("'", "\\'")
        return f"row.get('{field_name_escaped}', None)"

    processed_expr = re.sub(r"`([^`]+)`", replace_field, processed_expr)
    return processed_expr, string_literals


def _validate_expr(expr: str) -> None:
    """Validate that an expression is syntactically usable.

    Raises:
        ValueError: If the expression cannot be compiled (syntax error). This is
            distinct from per-row runtime errors (e.g. comparing ``None``), which
            callers may legitimately skip.
    """
    processed_expr, _ = _process_expr(expr)
    try:
        _check_filter_ast(processed_expr)
    except ValueError as e:
        raise ValueError(f"Invalid filter expression: {expr!r}. Error: {e}") from e


def _safe_eval_expr(expr: str, row: Row) -> bool:
    """
    Safely evaluate a boolean expression against a row.

    Supports:
    - Field access with backticks: `status`, `price`
    - Comparisons: ==, !=, <, >, <=, >=
    - Boolean operators: and, or, not
    - String literals: 'value', "value"
    - Numeric literals: 100, 3.14

    Args:
        expr: Expression string (e.g., "`status` == 'active' and `price` > 100")
        row: Row dictionary to evaluate against

    Returns:
        Boolean result of expression evaluation

    Raises:
        ValueError: If expression is invalid or unsafe
    """
    processed_expr, string_literals = _process_expr(expr)

    # Enforce the AST whitelist before evaluation: only row.get() calls,
    # constants, comparisons, boolean logic, and basic arithmetic survive.
    tree = _check_filter_ast(processed_expr)

    # Build a safe evaluation context
    safe_dict = {
        "row": row,
    }

    # Add string literals back
    for i, literal in enumerate(string_literals):
        safe_dict[f"__STRING_{i}__"] = literal

    try:
        code = compile(tree, "<filter_expr>", "eval")
        # Safe: the AST was validated against a strict whitelist above and
        # builtins are stripped from the evaluation namespace.
        result = eval(code, {"__builtins__": {}}, safe_dict)  # noqa: S307 # nosec B307
        return bool(result)
    except Exception as e:
        raise ValueError(f"Invalid filter expression: {expr}. Error: {e}") from e


def filter_expr(
    iterable: collections.abc.Iterable[Row],
    expression: str,
    engine: str | None = None,
) -> Iterator[Row]:
    """
    Filter rows using a boolean expression.

    Supports field access with backticks, comparisons, and boolean operators.
    Uses DuckDB pushdown for performance when available.

    Args:
        iterable: An iterable of row dictionaries, or a file path/stream
        expression: Boolean expression string (e.g., "`status` == 'active' and `price` > 100")
        engine: Optional engine to use ('duckdb' for optimization)

    Yields:
        Row dictionaries matching the expression

    Example:
        >>> from iterable.ops import filter as f
        >>> # Filter active items with price > 100
        >>> for row in f.filter_expr("data.csv", "`status` == 'active' and `price` > 100"):  # doctest: +SKIP
        ...     print(row)
    """
    # Try DuckDB pushdown for file paths
    if isinstance(iterable, str) and engine == "duckdb":
        try:
            # Convert expression to SQL WHERE clause
            sql_filter = _expr_to_sql(expression)
            with open_iterable(iterable, engine="duckdb", iterableargs={"filter": sql_filter}) as source:
                for row in source:
                    yield row
                return
        except Exception:
            # Fall back to Python evaluation
            pass

    # Validate the expression once up front so a malformed expression raises
    # rather than silently matching nothing.
    _validate_expr(expression)

    # Python fallback: evaluate expression for each row
    if isinstance(iterable, str):
        iterable = open_iterable(iterable)

    for row in iterable:
        try:
            if _safe_eval_expr(expression, row):
                yield row
        except ValueError:
            # Skip rows that cause evaluation errors (e.g. missing fields)
            continue


def _expr_to_sql(expr: str) -> str:
    """
    Convert a simple expression to SQL WHERE clause.

    This is a basic converter - handles simple cases.
    For complex expressions, falls back to Python evaluation.

    Args:
        expr: Expression string with backticks for fields

    Returns:
        SQL WHERE clause string
    """
    # Replace backticks with field names (no quotes needed for simple identifiers)
    sql = re.sub(r"`([^`]+)`", r"\1", expr)
    # Replace Python 'and'/'or' with SQL AND/OR
    sql = re.sub(r"\band\b", "AND", sql, flags=re.IGNORECASE)
    sql = re.sub(r"\bor\b", "OR", sql, flags=re.IGNORECASE)
    sql = re.sub(r"\bnot\b", "NOT", sql, flags=re.IGNORECASE)
    # Note: String literals should already be properly quoted
    return sql


def search(
    iterable: collections.abc.Iterable[Row],
    pattern: str,
    fields: list[str] | None = None,
    ignore_case: bool = False,
) -> Iterator[Row]:
    """
    Filter rows using regular expression pattern matching.

    Searches for the pattern in specified fields (or all fields if None).
    Returns rows where the pattern matches in any of the searched fields.

    Args:
        iterable: An iterable of row dictionaries, or a file path/stream
        pattern: Regular expression pattern to search for
        fields: List of field names to search (None for all string fields)
        ignore_case: Whether to perform case-insensitive search (default: False)

    Yields:
        Row dictionaries where pattern matches

    Example:
        >>> from iterable.ops import filter as f
        >>> # Search for error or warning in any field
        >>> for row in f.search("logs.jsonl", pattern="error|warning"):  # doctest: +SKIP
        ...     print(row)
        >>> # Search in specific fields
        >>> for row in f.search("data.csv", pattern=r"\\d{3}-\\d{3}-\\d{4}", fields=["phone"]):  # doctest: +SKIP
        ...     print(row)
    """
    if isinstance(iterable, str):
        iterable = open_iterable(iterable)

    # Compile regex pattern
    flags = re.IGNORECASE if ignore_case else 0
    try:
        regex = re.compile(pattern, flags)
    except re.error as e:
        raise ValueError(f"Invalid regex pattern: {pattern}. Error: {e}") from e

    for row in iterable:
        # Determine which fields to search
        search_fields = fields if fields is not None else list(row.keys())

        # Check if pattern matches in any field
        for field_name in search_fields:
            value = row.get(field_name)
            if value is not None and isinstance(value, str):
                if regex.search(str(value)):
                    yield row
                    break  # Only yield once per row


def query_mistql(
    iterable: collections.abc.Iterable[Row],
    query: str,
    engine: str | None = None,
) -> Iterator[Row]:
    """
    Filter and select rows using a basic SQL-like query (MistQL-inspired).

    Supports:
    - SELECT field1, field2, ... or SELECT *
    - WHERE condition
    - Basic SQL syntax

    Args:
        iterable: An iterable of row dictionaries, or a file path/stream
        query: SQL-like query string (e.g., "SELECT * WHERE status = 'active'")
        engine: Optional engine to use ('duckdb' for optimization)

    Yields:
        Row dictionaries matching the query

    Example:
        >>> from iterable.ops import filter as f
        >>> # Simple WHERE query
        >>> for row in f.query_mistql("data.csv", "SELECT * WHERE status = 'active'"):  # doctest: +SKIP
        ...     print(row)
        >>> # Select specific fields
        >>> for row in f.query_mistql("data.csv", "SELECT id, name WHERE price > 100"):  # doctest: +SKIP
        ...     print(row)
    """
    # Parse query (basic parser)
    query_upper = query.upper().strip()

    # Extract SELECT clause
    if not query_upper.startswith("SELECT"):
        raise ValueError("Query must start with SELECT")

    # Extract WHERE clause
    where_pos = query_upper.find("WHERE")
    if where_pos == -1:
        # No WHERE clause - return all rows
        select_part = query[6:].strip()  # After "SELECT"
        fields = [f.strip() for f in select_part.split(",")] if select_part != "*" else None

        if isinstance(iterable, str):
            iterable = open_iterable(iterable)

        for row in iterable:
            if fields:
                yield {f: row.get(f) for f in fields}
            else:
                yield row
        return

    # Has WHERE clause
    select_part = query[6:where_pos].strip()  # Between SELECT and WHERE
    where_part = query[where_pos + 5 :].strip()  # After WHERE

    fields = [f.strip() for f in select_part.split(",")] if select_part != "*" else None

    # Try DuckDB for file paths
    if isinstance(iterable, str) and engine == "duckdb":
        try:
            # Use DuckDB's query support
            with open_iterable(iterable, engine="duckdb", iterableargs={"query": query}) as source:
                for row in source:
                    yield row
                return
        except Exception:
            # Fall back to Python evaluation
            pass

    # Python fallback: filter using WHERE expression
    if isinstance(iterable, str):
        iterable = open_iterable(iterable)

    # Convert WHERE clause to expression format
    where_expr = _sql_where_to_expr(where_part)

    for row in filter_expr(iterable, where_expr):
        if fields:
            yield {f: row.get(f) for f in fields}
        else:
            yield row


def _sql_where_to_expr(where_clause: str) -> str:
    """
    Convert SQL WHERE clause to expression format.

    Basic conversion - handles simple cases.
    Converts SQL field references to backtick format.

    Args:
        where_clause: SQL WHERE clause (e.g., "status = 'active'")

    Returns:
        Expression string with backticks (e.g., "`status` == 'active'")
    """
    # Protect string literals so identifiers/operators inside them are untouched.
    literals: list[str] = []

    def _protect(match: re.Match[str]) -> str:
        literals.append(match.group(0))
        return f"__LIT_{len(literals) - 1}__"

    protected = re.sub(r"(['\"])(?:\\.|(?!\1).)*\1", _protect, where_clause)

    # Normalize SQL comparison operators to Python ones, leaving compound
    # operators (==, <=, >=, !=) intact.
    protected = protected.replace("<>", "!=")
    protected = re.sub(r"(?<![<>=!])=(?!=)", " == ", protected)

    # Wrap bare identifiers (field references) in backticks, skipping SQL/Python
    # keywords and the literal placeholders.
    keywords = {"and", "or", "not", "in", "is", "true", "false", "null", "none", "like"}

    def _wrap(match: re.Match[str]) -> str:
        word = match.group(0)
        if word.startswith("__LIT_") or word.lower() in keywords:
            return word
        return f"`{word}`"

    protected = re.sub(r"[A-Za-z_][A-Za-z0-9_]*", _wrap, protected)

    # Restore the protected string literals.
    for i, lit in enumerate(literals):
        protected = protected.replace(f"__LIT_{i}__", lit)

    return protected
