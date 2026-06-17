from __future__ import annotations

import zstandard as zstd

from ..base import BaseCodec
from ._stream import get_underlying_fileobj

# Zstandard file object doesn't support file seek so reset rewritten to close and open file


class ZSTDCodec(BaseCodec):
    def __init__(
        self, filename: str, compression_level: int = 19, mode: str = "rb", open_it: bool = False, options: dict = None
    ):
        if options is None:
            options = {}
        # Allow compression_level to be set from options (codecargs)
        if "compression_level" in options:
            self.compression_level = options["compression_level"]
        else:
            self.compression_level = compression_level
        rmode = "rb" if mode in ["r", "rb"] else "wb"
        self._base_file = None  # Store base file for proper cleanup
        super().__init__(filename, mode=rmode, open_it=open_it, options=options)

    def open(self) -> zstd.ZstdDecompressionReader:
        # If fileobj was provided (e.g., from cloud storage), use it
        if self._fileobj is not None or getattr(self, "_original_fileobj", None) is not None:
            underlying = get_underlying_fileobj(
                self,
                (zstd.ZstdDecompressionReader, zstd.ZstdCompressionWriter),
            )
            if underlying is None:
                raise ValueError("ZSTDCodec cannot determine underlying file object")
            if "r" in self.mode or "rb" in self.mode:
                # Reading: create decompression reader
                dctx = zstd.ZstdDecompressor()
                self._fileobj = dctx.stream_reader(underlying)
            else:
                # Writing: create compression writer
                cctx = zstd.ZstdCompressor(level=self.compression_level)
                self._fileobj = cctx.stream_writer(underlying)
        elif self.filename is not None:
            # Open from filename as usual
            # zstd.open() doesn't support compression level, so we need to handle it manually
            if "r" in self.mode or "rb" in self.mode:
                # Reading: use zstd.open() (decompression level doesn't matter)
                self._fileobj = zstd.open(self.filename, mode=self.mode)
            else:
                # Writing: open file and wrap with compressor to use compression level
                file_mode = "wb" if "b" in self.mode else "w"
                self._base_file = open(self.filename, file_mode)
                cctx = zstd.ZstdCompressor(level=self.compression_level)
                self._fileobj = cctx.stream_writer(self._base_file)
        else:
            raise ValueError("ZSTDCodec requires either filename or fileobj")
        return self._fileobj

    def reset(self):
        self.close()
        self._fileobj = self.open()

    def close(self) -> None:
        if self._fileobj is not None:
            self._fileobj.close()
            self._fileobj = None
        if getattr(self, "_base_file", None) is not None:
            self._base_file.close()
            self._base_file = None

    @staticmethod
    def id():
        return "zst"

    @staticmethod
    def fileexts() -> list[str]:
        return ["zstd", "zst"]
