"""Helpers to unfold nested dict/array-of-dict fields into dotted paths."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any

from .utils import get_dict_value_deep

DEFAULT_MAX_NESTED_DEPTH = 5


def unfold_nested_schema_fields(
    deep_schema: Mapping[str, Any],
    *,
    max_depth: int = DEFAULT_MAX_NESTED_DEPTH,
    keep_parents: bool = True,
    prefix: str = "",
    depth: int = 0,
) -> list[tuple[str, dict[str, Any]]]:
    """Expand a deep schema into ordered ``(path, type_meta)`` entries.

    Dict fields (and arrays of dicts) emit the parent path when ``keep_parents``
    is true, then recurse into child keys as ``parent.child``. Arrays of scalars
    stay a single field. Array-of-object child paths collect values across all
    elements (see :func:`project_row_nested`).
    """

    fields: list[tuple[str, dict[str, Any]]] = []
    for name, raw_info in deep_schema.items():
        if not isinstance(raw_info, Mapping):
            continue
        path = f"{prefix}.{name}" if prefix else str(name)
        field_type = str(raw_info.get("type") or "string")
        meta: dict[str, Any] = {"type": field_type}
        subtype = raw_info.get("subtype")
        if subtype is not None:
            meta["subtype"] = subtype
        nested = raw_info.get("schema")
        nested_schema = nested if isinstance(nested, Mapping) else None
        expand_children = (
            depth < max_depth and nested_schema is not None and (field_type == "dict" or field_type == "array")
        )
        if expand_children:
            if keep_parents:
                fields.append((path, meta))
            child_entries = unfold_nested_schema_fields(
                nested_schema,
                max_depth=max_depth,
                keep_parents=keep_parents,
                prefix=path,
                depth=depth + 1,
            )
            if field_type == "array":
                for child_path, child_meta in child_entries:
                    annotated = dict(child_meta)
                    annotated.setdefault("nested_from", "array")
                    fields.append((child_path, annotated))
            else:
                fields.extend(child_entries)
        else:
            fields.append((path, meta))
    return fields


def _is_array_of_mappings(value: Any) -> bool:
    return isinstance(value, list) and bool(value) and isinstance(value[0], Mapping)


def project_row_nested(
    row: Mapping[str, Any],
    *,
    max_depth: int = DEFAULT_MAX_NESTED_DEPTH,
    keep_parents: bool = True,
) -> dict[str, Any]:
    """Return a row with nested dict leaves projected onto dotted keys.

    Top-level keys are preserved when ``keep_parents`` is true. Arrays of
    objects project each element: scalar child paths become lists of values
    collected across the array (``languages.code -> ["rus", "tgk"]``).
    """

    projected: dict[str, Any] = dict(row) if keep_parents else {}

    def walk_mapping(obj: Mapping[str, Any], prefix: str, depth: int) -> None:
        if depth > max_depth:
            return
        for key, value in obj.items():
            path = f"{prefix}.{key}"
            if isinstance(value, Mapping):
                if keep_parents:
                    projected[path] = value
                walk_mapping(value, path, depth + 1)
            elif _is_array_of_mappings(value):
                if keep_parents:
                    projected[path] = value
                walk_array(value, path, depth + 1)
            else:
                projected[path] = value

    def walk_array(items: Sequence[Any], prefix: str, depth: int) -> None:
        if depth > max_depth:
            return
        keys: list[str] = []
        seen: set[str] = set()
        mappings = [item for item in items if isinstance(item, Mapping)]
        for item in mappings:
            for key in item:
                key_s = str(key)
                if key_s not in seen:
                    seen.add(key_s)
                    keys.append(key_s)
        for key in keys:
            path = f"{prefix}.{key}"
            scalar_values: list[Any] = []
            nested_mappings: list[Mapping[str, Any]] = []
            nested_arrays: list[Any] = []
            saw_null = False
            for item in mappings:
                if key not in item:
                    continue
                value = item[key]
                if value is None:
                    saw_null = True
                    continue
                if isinstance(value, Mapping):
                    nested_mappings.append(value)
                elif _is_array_of_mappings(value):
                    nested_arrays.extend(value)
                else:
                    scalar_values.append(value)
            if nested_mappings:
                if keep_parents:
                    projected[path] = nested_mappings
                walk_array(nested_mappings, path, depth + 1)
            elif nested_arrays:
                if keep_parents:
                    projected[path] = nested_arrays
                walk_array(nested_arrays, path, depth + 1)
            elif scalar_values or saw_null:
                projected[path] = scalar_values

    for key, value in row.items():
        if isinstance(value, Mapping):
            walk_mapping(value, str(key), 1)
        elif _is_array_of_mappings(value):
            walk_array(value, str(key), 1)
        elif not keep_parents:
            projected[str(key)] = value
    return projected


def nested_field_value(row: Mapping[str, Any], path: str) -> Any:
    """Read a top-level or dotted path from ``row``.

    Paths under arrays of objects return the list of values across elements.
    Dict paths return a single scalar/object. Missing paths return ``None``.
    """

    if "." not in path:
        return row.get(path)
    projected = project_row_nested(row, keep_parents=True)
    if path in projected:
        return projected[path]
    return get_dict_value_deep(row, path)


__all__ = [
    "DEFAULT_MAX_NESTED_DEPTH",
    "nested_field_value",
    "project_row_nested",
    "unfold_nested_schema_fields",
]
