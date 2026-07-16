from __future__ import annotations

import json
import typing
from collections import OrderedDict
from collections.abc import Callable, Iterator
from statistics import mean
from typing import Any, cast

import chardet

from ..base import BaseIterable

DEFAULT_DELIMITERS = [",", ";", "\t", "|"]


def hashable_repr(value: typing.Any) -> str:
    """
    Return a hashable string representation of a value for use in sets/dict keys.

    Handles unhashable types (list, dict, etc.) via JSON serialization so that
    unique counting and deduplication work on rows containing nested structures.
    """
    try:
        hash(value)
        return repr(value)
    except TypeError:
        return json.dumps(value, sort_keys=True, default=str)


def hashable_key(value: typing.Any) -> str | typing.Any:
    """
    Return a value suitable for use as a dict key: the value itself if hashable,
    otherwise a hashable string representation. Use when the caller needs the
    original value as the key when possible (e.g. for frequency result dicts).
    """
    try:
        hash(value)
        return value
    except TypeError:
        return json.dumps(value, sort_keys=True, default=str)


def rowincount(filename: str | None = None, fileobj: typing.IO[Any] | None = None) -> int:
    """Count newline-delimited rows without changing a seekable stream.

    Text codecs expose ``str`` chunks while ordinary files expose ``bytes``;
    selecting the delimiter from the first chunk keeps totals usable for both
    paths.  A seekable stream is restored to its original position so a
    progress query cannot consume the source.
    """
    if filename is not None:
        with open(filename, "rb") as f:
            return sum(chunk.count(b"\n") for chunk in iter(lambda: f.read(1024 * 1024), b""))
    if fileobj is None:
        raise ValueError("Filename or fileobj should not be None")

    original_pos = None
    try:
        original_pos = fileobj.tell()
    except (AttributeError, OSError, ValueError):
        pass

    total = 0
    try:
        while True:
            chunk = fileobj.read(1024 * 1024)
            if not chunk:
                break
            delimiter = b"\n" if isinstance(chunk, bytes) else "\n"
            total += chunk.count(delimiter)
    finally:
        if original_pos is not None:
            try:
                fileobj.seek(original_pos)
            except (AttributeError, OSError, ValueError):
                pass
    return total


def detect_encoding_raw(
    filename: str | None = None,
    stream: typing.BinaryIO | None = None,
    limit: int = 1000000,
) -> dict[str, Any]:
    """Detect file or file object encoding reading 1MB data by default and using chardet"""
    if filename is not None:
        f = open(filename, "rb")
        chunk = f.read(limit)
        f.close()
        return cast(dict[str, Any], chardet.detect(chunk))
    if stream is not None:
        return cast(dict[str, Any], chardet.detect(stream.read(limit)))
    raise ValueError("Filename or stream should not be None")


def detect_delimiter(
    filename: str | None = None,
    stream: typing.IO[str] | None = None,
    encoding: str = "utf8",
    limit: int = 20,
    threshold: float = 0.6,
) -> str:
    """Detect CSV file or file object delimiter with known encoding and limit with number of lines"""
    lines: list[str] = []
    char_map: dict[str, list[int]] = {char: [] for char in DEFAULT_DELIMITERS}
    if filename:
        f = open(filename, encoding=encoding)
        for _n in range(0, limit):
            line = f.readline().strip()
            if len(line) > 0:
                lines.append(line)
        f.close()
    elif stream is not None:
        for _n in range(0, limit):
            line = stream.readline()
            if not line:
                break
            line = line.strip()
            if len(line) > 0:
                lines.append(line)
    else:
        raise ValueError("Filename or stream should not be None")

    if not lines:
        return ","

    for line in lines:
        for char in DEFAULT_DELIMITERS:
            char_map[char].append(line.count(char))

    candidates: dict[str, int] = {}
    for char in char_map:
        if min(char_map[char]) != 0 and mean(char_map[char]) / max(char_map[char]) > threshold:
            candidates[char] = max(char_map[char])

    if candidates:
        delimiter = max(candidates, key=lambda c: candidates[c])
    else:
        delimiter = max(DEFAULT_DELIMITERS, key=lambda c: sum(line.count(c) for line in lines))
    return delimiter


