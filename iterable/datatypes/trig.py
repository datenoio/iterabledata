"""TriG (RDF Triple Graph) format support using rdflib."""

from __future__ import annotations

import typing

try:
    from rdflib import ConjunctiveGraph

    HAS_RDFLIB = True
except ImportError:
    ConjunctiveGraph = None  # type: ignore[misc, assignment]
    HAS_RDFLIB = False

from ..base import BaseCodec, BaseFileIterable
from ..types import Row
from ._shared import rdf_term_to_str


class TriGIterable(BaseFileIterable):
    """TriG RDF format: yields one record per quad (subject, predicate, object, graph)."""

    datamode = "text"

    def __init__(
        self,
        filename: str | None = None,
        stream: typing.IO[typing.Any] | None = None,
        codec: BaseCodec | None = None,
        mode: str = "r",
        options: dict[str, typing.Any] | None = None,
    ):
        if options is None:
            options = {}
        if not HAS_RDFLIB:
            raise ImportError("TriG support requires 'rdflib'. Install with: pip install iterabledata[rdf]") from None
        super().__init__(filename, stream, codec=codec, binary=False, mode=mode, options=options)
        self.graph = None
        self.iterator = None
        self.pos = 0
        self.reset()

    def reset(self) -> None:
        """Reset iterable and (re)load graph."""
        super().reset()
        self.pos = 0
        if self.mode == "r":
            self.graph = ConjunctiveGraph()
            if self.fobj is not None:
                content = self.fobj.read()
                self.graph.parse(data=content, format="trig")
            elif self.filename is not None:
                self.graph.parse(self.filename, format="trig")
            quads = []
            for quad in self.graph.quads():
                s, p, o, g = quad
                quads.append(
                    {
                        "subject": rdf_term_to_str(s),
                        "predicate": rdf_term_to_str(p),
                        "object": rdf_term_to_str(o),
                        "graph": rdf_term_to_str(g),
                    }
                )
            self.iterator = iter(quads)
        else:
            self.graph = ConjunctiveGraph()

    @staticmethod
    def id() -> str:
        return "trig"

    @staticmethod
    def is_flatonly() -> bool:
        return True

    def read(self, skip_empty: bool = True) -> Row:
        """Read single quad record."""
        try:
            row = next(self.iterator)
            self.pos += 1
            return row
        except (StopIteration, EOFError, ValueError):
            raise StopIteration from None
