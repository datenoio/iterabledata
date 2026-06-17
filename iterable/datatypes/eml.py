from __future__ import annotations

import email
import typing
from email.utils import parsedate_to_datetime
from typing import Any

from ..base import BaseCodec, BaseFileIterable
from ..types import Row


class EMLIterable(BaseFileIterable):
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
            # EML files are single email messages
            # If filename is provided, read it; otherwise use stream
            if self.filename:
                with open(self.filename, encoding=self.encoding) as f:
                    content = f.read()
            else:
                content = self.fobj.read()

            msg = email.message_from_string(content)
            self.entry = self._email_to_dict(msg)
            self.iterator = iter([self.entry])
        else:
            self.entry = None

    @staticmethod
    def id() -> str:
        return "eml"

    @staticmethod
    def is_flatonly() -> bool:
        return False

    def _email_to_dict(self, msg: email.message.Message) -> dict:
        """Convert email message to dictionary"""
        result = {}

        # Basic headers
        for header in [
            "From",
            "To",
            "Cc",
            "Bcc",
            "Subject",
            "Date",
            "Message-ID",
            "In-Reply-To",
            "References",
            "Reply-To",
            "Sender",
        ]:
            value = msg.get(header)
            if value:
                result[header.lower()] = value

        # Parse date
        if "date" in result:
            try:
                result["date_parsed"] = parsedate_to_datetime(result["date"]).isoformat()
            except Exception:
                pass

        # Body content
        if msg.is_multipart():
            parts = []
            for part in msg.walk():
                if part.get_content_maintype() == "text":
                    payload = part.get_payload(decode=True)
                    if payload:
                        try:
                            content = payload.decode("utf-8", errors="ignore")
                        except Exception:
                            content = str(payload)
                        parts.append({"content_type": part.get_content_type(), "content": content})
            result["body"] = parts
            result["body_text"] = "\n\n".join([p["content"] for p in parts])
        else:
            payload = msg.get_payload(decode=True)
            if payload:
                try:
                    result["body"] = payload.decode("utf-8", errors="ignore")
                except Exception:
                    result["body"] = str(payload)
            else:
                result["body"] = msg.get_payload()
            result["body_text"] = result.get("body", "")

        # All headers
        result["headers"] = dict(msg.items())

        # Attachments info
        attachments = []
        if msg.is_multipart():
            for part in msg.walk():
                if part.get_content_disposition() == "attachment":
                    payload = part.get_payload(decode=True)
                    attachments.append(
                        {
                            "filename": part.get_filename(),
                            "content_type": part.get_content_type(),
                            "size": len(payload) if payload else 0,
                        }
                    )
        if attachments:
            result["attachments"] = attachments

        return result

    def read(self, skip_empty: bool = True) -> dict:
        """Read single EML record"""
        row = next(self.iterator)
        self.pos += 1
        return row

    def write(self, record: Row) -> None:
        """Write single EML record"""
        msg = email.message.EmailMessage()

        # Set headers
        for key, value in record.items():
            if key.lower() in [
                "from",
                "to",
                "cc",
                "bcc",
                "subject",
                "date",
                "message-id",
                "in-reply-to",
                "references",
                "reply-to",
                "sender",
            ]:
                msg[key] = str(value)
            elif key == "body" or key == "body_text":
                msg.set_content(str(value))

        # Write to file
        if self.filename:
            with open(self.filename, "w", encoding=self.encoding) as f:
                f.write(msg.as_string())
        else:
            self.fobj.write(msg.as_string())

    def write_bulk(self, records: list[Row]) -> None:
        """Write bulk EML records"""
        # EML typically contains one message, so write the first one
        if records:
            self.write(records[0])
