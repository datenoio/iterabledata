"""Shared JSON value encoding for JSON-family writers.

The standard ``json`` module only serializes ``dict``, ``list``, ``tuple``, ``str``,
``int``, ``float``, ``bool`` and ``None``. Records read from Parquet, databases,
pickles or ``ijson`` routinely contain other Python types; this module gives every
JSON writer one ``default=`` hook so those values are never written as ``null``.

Encoding table:

- ``datetime``/``date``/``time``: ISO 8601 (``isoformat()``)
- ``Decimal``: JSON number when it round-trips through a float, otherwise a string
  (``decimal="string"`` always writes strings)
- ``UUID``: canonical string
- ``bytes``/``bytearray``/``memoryview``: base64 string
- ``timedelta``: ISO 8601 duration (``PT5S``, ``-P1DT2H``)
- ``set``/``frozenset``: array (sorted when the members are comparable)
- NumPy scalars and arrays: ``.item()`` / ``.tolist()``
- anything else: ``str(value)``, or ``WriteError`` with ``on_unknown_type="raise"``
"""

from __future__ import annotations

import base64
import datetime
import decimal
import uuid
from collections.abc import Callable
from typing import Any

from ..exceptions import WriteError

DECIMAL_MODES = ("auto", "string")
UNKNOWN_TYPE_MODES = ("str", "raise")

_US_PER_SECOND = 1_000_000
_US_PER_MINUTE = 60 * _US_PER_SECOND
_US_PER_HOUR = 60 * _US_PER_MINUTE
_US_PER_DAY = 24 * _US_PER_HOUR


def iso_duration(value: datetime.timedelta) -> str:
    """Format a ``timedelta`` as an ISO 8601 duration (``P1DT2H3M4.5S``)."""
    total = (value.days * 86400 + value.seconds) * _US_PER_SECOND + value.microseconds
    sign = "-" if total < 0 else ""
    total = abs(total)
    days, total = divmod(total, _US_PER_DAY)
    hours, total = divmod(total, _US_PER_HOUR)
    minutes, total = divmod(total, _US_PER_MINUTE)
    seconds, micros = divmod(total, _US_PER_SECOND)
    date_part = f"{days}D" if days else ""
    time_part = ""
    if hours:
        time_part += f"{hours}H"
    if minutes:
        time_part += f"{minutes}M"
    if seconds or micros or not (days or hours or minutes):
        if micros:
            time_part += f"{seconds}.{micros:06d}".rstrip("0") + "S"
        else:
            time_part += f"{seconds}S"
    return f"{sign}P{date_part}" + (f"T{time_part}" if time_part else "")


def _encode_decimal(value: decimal.Decimal, mode: str) -> float | str:
    if mode == "auto" and value.is_finite():
        as_float = float(value)
        # Use the float only when its shortest repr is numerically the same decimal,
        # so "1.23" stays 1.23 while values beyond float precision stay exact text.
        if decimal.Decimal(repr(as_float)) == value:
            return as_float
    return str(value)


def _encode_set(value: set[Any] | frozenset[Any]) -> list[Any]:
    try:
        return sorted(value)
    except TypeError:
        return list(value)


def make_json_default(decimal_mode: str = "auto", on_unknown_type: str = "str") -> Callable[[Any], Any]:
    """Build a ``default=`` hook for ``json.dumps``.

    Args:
        decimal_mode: ``"auto"`` writes a ``Decimal`` as a number when a float represents
            it exactly in shortest form, otherwise as a string; ``"string"`` always writes strings.
        on_unknown_type: ``"str"`` writes ``str(value)`` for unsupported objects;
            ``"raise"`` raises :class:`~iterable.exceptions.WriteError`.

    Raises:
        ValueError: If either mode is not recognized.
    """
    if decimal_mode not in DECIMAL_MODES:
        raise ValueError(f"Invalid 'decimal' value: {decimal_mode!r}. Valid values are: {', '.join(DECIMAL_MODES)}")
    if on_unknown_type not in UNKNOWN_TYPE_MODES:
        raise ValueError(
            f"Invalid 'on_unknown_type' value: {on_unknown_type!r}. Valid values are: {', '.join(UNKNOWN_TYPE_MODES)}"
        )

    def default(obj: Any) -> Any:
        if isinstance(obj, (datetime.datetime, datetime.date, datetime.time)):
            return obj.isoformat()
        if isinstance(obj, decimal.Decimal):
            return _encode_decimal(obj, decimal_mode)
        if isinstance(obj, uuid.UUID):
            return str(obj)
        if isinstance(obj, (bytes, bytearray, memoryview)):
            return base64.b64encode(bytes(obj)).decode("ascii")
        if isinstance(obj, datetime.timedelta):
            return iso_duration(obj)
        if isinstance(obj, (set, frozenset)):
            return _encode_set(obj)
        if type(obj).__module__ == "numpy":
            if hasattr(obj, "tolist"):
                return obj.tolist()
            if hasattr(obj, "item"):
                return obj.item()
        if on_unknown_type == "raise":
            raise WriteError(
                f"Cannot serialize value of type {type(obj).__module__}.{type(obj).__qualname__} to JSON; "
                "pass on_unknown_type='str' to write its string form",
                error_code="UNSUPPORTED_JSON_VALUE",
            )
        return str(obj)

    return default


encode_default = make_json_default()
"""Default hook: ``decimal="auto"``, ``on_unknown_type="str"``."""


def json_default_from_options(options: dict[str, Any] | None) -> Callable[[Any], Any]:
    """Return the ``default=`` hook configured by writer options ``decimal`` and ``on_unknown_type``."""
    if not options:
        return encode_default
    decimal_mode = options.get("decimal", "auto")
    on_unknown_type = options.get("on_unknown_type", "str")
    if decimal_mode == "auto" and on_unknown_type == "str":
        return encode_default
    return make_json_default(decimal_mode, on_unknown_type)
