"""GEXF format support using NetworkX."""

from __future__ import annotations

import typing

try:
    import networkx as nx

    HAS_NETWORKX = True
except ImportError:
    nx = None  # type: ignore[assignment]
    HAS_NETWORKX = False

from ..base import BaseCodec, BaseFileIterable
from ..types import Row
from ._shared import graph_to_records


class GEXFIterable(BaseFileIterable):
    """GEXF format: yields node records then edge records (id/source/target + attributes)."""

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
        if not HAS_NETWORKX:
            raise ImportError(
                "GEXF support requires 'networkx'. Install with: pip install iterabledata[graph]"
            ) from None
        super().__init__(filename, stream, codec=codec, binary=False, mode=mode, options=options)
        self._records: list[Row] = []
        self._iterator = None
        self.pos = 0
        self.reset()

    def reset(self) -> None:
        """Reset and (re)load graph."""
        super().reset()
        self.pos = 0
        if self.mode == "r":
            if self.fobj is not None:
                G = nx.read_gexf(self.fobj)
            elif self.filename is not None:
                G = nx.read_gexf(self.filename)
            else:
                G = nx.Graph()
            self._records = graph_to_records(G)
            self._iterator = iter(self._records)
        else:
            self._records = []
            self._iterator = iter([])

    @staticmethod
    def id() -> str:
        return "gexf"

    @staticmethod
    def is_flatonly() -> bool:
        return False

    def read(self, skip_empty: bool = True) -> Row:
        """Read single node or edge record."""
        try:
            row = next(self._iterator)
            self.pos += 1
            return row
        except (StopIteration, EOFError, ValueError):
            raise StopIteration from None