def get_dict_value(d: dict[str, Any] | list[dict[str, Any]] | None, keys: list[str]) -> list[Any]:
    """Return value of selected dict key"""
    out: list[Any] = []
    if d is None:
        return out
    if len(keys) == 1:
        if isinstance(d, (dict, OrderedDict)):
            if keys[0] in d.keys():
                out.append(d[keys[0]])
        else:
            for r in d:
                if r and keys[0] in r.keys():
                    out.append(r[keys[0]])
    else:
        if isinstance(d, (dict, OrderedDict)):
            if keys[0] in d.keys():
                out.extend(get_dict_value(d[keys[0]], keys[1:]))
        else:
            for r in d:
                if keys[0] in r.keys():
                    out.extend(get_dict_value(r[keys[0]], keys[1:]))
    return out


def strip_dict_fields(record: dict[str, Any], fields: list[str], startkey: int = 0) -> dict[str, Any]:
    """Remove selected dict fields"""
    keys = record.keys()
    localf: list[str] = []
    for field in fields:
        if len(field) > startkey:
            localf.append(field[startkey])
    for k in list(keys):
        if k not in localf:
            del record[k]

    if len(k) > 0:
        for nested_key in record.keys():
            if isinstance(record[nested_key], dict):
                record[nested_key] = strip_dict_fields(record[nested_key], fields, startkey + 1)
    return record


def dict_generator(indict: Any, pre: list[str] | None = None) -> Iterator[list[Any]]:
    """Processes python dictionary and return list of key values"""
    pre = pre[:] if pre else []
    if isinstance(indict, dict):
        for key, value in list(indict.items()):
            if key == "_id":
                continue
            if isinstance(value, dict):
                yield from dict_generator(value, pre + [key])
            elif isinstance(value, list) or isinstance(value, tuple):
                for v in value:
                    if isinstance(v, dict):
                        yield from dict_generator(v, pre + [key])
            else:
                yield pre + [key, value]
    else:
        yield indict


def guess_int_size(value: int) -> str:
    """Guess integer size"""
    if value < 255:
        return "uint8"
    if value < 65535:
        return "uint16"
    return "uint32"


def guess_datatype(s: str | int | float | None, qd: typing.Any) -> dict[str, str]:
    """Guesses type of data by string provided"""
    attrs: dict[str, str] = {"base": "str"}
    if s is None:
        return {"base": "empty"}
    if isinstance(s, int):
        return {"base": "int"}
    if isinstance(s, float):
        return {"base": "float"}
    elif type(s) is not str:
        return {"base": "typed"}
    if s.isdigit():
        if len(s) > 1 and s[0] == "0":
            attrs = {"base": "numstr"}
        else:
            attrs = {"base": "int", "subtype": guess_int_size(int(s))}
    else:
        try:
            float(s)
            attrs = {"base": "float"}
            return attrs
        except ValueError:
            pass
        if qd:
            is_date = False
            res = qd.match(s)
            if res:
                pattern_str = getattr(qd, "pattern", str(qd))
                attrs = {"base": "date", "pat": pattern_str}
                is_date = True
            if not is_date:
                if len(s.strip()) == 0:
                    attrs = {"base": "empty"}
    return attrs


def count_file_newlines(filename: str | None = None, stream: typing.BinaryIO | None = None) -> int:
    """Counts number of lines in file"""

    def _make_gen(reader: Callable[[int], bytes]) -> Iterator[bytes]:
        while True:
            b = reader(2**16)
            if not b:
                break
            yield b

    if filename:
        with open(filename, "rb") as f:
            count = sum(buf.count(b"\n") for buf in _make_gen(f.read))
    elif stream is not None:
        count = sum(buf.count(b"\n") for buf in _make_gen(stream.read))
    else:
        raise ValueError("Filename or stream should not be None")
    return count


def get_dict_keys(iterable: list[dict[str, Any]], limit: int = 1000) -> list[str]:
    """Returns dictionary keys"""
    n = 0
    keys: list[str] = []
    for item in iterable:
        if limit and n >= limit:
            break
        n += 1
        dk = dict_generator(item)
        for i in dk:
            k = ".".join(i[:-1])
            if k not in keys:
                keys.append(k)
    return keys


def get_iterable_keys(iterable: BaseIterable, limit: int = 1000) -> list[str]:
    """Returns BaseIterable object keys"""
    n = 0
    keys: list[str] = []
    for item in iterable:
        if limit and n >= limit:
            break
        n += 1
        dk = dict_generator(item)
        for i in dk:
            k = ".".join(i[:-1])
            if k not in keys:
                keys.append(k)
    return keys


