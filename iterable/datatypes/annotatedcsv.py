from __future__ import annotations

import csv
import logging
import typing
from datetime import datetime
from typing import Any

from ..base import BaseCodec, BaseFileIterable
from ..helpers.utils import rowincount
from ..types import Row

DEFAULT_ENCODING = "utf8"
DEFAULT_DELIMITER = ","


def parse_datatype(dtype_str: str):
    """Parse InfluxDB datatype string to Python type"""
    dtype_str = dtype_str.strip().lower()

    if dtype_str.startswith("datetime"):
        return "datetime"
    elif dtype_str in ("string", "long", "double", "boolean", "unsignedlong", "duration", "base64binary"):
        return dtype_str
    else:
        return "string"  # Default


def convert_value(value: str, dtype: str):
    """Convert a string value to the appropriate Python type based on datatype"""
    if not value or value == "":
        return None

    dtype = dtype.strip().lower()

    if dtype.startswith("datetime"):
        # Try to parse RFC3339 datetime
        try:
            # Remove timezone info for simplicity, or use dateutil if available
            if "T" in value:
                # RFC3339 format: 2025-12-19T15:12:51Z
                dt_str = value.replace("Z", "+00:00")
                return datetime.fromisoformat(dt_str.replace("Z", ""))
            return datetime.fromisoformat(value)
        except (ValueError, AttributeError):
            return value
    elif dtype == "long" or dtype == "unsignedlong":
        try:
            return int(value)
        except ValueError:
            return value
    elif dtype == "double":
        try:
            return float(value)
        except ValueError:
            return value
    elif dtype == "boolean":
        return value.lower() in ("true", "t", "1", "yes")
    elif dtype == "duration":
        # Duration format - return as string for now
        return value
    elif dtype == "base64binary":
        # Base64 binary - return as string for now
        return value
    else:  # string or unknown
        return value


