"""Validation hooks infrastructure for automatic data validation."""

import logging
import warnings
from typing import Any, Protocol, runtime_checkable

from ..types import Row

logger = logging.getLogger(__name__)


@runtime_checkable
class ValidationHook(Protocol):
    """
    Protocol for validation hooks.

    Validation hooks are callable objects that take a row and return a row.
    They can raise exceptions to indicate validation failure, or return
    a (possibly transformed) row to indicate success.
    """

    def __call__(self, row: Row) -> Row:
        """
        Validate and return row, or raise exception.

        Args:
            row: Row dictionary to validate

        Returns:
            Validated row (may be transformed)

        Raises:
            Exception: If validation fails
        """
        ...


def apply_validation_hooks(
    row: Row,
    hooks: list[ValidationHook],
    on_error: str = "raise",
) -> Row | None:
    """
    Apply validation hooks to a row with error handling.

    Args:
        row: Row to validate
        hooks: List of validation hooks to apply
        on_error: Error handling policy - 'raise', 'skip', 'log', or 'warn'

    Returns:
        Validated row, or None if skipped

    Raises:
        Exception: If on_error='raise' and validation fails
    """
    if not hooks:
        return row

    for hook in hooks:
        try:
            row = hook(row)
        except Exception as e:
            if on_error == "raise":
                raise
            elif on_error == "skip":
                return None  # Signal to skip this row
            elif on_error == "log":
                logger.warning(f"Validation failed: {e}", exc_info=False)
                # Continue with next hook or return row as-is
            elif on_error == "warn":
                warnings.warn(f"Validation failed: {e}", UserWarning, stacklevel=2)
                # Continue with next hook or return row as-is
            else:
                # Unknown policy, default to raise
                raise ValueError(f"Unknown validation error policy: {on_error}") from e

    return row


def schema_validator(schema: dict[str, Any]) -> ValidationHook:
    """
    Create a validation hook from a schema.

    Args:
        schema: Schema dictionary from schema.infer() or manually created

    Returns:
        Validation hook function

    Example:
        >>> from iterable.ops import schema
        >>> from iterable.helpers.validation import schema_validator
        >>>
        >>> sch = schema.infer('data.csv')  # doctest: +SKIP
        >>> hook = schema_validator(sch)  # doctest: +SKIP
        >>>
        >>> with open_iterable('data.csv', validation_hook=hook) as source:  # doctest: +SKIP
        ...     for row in source:
        ...         process(row)
    """

    def validate_row(row: Row) -> Row:
        """Validate row against schema"""
        errors = []
        schema_fields = schema.get("fields", {})

        for field_name, field_schema in schema_fields.items():
            value = row.get(field_name)
            field_type = field_schema.get("type")
            nullable = field_schema.get("nullable", False)

            # Check nullable
            if value is None and not nullable:
                errors.append(f"Field '{field_name}' is required but missing")
                continue

            if value is None:
                continue  # Nullable field with None value is OK

            # Type checking (with conversion support for CSV string types)
            if field_type:
                expected_type = field_type.lower()
                actual_type = type(value).__name__

                # Type mapping and conversion: explicit name -> type lookup
                # (never eval type names coming from schema input).
                type_map: dict[type, tuple[str, ...]] = {
                    int: ("int", "integer"),
                    float: ("float", "double"),
                    str: ("str", "string"),
                    bool: ("bool", "boolean"),
                }

                type_matches = False
                # Check if actual type matches expected
                for python_type, aliases in type_map.items():
                    if expected_type in aliases:
                        if isinstance(value, python_type):
                            type_matches = True
                            break

                # If not matching and value is string (common in CSV), try conversion
                if not type_matches and isinstance(value, str):
                    try:
                        if expected_type in ("int", "integer"):
                            int(value)  # Try conversion
                            type_matches = True  # Can be converted, so it's valid
                        elif expected_type in ("float", "double"):
                            float(value)  # Try conversion
                            type_matches = True
                        elif expected_type in ("bool", "boolean"):
                            # String bools are valid
                            type_matches = True
                    except (ValueError, TypeError):
                        pass  # Conversion failed, type doesn't match

                if not type_matches:
                    errors.append(f"Field '{field_name}' has type '{actual_type}' but expected '{expected_type}'")

        if errors:
            raise ValueError(f"Schema validation failed: {', '.join(errors)}")

        return row

    return validate_row


def rules_validator(rules: dict[str, list[str]]) -> ValidationHook:
    """
    Create a validation hook from validation rules.

    Args:
        rules: Dictionary mapping field names to lists of rule names
               (e.g., {"email": ["common.email", "required"]})

    Returns:
        Validation hook function

    Example:
        >>> from iterable.helpers.validation import rules_validator
        >>>
        >>> rules = {"email": ["common.email"], "url": ["common.url"]}  # doctest: +SKIP
        >>> hook = rules_validator(rules)  # doctest: +SKIP
        >>>
        >>> with open_iterable('data.csv', validation_hook=hook) as source:  # doctest: +SKIP
        ...     for row in source:
        ...         process(row)
    """
    from ..validate.rules import validate_value

    def validate_row(row: Row) -> Row:
        """Validate row against rules"""
        errors = []

        for field_name, rule_names in rules.items():
            value = row.get(field_name)

            for rule_name in rule_names:
                if rule_name == "required":
                    if value is None or value == "":
                        errors.append(f"Field '{field_name}' is required")
                        continue
                else:
                    try:
                        is_valid, error_msg = validate_value(value, rule_name)
                        if not is_valid:
                            errors.append(f"Field '{field_name}': {error_msg or f'failed rule {rule_name}'}")
                    except ValueError as e:
                        # Rule not found or other validation error
                        errors.append(f"Field '{field_name}': {str(e)}")

        if errors:
            raise ValueError(f"Rule validation failed: {', '.join(errors)}")

        return row

    return validate_row
