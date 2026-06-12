from __future__ import annotations

import bz2
from typing import Any

from ..base import BaseCodec


class BZIP2Codec(BaseCodec):
    def __init__(
        self,
        filename: str | None = None,
        fileobj: Any = None,
        compression_level: int = 5,
        mode: str = "r",
        open_it: bool = False,
        options: dict | None = None,
    ):
        if options is None:
            options = {}
        self.compression_level = compression_level
        super().__init__(filename=filename, fileobj=fileobj, mode=mode, open_it=open_it, options=options)

    def open(self) -> bz2.BZ2File:
        # Prefer _original_fileobj on reset (after close() set _fileobj=None)
        original = getattr(self, "_original_fileobj", None)
        if original is not None:
            self._fileobj = bz2.BZ2File(original, mode=self.mode, compresslevel=self.compression_level)
            return self._fileobj
        # If fileobj was provided (e.g., from cloud storage), wrap it with BZ2File
        if self._fileobj is not None and not isinstance(self._fileobj, bz2.BZ2File):
            if not hasattr(self, "_original_fileobj"):
                self._original_fileobj = self._fileobj
            self._fileobj = bz2.BZ2File(self._original_fileobj, mode=self.mode, compresslevel=self.compression_level)
        elif self.filename is not None:
            self._fileobj = bz2.open(self.filename, self.mode, compresslevel=self.compression_level)
        else:
            raise ValueError("BZIP2Codec requires either filename or fileobj")
        return self._fileobj

    def close(self) -> None:
        if self._fileobj is not None:
            self._fileobj.close()
            self._fileobj = None

    @staticmethod
    def fileexts() -> list[str]:
        return [
            "bz2",
        ]
