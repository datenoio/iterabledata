"""
Schema generation operations.

Provides functions for inferring schemas from data and converting
to various schema formats (JSON Schema, Avro, Parquet, etc.).
"""

from __future__ import annotations

import collections.abc
import json
from collections.abc import Mapping
from typing import Any

from ..helpers.detect import open_iterable
from ..helpers.nested import (
    DEFAULT_MAX_NESTED_DEPTH,
    nested_field_value,
    unfold_nested_schema_fields,
)
from ..helpers.schema import schema_from_list_of_dicts
from ..helpers.utils import hashable_repr
from ..types import Row


def infer(
    iterable: collections.abc.Iterable[Row],
    detect_dates: bool = False,
    detect_constraints: bool = False,
    sample_size: int = 10000,
    *,
    flatten_nested: bool = False,
    max_nested_depth: int = DEFAULT_MAX_NESTED_DEPTH,
    keep_nested_parents: bool = True,
) -> dict[str, Any]:
    """
    Infer schema from an iterable dataset.

    Detects field names, types, nullability, and optionally constraints.

    Args:
        iterable: An iterable of row dictionaries, or a file path/stream
        detect_dates: Whether to detect date and datetime fields (default: False)
        detect_constraints: Whether to detect constraints (min/max, length, etc.) (default: False)
        sample_size: Number of rows to sample for inference (default: 10000)
        flatten_nested: When True, unfold dict / array-of-dict nests into dotted
            paths such as ``capital_city.lat`` (default: False)
        max_nested_depth: Maximum nest depth to unfold when ``flatten_nested``
        keep_nested_parents: Keep parent ``dict``/``array`` fields alongside children

    Returns:
        Dictionary containing schema information:
        - fields: Dictionary mapping field names to metadata
        - constraints: Dictionary of detected constraints (if detect_constraints=True)

    Example:
        >>> from iterable.ops import schema
        >>> sch = schema.infer("data.csv", detect_dates=True)  # doctest: +SKIP
        >>> print(sch["fields"]["price"]["type"])  # doctest: +SKIP
    """
    del detect_dates  # reserved for future date-shape detection
    if isinstance(iterable, str):
        iterable = open_iterable(iterable)

    # Sample rows for inference
    sample_rows: list[Row] = []
    for i, row in enumerate(iterable):
        if i >= sample_size:
            break
        sample_rows.append(row)

    if not sample_rows:
        return {"fields": {}, "constraints": {}}

    # Use existing schema inference
    inferred_schema = schema_from_list_of_dicts(sample_rows)
    if flatten_nested:
        field_entries = unfold_nested_schema_fields(
            inferred_schema,
            max_depth=max_nested_depth,
            keep_parents=keep_nested_parents,
        )
    else:
        field_entries = []
        for name, info in inferred_schema.items():
            if not isinstance(info, dict):
                continue
            meta: dict[str, Any] = {"type": info.get("type", "string")}
            if "subtype" in info:
                meta["subtype"] = info["subtype"]
            field_entries.append((str(name), meta))

    # Convert to our format
    fields: dict[str, dict[str, Any]] = {}
    constraints: dict[str, dict[str, Any]] = {}

    total_rows = len(sample_rows)

    for field_name, field_info in field_entries:
        fields[field_name] = {
            "type": field_info.get("type", "string"),
            "nullable": True,  # Determined from data below
            "sample_values": [],
        }
        if "subtype" in field_info:
            fields[field_name]["subtype"] = field_info["subtype"]

        # Determine nullability from the sampled data. A field is nullable if any
        # sampled row has a None value for it or omits the field entirely.
        if flatten_nested or "." in field_name:
            present_values = [nested_field_value(row, field_name) for row in sample_rows]
            null_count = sum(1 for value in present_values if value is None or value == [])
            fields[field_name]["nullable"] = null_count > 0
            values = []
            for value in present_values:
                if isinstance(value, list) and (not value or not isinstance(value[0], Mapping)):
                    values.extend(value)
                elif value is not None and value != []:
                    values.append(value)
            sample_values = present_values[:5]
        else:
            present_values = [row.get(field_name) for row in sample_rows if field_name in row]
            null_count = sum(1 for v in present_values if v is None)
            missing_count = total_rows - len(present_values)
            fields[field_name]["nullable"] = (null_count + missing_count) > 0
            values = [row.get(field_name) for row in sample_rows if field_name in row]
            sample_values = [row.get(field_name) for row in sample_rows[:5] if field_name in row]

        # Detect constraints if requested
        if detect_constraints:
            field_constraints: dict[str, Any] = {}
            # Collect values for constraint detection
            if values:
                non_null_values = [v for v in values if v is not None]

                if non_null_values:
                    # Numeric constraints
                    if field_info.get("type") in ["integer", "float"]:
                        numeric_values = [v for v in non_null_values if isinstance(v, (int, float))]
                        if numeric_values:
                            field_constraints["min"] = min(numeric_values)
                            field_constraints["max"] = max(numeric_values)

                    # String length constraints
                    if field_info.get("type") == "string":
                        string_values = [v for v in non_null_values if isinstance(v, str)]
                        if string_values:
                            lengths = [len(v) for v in string_values]
                            field_constraints["min_length"] = min(lengths)
                            field_constraints["max_length"] = max(lengths)

                    # Enum-like detection (if limited distinct values)
                    distinct_reprs: set[str] = set()
                    distinct_values: list[Any] = []
                    for v in non_null_values:
                        r = hashable_repr(v)
                        if r not in distinct_reprs:
                            distinct_reprs.add(r)
                            distinct_values.append(v)
                    if len(distinct_values) <= 10 and len(non_null_values) > 5:
                        # Might be an enum
                        field_constraints["possible_values"] = distinct_values

            if field_constraints:
                constraints[field_name] = field_constraints

        # Add sample values
        fields[field_name]["sample_values"] = sample_values[:5]

    result: dict[str, Any] = {"fields": fields}
    if detect_constraints:
        result["constraints"] = constraints

    return result


