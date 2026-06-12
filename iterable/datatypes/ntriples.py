from __future__ import annotations

import typing
from typing import Any

from ..base import BaseCodec, BaseFileIterable
from ..helpers.utils import rowincount
from ..types import Row


class NTriplesIterable(BaseFileIterable):
    """
    N-Triples RDF format reader/writer.
    Format: subject predicate object .
    One triple per line.
    """

    datamode = "text"

    def __init__(
        self,
        filename: str = None,
        stream: typing.IO[Any] | None = None,
        codec: BaseCodec | None = None,
        mode: str = "r",
        encoding: str = "utf8",
        options: dict[str, Any] | None = None,
    ):
        if options is None:
            options = {}
        super().__init__(filename, stream, codec=codec, binary=False, mode=mode, encoding=encoding, options=options)
        self.reset()
        pass

    def reset(self):
        """Reset iterable"""
        super().reset()
        self.pos = 0

    @staticmethod
    def id() -> str:
        return "ntriples"

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

    def _parse_uri_or_literal(self, s: str) -> dict:
        """Parse URI or literal from N-Triples format"""
        s = s.strip()

        if s.startswith("<") and s.endswith(">"):
            # URI reference
            return {"type": "uri", "value": s[1:-1]}
        elif s.startswith('"'):
            # Literal
            # Handle escaped quotes and find the end
            end_quote = -1
            i = 1
            while i < len(s):
                if s[i] == '"' and (i == 0 or s[i - 1] != "\\"):
                    end_quote = i
                    break
                i += 1

            if end_quote == -1:
                return {"type": "literal", "value": s[1:], "datatype": None, "language": None}

            value = s[1:end_quote].replace('\\"', '"').replace("\\n", "\n").replace("\\r", "\r").replace("\\t", "\t")
            rest = s[end_quote + 1 :].strip()

            if rest.startswith("^^<"):
                # Has datatype
                datatype_end = rest.index(">", 3)
                datatype = rest[3:datatype_end]
                return {"type": "literal", "value": value, "datatype": datatype, "language": None}
            elif rest.startswith("@"):
                # Has language tag
                language = rest[1:].strip()
                return {"type": "literal", "value": value, "datatype": None, "language": language}
            else:
                return {"type": "literal", "value": value, "datatype": None, "language": None}
        else:
            # Blank node
            if s.startswith("_:"):
                return {"type": "bnode", "value": s}
            else:
                return {"type": "unknown", "value": s}

    def _parse_triple(self, line: str) -> dict:
        """Parse N-Triples line into dictionary"""
        line = line.strip()

        # Skip comments and empty lines
        if not line or line.startswith("#"):
            return None

        # Remove trailing period
        if line.endswith("."):
            line = line[:-1].strip()

        # Split by whitespace, but handle quoted strings
        parts = []
        current = ""
        in_quotes = False
        escape_next = False

        for char in line:
            if escape_next:
                current += char
                escape_next = False
            elif char == "\\":
                escape_next = True
                current += char
            elif char == '"' and not escape_next:
                in_quotes = not in_quotes
                current += char
            elif char in [" ", "\t"] and not in_quotes:
                if current.strip():
                    parts.append(current.strip())
                    current = ""
            else:
                current += char

        if current.strip():
            parts.append(current.strip())

        if len(parts) < 3:
            return {"raw_line": line}

        subject = self._parse_uri_or_literal(parts[0])
        predicate = self._parse_uri_or_literal(parts[1])
        obj = self._parse_uri_or_literal(" ".join(parts[2:]))  # Object might contain spaces

        return {
            "subject": subject.get("value", parts[0]),
            "subject_type": subject.get("type", "unknown"),
            "predicate": predicate.get("value", parts[1]),
            "predicate_type": predicate.get("type", "unknown"),
            "object": obj.get("value", " ".join(parts[2:])),
            "object_type": obj.get("type", "unknown"),
            "object_datatype": obj.get("datatype"),
            "object_language": obj.get("language"),
        }

    def read(self, skip_empty: bool = True) -> dict:
        """Read single N-Triples record"""
        while True:
            line = self.fobj.readline()
            if not line:
                raise StopIteration

            line = line.strip()
            if skip_empty and len(line) == 0:
                continue

            result = self._parse_triple(line)
            if result is None:
                continue

            self.pos += 1
            return result

    def _format_uri_or_literal(
        self, value: str, value_type: str = None, datatype: str = None, language: str = None
    ) -> str:
        """Format URI or literal for N-Triples output"""
        if value_type == "uri" or (
            value_type is None
            and (value.startswith("http://") or value.startswith("https://") or value.startswith("urn:"))
        ):
            if not value.startswith("<") and not value.endswith(">"):
                return f"<{value}>"
            return value
        elif value_type == "bnode" or (value_type is None and value.startswith("_:")):
            return value
        else:
            # Literal
            escaped_value = (
                value.replace("\\", "\\\\")
                .replace('"', '\\"')
                .replace("\n", "\\n")
                .replace("\r", "\\r")
                .replace("\t", "\\t")
            )
            if datatype:
                return f'"{escaped_value}"^^<{datatype}>'
            elif language:
                return f'"{escaped_value}"@{language}'
            else:
                return f'"{escaped_value}"'

    def write(self, record: Row) -> None:
        """Write single N-Triples record"""
        subject = record.get("subject", record.get("subject_value", ""))
        subject_type = record.get("subject_type", "uri")
        predicate = record.get("predicate", record.get("predicate_value", ""))
        predicate_type = record.get("predicate_type", "uri")
        obj = record.get("object", record.get("object_value", ""))
        obj_type = record.get("object_type", "literal")
        obj_datatype = record.get("object_datatype")
        obj_language = record.get("object_language")

        subject_str = self._format_uri_or_literal(subject, subject_type)
        predicate_str = self._format_uri_or_literal(predicate, predicate_type)
        object_str = self._format_uri_or_literal(obj, obj_type, obj_datatype, obj_language)

        line = f"{subject_str} {predicate_str} {object_str} .\n"
        self.fobj.write(line)

    def write_bulk(self, records: list[Row]) -> None:
        """Write bulk N-Triples records"""
        for record in records:
            self.write(record)
