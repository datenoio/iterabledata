from __future__ import annotations

import re
import typing
from typing import Any

from ..base import BaseCodec, BaseFileIterable
from ..types import Row


class ApacheLogIterable(BaseFileIterable):
    datamode = "text"

    def __init__(
        self,
        filename: str = None,
        stream: typing.IO[Any] | None = None,
        codec: BaseCodec | None = None,
        mode: str = "r",
        log_format: str = "common",
        options: dict[str, Any] | None = None,
    ):
        # Check log format before opening file
        if options is None:
            options = {}
        self.log_format = log_format
        if "log_format" in options:
            self.log_format = options["log_format"]

        # Define log format patterns
        self.patterns = {
            "common": r'(\S+) (\S+) (\S+) \[([^\]]+)\] "(\S+) (\S+) (\S+)" (\d+) (\S+)',
            "combined": r'(\S+) (\S+) (\S+) \[([^\]]+)\] "(\S+) (\S+) (\S+)" (\d+) (\S+) "([^"]*)" "([^"]*)"',
            "vhost_common": r'(\S+) (\S+) \[([^\]]+)\] "(\S+) (\S+) (\S+)" (\d+) (\S+)',
        }

        self.field_names = {
            "common": [
                "remote_host",
                "remote_logname",
                "remote_user",
                "time",
                "method",
                "request",
                "protocol",
                "status",
                "size",
            ],
            "combined": [
                "remote_host",
                "remote_logname",
                "remote_user",
                "time",
                "method",
                "request",
                "protocol",
                "status",
                "size",
                "referer",
                "user_agent",
            ],
            "vhost_common": [
                "remote_host",
                "remote_logname",
                "time",
                "method",
                "request",
                "protocol",
                "status",
                "size",
            ],
        }

        if self.log_format not in self.patterns:
            raise ValueError(f"Unknown log format: {self.log_format}. Supported: {', '.join(self.patterns.keys())}")

        super().__init__(filename, stream, codec=codec, binary=False, mode=mode, options=options)

        self.pattern = re.compile(self.patterns[self.log_format])
        self.keys = self.field_names[self.log_format]
        self.reset()
        pass

    def reset(self):
        """Reset iterable"""
        super().reset()
        self.pos = 0
        # File is already opened by parent class

    @staticmethod
    def has_totals() -> bool:
        """Has totals indicator"""
        return True

    def totals(self):
        """Returns file totals"""
        from ..helpers.utils import rowincount

        return rowincount(self.filename, self.fobj)

    @staticmethod
    def id() -> str:
        return "apachelog"

    @staticmethod
    def is_flatonly() -> bool:
        return True

    def read(self, skip_empty: bool = True) -> dict:
        """Read single Apache log record"""
        while True:
            line = self.fobj.readline()
            if not line:
                raise StopIteration

            line = line.strip()
            if skip_empty and len(line) == 0:
                continue

            # Parse log line
            match = self.pattern.match(line)
            if match:
                values = match.groups()
                result = dict(zip(self.keys, values, strict=False))
                self.pos += 1
                return result
            else:
                # If line doesn't match, return as raw line
                if not skip_empty:
                    return {"raw_line": line}
                # Otherwise skip and continue
                continue

    def write(self, record: Row) -> None:
        """Write single Apache log record"""
        # Reconstruct log line from dict
        if self.log_format == "common":
            remote_host = record.get("remote_host", "-")
            remote_logname = record.get("remote_logname", "-")
            remote_user = record.get("remote_user", "-")
            time = record.get("time", "-")
            method = record.get("method", "-")
            request = record.get("request", "-")
            protocol = record.get("protocol", "-")
            status = record.get("status", "-")
            size = record.get("size", "-")
            line = (
                f"{remote_host} {remote_logname} {remote_user} [{time}] "
                f'"{method} {request} {protocol}" {status} {size}\n'
            )
        elif self.log_format == "combined":
            remote_host = record.get("remote_host", "-")
            remote_logname = record.get("remote_logname", "-")
            remote_user = record.get("remote_user", "-")
            time = record.get("time", "-")
            method = record.get("method", "-")
            request = record.get("request", "-")
            protocol = record.get("protocol", "-")
            status = record.get("status", "-")
            size = record.get("size", "-")
            referer = record.get("referer", "-")
            user_agent = record.get("user_agent", "-")
            line = (
                f"{remote_host} {remote_logname} {remote_user} [{time}] "
                f'"{method} {request} {protocol}" {status} {size} '
                f'"{referer}" "{user_agent}"\n'
            )
        else:
            # Generic format
            line = " ".join([str(record.get(key, "-")) for key in self.keys]) + "\n"
        self.fobj.write(line)

    def write_bulk(self, records: list[Row]) -> None:
        """Write bulk Apache log records"""
        for record in records:
            self.write(record)
