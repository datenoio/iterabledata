from __future__ import annotations

import typing

try:
    import vobject

    HAS_VOBJECT = True
except ImportError:
    try:
        import vcard

        HAS_VCARD = True
        HAS_VOBJECT = False
    except ImportError:
        HAS_VCARD = False
        HAS_VOBJECT = False

from typing import Any

from ..base import BaseCodec, BaseFileIterable
from ..types import Row


class VCFIterable(BaseFileIterable):
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
        if not HAS_VOBJECT and not HAS_VCARD:
            raise ImportError("VCF support requires 'vobject' or 'vcard' package")
        super().__init__(filename, stream, codec=codec, binary=False, mode=mode, encoding=encoding, options=options)
        self.reset()
        pass

    def _parse_entry(self, part: str, row_number: int) -> dict | None:
        """Parse one vCard block, routing failures through the error policy."""
        try:
            vcard_str = "BEGIN:VCARD\n" + part
            if HAS_VOBJECT:
                if not vcard_str.endswith("\nEND:VCARD"):
                    vcard_str += "\nEND:VCARD"
                vcard_obj = vobject.readOne(vcard_str)
            else:
                vcard_obj = vcard.read_vcard(vcard_str)
            return self._vcard_to_dict(vcard_obj)
        except Exception as e:
            entry = self._parse_vcard_manual(part)
            if entry:
                return entry
            # Manual fallback also failed: apply on_error policy
            # ("raise" raises FormatParseError; "skip"/"warn" drop the entry).
            self._handle_parse_failure(
                "Failed to parse vCard entry",
                e,
                row_number=row_number,
                original_line=part[:200],
            )
            return None

    def reset(self):
        """Reset iterable"""
        super().reset()
        self.pos = 0
        if self.mode == "r":
            content = self.fobj.read()
            self.entries = []
            parts = content.split("BEGIN:VCARD")
            row_number = 0
            for part in parts:
                part = part.strip()
                if not part:
                    continue
                row_number += 1
                entry = self._parse_entry(part, row_number)
                if entry is not None:
                    self.entries.append(entry)

            if content.strip() and not self.entries and self._on_error == "raise":
                # Non-empty input that produced zero entries must not read as
                # a valid empty dataset under the default policy.
                self._handle_parse_failure("No parseable vCard entries found in non-empty input")

            self.iterator = iter(self.entries)
        else:
            self.entries = []

    @staticmethod
    def id() -> str:
        return "vcf"

    @staticmethod
    def is_flatonly() -> bool:
        return False

    def _vcard_to_dict(self, vcard_obj):
        """Convert vCard object to dictionary"""
        result = {}

        if HAS_VOBJECT:
            for child in vcard_obj.getChildren():
                key = child.name.lower()
                value = str(child.value) if hasattr(child, "value") else str(child)

                if key in result:
                    if not isinstance(result[key], list):
                        result[key] = [result[key]]
                    result[key].append(value)
                else:
                    result[key] = value
        else:
            # vcard library
            for key, value in vcard_obj.items():
                result[key.lower()] = value

        return result

    def _parse_vcard_manual(self, content):
        """Manual parsing fallback"""
        entry = {}
        for line in content.split("\n"):
            line = line.strip()
            if not line or line.startswith("END:"):
                continue
            if ":" in line:
                key, value = line.split(":", 1)
                key = key.split(";")[0].lower()  # Remove parameters
                if key in entry:
                    if not isinstance(entry[key], list):
                        entry[key] = [entry[key]]
                    entry[key].append(value)
                else:
                    entry[key] = value
        return entry if entry else None

    def read(self, skip_empty: bool = True) -> dict:
        """Read single VCF record"""
        row = next(self.iterator)
        self.pos += 1
        return row

    def write(self, record: Row) -> None:
        """Write single VCF record"""
        self.fobj.write("BEGIN:VCARD\n")
        self.fobj.write("VERSION:3.0\n")

        for key, value in record.items():
            if isinstance(value, list):
                for v in value:
                    self.fobj.write(f"{key.upper()}:{v}\n")
            else:
                self.fobj.write(f"{key.upper()}:{value}\n")

        self.fobj.write("END:VCARD\n\n")

    def write_bulk(self, records: list[Row]) -> None:
        """Write bulk VCF records"""
        for record in records:
            self.write(record)