def to_jsonschema(schema: dict[str, Any]) -> dict[str, Any]:
    """
    Convert inferred schema to JSON Schema format.

    Args:
        schema: Schema dictionary from infer()

    Returns:
        JSON Schema document

    Example:
        >>> from iterable.ops import schema
        >>> sch = schema.infer("data.csv")  # doctest: +SKIP
        >>> json_schema = schema.to_jsonschema(sch)  # doctest: +SKIP
    """
    json_schema: dict[str, Any] = {
        "$schema": "http://json-schema.org/draft-07/schema#",
        "type": "object",
        "properties": {},
        "required": [],
    }

    fields = schema.get("fields", {})
    for field_name, field_info in fields.items():
        field_type = field_info.get("type", "string")

        # Map types to JSON Schema types
        type_mapping = {
            "string": "string",
            "integer": "integer",
            "float": "number",
            "boolean": "boolean",
            "datetime": "string",  # JSON Schema uses string for dates
            "array": "array",
            "dict": "object",
        }

        json_type = type_mapping.get(field_type, "string")

        prop: dict[str, Any] = {"type": json_type}

        # Add format for datetime
        if field_type == "datetime":
            prop["format"] = "date-time"

        # Add constraints
        constraints = schema.get("constraints", {}).get(field_name, {})
        if "min" in constraints:
            prop["minimum"] = constraints["min"]
        if "max" in constraints:
            prop["maximum"] = constraints["max"]
        if "min_length" in constraints:
            prop["minLength"] = constraints["min_length"]
        if "max_length" in constraints:
            prop["maxLength"] = constraints["max_length"]
        if "possible_values" in constraints:
            prop["enum"] = constraints["possible_values"]

        json_schema["properties"][field_name] = prop

        # Add to required if not nullable
        if not field_info.get("nullable", True):
            json_schema["required"].append(field_name)

    return json_schema


