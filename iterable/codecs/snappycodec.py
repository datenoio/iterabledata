"""Snappy compression codec with lazy, streaming (de)compression.

Files are read and written using the snappy *framing* format
(``snappy.StreamCompressor`` / ``snappy.StreamDecompressor``), so both
directions run in bounded memory regardless of file size.

Legacy files produced with the raw one-shot ``snappy.compress`` API carry no
framing and cannot be decompressed incrementally; for those the codec falls
back to a full-buffer decompress (memory is O(uncompressed size)).
"""

from __future__ import annotations

import io
import typing

from ..base import BaseCodec
from .profiles import resolve_profile

try:
    import snappy
except ImportError:
    snappy = None

# Stream identifier chunk that starts every framed snappy stream.
_FRAMED_MAGIC = b"\xff\x06\x00\x00sNaPpY"
_READ_CHUNK = 64 * 1024


class _SnappyStreamReader(io.RawIOBase):
    """Lazy file-like reader that decompresses framed snappy incrementally."""

    def __init__(self, fileobj: typing.IO[bytes], initial: bytes = b""):
        self._fileobj = fileobj
        self._decompressor = snappy.StreamDecompressor()
        self._pending = initial
        self._buffer = bytearray()
        self._eof = False

    def readable(self) -> bool:
        return True

    def _fill(self) -> None:
        while not self._buffer and not self._eof:
            chunk = self._pending or self._fileobj.read(_READ_CHUNK)
            self._pending = b""
            if not chunk:
                self._eof = True
                self._buffer += self._decompressor.flush()
                break
            self._buffer += self._decompressor.decompress(chunk)

    def readinto(self, b) -> int:
        self._fill()
        n = min(len(b), len(self._buffer))
        b[:n] = self._buffer[:n]
        del self._buffer[:n]
        return n

    def close(self) -> None:
        if not self.closed:
            try:
                self._fileobj.close()
            finally:
                super().close()


class _SnappyStreamWriter(io.RawIOBase):
    """Lazy file-like writer that compresses to framed snappy incrementally."""

    def __init__(self, fileobj: typing.IO[bytes]):
        self._fileobj = fileobj
        self._compressor = snappy.StreamCompressor()

    def writable(self) -> bool:
        return True

    def write(self, b) -> int:
        data = bytes(b)
        if data:
            self._fileobj.write(self._compressor.compress(data))
        return len(data)

    def flush(self) -> None:
        if not self.closed:
            remaining = self._compressor.flush()
            if remaining:
                self._fileobj.write(remaining)
            self._fileobj.flush()

    def close(self) -> None:
        if not self.closed:
            try:
                self.flush()
                self._fileobj.close()
            finally:
                super().close()


class SnappyCodec(BaseCodec):
    def __init__(
        self,
        filename: str,
        compression_level: int | None = None,
        mode: str = "r",
        open_it: bool = False,
        options: dict | None = None,
    ):
        """
        Snappy compression codec.
        Note: Snappy doesn't support compression levels (fixed algorithm).
        """
        if options is None:
            options = {}
        profile, _ = resolve_profile(
            "snappy", profile=options.get("profile", "balanced"), explicit_level=None, default_level=0
        )
        self.profile = profile
        self.effective_settings = {"codec": "snappy", "profile": "fixed", "framing": "auto"}
        super().__init__(filename, mode=mode, open_it=open_it, options=options)

    def open(self) -> typing.IO:
        if snappy is None:
            raise ImportError(
                "python-snappy library is required for Snappy compression. Install it with: pip install python-snappy"
            )

        if "r" in self.mode:
            base = open(self.filename, "rb")
            header = base.read(len(_FRAMED_MAGIC))
            if header == _FRAMED_MAGIC:
                # Framed stream: decompress lazily in bounded memory.
                self._fileobj = io.BufferedReader(_SnappyStreamReader(base, initial=header))
                self.effective_settings["framing"] = "framed-stream"
            else:
                # Legacy raw snappy blob: no framing, so streaming is
                # impossible. Fall back to a one-shot decompress.
                compressed_data = header + base.read()
                base.close()
                decompressed = snappy.decompress(compressed_data) if compressed_data else b""
                self._fileobj = io.BytesIO(decompressed)
                self.effective_settings["framing"] = "legacy-raw-buffered"
        else:
            base = open(self.filename, "wb")
            self._fileobj = io.BufferedWriter(_SnappyStreamWriter(base))
        return self._fileobj

    def close(self):
        if getattr(self, "_fileobj", None) is not None:
            if not getattr(self._fileobj, "closed", False):
                self._fileobj.close()
            self._fileobj = None

    def reset(self):
        """Reset by closing and reopening the underlying file."""
        self.close()
        self.open()

    @staticmethod
    def id():
        return "snappy"

    @staticmethod
    def fileexts() -> list[str]:
        return ["snappy", "sz"]
