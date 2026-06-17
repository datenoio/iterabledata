from __future__ import annotations

import typing
from typing import Any

from ..base import BaseCodec
from .csv import CSVIterable


class PSVIterable(CSVIterable):
    """Pipe-Separated Values iterable - extends CSV with pipe delimiter"""

    def __init__(
        self,
        filename: str | None = None,
        stream: typing.IO[Any] | None = None,
        codec: BaseCodec | None = None,
        keys: list[str] | None = None,
        quotechar: str = '"',
        mode: str = "r",
        encoding: str | None = None,
        autodetect: bool = False,
        options: dict[str, Any] | None = None,
    ):
        # Force delimiter to pipe
        if options is None:
            options = {}
        options["delimiter"] = "|"
        super().__init__(
            filename,
            stream,
            codec=codec,
            keys=keys,
            delimiter="|",
            quotechar=quotechar,
            mode=mode,
            encoding=encoding,
            autodetect=False,
            options=options,
        )

    @staticmethod
    def id() -> str:
        return "psv"

    @staticmethod
    def is_flatonly() -> bool:
        return True


class SSVIterable(CSVIterable):
    """Semicolon-Separated Values iterable - extends CSV with semicolon delimiter"""

    def __init__(
        self,
        filename: str | None = None,
        stream: typing.IO[Any] | None = None,
        codec: BaseCodec | None = None,
        keys: list[str] | None = None,
        quotechar: str = '"',
        mode: str = "r",
        encoding: str | None = None,
        autodetect: bool = False,
        options: dict[str, Any] | None = None,
    ):
        # Force delimiter to semicolon
        if options is None:
            options = {}
        options["delimiter"] = ";"
        super().__init__(
            filename,
            stream,
            codec=codec,
            keys=keys,
            delimiter=";",
            quotechar=quotechar,
            mode=mode,
            encoding=encoding,
            autodetect=False,
            options=options,
        )

    @staticmethod
    def id() -> str:
        return "ssv"

    @staticmethod
    def is_flatonly() -> bool:
        return True
