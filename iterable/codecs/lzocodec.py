from __future__ import annotations

import io
import typing

from ..base import BaseCodec

try:
    import lzo
except ImportError:
    lzo = None


class LZOCodec(BaseCodec):
    def __init__(
        self, filename: str, compression_level: int = 1, mode: str = "r", open_it: bool = False, options: dict = None
    ):
        """
        LZO compression codec.
        compression_level: 1 (fastest) to 9 (best compression), default is 1
        """
        if options is None:
            options = {}
        self.compression_level = compression_level
        super().__init__(filename, mode=mode, open_it=open_it, options=options)

    def open(self) -> typing.IO:
        if lzo is None:
            raise ImportError(
                "python-lzo library is required for LZO compression. Install it with: pip install python-lzo"
            )

        if "r" in self.mode:
            # Reading: read entire file, decompress, provide as BytesIO
            with open(self.filename, "rb") as f:
                compressed_data = f.read()

            if compressed_data:
                decompressed_data = lzo.decompress(compressed_data)
            else:
                decompressed_data = b""

            self._buffer = io.BytesIO(decompressed_data)
            self._fileobj = self._buffer
        else:
            # Writing: buffer data, compress on close
            self._buffer = io.BytesIO()
            self._fileobj = self._buffer

        return self._fileobj

    def close(self) -> None:
        if hasattr(self, "_fileobj") and self._fileobj:
            if "w" in self.mode or "a" in self.mode:
                if hasattr(self, "_buffer") and self._buffer:
                    data = self._buffer.getvalue()
                    if data:
                        compressed_data = lzo.compress(data, self.compression_level)
                        with open(self.filename, "wb") as f:
                            f.write(compressed_data)
                    self._buffer.close()
                    self._buffer = None
            else:
                if hasattr(self, "_buffer") and self._buffer:
                    self._buffer.close()
                    self._buffer = None
            self._fileobj = None

    def reset(self):
        """Reset file position"""
        if hasattr(self, "_buffer") and self._buffer:
            if "r" in self.mode:
                self._buffer.seek(0)
            else:
                # For writing, we need to reopen
                self.close()
                self.open()

    @staticmethod
    def id():
        return "lzo"

    @staticmethod
    def fileexts() -> list[str]:
        return ["lzo", "lzop"]
