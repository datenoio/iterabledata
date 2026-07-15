from __future__ import annotations

import datetime
import pickle
import typing
import warnings
from typing import Any

from ..base import DEFAULT_BULK_NUMBER, BaseCodec, BaseFileIterable
from ..types import Row


def date_handler(obj):
    return obj.isoformat() if isinstance(obj, (datetime.datetime, datetime.date)) else None


class PickleIterable(BaseFileIterable):
    """Python pickle reader/writer.

    .. warning:: **Never open pickle files from untrusted sources.**
       Unpickling executes arbitrary code embedded in the file
       (``pickle.load`` is inherently unsafe by design; see the ``pickle``
       module documentation). Only use this format for data you produced
       yourself or received from a fully trusted party. For untrusted data
       interchange prefer JSON Lines, CSV, or Parquet.

    Pass ``trust=True`` in options to acknowledge this risk explicitly and
    suppress the warning emitted when opening a pickle source for reading::

        open_iterable("data.pickle", iterableargs={"trust": True})
    """

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
        trusted = bool(options.pop("trust", False))
        super().__init__(filename, stream, codec=codec, binary=True, mode=mode, options=options)
        if mode == "r" and not trusted:
            warnings.warn(
                "Loading pickle data executes arbitrary code embedded in the file; "
                "only open pickle sources you fully trust. Pass trust=True in "
                "iterableargs to acknowledge this and silence the warning.",
                UserWarning,
                stacklevel=2,
            )
        self.pos = 0
        pass

    @staticmethod
    def id() -> str:
        return "pickle"

    @staticmethod
    def is_flatonly() -> bool:
        return False

    def read(self, skip_empty: bool = True) -> dict:
        """Read single record"""
        try:
            # Documented trust requirement: see class docstring. Pickle is
            # only safe for data produced by a trusted party.
            return pickle.load(self.fobj)  # nosec B301
        except EOFError:
            raise StopIteration from None

    def read_bulk(self, num: int = DEFAULT_BULK_NUMBER) -> list[dict]:
        """Read bulk records"""
        chunk: list[dict] = []
        for _ in range(num):
            try:
                chunk.append(pickle.load(self.fobj))  # nosec B301
            except EOFError:
                break
        return chunk

    def write(self, record: Row) -> None:
        """Write single record into file"""
        pickle.dump(record, self.fobj)

    def write_bulk(self, records: list[Row]) -> None:
        """Write bulk records"""
        for record in records:
            pickle.dump(record, self.fobj)
