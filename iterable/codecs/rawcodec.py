from __future__ import annotations

import io
import typing

from ..base import BaseCodec


class RAWCodec(BaseCodec):
    def __init__(self, filename: str, mode: str = "r", open_it: bool = False, options: dict = None):
        if options is None:
            options = {}
        super().__init__(filename, mode=mode, open_it=open_it, options=options)

    def open(self) -> typing.IO:
        # RAW is a passthrough codec; open using the requested mode.
        self._fileobj = open(self.filename, self.mode)
        return self._fileobj

    def textIO(self, encoding: str = "utf8"):
        """
        Return a text wrapper over the underlying stream.

        RAWCodec may already open files in text mode; in that case, avoid wrapping
        a TextIO object with another TextIOWrapper (which breaks reads).
        """
        fobj = self.fileobj()
        if isinstance(fobj, io.TextIOBase):
            return fobj
        return io.TextIOWrapper(fobj, encoding=encoding, write_through=False)

    def close(self):
        if self._fileobj is not None:
            self._fileobj.close()
            self._fileobj = None

    @staticmethod
    def id():
        return "raw"

    @staticmethod
    def fileexts() -> list[str]:
        return []