class AnnotatedCSVIterable(BaseFileIterable):
    """InfluxDB Annotated CSV iterable"""

    def __init__(
        self,
        filename: str = None,
        stream: typing.IO[Any] | None = None,
        codec: BaseCodec | None = None,
        keys: list[str] | None = None,
        delimiter: str | None = None,
        quotechar: str = '"',
        mode: str = "r",
        encoding: str | None = None,
        autodetect: bool = False,
        options: dict[str, Any] | None = None,
    ):
        if options is None:
            options = {}
        logging.debug(f"Params: encoding: {encoding}, options {options}")
        self.encoding = None
        self.fileobj = stream

        if encoding is not None:
            self.encoding = encoding
        elif "encoding" in options.keys() and options["encoding"] is not None:
            self.encoding = options["encoding"]

        if mode == "r":
            if self.encoding is None:
                self.encoding = DEFAULT_ENCODING
        elif self.encoding is None:
            self.encoding = DEFAULT_ENCODING

        logging.debug(f"Final encoding {self.encoding}")
        self.keys = keys

        super().__init__(
            filename, stream, codec=codec, binary=False, encoding=self.encoding, mode=mode, options=options
        )

        if not delimiter:
            self.delimiter = DEFAULT_DELIMITER
        else:
            self.delimiter = delimiter
        self.quotechar = quotechar

        # Annotations storage
        self.annotations = {}
        self.datatypes = []
        self.group_flags = []
        self.default_values = []
        self.header_row = None
        self.write_options = options  # Store options for writing annotations

        logging.debug(f"Detected delimiter {self.delimiter}")
        self.reset()

    @staticmethod
    def has_totals() -> bool:
        """Has totals indicator"""
        return True

    def totals(self):
        """Returns file totals"""
        return rowincount(self.filename, self.fobj)

    def reset(self):
        """Reset iterable"""
        super().reset()

        if self.fobj is None and self.codec is not None:
            fobj = self.codec.textIO(self.encoding)
        else:
            fobj = self.fobj

        self.reader = None
        self.pos = 0

        if self.mode == "r":
            # Read entire file content to parse annotations and find header
            fobj.seek(0)
            all_lines = fobj.readlines()
            fobj.seek(0)

            # Parse annotations
            self._read_annotations_from_lines(all_lines)

            # Find header row index
            header_idx = 0
            for i, line in enumerate(all_lines):
                line = line.strip()
                if not line:
                    continue
                reader = csv.reader([line], delimiter=self.delimiter, quotechar=self.quotechar)
                row = next(reader)
                if row and row[0].strip().startswith("#"):
                    continue
                elif row:
                    header_idx = i
                    if not self.header_row:
                        self.header_row = row
                    break

            # Create StringIO with data lines (after header)
            from io import StringIO

            data_lines = "".join(all_lines[header_idx + 1 :])
            data_fobj = StringIO(data_lines)

            # Extract fieldnames from header_row
            # Note: header_row may have empty columns at the start (group columns)
            # We need to preserve the column positions to align with datatypes
            if self.header_row:
                # Use all columns from header_row, including empty ones
                # DictReader will map data columns by position
                fieldnames = [col.strip() if col.strip() else f"_col{i}" for i, col in enumerate(self.header_row)]
                self.reader = csv.DictReader(
                    data_fobj, fieldnames=fieldnames, delimiter=self.delimiter, quotechar=self.quotechar
                )
            elif self.keys is not None:
                self.reader = csv.DictReader(
                    data_fobj, fieldnames=self.keys, delimiter=self.delimiter, quotechar=self.quotechar
                )
            else:
                self.reader = csv.DictReader(data_fobj, delimiter=self.delimiter, quotechar=self.quotechar)

        if self.mode in ["w", "wr"] and self.keys is not None:
            self.writer = csv.DictWriter(fobj, fieldnames=self.keys, delimiter=self.delimiter, quotechar=self.quotechar)
            # Don't write header here - it will be written after annotations in _write_annotations()
            # if annotations are present, otherwise writeheader() will be called in write()
        else:
            self.writer = None

    def _read_annotations_from_lines(self, lines):
        """Read InfluxDB CSV annotations from lines"""
        self.annotations = {}
        self.datatypes = []
        self.group_flags = []
        self.default_values = []
        self.header_row = None

        for line in lines:
            line = line.rstrip("\n\r")
            if not line.strip():
                continue

            # Parse CSV line
            reader = csv.reader([line], delimiter=self.delimiter, quotechar=self.quotechar)
            row = next(reader)

            if not row or not row[0]:
                continue

            first_col = row[0].strip()

            # Check if it's an annotation (starts with #)
            if first_col.startswith("#"):
                annotation_type = first_col[1:].lower()

                if annotation_type == "datatype":
                    self.datatypes = [parse_datatype(dt) for dt in row[1:]]
                    self.annotations["datatype"] = self.datatypes
                elif annotation_type == "group":
                    self.group_flags = [val.lower() == "true" for val in row[1:]]
                    self.annotations["group"] = self.group_flags
                elif annotation_type == "default":
                    self.default_values = row[1:]
                    self.annotations["default"] = self.default_values
                else:
                    # Store other annotations
                    self.annotations[annotation_type] = row[1:]
            else:
                # This is the header row
                if not self.header_row:
                    self.header_row = row
                break

    @staticmethod
    def id() -> str:
        return "annotatedcsv"

    @staticmethod
    def is_flatonly() -> bool:
        return True

    def read(self, skip_empty: bool = True) -> dict:
        """Read single annotated CSV record"""
        while True:
            row = next(self.reader)

            # Skip annotation rows - check if any value starts with #
            if row:
                for _key, value in row.items():
                    if value and str(value).strip().startswith("#"):
                        continue  # Skip this row, it's an annotation
                # Also check if the row looks like an annotation row (first key/value is #something)
                first_key = list(row.keys())[0] if row else None
                first_value = list(row.values())[0] if row else None
                if first_key and str(first_key).strip().startswith("#"):
                    continue
                if first_value and str(first_value).strip().startswith("#"):
                    continue

            if skip_empty and len(row) == 0:
                continue

            break

        # Apply type conversions if datatypes are available
        # Datatypes align with header columns by position
        # In InfluxDB annotated CSV, datatypes may not cover all columns
        # We need to map datatypes to the appropriate columns
        if self.datatypes and len(self.datatypes) > 0 and self.header_row:
            converted_row = {}
            # Get ordered keys from header_row to maintain column order
            header_keys = [col.strip() if col.strip() else f"_col{i}" for i, col in enumerate(self.header_row)]

            # Count non-empty columns in header to understand alignment
            non_empty_cols = [i for i, col in enumerate(self.header_row) if col.strip()]

            # If datatypes count matches non-empty columns, align them
            # Otherwise, try to align from the start (skipping empty columns)
            dtype_offset = 0
            if len(self.datatypes) == len(non_empty_cols):
                # Datatypes align with non-empty columns
                dtype_offset = -1  # Special flag to use non-empty column index
            elif len(self.datatypes) == len(self.header_row):
                # Datatypes align with all columns
                dtype_offset = 0

            for i, key in enumerate(header_keys):
                value = row.get(key, "")

                # Determine datatype index
                if dtype_offset == -1:
                    # Use index in non-empty columns list
                    if i in non_empty_cols:
                        dtype_idx = non_empty_cols.index(i)
                        if dtype_idx < len(self.datatypes):
                            dtype = self.datatypes[dtype_idx]
                            converted_row[key] = convert_value(value, dtype) if value else value
                        else:
                            converted_row[key] = value
                    else:
                        converted_row[key] = value
                else:
                    # Use direct index alignment
                    dtype_idx = i + dtype_offset
                    if dtype_idx >= 0 and dtype_idx < len(self.datatypes):
                        dtype = self.datatypes[dtype_idx]
                        converted_row[key] = convert_value(value, dtype) if value else value
                    elif len(self.datatypes) == len(non_empty_cols):
                        # If datatypes match non-empty columns exactly, try that alignment
                        if i in non_empty_cols:
                            dtype_idx = non_empty_cols.index(i)
                            if dtype_idx < len(self.datatypes):
                                dtype = self.datatypes[dtype_idx]
                                converted_row[key] = convert_value(value, dtype) if value else value
                            else:
                                converted_row[key] = value
                        else:
                            converted_row[key] = value
                    else:
                        # Try to infer type for columns without explicit datatype
                        # If value looks like a number, try to convert
                        if value and value.strip():
                            try:
                                if "." in value:
                                    converted_row[key] = float(value)
                                else:
                                    converted_row[key] = int(value)
                            except ValueError:
                                converted_row[key] = value
                        else:
                            converted_row[key] = value
            row = converted_row
        elif self.datatypes and len(self.datatypes) > 0:
            # Fallback: apply by iteration order
            converted_row = {}
            for i, (key, value) in enumerate(row.items()):
                if i < len(self.datatypes):
                    dtype = self.datatypes[i]
                    converted_row[key] = convert_value(value, dtype)
                else:
                    converted_row[key] = value
            row = converted_row

        # Apply default values if available
        # Default values align with header columns by position
        if self.default_values and len(self.default_values) > 0 and self.header_row:
            header_keys = [col.strip() if col.strip() else f"_col{i}" for i, col in enumerate(self.header_row)]
            non_empty_cols = [i for i, col in enumerate(self.header_row) if col.strip()]

            for i, key in enumerate(header_keys):
                value = row.get(key, "")
                # Apply default if value is empty
                if not value or value == "" or value is None:
                    # Find corresponding default value
                    if len(self.default_values) == len(non_empty_cols) and i in non_empty_cols:
                        default_idx = non_empty_cols.index(i)
                        if default_idx < len(self.default_values):
                            default_val = self.default_values[default_idx]
                            if default_val and default_val != "":
                                # Apply type conversion if datatype available
                                # Apply type conversion if datatype available
                                # Find the datatype for this column
                                dtype = None
                                if len(self.datatypes) == len(non_empty_cols):
                                    if i in non_empty_cols:
                                        dtype_idx = non_empty_cols.index(i)
                                        if dtype_idx < len(self.datatypes):
                                            dtype = self.datatypes[dtype_idx]
                                elif i < len(self.datatypes):
                                    dtype = self.datatypes[i]

                                if dtype:
                                    row[key] = convert_value(default_val, dtype)
                                else:
                                    row[key] = default_val
                    elif i < len(self.default_values):
                        default_val = self.default_values[i]
                        if default_val and default_val != "":
                            row[key] = default_val

        self.pos += 1
        return row

    def write(self, record: Row) -> None:
        """Write single annotated CSV record"""
        # If this is the first write, write annotations
        if self.pos == 0:
            self._write_annotations()

        self.writer.writerow(record)
        self.pos += 1

    def write_bulk(self, records: list[Row]) -> None:
        """Write bulk annotated CSV records"""
        if self.pos == 0:
            self._write_annotations()
        self.writer.writerows(records)
        self.pos += len(records)

    def _write_annotations(self):
        """Write InfluxDB CSV annotations"""
        if not self.keys:
            return

        # Write datatype annotation if available
        if "datatypes" in self.write_options and self.write_options["datatypes"]:
            datatypes = self.write_options["datatypes"]
            if len(datatypes) == len(self.keys):
                row = ["#datatype"] + datatypes
                self.fobj.write(self.delimiter.join(row) + "\n")

        # Write group annotation if available
        if "group" in self.write_options and self.write_options["group"]:
            group_flags = self.write_options["group"]
            if len(group_flags) == len(self.keys):
                row = ["#group"] + ["true" if flag else "false" for flag in group_flags]
                self.fobj.write(self.delimiter.join(row) + "\n")

        # Write default annotation if available
        if "default" in self.write_options and self.write_options["default"]:
            default_values = self.write_options["default"]
            if len(default_values) == len(self.keys):
                row = ["#default"] + [str(v) if v is not None else "" for v in default_values]
                self.fobj.write(self.delimiter.join(row) + "\n")

        # Write header row after annotations (if annotations were written) or if no annotations
        if self.writer:
            self.writer.writeheader()
