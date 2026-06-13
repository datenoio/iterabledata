from __future__ import annotations

import typing

try:
    from warcio.archiveiterator import ArchiveIterator  # type: ignore[import-untyped]
    from warcio.warcwriter import WARCWriter  # type: ignore[import-untyped]

    HAS_WARCIO = True
except ImportError:
    HAS_WARCIO = False

from typing import Any

from ..base import BaseCodec, BaseFileIterable
from ..types import Row


class WARCIterable(BaseFileIterable):
    """
    WARC (Web ARChive) file format reader/writer.
    WARC files contain web archive records including HTTP requests/responses,
    metadata, and resource records.
    """

    datamode = "binary"

    def __init__(
        self,
        filename: str = None,
        stream: typing.IO[Any] | None = None,
        codec: BaseCodec | None = None,
        mode: str = "r",
        options: dict[str, Any] | None = None,
    ):
        if options is None:
            options = {}
        if not HAS_WARCIO:
            raise ImportError("WARC file support requires 'warcio' package. Install it with: pip install warcio")
        super().__init__(filename, stream, codec=codec, binary=True, mode=mode, noopen=True, options=options)
        self.pos = 0
        self.archive_iterator = None
        self.warc_writer = None
        self._fileobj = None  # Track opened file for cleanup
        self.reset()

    def reset(self):
        """Reset iterable"""
        super().reset()
        self.pos = 0

        # Close previously opened file if we opened it
        if self._fileobj is not None and self.filename:
            try:
                self._fileobj.close()
            except Exception:
                pass
        self._fileobj = None

        if self.mode == "r":
            # For reading, initialize ArchiveIterator
            if self.codec is not None:
                # Ensure codec is opened, reset if already open to start from beginning
                if self.codec._fileobj is None:
                    self.codec.open()
                else:
                    self.codec.reset()
                fileobj = self.codec.fileobj()
            elif self.filename:
                self._fileobj = open(self.filename, "rb")
                fileobj = self._fileobj
            else:
                fileobj = self.fobj

            # Seek back to beginning if file is seekable
            if hasattr(fileobj, "seek"):
                try:
                    fileobj.seek(0)
                except OSError:
                    pass  # File might not be seekable (e.g., stdin)

            self.archive_iterator = ArchiveIterator(fileobj)
        elif self.mode == "w":
            # For writing, initialize WARCWriter
            if self.codec is not None:
                # Ensure codec is opened before getting fileobj
                if self.codec._fileobj is None:
                    self.codec.open()
                fileobj = self.codec.fileobj()
            elif self.filename:
                self._fileobj = open(self.filename, "wb")
                fileobj = self._fileobj
            else:
                fileobj = self.fobj

            self.warc_writer = WARCWriter(fileobj)

    @staticmethod
    def has_totals() -> bool:
        """Has totals indicator"""
        return False  # WARC files don't have a reliable way to count records without iterating

    def totals(self):
        """Returns file totals - not supported for WARC files"""
        raise NotImplementedError("WARC files don't support totals counting")

    @staticmethod
    def id() -> str:
        return "warc"

    @staticmethod
    def is_flatonly() -> bool:
        return False  # WARC records can contain nested structures

    def read(self, skip_empty: bool = True) -> dict:
        """Read single WARC record"""
        if self.archive_iterator is None:
            raise RuntimeError("WARC file not opened for reading")

        try:
            record = next(self.archive_iterator)
        except StopIteration:
            raise StopIteration from None

        # Extract WARC record information
        rec_headers_dict = dict(record.rec_headers.headers)
        result = {
            "rec_type": record.rec_type,
            "rec_headers": rec_headers_dict,  # Keep as dict
            "content_type": record.content_type,
            "length": record.length,
        }

        # Add common headers as top-level fields for convenience
        if "WARC-Target-URI" in record.rec_headers:
            result["target_uri"] = record.rec_headers.get_header("WARC-Target-URI")
        if "WARC-Date" in record.rec_headers:
            result["date"] = record.rec_headers.get_header("WARC-Date")
        if "WARC-Record-ID" in record.rec_headers:
            result["record_id"] = record.rec_headers.get_header("WARC-Record-ID")
        if "WARC-Type" in record.rec_headers:
            result["warc_type"] = record.rec_headers.get_header("WARC-Type")

        # Extract HTTP headers and metadata if available
        # warcio provides http_headers for records containing HTTP data
        # Always include http_headers field (even if None) to ensure Parquet schema includes it
        if hasattr(record, "http_headers") and record.http_headers is not None:
            # Extract HTTP headers as dictionary
            result["http_headers"] = dict(record.http_headers.headers)

            # For response records, extract status code and status line
            if record.rec_type == "response":
                try:
                    status_code = record.http_headers.get_statuscode()
                    if status_code:
                        result["http_status_code"] = status_code
                except (AttributeError, ValueError):
                    pass

                try:
                    status_line = record.http_headers.get_statusline()
                    if status_line:
                        result["http_status_line"] = status_line
                except (AttributeError, ValueError):
                    pass

            # For request records, extract request line and parse method/path/protocol
            elif record.rec_type == "request":
                try:
                    request_line = record.http_headers.get_requestline()
                    if request_line:
                        result["http_request_line"] = request_line
                        # Parse request line: "METHOD PATH PROTOCOL"
                        parts = request_line.split(" ", 2)
                        if len(parts) >= 1:
                            result["http_method"] = parts[0]
                        if len(parts) >= 2:
                            result["http_path"] = parts[1]
                        if len(parts) >= 3:
                            result["http_protocol"] = parts[2]
                except (AttributeError, ValueError):
                    pass
        else:
            # Always include http_headers field (even if None) to ensure Parquet schema includes it
            result["http_headers"] = None

        # Read payload content if it's a response or resource record
        if record.rec_type in ["response", "resource"]:
            try:
                content = record.content_stream().read()
                # Try to decode as text if it's text content
                if record.content_type and "text" in record.content_type.lower():
                    try:
                        result["content"] = content.decode("utf-8", errors="replace")
                    except Exception:
                        result["content"] = content
                else:
                    result["content"] = content
                result["content_length"] = len(content)
            except Exception:
                result["content"] = None
                result["content_length"] = 0
        else:
            result["content"] = None
            result["content_length"] = 0

        self.pos += 1
        return result

    def write(self, record: Row) -> None:
        """Write single WARC record"""
        if self.warc_writer is None:
            raise RuntimeError("WARC file not opened for writing")

        import io

        # Extract record information
        rec_type = record.get("rec_type", "response")
        target_uri = record.get("target_uri", record.get("url", ""))
        warc_headers = record.get("rec_headers", {})

        # Get content
        content = record.get("content", b"")
        if isinstance(content, str):
            content = content.encode("utf-8")
        elif content is None:
            content = b""

        # Create payload stream
        payload_stream = io.BytesIO(content)
        content_length = len(content)

        # Determine content type
        content_type = record.get("content_type", "application/octet-stream")

        # Use WARCWriter helper to build a valid WARC/1.0 record (proper status line + headers).
        warc_headers_dict = {k: str(v) for k, v in (warc_headers or {}).items()}

        # warcio expects HTTP payloads for 'response'/'request' unless http_headers are provided.
        # Many callers (including our tests) provide arbitrary payload bytes, so store those as
        # 'resource' records while preserving target_uri and provided WARC headers.
        create_type = rec_type
        if rec_type in ("response", "request") and record.get("http_headers") is None:
            create_type = "resource"

        warc_record = self.warc_writer.create_warc_record(
            target_uri or "",
            create_type,
            payload=payload_stream,
            length=content_length,
            warc_content_type=content_type,
            warc_headers_dict=warc_headers_dict,
        )
        self.warc_writer.write_record(warc_record)

    def write_bulk(self, records: list[Row]) -> None:
        """Write bulk WARC records"""
        for record in records:
            self.write(record)

    def close(self):
        """Close WARC file"""
        # WARCWriter doesn't have a close method, but we should close the underlying file
        if self._fileobj is not None:
            try:
                self._fileobj.close()
            except Exception:
                pass
            self._fileobj = None
        # Close codec if it was opened
        if self.codec is not None and self.codec._fileobj is not None:
            try:
                self.codec.close()
            except Exception:
                pass
        super().close()
