"""LZO compression codec with block-framed streaming.

``python-lzo`` only exposes one-shot ``compress``/``decompress`` calls, so true
stream compression is not available. To keep memory bounded this codec writes
its own block-framed container: an ``ILZO1`` magic header followed by
length-prefixed blocks, each an independent one-shot LZO payload of at most
``_BLOCK_SIZE`` plaintext bytes. Reading framed files decompresses one block at
a time, so peak memory is O(block size) rather than O(file size).

Legacy files (a single raw ``lzo.compress`` blob, as written by earlier
versions of this codec) are still readable via a full-buffer fallback; for
those, memory is O(uncompressed size) because the format cannot be streamed.
Note that neither framing is the ``lzop`` tool's container format.
"""

from __future__ import annotations

import io
import struct
import typing

from ..base import BaseCodec
from .profiles import profile_options, resolve_profile

try:
    import lzo
except ImportError:
    lzo = None

_FRAME_MAGIC = b"ILZO1"
_BLOCK_HEADER = struct.Struct(">I")
# Plaintext bytes per compressed block; bounds read/write memory.
_BLOCK_SIZE = 256 * 1024


class _LZOBlockReader(io.RawIOBase):
    """Lazy reader decompressing an ILZO1 block-framed file one block at a time."""

    def __init__(self, fileobj: typing.IO[bytes]):
        self._fileobj = fileobj
        self._buffer = bytearray()
        self._eof = False

    def readable(self) -> bool:
        return True

    def _fill(self) -> None:
        while not self._buffer and not self._eof:
            header = self._fileobj.read(_BLOCK_HEADER.size)
            if not header:
                self._eof = True
                break
            if len(header) < _BLOCK_HEADER.size:
                raise ValueError("Truncated LZO block header")
            (block_len,) = _BLOCK_HEADER.unpack(header)
            block = self._fileobj.read(block_len)
            if len(block) < block_len:
                raise ValueError("Truncated LZO block payload")
            self._buffer += lzo.decompress(block)

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


class _LZOBlockWriter(io.RawIOBase):
    """Lazy writer compressing plaintext into ILZO1 length-prefixed blocks."""

    def __init__(self, fileobj: typing.IO[bytes], compression_level: int):
        self._fileobj = fileobj
        self._compression_level = compression_level
        self._plain = bytearray()
        self._fileobj.write(_FRAME_MAGIC)

    def writable(self) -> bool:
        return True

    def _flush_block(self) -> None:
        if not self._plain:
            return
        block = lzo.compress(bytes(self._plain), self._compression_level)
        self._fileobj.write(_BLOCK_HEADER.pack(len(block)))
        self._fileobj.write(block)
        self._plain.clear()

    def write(self, b) -> int:
        data = bytes(b)
        self._plain += data
        while len(self._plain) >= _BLOCK_SIZE:
            chunk = bytes(self._plain[:_BLOCK_SIZE])
            del self._plain[:_BLOCK_SIZE]
            block = lzo.compress(chunk, self._compression_level)
            self._fileobj.write(_BLOCK_HEADER.pack(len(block)))
            self._fileobj.write(block)
        return len(data)

    def flush(self) -> None:
        if not self.closed:
            self._flush_block()
            self._fileobj.flush()

    def close(self) -> None:
        if not self.closed:
            try:
                self.flush()
                self._fileobj.close()
            finally:
                super().close()


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
        self.profile, self.compression_level = resolve_profile(
            "lzo",
            profile=options.get("profile"),
            explicit_level=options.get("compression_level"),
            default_level=compression_level,
        )
        self.effective_settings = profile_options("lzo", self.profile, self.compression_level)
        self.effective_settings["container"] = "ILZO1 (not lzop)"
        super().__init__(filename, mode=mode, open_it=open_it, options=options)

    def open(self) -> typing.IO:
        if lzo is None:
            raise ImportError(
                "python-lzo library is required for LZO compression. Install it with: pip install python-lzo"
            )

        if "r" in self.mode:
            base = open(self.filename, "rb")
            header = base.read(len(_FRAME_MAGIC))
            if header == _FRAME_MAGIC:
                # Block-framed file: decompress lazily block by block.
                self._fileobj = io.BufferedReader(_LZOBlockReader(base))
                self.effective_settings["container"] = "ILZO1"
            else:
                # Legacy one-shot blob: cannot be streamed, decompress fully.
                compressed_data = header + base.read()
                base.close()
                decompressed = lzo.decompress(compressed_data) if compressed_data else b""
                self._fileobj = io.BytesIO(decompressed)
                self.effective_settings["container"] = "legacy-raw-buffered"
        else:
            base = open(self.filename, "wb")
            self._fileobj = io.BufferedWriter(_LZOBlockWriter(base, self.compression_level))
        return self._fileobj

    def close(self) -> None:
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
        return "lzo"

    @staticmethod
    def fileexts() -> list[str]:
        return ["lzo", "lzop"]