def to_yaml(schema: dict[str, Any]) -> str:
    """
    Convert inferred schema to YAML format.

    Args:
        schema: Schema dictionary from infer()

    Returns:
        YAML string

    Example:
        >>> from iterable.ops import schema
        >>> sch = schema.infer("data.csv")  # doctest: +SKIP
        >>> yaml_str = schema.to_yaml(sch)  # doctest: +SKIP
    """
    try:
        import yaml

        return yaml.dump(schema, default_flow_style=False, allow_unicode=True)
    except ImportError:
        # Fallback to JSON-like YAML if pyyaml not available
        return json.dumps(schema, indent=2)


def to_cerberus(schema: dict[str, Any]) -> dict[str, Any]:
    """
    Convert inferred schema to Cerberus validation schema format.

    Args:
        schema: Schema dictionary from infer()

    Returns:
        Cerberus-compatible schema dictionary

    Example:
        >>> from iterable.ops import schema
        >>> sch = schema.infer("data.csv")  # doctest: +SKIP
        >>> cerberus_schema = schema.to_cerberus(sch)  # doctest: +SKIP
    """
    cerberus_schema: dict[str, Any] = {}

    fields = schema.get("fields", {})
    for field_name, field_info in fields.items():
        field_type = field_info.get("type", "string")

        # Map types to Cerberus types
        type_mapping = {
            "string": "string",
            "integer": "integer",
            "float": "number",
            "boolean": "boolean",
            "datetime": "datetime",
            "array": "list",
            "dict": "dict",
        }

        cerberus_type = type_mapping.get(field_type, "string")

        nullable = field_info.get("nullable", True)
        rule: dict[str, Any] = {"type": cerberus_type, "nullable": nullable, "required": not nullable}

        # Add constraints
        constraints = schema.get("constraints", {}).get(field_name, {})
        if "min" in constraints:
            rule["min"] = constraints["min"]
        if "max" in constraints:
            rule["max"] = constraints["max"]
        if "min_length" in constraints:
            rule["minlength"] = constraints["min_length"]
        if "max_length" in constraints:
            rule["maxlength"] = constraints["max_length"]
        if "possible_values" in constraints:
            rule["allowed"] = constraints["possible_values"]

        cerberus_schema[field_name] = rule

    return cerberus_schema


def to_avro(schema: dict[str, Any], namespace: str = "iterabledata") -> dict[str, Any]:
    """
    Convert inferred schema to Avro schema format.

    Args:
        schema: Schema dictionary from infer()
        namespace: Avro namespace (default: "iterabledata")

    Returns:
        Avro schema JSON

    Example:
        >>> from iterable.ops import schema
        >>> sch = schema.infer("data.csv")  # doctest: +SKIP
        >>> avro_schema = schema.to_avro(sch)  # doctest: +SKIP
    """
    fields_list: list[dict[str, Any]] = []

    schema_fields = schema.get("fields", {})
    for field_name, field_info in schema_fields.items():
        field_type = field_info.get("type", "string")

        # Map types to Avro types
        type_mapping = {
            "string": "string",
            "integer": "long",
            "float": "double",
            "boolean": "boolean",
            "datetime": "string",  # Avro uses string for dates
            "array": {"type": "array", "items": "string"},
            "dict": "map",
        }

        avro_type = type_mapping.get(field_type, "string")

        # Handle nullable fields (union with null)
        if field_info.get("nullable", True):
            avro_type = ["null", avro_type]

        field_def: dict[str, Any] = {
            "name": field_name,
            "type": avro_type,
        }

        # Add default for nullable fields
        if field_info.get("nullable", True):
            field_def["default"] = None

        fields_list.append(field_def)

    avro_schema: dict[str, Any] = {
        "type": "record",
        "name": "Record",
        "namespace": namespace,
        "fields": fields_list,
    }

    return avro_schema


