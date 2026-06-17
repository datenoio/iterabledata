from __future__ import annotations

import csv
import json
import logging
import os
import typing
from typing import Any

from ..base import BaseCodec, BaseFileIterable
from ..helpers.utils import rowincount
from ..types import Row

DEFAULT_ENCODING = "utf8"
DEFAULT_DELIMITER = ","


class CSVWIterable(BaseFileIterable):
    """CSV on the Web (CSVW) iterable - CSV with JSON-LD metadata"""

    def __init__(
        self,
        filename: str | None = None,
        stream: typing.IO[Any] | None = None,
        codec: BaseCodec | None = None,
        metadata_file: str | None = None,
        delimiter: str | None = None,
        quotechar: str = '"',
        mode: str = "r",
        encoding: str | None = None,
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

        super().__init__(
            filename, stream, codec=codec, binary=False, encoding=self.encoding, mode=mode, options=options
        )

        if not delimiter:
            self.delimiter = DEFAULT_DELIMITER
        else:
            self.delimiter = delimiter
        self.quotechar = quotechar

        # Metadata handling
        self.metadata_file = metadata_file
        if "metadata_file" in options:
            self.metadata_file = options["metadata_file"]

        # If no metadata file specified, try to find it
        if self.metadata_file is None and filename:
            # CSVW convention: metadata file is CSV filename with .csv-metadata.json extension
            base = filename.rsplit(".", 1)[0]
            metadata_candidates = [base + "-metadata.json", base + ".csv-metadata.json", base + ".json"]
            for candidate in metadata_candidates:
                if os.path.exists(candidate):
                    self.metadata_file = candidate
                    break

        self.metadata = {}
        self.schema = {}
        self.columns = []

        logging.debug(f"Detected delimiter {self.delimiter}")
        self.reset()

    def _load_metadata(self):
        """Load CSVW metadata from JSON file"""
        if not self.metadata_file or not os.path.exists(self.metadata_file):
            return

        try:
            with open(self.metadata_file, encoding="utf-8") as f:
                self.metadata = json.load(f)

            # Extract table schema
            if "@context" in self.metadata:
                # This is a CSVW metadata file
                if "tableSchema" in self.metadata:
                    self.schema = self.metadata["tableSchema"]
                elif "tables" in self.metadata and len(self.metadata["tables"]) > 0:
                    # Multiple tables - use first one
                    table = self.metadata["tables"][0]
                    if "tableSchema" in table:
                        self.schema = table["tableSchema"]

                # Extract columns
                if "columns" in self.schema:
                    self.columns = self.schema["columns"]

                # Extract delimiter from dialect if present
                if "dialect" in self.metadata:
                    dialect = self.metadata["dialect"]
                    if "delimiter" in dialect:
                        self.delimiter = dialect["delimiter"]
                    if "encoding" in dialect:
                        self.encoding = dialect["encoding"]
        except Exception as e:
            logging.warning(f"Failed to load CSVW metadata: {e}")
            self.metadata = {}
            self.schema = {}
            self.columns = []

    @staticmethod
    def has_totals() -> bool:
        """Has totals indicator"""
        return True

    def totals(self):
        """Returns file totals"""
        # CSVW totals should include header row (+1)
        total = rowincount(self.filename, self.fobj)
        return total + 1 if total > 0 else 1

    def reset(self):
        """Reset iterable"""
        super().reset()

        if self.fobj is None and self.codec is not None:
            fobj = self.codec.textIO(self.encoding)
        else:
            fobj = self.fobj

        self.reader = None
        self.writer = None
        self.pos = 0

        if self.mode == "r":
            # Load metadata
            self._load_metadata()

            # Create CSV reader - use CSV headers, not metadata fieldnames
            # The CSV file has its own headers which should be used
            self.reader = csv.DictReader(fobj, delimiter=self.delimiter, quotechar=self.quotechar)
        elif self.mode in ["w", "wr"]:
            # Load metadata for writing
            self._load_metadata()

            # Determine fieldnames from metadata or options
            # Options are set as attributes in base class, check for 'keys' attribute
            if hasattr(self, "keys") and self.keys:
                pass  # Already set
            elif hasattr(self, "options") and self.options and "keys" in self.options:
                self.keys = self.options["keys"]
            elif self.columns:
                self.keys = []
                for col in self.columns:
                    if "titles" in col and len(col["titles"]) > 0:
                        self.keys.append(col["titles"][0])
                    elif "name" in col:
                        self.keys.append(col["name"])
            else:
                self.keys = None

            if self.keys:
                self.writer = csv.DictWriter(
                    fobj, fieldnames=self.keys, delimiter=self.delimiter, quotechar=self.quotechar
                )
                self.writer.writeheader()
            else:
                self.writer = None

    @staticmethod
    def id() -> str:
        return "csvw"

    @staticmethod
    def is_flatonly() -> bool:
        return True

    def read(self, skip_empty: bool = True) -> dict:
        """Read single CSVW record"""
        row = next(self.reader)

        if skip_empty and len(row) == 0:
            return self.read(skip_empty)

        # Apply type conversions based on metadata
        if self.columns:
            converted_row = {}
            for i, (key, value) in enumerate(row.items()):
                if i < len(self.columns):
                    col_meta = self.columns[i]
                    # Get datatype from metadata
                    datatype = col_meta.get("datatype", {}).get("base", "string")

                    # Convert value based on datatype
                    if value and value != "":
                        if datatype in ["integer", "int", "long"]:
                            try:
                                converted_row[key] = int(value)
                            except ValueError:
                                converted_row[key] = value
                        elif datatype in ["number", "float", "double", "decimal"]:
                            try:
                                converted_row[key] = float(value)
                            except ValueError:
                                converted_row[key] = value
                        elif datatype == "boolean":
                            converted_row[key] = value.lower() in ("true", "t", "1", "yes")
                        elif datatype.startswith("date") or datatype.startswith("time"):
                            # Keep as string for date/time types
                            converted_row[key] = value
                        else:
                            converted_row[key] = value
                    else:
                        converted_row[key] = None
                else:
                    converted_row[key] = value
            row = converted_row

        self.pos += 1
        return row

    def write(self, record: Row) -> None:
        """Write single CSVW record"""
        if self.writer:
            self.writer.writerow(record)
        else:
            # Fallback to regular CSV writing
            if not hasattr(self, "csv_writer"):
                self.csv_writer = csv.DictWriter(
                    self.fobj, fieldnames=record.keys(), delimiter=self.delimiter, quotechar=self.quotechar
                )
                self.csv_writer.writeheader()
            self.csv_writer.writerow(record)
        self.pos += 1

    def write_bulk(self, records: list[Row]) -> None:
        """Write bulk CSVW records"""
        if self.writer:
            self.writer.writerows(records)
        else:
            if not hasattr(self, "csv_writer"):
                if records:
                    self.csv_writer = csv.DictWriter(
                        self.fobj, fieldnames=records[0].keys(), delimiter=self.delimiter, quotechar=self.quotechar
                    )
                    self.csv_writer.writeheader()
            if hasattr(self, "csv_writer"):
                self.csv_writer.writerows(records)
        self.pos += len(records)
