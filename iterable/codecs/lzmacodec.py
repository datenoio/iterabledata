from __future__ import annotations

import lzma

from ..base import BaseCodec


class LZMACodec(BaseCodec):
    def __init__(
        self, filename: str, compression_level: int = 5, mode: str = "r", open_it: bool = False, options: dict = None
    ):
        if options is None:
            options = {}
        self.compression_level = compression_level
        super().__init__(filename, mode=mode, open_it=open_it, options=options)

    def open(self) -> lzma.LZMAFile:
        kwargs: dict = {"format": lzma.FORMAT_XZ}
        if self.mode in ("w", "wb"):
            kwargs["preset"] = self.compression_level
        self._fileobj = lzma.LZMAFile(self.filename, mode=self.mode, **kwargs)
        return self._fileobj

    def reset(self):
        if self.mode in ["w", "wb"]:
            pass
        else:
            super().reset()

    def close(self) -> None:
        if self._fileobj is not None:
            self._fileobj.close()
            self._fileobj = None

    @staticmethod
    def id():
        return "xz"

    @staticmethod
    def fileexts() -> list[str]:
        return ["xz", "lzma"]
