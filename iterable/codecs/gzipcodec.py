from __future__ import annotations

import gzip
from typing import IO, Any

from ..base import BaseCodec
from ._stream import get_underlying_fileobj


class GZIPCodec(BaseCodec):
    def __init__(
        self,
        filename: str | None = None,
        fileobj: IO[Any] | None = None,
        compression_level: int = 5,
        mode: str = "r",
        open_it: bool = False,
        options: dict | None = None,
    ):
        if options is None:
            options = {}
        self.compression_level = compression_level
        super().__init__(filename=filename, fileobj=fileobj, mode=mode, open_it=open_it, options=options)

    def open(self) -> gzip.GzipFile:
        underlying = get_underlying_fileobj(self, gzip.GzipFile)
        if underlying is not None:
            self._fileobj = gzip.GzipFile(fileobj=underlying, mode=self.mode, compresslevel=self.compression_level)
        elif self.filename is not None:
            self._fileobj = gzip.GzipFile(filename=self.filename, mode=self.mode, compresslevel=self.compression_level)
        else:
            raise ValueError("GZIPCodec requires either filename or fileobj")
        return self._fileobj

    def close(self) -> None:
        if self._fileobj is not None:
            self._fileobj.close()
            self._fileobj = None

    @staticmethod
    def id():
        return "gzip"

    @staticmethod
    def fileexts() -> list[str]:
        return [
            "gz",
        ]
