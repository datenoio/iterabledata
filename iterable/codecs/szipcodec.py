from __future__ import annotations

from ..base import BaseCodec

try:
    import py7zr

    HAS_PY7ZR = True
except ImportError:
    HAS_PY7ZR = False
    py7zr = None


class SZipCodec(BaseCodec):
    def __init__(
        self,
        filename: str,
        compression_level: int = 5,
        mode: str = "r",
        open_it: bool = False,
        options: dict | None = None,
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

    def open(self):
        if not HAS_PY7ZR or py7zr is None:
            raise ImportError(
                "7z/SZip support requires py7zr. Install with: pip install iterabledata[szip] or pip install py7zr"
            )
        self._archiveobj = py7zr.SevenZipFile(self.filename, mode=self.mode)
        fnames = self._archiveobj.getnames()

        self._fileobj = self._archiveobj.open(fnames[0], self.filemode)
        return self._fileobj

    def close(self) -> None:
        if getattr(self, "_fileobj", None) is not None:
            self._fileobj.close()
            self._fileobj = None
        if getattr(self, "_archiveobj", None) is not None:
            self._archiveobj.close()
            self._archiveobj = None

    @staticmethod
    def fileexts() -> list[str]:
        return [
            "7z",
        ]
