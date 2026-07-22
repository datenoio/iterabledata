"""HDT (Header Dictionary Triples) RDF reader.

Uses the optional ``hdt`` package to stream triples as::

    {"subject": "...", "predicate": "...", "object": "..."}

Install with::

    pip install hdt

Read-only. Format id: ``hdt``.
"""

from __future__ import annotations

import typing
from typing import Any

from ..base import BaseCodec, BaseFileIterable
from ..exceptions import ReadError, WriteNotSupportedError
from ..types import Row

try:
    from hdt import HDTDocument  # type: ignore[import-untyped]

    HAS_HDT = True
except ImportError:
    HAS_HDT = False

_IMPORT_ERROR = "HDT support requires the 'hdt' package. Install with: pip install hdt"


class HDTIterable(BaseFileIterable):
    """Read-only HDT triple iterable."""

    datamode = "binary"

    def __init__(
        self,
        filename: str | None = None,
        stream: typing.IO[Any] | None = None,
        codec: BaseCodec | None = None,
        mode: str = "r",
        options: dict[str, Any] | None = None,
    ):
        if options is None:
            options = {}
        if not HAS_HDT:
            raise ImportError(_IMPORT_ERROR)
        if mode not in ("r", "rb"):
            raise WriteNotSupportedError("hdt", "HDT is read-only")
        if filename is None:
            raise ReadError(
                "HDT reading requires a filename",
                filename=None,
                error_code="RESOURCE_REQUIREMENT_NOT_MET",
            )
        if stream is not None or codec is not None:
            raise ReadError(
                "HDT reading requires a filename, not a stream or codec",
                filename=None,
                error_code="RESOURCE_REQUIREMENT_NOT_MET",
            )
        self._subject = options.pop("subject", "")
        self._predicate = options.pop("predicate", "")
        self._object = options.pop("object", "")
        super().__init__(
            filename=filename,
            stream=None,
            codec=None,
            binary=True,
            mode="r",
            noopen=True,
            options=options,
        )
        self._doc: Any = None
        self._iterator: typing.Iterator[Any] | None = None
        self.reset()

    @staticmethod
    def id() -> str:
        return "hdt"

    @staticmethod
    def is_flatonly() -> bool:
        return True

    def is_streaming(self) -> bool:
        return True

    def reset(self) -> None:
        self.pos = 0
        assert self.filename is not None
        if self._doc is not None:
            try:
                self._doc = None
            except Exception:
                pass
        self._doc = HDTDocument(self.filename)
        # search returns (triples_iterator, cardinality)
        result = self._doc.search_triples(self._subject, self._predicate, self._object)
        if isinstance(result, tuple) and len(result) >= 1:
            self._iterator = iter(result[0])
        else:
            self._iterator = iter(result)

    def read(self, skip_empty: bool = True) -> Row:
        if self._iterator is None:
            raise StopIteration
        triple = next(self._iterator)
        self.pos += 1
        if isinstance(triple, (tuple, list)) and len(triple) >= 3:
            s, p, o = triple[0], triple[1], triple[2]
        else:
            s = getattr(triple, "subject", None) or str(triple)
            p = getattr(triple, "predicate", "")
            o = getattr(triple, "object", "")
        return {"subject": s, "predicate": p, "object": o}

    def close(self) -> None:
        if getattr(self, "_closed", False):
            return
        self._doc = None
        self._iterator = None
        super().close()

    def write(self, record: Row) -> None:
        raise WriteNotSupportedError("hdt", "HDT is read-only")

    def write_bulk(self, records: list[Row]) -> None:
        raise WriteNotSupportedError("hdt", "HDT is read-only")
