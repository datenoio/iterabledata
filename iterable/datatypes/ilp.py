from __future__ import annotations

import typing
from typing import Any

from ..base import BaseCodec, BaseFileIterable
from ..helpers.utils import rowincount
from ..types import Row


def parse_line_protocol(line: str) -> dict:
    """
    Parse a single InfluxDB Line Protocol line.

    Format: measurement[,tag_key=tag_value[,tag_key=tag_value]]
    field_key=field_value[,field_key=field_value] [timestamp]

    Returns a dict with keys: measurement, tags (dict), fields (dict), time (optional)
    """
    line = line.strip()
    if not line:
        raise ValueError("Empty line")

    # Parse ILP line character by character to handle quoted strings properly
    # Format: measurement[,tags] fields [timestamp]
    # Tags and fields are separated by space
    # Fields and timestamp are separated by space

    measurement_part = ""
    fields_part = ""
    timestamp_part = None

    i = 0
    in_quotes = False
    escape_next = False
    current_part = "measurement"  # measurement, fields, timestamp

    while i < len(line):
        char = line[i]

        if escape_next:
            escape_next = False
            if current_part == "measurement":
                measurement_part += char
            elif current_part == "fields":
                fields_part += char
            i += 1
            continue

        if char == "\\":
            escape_next = True
            if current_part == "measurement":
                measurement_part += char
            elif current_part == "fields":
                fields_part += char
            i += 1
            continue

        if char == '"':
            in_quotes = not in_quotes
            if current_part == "measurement":
                measurement_part += char
            elif current_part == "fields":
                fields_part += char
            i += 1
            continue

        if char == " " and not in_quotes:
            # Space outside quotes - might be a separator
            if current_part == "measurement":
                # Check if next part has = (indicating fields)
                remaining = line[i + 1 :].strip()
                if "=" in remaining:
                    # Next part is fields
                    current_part = "fields"
                else:
                    # Might be timestamp or just part of measurement
                    measurement_part += char
            elif current_part == "fields":
                # Check if remaining looks like timestamp (all digits or long)
                remaining = line[i + 1 :].strip()
                if remaining and (remaining.isdigit() or ("=" not in remaining and len(remaining) > 10)):
                    # This is timestamp
                    timestamp_part = remaining
                    break
                else:
                    # Still part of fields (quoted string with space)
                    fields_part += char
            i += 1
            continue

        # Regular character
        if current_part == "measurement":
            measurement_part += char
        elif current_part == "fields":
            fields_part += char
        i += 1

    # Clean up
    measurement_part = measurement_part.strip()
    fields_part = fields_part.strip()
    if timestamp_part:
        timestamp_part = timestamp_part.strip()

    # Parse measurement and tags
    # Tags come after measurement, separated by commas
    # Format: measurement,tag1=val1,tag2=val2
    if "," in measurement_part:
        # Check if there are tags (tags have = signs)
        comma_pos = measurement_part.find(",")
        # Check if there's an = sign after the first comma (indicating tags)
        if "=" in measurement_part[comma_pos + 1 :]:
            measurement = measurement_part[:comma_pos]
            tags_str = measurement_part[comma_pos + 1 :]

            tags = {}
            # Parse tags - split on commas, but handle escaped commas
            # Use a simple approach: split on comma, then check for escaped commas
            # For ILP, commas in tag values should be escaped, so we can split on comma
            tag_parts = tags_str.split(",")
            for tag_part in tag_parts:
                if "=" in tag_part:
                    # Split on first = (tag keys can't contain =)
                    eq_pos = tag_part.find("=")
                    if eq_pos > 0:
                        tag_key = tag_part[:eq_pos]
                        tag_value = tag_part[eq_pos + 1 :]
                        tags[tag_key] = unescape_value(tag_value)
        else:
            # No tags, comma is part of measurement name
            measurement = measurement_part
            tags = {}
    else:
        # No tags
        measurement = measurement_part
        tags = {}

    # Parse fields
    fields = {}
    if fields_part:
        # Parse fields - need to handle quoted strings properly
        # Fields are separated by commas, but quoted strings can contain commas
        i = 0
        while i < len(fields_part):
            # Find the next = sign
            eq_pos = fields_part.find("=", i)
            if eq_pos == -1:
                break

            field_key = fields_part[i:eq_pos]
            field_value_start = eq_pos + 1

            # Check if value is quoted
            if field_value_start < len(fields_part) and fields_part[field_value_start] == '"':
                # Find the closing quote (handling escaped quotes)
                quote_end = field_value_start + 1
                while quote_end < len(fields_part):
                    if fields_part[quote_end] == '"' and (
                        quote_end == field_value_start + 1 or fields_part[quote_end - 1] != "\\"
                    ):
                        break
                    quote_end += 1

                field_value = fields_part[field_value_start : quote_end + 1]
                # Find next comma after the quoted value
                next_comma = fields_part.find(",", quote_end + 1)
                if next_comma == -1:
                    next_comma = len(fields_part)
                i = next_comma + 1
            else:
                # Unquoted value - find next comma
                next_comma = fields_part.find(",", field_value_start)
                if next_comma == -1:
                    field_value = fields_part[field_value_start:]
                    i = len(fields_part)
                else:
                    field_value = fields_part[field_value_start:next_comma]
                    i = next_comma + 1

            # Parse field value
            fields[field_key] = parse_field_value(field_value)

    # Parse timestamp
    time = None
    if timestamp_part:
        # Return timestamp as string (as per test expectation)
        time = str(timestamp_part)

    result = {"measurement": measurement, "tags": tags, "fields": fields}
    if time is not None:
        result["time"] = time

    return result


