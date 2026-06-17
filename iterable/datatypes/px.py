from __future__ import annotations

import re
import typing
from itertools import product
from typing import Any

from ..base import DEFAULT_BULK_NUMBER, BaseCodec, BaseFileIterable
from ..exceptions import WriteNotSupportedError
from ..types import Row

DEFAULT_ENCODING = "utf8"


class PXIterable(BaseFileIterable):
    """PC-Axis (PX) file format reader"""

    def __init__(
        self,
        filename: str | None = None,
        stream: typing.IO[Any] | None = None,
        codec: BaseCodec | None = None,
        mode: str = "r",
        encoding: str | None = None,
        options: dict[str, Any] | None = None,
    ):
        if options is None:
            options = {}
        self.encoding = encoding or options.get("encoding", DEFAULT_ENCODING)
        super().__init__(
            filename, stream, codec=codec, binary=False, encoding=self.encoding, mode=mode, options=options
        )
        self.metadata = {}
        self.stub_vars = []
        self.heading_vars = []
        self.values = {}
        self.codes = {}
        self.data_values = []
        self.reset()

    def _parse_metadata_line(self, line: str) -> tuple[str, str]:
        """Parse a metadata line like KEY="value"; or KEY=value;"""
        line = line.strip()
        if not line or line.startswith("#"):
            return None, None

        # Remove trailing semicolon
        if line.endswith(";"):
            line = line[:-1]

        # Split on first =
        if "=" not in line:
            return None, None

        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip()

        # Remove outer quotes only if it's a single quoted scalar (not a quoted list like `"a" "b"`).
        if value.startswith('"') and value.endswith('"') and value.count('"') == 2:
            value = value[1:-1]

        return key.upper(), value

    def _parse_list_value(self, value: str) -> list[str]:
        """Parse a quoted list like "value1" "value2" "value3" """
        # Extract all quoted strings
        matches = re.findall(r'"([^"]*)"', value)
        return matches if matches else [value.strip()]

    def _parse_metadata(self, content: str):
        """Parse PC-Axis metadata section"""
        lines = content.split("\n")
        data_start_idx = 0

        for i, line in enumerate(lines):
            line = line.strip()

            # Check for DATA= marker
            if line.upper().startswith("DATA="):
                data_start_idx = i + 1
                # Handle DATA= on same line
                if "=" in line:
                    key, value = self._parse_metadata_line(line)
                    if key == "DATA":
                        # Data might start on same line
                        if value and value.strip():
                            data_start_idx = i
                break

            # Parse metadata line
            key, value = self._parse_metadata_line(line)
            if key:
                if key == "STUB":
                    self.stub_vars = self._parse_list_value(value)
                elif key == "HEADING":
                    self.heading_vars = self._parse_list_value(value)
                elif key.startswith("VALUES("):
                    # Extract variable name from VALUES("VarName")
                    var_match = re.search(r'VALUES\("([^"]+)"\)', line)
                    if var_match:
                        var_name = var_match.group(1)
                        self.values[var_name] = self._parse_list_value(value)
                elif key.startswith("CODES("):
                    # Extract variable name from CODES("VarName")
                    var_match = re.search(r'CODES\("([^"]+)"\)', line)
                    if var_match:
                        var_name = var_match.group(1)
                        self.codes[var_name] = self._parse_list_value(value)
                else:
                    self.metadata[key] = value

        return data_start_idx

    def _parse_data_section(self, content: str, start_idx: int):
        """Parse PC-Axis data section"""
        lines = content.split("\n")
        data_lines = lines[start_idx:]

        # Combine all data lines and split by whitespace
        data_text = " ".join(data_lines)
        # Remove trailing semicolon if present
        data_text = data_text.rstrip(";").strip()

        # Split by whitespace and filter empty strings
        values = [v for v in data_text.split() if v]

        # Try to convert to numbers
        self.data_values = []
        for v in values:
            try:
                # Try integer first
                if "." not in v:
                    self.data_values.append(int(v))
                else:
                    self.data_values.append(float(v))
            except ValueError:
                # Keep as string if conversion fails
                self.data_values.append(v)

    def _generate_records(self):
        """Generate flat records from multi-dimensional PC-Axis data"""
        records = []

        # Get all variable names in order
        self.stub_vars + self.heading_vars

        # Calculate dimensions
        stub_dims = [len(self.values.get(var, [])) for var in self.stub_vars]
        heading_dims = [len(self.values.get(var, [])) for var in self.heading_vars]

        # Total number of data points
        total_stub_combinations = 1
        for dim in stub_dims:
            total_stub_combinations *= dim if dim > 0 else 1

        total_heading_combinations = 1
        for dim in heading_dims:
            total_heading_combinations *= dim if dim > 0 else 1

        total_stub_combinations * total_heading_combinations

        # Generate all combinations of stub variables
        stub_value_lists = [self.values.get(var, [""]) for var in self.stub_vars]
        heading_value_lists = [self.values.get(var, [""]) for var in self.heading_vars]

        # Use empty list placeholder for missing values to avoid product errors
        stub_value_lists = [lst if lst else [""] for lst in stub_value_lists]
        heading_value_lists = [lst if lst else [""] for lst in heading_value_lists]

        stub_combinations = list(product(*stub_value_lists)) if stub_value_lists else [()]
        heading_combinations = list(product(*heading_value_lists)) if heading_value_lists else [()]

        # Create records
        data_idx = 0
        for stub_combo in stub_combinations:
            for heading_combo in heading_combinations:
                record = {}

                # Add stub variables
                for i, var in enumerate(self.stub_vars):
                    if i < len(stub_combo):
                        val = stub_combo[i]
                        record[var] = val if val != "" else None
                    else:
                        record[var] = None

                # Add heading variables
                for i, var in enumerate(self.heading_vars):
                    if i < len(heading_combo):
                        val = heading_combo[i]
                        record[var] = val if val != "" else None
                    else:
                        record[var] = None

                # Add data value
                if data_idx < len(self.data_values):
                    record["VALUE"] = self.data_values[data_idx]
                else:
                    record["VALUE"] = None

                # Add metadata fields
                for key, value in self.metadata.items():
                    if key not in ["STUB", "HEADING"]:
                        record[f"_{key}"] = value

                records.append(record)
                data_idx += 1

        return records

    def reset(self):
        """Reset iterable"""
        super().reset()
        self.pos = 0

        if self.mode == "r":
            # Read entire file content
            content = self.fobj.read()

            # Parse metadata and find data section
            data_start_idx = self._parse_metadata(content)

            # Parse data section
            self._parse_data_section(content, data_start_idx)

            # Generate flat records
            self.records = self._generate_records()
            self.iterator = iter(self.records)
        else:
            self.records = []
            raise WriteNotSupportedError("px", "PC-Axis file writing is not yet implemented")

    @staticmethod
    def id() -> str:
        return "px"

    @staticmethod
    def is_flatonly() -> bool:
        return True

    @staticmethod
    def has_totals() -> bool:
        """Has totals indicator"""
        return True

    def totals(self):
        """Returns file totals"""
        if hasattr(self, "records"):
            return len(self.records)
        return 0

    def read(self, skip_empty: bool = True) -> dict:
        """Read single PC-Axis record"""
        try:
            row = next(self.iterator)
            self.pos += 1
            return row
        except StopIteration:
            raise StopIteration from None

    def read_bulk(self, num: int = DEFAULT_BULK_NUMBER) -> list[dict]:
        """Read bulk PC-Axis records"""
        chunk = []
        for _n in range(0, num):
            try:
                chunk.append(self.read(skip_empty=False))
            except StopIteration:
                break
        return chunk

    def write(self, record: Row) -> None:
        """Write single PC-Axis record - not supported"""
        raise WriteNotSupportedError("px", "PC-Axis file writing is not yet implemented")

    def write_bulk(self, records: list[Row]) -> None:
        """Write bulk PC-Axis records - not supported"""
        raise WriteNotSupportedError("px", "PC-Axis file writing is not yet implemented")
