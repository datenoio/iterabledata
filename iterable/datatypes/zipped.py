from __future__ import annotations

from zipfile import ZipFile

from ..base import BaseIterable
from ..exceptions import FormatNotSupportedError


class ZIPSourceWrapper(BaseIterable):
    def __init__(self, filename: str, binary: bool = False):
        super().__init__()
        self.filename = filename
        self.fobj = ZipFile(filename, mode="r")
        self.filenames = self.fobj.namelist()
        self.filenum = 0
        self.filepos = 0
        self.globalpos = 0
        self.mode = "rb" if binary else "r"
        self.current_file = self.fobj.open(self.filenames[self.filenum], mode=self.mode)

    @staticmethod
    def id() -> str:
        return "zipped"

    def reset(self) -> None:
        """Reset to the first file in the archive."""
        if self.current_file:
            self.current_file.close()
        self.filenum = 0
        self.filepos = 0
        self.globalpos = 0
        self.current_file = self.fobj.open(self.filenames[self.filenum], mode=self.mode)

    def close(self):
        if self.current_file:
            self.current_file.close()
            self.current_file = None
        self.fobj.close()

    def iterfile(self) -> bool:
        if self.current_file:
            self.current_file.close()
        if self.filenum < len(self.filenames) - 1:
            self.filenum += 1
            filename = self.filenames[self.filenum]
            self.current_file = self.fobj.open(filename, mode=self.mode)
            self.filepos = 0
            return True
        else:
            return False

    def read(self, skip_empty: bool = True) -> dict:
        """Read single record"""
        try:
            row = self.read_single()
            return row
        except StopIteration:
            if self.iterfile():
                row = self.read_single()
                return row
            else:
                raise StopIteration from None

    def __iter__(self) -> ZIPSourceWrapper:
        self.filenum = 0
        filename = self.filenames[self.filenum]
        self.current_file = self.fobj.open(filename, mode=self.mode)
        return self

    def read_single(self):
        """Not implemented single record read"""
        raise FormatNotSupportedError("zipped", "Single record reading is not supported for ZIP files")
