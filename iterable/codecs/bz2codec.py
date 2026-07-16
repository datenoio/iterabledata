from __future__ import annotations

import bz2
from typing import Any

from ..base import BaseCodec
from ._stream import get_underlying_fileobj
from .profiles import profile_options, resolve_profile


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
        profile, self.compression_level = resolve_profile(
            "bz2",
            profile=options.get("profile"),
            explicit_level=options.get("compression_level"),
            default_level=compression_level,
        )
        self.profile = profile
        self.effective_settings = profile_options("bz2", profile, self.compression_level)
        super().__init__(filename=filename, fileobj=fileobj, mode=mode, open_it=open_it, options=options)

    def open(self) -> bz2.BZ2File:
        underlying = get_underlying_fileobj(self, bz2.BZ2File)
        if underlying is not None:
            self._fileobj = bz2.BZ2File(underlying, mode=self.mode, compresslevel=self.compression_level)
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
