from __future__ import annotations

import typing

try:
    from rdflib import BNode, Graph, Literal, URIRef
    from rdflib.namespace import RDF  # noqa: F401

    HAS_RDFLIB = True
except ImportError:
    HAS_RDFLIB = False

from typing import Any

from ..base import BaseCodec, BaseFileIterable
from ..types import Row


class TurtleIterable(BaseFileIterable):
    datamode = "text"

    def __init__(
        self,
        filename: str = None,
        stream: typing.IO[Any] | None = None,
        codec: BaseCodec | None = None,
        mode: str = "r",
        subject: str = None,
        predicate: str = None,
        options: dict[str, Any] | None = None,
    ):
        if options is None:
            options = {}
        if not HAS_RDFLIB:
            raise ImportError("RDF/Turtle support requires 'rdflib' package")
        super().__init__(filename, stream, codec=codec, binary=False, mode=mode, options=options)
        self.subject = subject
        self.predicate = predicate
        if "subject" in options:
            self.subject = options["subject"]
        if "predicate" in options:
            self.predicate = options["predicate"]
        self.graph = None
        self.reset()
        pass

    def reset(self):
        """Reset iterable"""
        super().reset()
        self.pos = 0

        if self.mode == "r":
            # Load RDF graph
            self.graph = Graph()
            if self.fobj is not None:
                # Read from file object
                content = self.fobj.read()
                self.graph.parse(data=content, format="turtle")
            elif self.filename is not None:
                self.graph.parse(self.filename, format="turtle")

            # Convert triples to dict records
            # Each record represents a subject with its properties
            subjects = {}
            for s, p, o in self.graph:
                s_str = str(s)
                if s_str not in subjects:
                    subjects[s_str] = {"subject": s_str}
                # Convert predicate to key (use local name if URI)
                p_key = str(p).split("/")[-1].split("#")[-1]
                # Convert object to value
                if isinstance(o, Literal):
                    o_value = str(o)
                else:
                    o_value = str(o)
                subjects[s_str][p_key] = o_value

            self.iterator = iter(list(subjects.values()))
        else:
            # Write mode
            self.graph = Graph()
            self.subjects = {}  # Track subjects we've seen

    @staticmethod
    def id() -> str:
        return "turtle"

    @staticmethod
    def is_flatonly() -> bool:
        return False

    def read(self, skip_empty: bool = True) -> dict:
        """Read single Turtle/RDF record"""
        try:
            row = next(self.iterator)
            self.pos += 1
            return row
        except (StopIteration, EOFError, ValueError):
            raise StopIteration from None

    def write(self, record: Row) -> None:
        """Write single Turtle/RDF record"""
        # Convert dict to RDF triples
        subject_uri = record.get("subject", record.get("@id"))
        if not subject_uri:
            # Generate a blank node
            subject = BNode()
        else:
            subject = URIRef(subject_uri)

        for key, value in record.items():
            if key in ["subject", "@id"]:
                continue
            predicate = URIRef(key)
            if isinstance(value, str) and (value.startswith("http://") or value.startswith("https://")):
                object_ref = URIRef(value)
            else:
                object_ref = Literal(value)
            self.graph.add((subject, predicate, object_ref))

    def write_bulk(self, records: list[Row]) -> None:
        """Write bulk Turtle/RDF records"""
        for record in records:
            self.write(record)

    def close(self):
        """Close and serialize graph if in write mode"""
        if self.mode in ["w", "wr"] and self.graph is not None:
            if self.fobj is not None:
                self.fobj.write(self.graph.serialize(format="turtle"))
            elif self.filename is not None:
                self.graph.serialize(destination=self.filename, format="turtle")
        super().close()
