"""JSON decoding and encoding for the JSON and JSON Lines datatypes.

Decoding uses ``msgspec`` and encoding uses ``orjson`` when they are installed (the
``iterabledata[fast]`` extra); otherwise both use the standard library. Results do not depend
on what is installed:

- Decoders return the same values. ``msgspec`` keeps integers beyond 64 bits exact (``orjson``
  turns them into floats, which is why it is not used for decoding). Input that ``msgspec``
  rejects but ``json`` accepts, such as ``NaN`` literals, is decoded by ``json``.
- Encoders write compact JSON (``separators=(",", ":")``), keep non-ASCII characters, write
  NaN and infinities as ``null`` and pass datetimes, dataclasses and unsupported types to the
  ``default`` hook. The bytes are identical except for floats below ``1e-4``, which ``orjson``
  writes in positional form (``0.00001``) and ``json`` in exponent form (``1e-05``). Records
  that ``orjson`` cannot encode (integers beyond 64 bits, non-string keys) fall back to
  ``json``. ``orjson`` older than 3.11.7 writes ``1e16`` instead of ``1e+16`` and is not used.

Set ``ITERABLEDATA_JSON_BACKEND=stdlib`` (or call ``configure("stdlib")``) to force the
standard library.
"""

from __future__ import annotations

import importlib
import json
import math
import os
from collections.abc import Callable, Iterable
from typing import Any

BACKEND_ENV = "ITERABLEDATA_JSON_BACKEND"
BACKEND_CHOICES = ("auto", "stdlib")
# First orjson release whose float output matches ``repr(float)`` (``1e+16``).
MIN_ORJSON_VERSION = (3, 11, 7)

Default = Callable[[Any], Any] | None
Decoder = Callable[[str | bytes], Any]
Encoder = Callable[[Any], str]
LinesEncoder = Callable[[Iterable[Any]], str]

_SEPARATORS = (",", ":")
_backends: dict[str, str] | None = None


def _importable(module: str, min_version: tuple[int, ...] = ()) -> bool:
    try:
        imported = importlib.import_module(module)
    except ImportError:
        return False
    if not min_version:
        return True
    parts = str(getattr(imported, "__version__", "0")).split(".")
    version = tuple(int(part) if part.isdigit() else 0 for part in parts[: len(min_version)])
    return version >= min_version


def configure(backend: str | None = None) -> dict[str, str]:
    """Select the backends: ``"auto"`` (default) or ``"stdlib"``.

    ``None`` reads ``ITERABLEDATA_JSON_BACKEND``. Iterables opened afterwards use the new
    selection. Returns the selection as ``{"decode": ..., "encode": ...}``.
    """
    global _backends
    choice = (backend or os.environ.get(BACKEND_ENV) or "auto").strip().lower()
    if choice not in BACKEND_CHOICES:
        raise ValueError(f"{BACKEND_ENV} must be one of {BACKEND_CHOICES}, got {choice!r}")
    if choice == "stdlib":
        _backends = {"decode": "json", "encode": "json"}
    else:
        _backends = {
            "decode": "msgspec" if _importable("msgspec") else "json",
            "encode": "orjson" if _importable("orjson", MIN_ORJSON_VERSION) else "json",
        }
    return dict(_backends)


def backends() -> dict[str, str]:
    """The active backends, ``{"decode": "msgspec" | "json", "encode": "orjson" | "json"}``."""
    return dict(_backends if _backends is not None else configure())


def make_decoder() -> Decoder:
    """Return a ``loads`` function for one JSON document (``str`` or UTF-8 ``bytes``)."""
    if backends()["decode"] != "msgspec":
        return json.loads
    import msgspec

    decode = msgspec.json.Decoder().decode
    decode_error = msgspec.DecodeError

    def loads(data: str | bytes) -> Any:
        try:
            return decode(data)
        except decode_error:
            # NaN/Infinity literals, lone surrogates and similar input that only ``json`` accepts.
            return json.loads(data)

    return loads


def _finite(value: Any) -> Any:
    """Copy of ``value`` with NaN and infinities replaced by ``None``."""
    if isinstance(value, float):
        return value if math.isfinite(value) else None
    if isinstance(value, dict):
        return {k: _finite(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [_finite(v) for v in value]
    return value


def _stdlib_encoder(default: Default) -> Encoder:
    encode = json.JSONEncoder(ensure_ascii=False, separators=_SEPARATORS, allow_nan=False, default=default).encode
    finite_default = None if default is None else (lambda obj: _finite(default(obj)))
    encode_finite = json.JSONEncoder(
        ensure_ascii=False, separators=_SEPARATORS, allow_nan=False, default=finite_default
    ).encode

    def dumps(obj: Any) -> str:
        try:
            return encode(obj)
        except ValueError:
            # ``allow_nan=False`` rejects NaN and infinities; write them as ``null`` like orjson.
            return encode_finite(_finite(obj))

    return dumps


def make_encoder(default: Default = None) -> Encoder:
    """Return a ``dumps`` function that encodes one value as compact JSON text."""
    stdlib_dumps = _stdlib_encoder(default)
    if backends()["encode"] != "orjson":
        return stdlib_dumps
    import orjson

    orjson_dumps = orjson.dumps
    encode_error = orjson.JSONEncodeError
    option = orjson.OPT_PASSTHROUGH_DATETIME | orjson.OPT_PASSTHROUGH_DATACLASS

    def dumps(obj: Any) -> str:
        try:
            text: str = orjson_dumps(obj, default=default, option=option).decode("utf-8")
        except encode_error:
            return stdlib_dumps(obj)
        return text

    return dumps


def make_lines_encoder(default: Default = None) -> LinesEncoder:
    """Return a function that encodes records as JSON Lines text, one line per record."""
    dumps = make_encoder(default)
    if backends()["encode"] != "orjson":
        return lambda records: "".join([dumps(record) + "\n" for record in records])
    import orjson

    orjson_dumps = orjson.dumps
    encode_error = orjson.JSONEncodeError
    option = orjson.OPT_PASSTHROUGH_DATETIME | orjson.OPT_PASSTHROUGH_DATACLASS | orjson.OPT_APPEND_NEWLINE

    def dumps_lines(records: Iterable[Any]) -> str:
        records = records if isinstance(records, list) else list(records)
        try:
            encoded = b"".join([orjson_dumps(record, default=default, option=option) for record in records])
        except encode_error:
            return "".join([dumps(record) + "\n" for record in records])
        text: str = encoded.decode("utf-8")
        return text

    return dumps_lines
