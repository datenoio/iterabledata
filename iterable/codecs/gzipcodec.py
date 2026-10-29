from __future__ import annotations

import gzip
import importlib.util
import os
from typing import IO, Any

from ..base import BaseCodec
from ._stream import get_underlying_fileobj
from .profiles import profile_options, resolve_profile

GZIP_BACKENDS = ("auto", "stdlib", "isal")
# zlib level -> ISA-L level (ISA-L has 0-3). ISA-L level 1 matches zlib's level 1-2 ratio;
# its higher levels are faster than zlib 6-9 but compress less.
ISAL_LEVELS = {0: 0, 1: 1, 2: 1, 3: 2, 4: 2, 5: 2, 6: 3, 7: 3, 8: 3, 9: 3}
ISAL_THREADS = 4


def isal_available() -> bool:
    """Whether ISA-L (``isal``, the ``iterabledata[fast]`` extra) is installed."""
    return importlib.util.find_spec("isal") is not None


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
        profile, self.compression_level = resolve_profile(
            "gzip",
            profile=options.get("profile"),
            explicit_level=options.get("compression_level"),
            default_level=compression_level,
        )
        self.profile = profile
        self.effective_settings = profile_options("gzip", profile, self.compression_level)
        # "auto": ISA-L for writes at levels 1-2 (same ratio as zlib, faster) when installed;
        # "isal": ISA-L for reads and writes at any level; "stdlib": always zlib.
        self.backend = options.get("backend", "auto")
        if self.backend not in GZIP_BACKENDS:
            raise ValueError(f"Unsupported gzip backend {self.backend!r}; choose one of {', '.join(GZIP_BACKENDS)}")
        super().__init__(filename=filename, fileobj=fileobj, mode=mode, open_it=open_it, options=options)

    def _use_isal(self) -> bool:
        if self.backend == "stdlib":
            return False
        if self.backend == "isal":
            if not isal_available():
                raise ImportError(
                    "gzip backend='isal' requires isal. Install it with: pip install 'iterabledata[fast]'"
                )
            return True
        writing = self.mode.startswith(("w", "a"))
        return writing and 1 <= self.compression_level <= 2 and isal_available()

    def _wrapper_types(self) -> tuple[type, ...]:
        if not isal_available():
            return (gzip.GzipFile,)
        from isal import igzip_threaded

        return (gzip.GzipFile, igzip_threaded.FlushableBufferedWriter)

    def _open_isal(self, underlying: IO[Any] | None) -> Any:
        from isal import igzip, igzip_threaded

        level = ISAL_LEVELS.get(self.compression_level, 3)
        mode = self.mode if "b" in self.mode else self.mode + "b"
        if mode.startswith(("w", "a")) and self.profile == "fast":
            threads = min(ISAL_THREADS, os.cpu_count() or 1)
            target = underlying if underlying is not None else self.filename
            return igzip_threaded.open(target, mode, compresslevel=level, threads=threads)
        if underlying is not None:
            return igzip.IGzipFile(fileobj=underlying, mode=mode, compresslevel=level)
        return igzip.IGzipFile(filename=self.filename, mode=mode, compresslevel=level)

    def open(self) -> IO[Any]:
        underlying = get_underlying_fileobj(self, self._wrapper_types())
        if underlying is None and self.filename is None:
            raise ValueError("GZIPCodec requires either filename or fileobj")
        if self._use_isal():
            self._fileobj = self._open_isal(underlying)
        elif underlying is not None:
            self._fileobj = gzip.GzipFile(fileobj=underlying, mode=self.mode, compresslevel=self.compression_level)
        else:
            self._fileobj = gzip.GzipFile(filename=self.filename, mode=self.mode, compresslevel=self.compression_level)
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
