from __future__ import annotations

import zipfile

from ..base import BaseCodec


class ZIPCodec(BaseCodec):
    def __init__(
        self, filename: str, compression_level: int = 5, mode: str = "r", open_it: bool = False, options: dict = None
    ):
        if options is None:
            options = {}
        self.compression_level = compression_level
        if mode == "rb":
            mode = "r"
            self.filemode = "rb"
        else:
            self.filemode = "r"
        super().__init__(filename, mode=mode, open_it=open_it, options=options)

    def open(self) -> zipfile.ZipFile:
        self._archiveobj = zipfile.ZipFile(self.filename, mode=self.mode)
        fnames = self._archiveobj.namelist()
        self._fileobj = self._archiveobj.open(fnames[0], self.filemode)
        return self._fileobj

    def close(self) -> None:
        if self._fileobj is not None:
            self._fileobj.close()
            self._fileobj = None
        if getattr(self, "_archiveobj", None) is not None:
            self._archiveobj.close()
            self._archiveobj = None

    @staticmethod
    def id():
        return "zip"

    @staticmethod
    def fileexts() -> list[str]:
        return [
            "zip",
        ]
