from __future__ import annotations

import email
import typing
from typing import Any

from ..base import BaseCodec, BaseFileIterable
from ..types import Row


class MHTMLIterable(BaseFileIterable):
    def __init__(
        self,
        filename: str | None = None,
        stream: typing.IO[Any] | None = None,
        codec: BaseCodec | None = None,
        mode: str = "r",
        encoding: str = "utf8",
        options: dict[str, Any] | None = None,
    ):
        if options is None:
            options = {}
        super().__init__(filename, stream, codec=codec, binary=False, mode=mode, encoding=encoding, options=options)
        self.reset()
        pass

    def reset(self):
        """Reset iterable"""
        super().reset()
        self.pos = 0
        if self.mode == "r":
            content = self.fobj.read()

            # MHTML format: multipart/related message
            # Parse as email message
            msg = email.message_from_string(content)

            self.entries = []

            # Main HTML content
            main_content = None
            if msg.is_multipart():
                for part in msg.walk():
                    content_type = part.get_content_type()
                    content_disposition = part.get("Content-Disposition", "")

                    if "inline" in content_disposition.lower() or content_type == "text/html":
                        payload = part.get_payload(decode=True)
                        if payload:
                            try:
                                main_content = payload.decode("utf-8", errors="ignore")
                            except Exception:
                                main_content = str(payload)
                            break

                # Extract all parts as separate entries
                for part in msg.walk():
                    entry = {}
                    entry["content_type"] = part.get_content_type()
                    entry["content_id"] = part.get("Content-ID", "")
                    entry["content_location"] = part.get("Content-Location", "")
                    entry["content_disposition"] = part.get("Content-Disposition", "")

                    payload = part.get_payload(decode=True)
                    if payload:
                        content_type = part.get_content_type()
                        if content_type.startswith("text/"):
                            try:
                                entry["content"] = payload.decode("utf-8", errors="ignore")
                            except Exception:
                                entry["content"] = str(payload)
                        else:
                            # Binary content - store as base64 or hex
                            import base64

                            entry["content"] = base64.b64encode(payload).decode("ascii")
                            entry["content_encoding"] = "base64"
                            entry["content_size"] = len(payload)

                    if entry.get("content") or entry.get("content_id"):
                        self.entries.append(entry)
            else:
                # Single part message
                payload = msg.get_payload(decode=True)
                if payload:
                    try:
                        content = payload.decode("utf-8", errors="ignore")
                    except Exception:
                        content = str(payload)
                    self.entries.append({"content_type": msg.get_content_type(), "content": content})

            # If we have main content, add it as first entry
            if main_content and len(self.entries) > 0:
                self.entries[0]["main_content"] = main_content

            self.iterator = iter(self.entries)
        else:
            self.entries = []

    @staticmethod
    def id() -> str:
        return "mhtml"

    @staticmethod
    def is_flatonly() -> bool:
        return False

    def read(self, skip_empty: bool = True) -> dict:
        """Read single MHTML record"""
        row = next(self.iterator)
        self.pos += 1
        return row

    def write(self, record: Row) -> None:
        """Write single MHTML record"""
        # Create multipart/related message
        msg = email.message.EmailMessage()
        msg["From"] = record.get("from", "mhtml@example.com")
        msg["Subject"] = record.get("subject", "MHTML Document")
        msg["MIME-Version"] = "1.0"
        msg["Content-Type"] = 'multipart/related; boundary="----=_NextPart_000_0000_01"'

        # Main HTML part
        main_content = record.get("content") or record.get("main_content", "")
        if main_content:
            part = email.message.EmailMessage()
            part["Content-Type"] = "text/html; charset=utf-8"
            part["Content-Transfer-Encoding"] = "quoted-printable"
            part.set_payload(main_content)
            msg.attach(part)

        # Write to file
        if self.filename:
            with open(self.filename, "w", encoding=self.encoding) as f:
                f.write(msg.as_string())
        else:
            self.fobj.write(msg.as_string())

    def write_bulk(self, records: list[Row]) -> None:
        """Write bulk MHTML records"""
        # MHTML typically contains one document, so write the first one
        if records:
            self.write(records[0])
