from __future__ import annotations

from zipfile import ZipFile

from ..base import BaseFileIterable
from ..exceptions import FormatNotSupportedError


class ZIPSourceWrapper(BaseFileIterable):
    """Read-only wrapper that iterates over entries in a ZIP archive."""

    datamode = "binary"

    def __init__(
        self,
        filename: str,
        binary: bool = False,
        mode: str = "r",
        options: dict | None = None,
    ):
        if options is None:
            options = {}
        self._entry_mode = "rb" if binary else "r"
        self._archive: ZipFile | None = None
        self.filenames: list[str] = []
        self.filenum = 0
        self.filepos = 0
        self.globalpos = 0
        self.current_file = None
        super().__init__(
            filename=filename,
            binary=binary,
            mode=mode,
            noopen=True,
            options=options,
        )
        self._open_archive()

    @property
    def fobj(self) -> ZipFile | None:
        return self._archive

    @fobj.setter
    def fobj(self, value: ZipFile | None) -> None:
        self._archive = value

    def _open_archive(self) -> None:
        if self.filename is None:
            raise ValueError("ZIPSourceWrapper requires a filename")
        self._archive = ZipFile(self.filename, mode="r")
        self.filenames = self._archive.namelist()
        self.filenum = 0
        self.filepos = 0
        self.globalpos = 0
        if self.filenames:
            self.current_file = self._archive.open(self.filenames[self.filenum], mode=self._entry_mode)
        else:
            self.current_file = None

    @staticmethod
    def id() -> str:
        return "zipped"

    def reset(self) -> None:
        """Reset to the first file in the archive."""
        if getattr(self, "_closed", False):
            raise ValueError("Cannot reset a closed iterable")
        if self.current_file:
            self.current_file.close()
        self.filenum = 0
        self.filepos = 0
        self.globalpos = 0
        if self.filenames and self._archive is not None:
            self.current_file = self._archive.open(self.filenames[self.filenum], mode=self._entry_mode)
        else:
            self.current_file = None

    def close(self) -> None:
        if getattr(self, "_closed", False):
            return
        if self.current_file is not None:
            self.current_file.close()
            self.current_file = None
        super().close()

    def iterfile(self) -> bool:
        if self.current_file:
            self.current_file.close()
        if self.filenum < len(self.filenames) - 1:
            self.filenum += 1
            entry_name = self.filenames[self.filenum]
            if self._archive is not None:
                self.current_file = self._archive.open(entry_name, mode=self._entry_mode)
            self.filepos = 0
            return True
        return False

    def read(self, skip_empty: bool = True) -> dict:
        """Read single record."""
        try:
            return self.read_single()
        except StopIteration:
            if self.iterfile():
                return self.read_single()
            raise StopIteration from None

    def __iter__(self) -> ZIPSourceWrapper:
        self.filenum = 0
        if self.filenames and self._archive is not None:
            self.current_file = self._archive.open(self.filenames[self.filenum], mode=self._entry_mode)
        return self

    def read_single(self):
        """Not implemented single record read."""
        raise FormatNotSupportedError("zipped", "Single record reading is not supported for ZIP files")
