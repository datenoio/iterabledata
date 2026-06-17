from __future__ import annotations

import typing
from typing import Any

from ..base import BaseCodec
from ..types import Row
from .ntriples import NTriplesIterable


class NQuadsIterable(NTriplesIterable):
    """
    N-Quads RDF format reader/writer.
    Format: subject predicate object graph .
    One quad per line (N-Triples with graph context).
    """

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
        super().__init__(filename, stream, codec=codec, mode=mode, encoding=encoding, options=options)
        pass

    @staticmethod
    def id() -> str:
        return "nquads"

    def _parse_quad(self, line: str) -> dict:
        """Parse N-Quads line into dictionary"""
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

        # Object and graph might be in remaining parts
        # Graph is optional, so we need to detect it
        if len(parts) >= 4:
            # Has graph
            obj = self._parse_uri_or_literal(" ".join(parts[2:-1]))
            graph = self._parse_uri_or_literal(parts[-1])
        else:
            # No graph
            obj = self._parse_uri_or_literal(" ".join(parts[2:]))
            graph = None

        result = {
            "subject": subject.get("value", parts[0]),
            "subject_type": subject.get("type", "unknown"),
            "predicate": predicate.get("value", parts[1]),
            "predicate_type": predicate.get("type", "unknown"),
            "object": obj.get("value", " ".join(parts[2:-1] if len(parts) >= 4 else parts[2:])),
            "object_type": obj.get("type", "unknown"),
            "object_datatype": obj.get("datatype"),
            "object_language": obj.get("language"),
        }

        if graph:
            result["graph"] = graph.get("value", parts[-1] if len(parts) >= 4 else None)
            result["graph_type"] = graph.get("type", "unknown")

        return result

    def read(self, skip_empty: bool = True) -> dict:
        """Read single N-Quads record"""
        while True:
            line = self.fobj.readline()
            if not line:
                raise StopIteration

            line = line.strip()
            if skip_empty and len(line) == 0:
                continue

            result = self._parse_quad(line)
            if result is None:
                continue

            self.pos += 1
            return result

    def write(self, record: Row) -> None:
        """Write single N-Quads record"""
        subject = record.get("subject", record.get("subject_value", ""))
        subject_type = record.get("subject_type", "uri")
        predicate = record.get("predicate", record.get("predicate_value", ""))
        predicate_type = record.get("predicate_type", "uri")
        obj = record.get("object", record.get("object_value", ""))
        obj_type = record.get("object_type", "literal")
        obj_datatype = record.get("object_datatype")
        obj_language = record.get("object_language")
        graph = record.get("graph")
        graph_type = record.get("graph_type", "uri")

        subject_str = self._format_uri_or_literal(subject, subject_type)
        predicate_str = self._format_uri_or_literal(predicate, predicate_type)
        object_str = self._format_uri_or_literal(obj, obj_type, obj_datatype, obj_language)

        if graph:
            graph_str = self._format_uri_or_literal(graph, graph_type)
            line = f"{subject_str} {predicate_str} {object_str} {graph_str} .\n"
        else:
            line = f"{subject_str} {predicate_str} {object_str} .\n"

        self.fobj.write(line)