def unescape_value(value: str) -> str:
    """Unescape InfluxDB Line Protocol values"""
    # In ILP, commas, spaces, and equals signs need to be escaped
    # But for simplicity, we'll handle basic cases
    return value.replace("\\,", ",").replace("\\ ", " ").replace("\\=", "=")


def parse_field_value(value: str):
    """
    Parse a field value according to InfluxDB Line Protocol rules.

    - String values: must be quoted with double quotes
    - Integer values: followed by 'i'
    - Float values: decimal numbers
    - Boolean values: 't', 'T', 'true', 'True', 'TRUE' for true; 'f', 'F', 'false', 'False', 'FALSE' for false
    """
    if not value:
        return None

    # Boolean values
    if value.lower() in ("t", "true"):
        return True
    if value.lower() in ("f", "false"):
        return False

    # Integer values (end with 'i')
    if value.endswith("i"):
        try:
            return int(value[:-1])
        except ValueError:
            pass

    # String values (quoted)
    if value.startswith('"') and value.endswith('"'):
        # Unescape string
        return value[1:-1].replace('\\"', '"').replace("\\n", "\n").replace("\\t", "\t")

    # Float values
    try:
        return float(value)
    except ValueError:
        pass

    # Default: return as string
    return value


def format_line_protocol(record: dict) -> str:
    """
    Format a dictionary record into InfluxDB Line Protocol format.

    Expected keys:
    - measurement: str (required)
    - tags: dict (optional)
    - fields: dict (required)
    - time: int or str (optional)
    """
    measurement = record.get("measurement", "")
    tags = record.get("tags", {})
    fields = record.get("fields", {})
    time = record.get("time")

    # Build measurement part with tags
    # Format: measurement[,tag1=val1,tag2=val2]
    measurement_with_tags = measurement
    if tags:
        tag_parts = []
        for key, value in sorted(tags.items()):
            tag_parts.append(f"{key}={escape_value(str(value))}")
        measurement_with_tags += "," + ",".join(tag_parts)

    # Build fields part
    field_parts = []
    for key, value in fields.items():
        field_value = format_field_value(value)
        field_parts.append(f"{key}={field_value}")

    # Combine: measurement[,tags] fields [timestamp]
    line_parts = [measurement_with_tags, ",".join(field_parts)]

    # Add timestamp
    if time is not None:
        line_parts.append(str(time))

    return " ".join(line_parts)


def escape_value(value: str) -> str:
    """Escape InfluxDB Line Protocol values"""
    return value.replace(",", "\\,").replace(" ", "\\ ").replace("=", "\\=")


def format_field_value(value) -> str:
    """Format a Python value for InfluxDB Line Protocol"""
    if isinstance(value, bool):
        return "t" if value else "f"
    elif isinstance(value, int):
        return f"{value}i"
    elif isinstance(value, float):
        return str(value)
    elif isinstance(value, str):
        # Escape string and quote it
        escaped = value.replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n").replace("\t", "\\t")
        return f'"{escaped}"'
    else:
        # Convert to string and quote
        escaped = str(value).replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n").replace("\t", "\\t")
        return f'"{escaped}"'


class ILPIterable(BaseFileIterable):
    """InfluxDB Line Protocol iterable"""

    def __init__(
        self,
        filename: str | None = None,
        stream: typing.IO[Any] | None = None,
        codec: BaseCodec | None = None,
        mode: str = "r",
        encoding: str = "utf8",
        options: dict[str, Any] | None = None,
    ):
        if options is None:
            options = {}
        self.pos = 0
        super().__init__(filename, stream, codec=codec, binary=False, mode=mode, encoding=encoding, options=options)
        self.reset()

    @staticmethod
    def id() -> str:
        return "ilp"

    @staticmethod
    def is_flatonly() -> bool:
        return False

    def is_streaming(self) -> bool:
        """Records are decoded incrementally; the file is not fully loaded."""
        return True

    @staticmethod
    def has_totals() -> bool:
        """Has totals indicator"""
        return True

    def totals(self):
        """Returns file totals"""
        if self.codec is not None:
            fobj = self.codec.fileobj()
        else:
            fobj = self.fobj
        return rowincount(self.filename, fobj)

    def reset(self):
        """Reset iterable"""
        super().reset()
        self.pos = 0

    def read(self, skip_empty: bool = True) -> dict:
        """Read single ILP record"""
        while True:
            line = next(self.fobj)
            if skip_empty and not line.strip():
                continue
            self.pos += 1
            try:
                return parse_line_protocol(line)
            except (ValueError, IndexError):
                if not skip_empty:
                    raise
                # Skip malformed lines if skip_empty is True
                continue

    def write(self, record: Row) -> None:
        """Write single ILP record"""
        line = format_line_protocol(record)
        self.fobj.write(line + "\n")
        self.pos += 1

    def write_bulk(self, records: list[Row]) -> None:
        """Write bulk ILP records"""
        for record in records:
            self.write(record)
