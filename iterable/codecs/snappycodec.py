from __future__ import annotations

import io
import typing

from ..base import BaseCodec

try:
    import snappy
except ImportError:
    snappy = None


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
        super().__init__(filename, mode=mode, open_it=open_it, options=options)

    def open(self) -> typing.IO:
        if snappy is None:
            raise ImportError(
                "python-snappy library is required for Snappy compression. Install it with: pip install python-snappy"
            )

        if "r" in self.mode:
            # Reading: read entire file, decompress, provide as BytesIO
            # Only read if buffer doesn't exist or is closed
            if (
                not hasattr(self, "_buffer")
                or self._buffer is None
                or (hasattr(self._buffer, "closed") and self._buffer.closed)
            ):
                with open(self.filename, "rb") as f:
                    compressed_data = f.read()

                if compressed_data:
                    # Try streaming decompression first, fall back to simple decompress
                    try:
                        decompressor = snappy.StreamDecompressor()
                        decompressed_data = decompressor.decompress(compressed_data)
                        # Some python-snappy versions return b'' here without raising;
                        # fall back to the non-streaming API in that case.
                        if not decompressed_data:
                            decompressed_data = snappy.decompress(compressed_data)
                    except (AttributeError, TypeError):
                        # Fall back to simple decompress if StreamDecompressor not available
                        decompressed_data = snappy.decompress(compressed_data)
                else:
                    decompressed_data = b""

                self._buffer = io.BytesIO(decompressed_data)
            # Reset buffer position if it exists
            elif hasattr(self._buffer, "seek"):
                self._buffer.seek(0)

            self._fileobj = self._buffer
        else:
            # Writing: buffer data, compress on close
            if (
                not hasattr(self, "_buffer")
                or self._buffer is None
                or (hasattr(self._buffer, "closed") and self._buffer.closed)
            ):
                self._buffer = io.BytesIO()
            self._fileobj = self._buffer

        return self._fileobj

    def close(self):
        if hasattr(self, "_fileobj") and self._fileobj:
            if "w" in self.mode or "a" in self.mode:
                # Compress and write buffered data
                if hasattr(self, "_buffer") and self._buffer:
                    try:
                        # Check if buffer is still open
                        try:
                            data = self._buffer.getvalue()
                        except ValueError:
                            # Buffer already closed
                            data = None

                        if data:
                            # Try streaming compression first, fall back to simple compress
                            try:
                                compressor = snappy.StreamCompressor()
                                compressed_data = compressor.compress(data)
                            except (AttributeError, TypeError):
                                # Fall back to simple compress if StreamCompressor not available
                                compressed_data = snappy.compress(data)

                            with open(self.filename, "wb") as f:
                                f.write(compressed_data)
                    except (ValueError, OSError, AttributeError):
                        # Buffer already closed or other I/O error
                        pass
                    finally:
                        if hasattr(self, "_buffer") and self._buffer:
                            try:
                                # Only close if not already closed
                                if not self._buffer.closed:
                                    self._buffer.close()
                            except (ValueError, AttributeError):
                                pass
                        self._buffer = None
                        self._fileobj = None
            else:
                # Reading mode - don't close the buffer, it might be needed for reset()
                # Just mark fileobj as None but keep buffer alive
                # The buffer will be properly closed when the iterable is fully done
                self._fileobj = None
                # Don't close _buffer here - it's still needed for reset() operations

    def fileobj(self):
        """Return file object"""
        # If fileobj is None but buffer exists and is open, return buffer
        if self._fileobj is None and hasattr(self, "_buffer") and self._buffer:
            if not (hasattr(self._buffer, "closed") and self._buffer.closed):
                self._fileobj = self._buffer
                return self._fileobj
            else:
                # Buffer is closed, reopen it
                self.open()
                return self._fileobj
        return self._fileobj

    def reset(self):
        """Reset file position"""
        if hasattr(self, "_buffer") and self._buffer:
            if "r" in self.mode:
                # Check if buffer is closed, if so reopen
                if hasattr(self._buffer, "closed") and self._buffer.closed:
                    # Reopen the buffer
                    self.open()
                else:
                    self._buffer.seek(0)
                    self._fileobj = self._buffer
            else:
                # For writing, we need to reopen
                if (
                    hasattr(self, "_buffer")
                    and self._buffer
                    and hasattr(self._buffer, "closed")
                    and self._buffer.closed
                ):
                    self.open()
                else:
                    self.close()
                    self.open()

    @staticmethod
    def id():
        return "snappy"

    @staticmethod
    def fileexts() -> list[str]:
        return ["snappy", "sz"]