def to_parquet_metadata(schema: dict[str, Any]) -> dict[str, Any]:
    """
    Convert inferred schema to Parquet metadata format.

    Args:
        schema: Schema dictionary from infer()

    Returns:
        Parquet-compatible schema metadata

    Example:
        >>> from iterable.ops import schema
        >>> sch = schema.infer("data.csv")  # doctest: +SKIP
        >>> parquet_meta = schema.to_parquet_metadata(sch)  # doctest: +SKIP
    """
    # This is a simplified implementation
    # Full Parquet schema would require pyarrow
    fields_meta: list[dict[str, Any]] = []

    schema_fields = schema.get("fields", {})
    for field_name, field_info in schema_fields.items():
        field_type = field_info.get("type", "string")

        # Map types to Parquet types (simplified)
        type_mapping = {
            "string": "BYTE_ARRAY",
            "integer": "INT64",
            "float": "DOUBLE",
            "boolean": "BOOLEAN",
            "datetime": "INT96",  # Parquet uses INT96 for timestamps
            "array": "BYTE_ARRAY",
            "dict": "BYTE_ARRAY",
        }

        parquet_type = type_mapping.get(field_type, "BYTE_ARRAY")

        field_meta: dict[str, Any] = {
            "name": field_name,
            "type": parquet_type,
            "nullable": field_info.get("nullable", True),
        }

        fields_meta.append(field_meta)

    return {"fields": fields_meta}


def validate(
    iterable: collections.abc.Iterable[Row],
    schema: dict[str, Any],
    strict: bool = False,
) -> dict[str, Any]:
    """
    Validate data against an inferred or provided schema.

    Args:
        iterable: An iterable of row dictionaries, or a file path/stream
        schema: Schema dictionary from infer() or manually created
        strict: If True, enforce strict type checking and flag extra/missing fields

    Returns:
        Dictionary containing:
        - valid_rows: List of valid rows
        - invalid_rows: List of (row, errors) tuples
        - stats: Validation statistics

    Example:
        >>> from iterable.ops import schema
        >>> sch = schema.infer("data.csv")  # doctest: +SKIP
        >>> result = schema.validate("data.csv", sch)  # doctest: +SKIP
        >>> print(f"Valid: {len(result['valid_rows'])}, Invalid: {len(result['invalid_rows'])}")  # doctest: +SKIP
    """
    if isinstance(iterable, str):
        iterable = open_iterable(iterable)

    valid_rows: list[Row] = []
    invalid_rows: list[tuple[Row, list[str]]] = []
    stats = {"total": 0, "valid": 0, "invalid": 0, "errors_by_field": {}}

    schema_fields = schema.get("fields", {})

    for row in iterable:
        stats["total"] += 1
        errors: list[str] = []

        # Check each field in schema
        for field_name, field_info in schema_fields.items():
            value = row.get(field_name)

            # Check type
            expected_type = field_info.get("type", "string")
            if value is not None:
                type_mapping = {
                    "string": str,
                    "integer": int,
                    "float": (int, float),
                    "boolean": bool,
                }
                expected_python_type = type_mapping.get(expected_type)
                if expected_python_type and not isinstance(value, expected_python_type):
                    errors.append(f"{field_name}: expected {expected_type}, got {type(value).__name__}")

            # Check nullable
            if value is None and not field_info.get("nullable", True):
                errors.append(f"{field_name}: field is required but value is None")

        # Check for extra fields in strict mode
        if strict:
            schema_field_names = set(schema_fields.keys())
            row_field_names = set(row.keys())
            extra_fields = row_field_names - schema_field_names
            if extra_fields:
                errors.append(f"Extra fields not in schema: {', '.join(extra_fields)}")

        if errors:
            stats["invalid"] += 1
            invalid_rows.append((row, errors))
            for error in errors:
                field_name = error.split(":")[0]
                stats["errors_by_field"][field_name] = stats["errors_by_field"].get(field_name, 0) + 1
        else:
            stats["valid"] += 1
            valid_rows.append(row)

    return {
        "valid_rows": valid_rows,
        "invalid_rows": invalid_rows,
        "stats": stats,
    }
