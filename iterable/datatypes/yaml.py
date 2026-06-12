from __future__ import annotations

import typing

try:
    import yaml

    HAS_YAML = True
except ImportError:
    HAS_YAML = False

from typing import Any

from ..base import BaseCodec, BaseFileIterable
from ..types import Row


class YAMLIterable(BaseFileIterable):
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
        if not HAS_YAML:
            raise ImportError("YAML support requires 'pyyaml' package")
        super().__init__(filename, stream, codec=codec, binary=False, mode=mode, encoding=encoding, options=options)
        self.reset()
        pass

    def reset(self):
        """Reset iterable"""
        super().reset()
        self.pos = 0
        if self.mode == "r":
            # YAML can have multiple documents separated by ---
            self.documents = list(yaml.safe_load_all(self.fobj))
            self.current_doc = 0
            self.current_pos = 0
            # If documents are lists, iterate over items; otherwise treat as single-item lists
            self.data = []
            for doc in self.documents:
                if doc is None:
                    continue  # Skip empty documents
                if isinstance(doc, list):
                    self.data.extend(doc)
                elif isinstance(doc, dict):
                    self.data.append(doc)
                else:
                    self.data.append({"value": doc})
        else:
            self.data = []

    @staticmethod
    def id() -> str:
        return "yaml"

    @staticmethod
    def is_flatonly() -> bool:
        return False

    def read(self, skip_empty: bool = True) -> dict:
        """Read single YAML record"""
        if self.pos >= len(self.data):
            raise StopIteration
        row = self.data[self.pos]
        self.pos += 1
        return row

    def write(self, record: Row) -> None:
        """Write single YAML record"""
        if self._validation_hooks:
            validated = self._apply_validation_hooks(record)
            if validated is None:
                return
            record = validated
        yaml.dump(record, self.fobj, default_flow_style=False, allow_unicode=True)
        self.fobj.write("---\n")

    def write_bulk(self, records: list[Row]) -> None:
        """Write bulk YAML records"""
        if self._validation_hooks:
            validated_records = []
            for record in records:
                validated = self._apply_validation_hooks(record)
                if validated is not None:
                    validated_records.append(validated)
            records = validated_records
        for record in records:
            yaml.dump(record, self.fobj, default_flow_style=False, allow_unicode=True)
            self.fobj.write("---\n")