def is_flat_object(item: dict[str, Any]) -> bool:
    """Return True if the mapping has no nested containers."""
    for _k, v in item.items():
        if isinstance(v, (tuple, list, dict)):
            return False
    return True


def get_dict_value_path(adict: dict[str, Any], key: str, prefix: list[str] | None = None) -> Any:
    if prefix is None:
        prefix = key.split(".")
    if len(prefix) == 1:
        return adict[prefix[0]]
    return get_dict_value_path(adict[prefix[0]], key, prefix=prefix[1:])


def get_dict_value_deep(
    adict: dict[str, Any] | list[Any],
    key: str,
    prefix: list[str] | None = None,
    as_array: bool = False,
    splitter: str = ".",
) -> Any:
    """Used to get value from hierarhic dicts in python with params with dots as splitter"""
    if prefix is None:
        prefix = key.split(splitter)
    if len(prefix) == 1:
        if isinstance(adict, dict):
            if prefix[0] not in adict.keys():
                return None
            if as_array:
                return [
                    adict[prefix[0]],
                ]
            return adict[prefix[0]]
        elif isinstance(adict, list):
            if as_array:
                result: list[Any] = []
                for v in adict:
                    if isinstance(v, dict) and prefix[0] in v.keys():
                        result.append(v[prefix[0]])
                return result
            else:
                if len(adict) > 0 and isinstance(adict[0], dict) and prefix[0] in adict[0].keys():
                    return adict[0][prefix[0]]
        return None
    else:
        if isinstance(adict, dict):
            if prefix[0] in adict.keys():
                return get_dict_value_deep(adict[prefix[0]], key, prefix=prefix[1:], as_array=as_array)
        elif isinstance(adict, list):
            if as_array:
                result = []
                for v in adict:
                    if isinstance(v, dict) and prefix[0] in v.keys():
                        res = get_dict_value_deep(v[prefix[0]], key, prefix=prefix[1:], as_array=as_array)
                        if res:
                            result.extend(res if isinstance(res, list) else [res])
                return result
            else:
                if len(adict) > 0 and isinstance(adict[0], dict) and prefix[0] in adict[0].keys():
                    return get_dict_value_deep(adict[0][prefix[0]], key, prefix=prefix[1:], as_array=as_array)
        return None


def make_flat(item: dict[str, Any]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for k, v in item.items():
        if isinstance(v, (tuple, list, dict)):
            result[k] = str(v)
        else:
            result[k] = v
    return result


_EXTENDED_JSON_SCALAR_KEYS = frozenset(
    {
        "$oid",
        "$numberLong",
        "$numberInt",
        "$numberDouble",
        "$numberDecimal",
        "$date",
        "$timestamp",
        "$binary",
        "$regex",
        "$undefined",
        "$minKey",
        "$maxKey",
    }
)


def normalize_extended_json(value: Any) -> Any:
    """Convert MongoDB extended JSON wrappers to native Python values.

    Recursively unwraps common ``$type`` wrappers (for example
    ``{"$numberLong": "123"}`` or ``{"$oid": "..."}``) so columnar writers
    such as Parquet do not infer mixed struct/scalar types for the same field.
    """
    if isinstance(value, dict):
        if len(value) == 1:
            key, inner = next(iter(value.items()))
            if key in _EXTENDED_JSON_SCALAR_KEYS:
                if key == "$numberLong":
                    return int(inner)
                if key == "$numberInt":
                    return int(inner)
                if key in ("$numberDouble", "$numberDecimal"):
                    return float(inner)
                if key == "$oid":
                    return str(inner)
                if key == "$date":
                    if isinstance(inner, dict):
                        return normalize_extended_json(inner)
                    return inner
                if key == "$timestamp":
                    if isinstance(inner, dict) and "$numberLong" in inner:
                        return int(inner["$numberLong"])
                    return inner
                if key == "$binary":
                    if isinstance(inner, dict) and "base64" in inner:
                        return inner["base64"]
                    return inner
                if key == "$regex":
                    if isinstance(inner, dict):
                        return inner.get("pattern", inner)
                    return inner
                return inner
        return {k: normalize_extended_json(v) for k, v in value.items()}
    if isinstance(value, list):
        return [normalize_extended_json(v) for v in value]
    return value
