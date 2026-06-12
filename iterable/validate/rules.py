"""
Built-in validation rules and validator registration.

Provides common validation rules (email, URL, etc.) and a system
for registering custom validators.
"""

from __future__ import annotations

import re
from collections.abc import Callable
from typing import Any

# Registry for custom validators
_VALIDATOR_REGISTRY: dict[str, Callable[[Any], bool]] = {}


class ValidationError(Exception):
    """Exception raised when validation fails."""

    def __init__(self, message: str, field: str | None = None, rule: str | None = None):
        super().__init__(message)
        self.field = field
        self.rule = rule
        self.message = message


def _validate_email(value: Any) -> bool:
    """Validate email address format."""
    if not isinstance(value, str):
        return False
    # Basic email regex pattern
    pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
    return bool(re.match(pattern, value))


def _validate_url(value: Any) -> bool:
    """Validate URL format."""
    if not isinstance(value, str):
        return False
    # Basic URL pattern
    pattern = r"^https?://[^\s/$.?#].[^\s]*$"
    return bool(re.match(pattern, value))


def _validate_ru_inn(value: Any) -> bool:
    """Validate Russian INN (tax identification number)."""
    if not isinstance(value, str):
        return False
    # Remove spaces and hyphens
    inn = value.replace(" ", "").replace("-", "")
    # INN can be 10 or 12 digits
    if not (len(inn) == 10 or len(inn) == 12):
        return False
    if not inn.isdigit():
        return False
    # Basic format check - full validation would require checksum calculation
    return True


def _validate_ru_ogrn(value: Any) -> bool:
    """Validate Russian OGRN (state registration number)."""
    if not isinstance(value, str):
        return False
    # Remove spaces and hyphens
    ogrn = value.replace(" ", "").replace("-", "")
    # OGRN can be 13 or 15 digits
    if not (len(ogrn) == 13 or len(ogrn) == 15):
        return False
    if not ogrn.isdigit():
        return False
    # Basic format check - full validation would require checksum calculation
    return True


def _validate_required(value: Any) -> bool:
    """Validate that value is not None or empty."""
    if value is None:
        return False
    if isinstance(value, str) and len(value.strip()) == 0:
        return False
    return True


# Built-in validators
_BUILTIN_VALIDATORS: dict[str, Callable[[Any], bool]] = {
    "common.email": _validate_email,
    "common.url": _validate_url,
    "ru.org.inn": _validate_ru_inn,
    "ru.org.ogrn": _validate_ru_ogrn,
    "required": _validate_required,
}


def get_validator(rule_name: str) -> Callable[[Any], bool]:
    """
    Get a validator function by name.

    Args:
        rule_name: Name of the validator (e.g., "common.email")

    Returns:
        Validator function that takes a value and returns True/False

    Raises:
        ValueError: If validator not found
    """
    # Check built-in validators first
    if rule_name in _BUILTIN_VALIDATORS:
        return _BUILTIN_VALIDATORS[rule_name]

    # Check custom validators
    if rule_name in _VALIDATOR_REGISTRY:
        return _VALIDATOR_REGISTRY[rule_name]

    raise ValueError(f"Unknown validator: {rule_name}")


def register(name: str, validator: Callable[[Any], bool]) -> None:
    """
    Register a custom validator function.

    Args:
        name: Name to register the validator under
        validator: Function that takes a value and returns True/False

    Example:
        >>> def validate_positive(value):
        ...     return isinstance(value, (int, float)) and value > 0
        >>> register("positive", validate_positive)
    """
    _VALIDATOR_REGISTRY[name] = validator


def validate_value(value: Any, rule_name: str) -> tuple[bool, str | None]:
    """
    Validate a value against a rule.

    Args:
        value: Value to validate
        rule_name: Name of the validation rule

    Returns:
        Tuple of (is_valid, error_message)
    """
    try:
        validator = get_validator(rule_name)
        is_valid = validator(value)
        if is_valid:
            return (True, None)
        else:
            return (False, f"Value failed validation rule '{rule_name}'")
    except ValueError as e:
        return (False, str(e))
    except Exception as e:
        return (False, f"Validation error: {e}")
