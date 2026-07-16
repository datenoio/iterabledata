from __future__ import annotations

import brotli_file

from ..base import BaseCodec
from .profiles import profile_options, resolve_profile

BROTLI_DEFAULT_COMPRESSION_LEVEL = 11


class BrotliCodec(BaseCodec):
    def __init__(
        self,
        filename: str,
        compression_level: int = BROTLI_DEFAULT_COMPRESSION_LEVEL,
        mode: str = "r",
        open_it: bool = False,
        options: dict = None,
    ):
        "Code to support Brotli compression"
        if options is None:
            options = {}
        self.profile, self.compression_level = resolve_profile(
            "brotli",
            profile=options.get("profile"),
            explicit_level=options.get("compression_level"),
            default_level=compression_level,
        )
        self.effective_settings = profile_options("brotli", self.profile, self.compression_level)
        super().__init__(filename, mode=mode, open_it=open_it, options=options)

    def open(self) -> brotli_file.BrotliFile:
        self._fileobj = brotli_file.open(self.filename, mode=self.mode, quality=self.compression_level)
        return self._fileobj

    def close(self):
        self._fileobj.close()

    @staticmethod
    def id():
        return "brotli"

    @staticmethod
    def fileexts() -> list[str]:
        return ["br", "brotli"]
