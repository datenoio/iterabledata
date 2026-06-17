from __future__ import annotations

import typing

try:
    import bencode

    HAS_BENCODE = True
except ImportError:
    try:
        import bencodepy

        HAS_BENCODEPY = True
        HAS_BENCODE = False
    except ImportError:
        HAS_BENCODEPY = False
        HAS_BENCODE = False

from typing import Any

from ..base import BaseCodec, BaseFileIterable
from ..types import Row


class BencodeIterable(BaseFileIterable):
    datamode = "binary"

    def __init__(
        self,
        filename: str | None = None,
        stream: typing.IO[Any] | None = None,
        codec: BaseCodec | None = None,
        mode: str = "r",
        options: dict[str, Any] | None = None,
    ):
        if options is None:
            options = {}
        if not HAS_BENCODE and not HAS_BENCODEPY:
            raise ImportError("Bencode support requires 'bencode' or 'bencodepy' package")
        super().__init__(filename, stream, codec=codec, mode=mode, binary=True, options=options)
        self.reset()
        pass

    def reset(self):
        """Reset iterable"""
        super().reset()
        self.pos = 0
        if self.mode == "r":
            content = self.fobj.read()

            if HAS_BENCODE:
                try:
                    data = bencode.bdecode(content)
                    if isinstance(data, dict):
                        # Torrent file structure
                        if "info" in data:
                            # Single torrent file
                            self.items = [self._convert_to_dict(data)]
                        else:
                            # Multiple entries
                            self.items = [self._convert_to_dict(data)]
                    elif isinstance(data, list):
                        self.items = [self._convert_to_dict(item) for item in data]
                    else:
                        self.items = [{"value": data}]
                except Exception:
                    self.items = []
            else:
                # bencodepy
                try:
                    decoder = bencodepy.BencodeDecoder()
                    data = decoder.decode(content)
                    if isinstance(data, dict):
                        self.items = [self._convert_to_dict(data)]
                    elif isinstance(data, list):
                        self.items = [self._convert_to_dict(item) for item in data]
                    else:
                        self.items = [{"value": data}]
                except Exception:
                    self.items = []

            self.iterator = iter(self.items)
        else:
            self.items = []

    @staticmethod
    def id() -> str:
        return "bencode"

    @staticmethod
    def is_flatonly() -> bool:
        return False

    def _convert_to_dict(self, obj):
        """Convert bencode object to Python dict"""
        if isinstance(obj, dict):
            result = {}
            for k, v in obj.items():
                key = k.decode("utf-8") if isinstance(k, bytes) else str(k)
                result[key] = self._convert_to_dict(v)
            return result
        elif isinstance(obj, list):
            return [self._convert_to_dict(item) for item in obj]
        elif isinstance(obj, bytes):
            try:
                return obj.decode("utf-8")
            except Exception:
                return obj.hex()
        else:
            return obj

    def read(self, skip_empty: bool = True) -> dict:
        """Read single Bencode record"""
        row = next(self.iterator)
        self.pos += 1

        if isinstance(row, dict):
            return row
        else:
            return {"value": row}

    def write(self, record: Row) -> None:
        """Write single Bencode record"""
        if HAS_BENCODE:
            bencode_data = bencode.bencode(record)
        else:
            encoder = bencodepy.BencodeEncoder()
            bencode_data = encoder.encode(record)
        self.fobj.write(bencode_data)

    def write_bulk(self, records: list[Row]) -> None:
        """Write bulk Bencode records"""
        for record in records:
            self.write(record)
