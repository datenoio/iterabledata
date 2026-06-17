from __future__ import annotations

import typing
from typing import Any

from ..base import BaseCodec, BaseFileIterable
from ..exceptions import FormatParseError, WriteError
from ..helpers.utils import rowincount
from ..types import Row


class LIBSVMIterable(BaseFileIterable):
    """
    LIBSVM format reader/writer.

    LIBSVM format is a sparse data format commonly used in machine learning.
    Each line represents a data point with a label and sparse feature vector:
    <label> <index1>:<value1> <index2>:<value2> ...

    Example:
        1 1:0.5 3:0.8 5:1.0
        -1 2:0.3 4:0.9
        1 1:0.2 3:0.6
    """

    datamode = "text"

    def __init__(
        self,
        filename: str | None = None,
        stream: typing.IO[Any] | None = None,
        codec: BaseCodec | None = None,
        mode: str = "r",
        encoding: str = "utf8",
        label_key: str = "label",
        features_key: str = "features",
        options: dict[str, Any] | None = None,
    ):
        """
        Initialize LIBSVM iterable.

        Args:
            label_key: Key name for the label when reading (default: 'label')
            features_key: Key name for the features dict when reading (default: 'features')
        """
        if options is None:
            options = {}
        self.label_key = label_key
        self.features_key = features_key
        if "label_key" in options:
            self.label_key = options["label_key"]
        if "features_key" in options:
            self.features_key = options["features_key"]
        self.pos = 0
        super().__init__(filename, stream, codec=codec, binary=False, mode=mode, encoding=encoding, options=options)
        self.reset()

    def reset(self):
        """Reset iterable"""
        super().reset()
        self.pos = 0

    @staticmethod
    def id() -> str:
        return "libsvm"

    @staticmethod
    def is_flatonly() -> bool:
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

    def _parse_line(self, line: str) -> dict:
        """
        Parse a single LIBSVM line.

        Args:
            line: LIBSVM format line

        Returns:
            dict: Parsed record with label and features
        """
        line = line.strip()
        if not line:
            return None

        parts = line.split()
        if not parts:
            return None

        # First part is the label
        try:
            label = float(parts[0])
            # Convert to int if it's a whole number
            if label.is_integer():
                label = int(label)
        except ValueError as e:
            raise FormatParseError(
                format_id="libsvm",
                message=f"Invalid label in LIBSVM line: {line}",
                filename=self.filename,
                row_number=self.pos + 1,
                original_line=line,
            ) from e

        # Remaining parts are feature:value pairs
        features = {}
        for part in parts[1:]:
            if ":" not in part:
                raise FormatParseError(
                    format_id="libsvm",
                    message=f"Invalid feature format in LIBSVM line: {line}",
                    filename=self.filename,
                    row_number=self.pos + 1,
                    original_line=line,
                )
            index_str, value_str = part.split(":", 1)
            try:
                index = int(index_str)
                value = float(value_str)
            except ValueError as e:
                raise FormatParseError(
                    format_id="libsvm",
                    message=f"Invalid feature index or value in LIBSVM line: {line}",
                    filename=self.filename,
                    row_number=self.pos + 1,
                    original_line=line,
                ) from e
            features[index] = value

        return {self.label_key: label, self.features_key: features}

    def _format_line(self, record: dict) -> str:
        """
        Format a record as a LIBSVM line.

        Args:
            record: Dictionary with label and features

        Returns:
            str: LIBSVM format line
        """
        # Get label
        label = record.get(self.label_key, record.get("label", 0))

        # Get features
        features = record.get(self.features_key, record.get("features", {}))

        # Format features as index:value pairs, sorted by index
        feature_parts = []
        if isinstance(features, dict):
            for index in sorted(features.keys()):
                value = features[index]
                feature_parts.append(f"{index}:{value}")
        elif isinstance(features, (list, tuple)):
            # If features is a list/tuple, use 1-based indexing
            for i, value in enumerate(features, start=1):
                if value != 0:  # Only include non-zero features (sparse format)
                    feature_parts.append(f"{i}:{value}")
        else:
            raise WriteError(
                f"Features must be dict, list, or tuple, got {type(features)}",
                filename=self.filename,
                error_code="INVALID_PARAMETER",
            )

        # Combine label and features
        line_parts = [str(label)] + feature_parts
        return " ".join(line_parts)

    def read(self, skip_empty: bool = True) -> dict:
        """Read single LIBSVM record"""
        while True:
            line = next(self.fobj)
            if not skip_empty or line.strip():
                break
        parsed = self._parse_line(line)
        if parsed is None:
            raise StopIteration
        self.pos += 1
        return parsed

    def write(self, record: Row) -> None:
        """Write single LIBSVM record"""
        line = self._format_line(record)
        self.fobj.write(line + "\n")
        self.pos += 1

    def write_bulk(self, records: list[Row]) -> None:
        """Write bulk LIBSVM records"""
        if not records:
            return
        # Write all records with minimal I/O
        lines = [self._format_line(record) for record in records]
        self.fobj.write("\n".join(lines) + "\n")
        self.pos += len(records)
