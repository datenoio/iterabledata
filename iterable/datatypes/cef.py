from __future__ import annotations

import re
import typing
from typing import Any
from urllib.parse import unquote

from ..base import BaseCodec, BaseFileIterable
from ..helpers.utils import rowincount
from ..types import Row


class CEFIterable(BaseFileIterable):
    """
    Common Event Format (CEF) reader/writer.
    CEF format: CEF:Version|Device Vendor|Device Product|Device Version|Signature ID|Name|Severity|Extension
    """

    datamode = "text"

    def __init__(
        self,
        filename: str = None,
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

    @staticmethod
    def id() -> str:
        return "cef"

    @staticmethod
    def is_flatonly() -> bool:
        return True

    @staticmethod
    def has_totals() -> bool:
        """Has totals indicator"""
        return True

    def totals(self):
        """Returns file totals"""
        if self.codec is not None:
            fobj = self.codec.fileobj()
        else:
            fobj = self.fobj
        return rowincount(self.filename, fobj)

    def _parse_cef(self, line: str) -> dict:
        """Parse CEF line into dictionary"""
        # CEF format: CEF:Version|Device Vendor|Device Product|Device Version|Signature ID|Name|Severity|Extension
        if not line.startswith("CEF:"):
            return {"raw_line": line}

        # Remove CEF: prefix
        line = line[4:]

        # Split by pipe, but handle escaped pipes in extension
        parts = []
        current = ""
        escape_next = False
        for char in line:
            if escape_next:
                current += char
                escape_next = False
            elif char == "\\":
                escape_next = True
            elif char == "|" and not escape_next:
                parts.append(current)
                current = ""
            else:
                current += char
        if current:
            parts.append(current)

        result = {}

        # Standard CEF fields
        if len(parts) > 0:
            result["cef_version"] = parts[0]
        if len(parts) > 1:
            result["device_vendor"] = parts[1]
        if len(parts) > 2:
            result["device_product"] = parts[2]
        if len(parts) > 3:
            result["device_version"] = parts[3]
        if len(parts) > 4:
            result["signature_id"] = parts[4]
        if len(parts) > 5:
            result["name"] = parts[5]
        if len(parts) > 6:
            result["severity"] = parts[6]

        # Parse extension (key=value pairs)
        if len(parts) > 7:
            extension = parts[7]
            # Parse extension fields (key=value pairs, space-separated)
            # Handle escaped spaces and equals signs
            ext_parts = re.split(r"(?<!\\)=", extension)
            i = 0
            while i < len(ext_parts) - 1:
                key = ext_parts[i].strip().replace("\\=", "=").replace("\\ ", " ")
                value = ext_parts[i + 1]

                # Find the end of this value (next space that's not escaped, or end)
                # For simplicity, we'll split by spaces and reconstruct
                value_parts = []
                for j in range(i + 1, len(ext_parts)):
                    if j == i + 1:
                        value_parts.append(ext_parts[j])
                    else:
                        # Check if this starts a new key (has space before =)
                        if " " in ext_parts[j]:
                            space_idx = ext_parts[j].index(" ")
                            value_parts.append(ext_parts[j][:space_idx])
                            ext_parts[j] = ext_parts[j][space_idx + 1 :]
                            break
                        else:
                            value_parts.append(ext_parts[j])

                value = "=".join(value_parts).strip()
                # Unescape value
                value = (
                    value.replace("\\=", "=")
                    .replace("\\ ", " ")
                    .replace("\\n", "\n")
                    .replace("\\r", "\r")
                    .replace("\\t", "\t")
                )
                # URL decode
                try:
                    value = unquote(value)
                except Exception:
                    pass

                result[key] = value
                i += len(value_parts)

        return result

    def read(self, skip_empty: bool = True) -> dict:
        """Read single CEF record"""
        while True:
            line = self.fobj.readline()
            if not line:
                raise StopIteration

            line = line.strip()
            if skip_empty and len(line) == 0:
                continue

            result = self._parse_cef(line)
            self.pos += 1
            return result

    def _escape_cef_value(self, value: str) -> str:
        """Escape CEF value"""
        return (
            str(value)
            .replace("\\", "\\\\")
            .replace("|", "\\|")
            .replace("=", "\\=")
            .replace("\n", "\\n")
            .replace("\r", "\\r")
            .replace("\t", "\\t")
        )

    def write(self, record: Row) -> None:
        """Write single CEF record"""
        # Build CEF line
        parts = []

        # Standard CEF fields
        parts.append(str(record.get("cef_version", "0")))
        parts.append(str(record.get("device_vendor", "-")))
        parts.append(str(record.get("device_product", "-")))
        parts.append(str(record.get("device_version", "-")))
        parts.append(str(record.get("signature_id", "-")))
        parts.append(str(record.get("name", "-")))
        parts.append(str(record.get("severity", "0")))

        # Build extension
        extension_parts = []
        for key, value in record.items():
            if key not in [
                "cef_version",
                "device_vendor",
                "device_product",
                "device_version",
                "signature_id",
                "name",
                "severity",
            ]:
                escaped_key = self._escape_cef_value(key)
                escaped_value = self._escape_cef_value(value)
                extension_parts.append(f"{escaped_key}={escaped_value}")

        if extension_parts:
            parts.append(" ".join(extension_parts))

        line = "CEF:" + "|".join(parts) + "\n"
        self.fobj.write(line)

    def write_bulk(self, records: list[Row]) -> None:
        """Write bulk CEF records"""
        for record in records:
            self.write(record)
