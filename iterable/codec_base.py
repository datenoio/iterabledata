"""Base compression codec class."""

from __future__ import annotations

import io
import typing
from types import TracebackType
from typing import Any


class BaseCodec:
    """Basic codec class."""

    def __init__(
        self,
        filename: str | None = None,
        fileobj: typing.IO[Any] | None = None,
        mode: str = "r",
        open_it: bool = False,
        options: dict[str, Any] | None = None,
    ) -> None:
        if options is None:
            options = {}
        self._fileobj: typing.IO[Any] | None = fileobj
        self.filename = filename
        self.mode = mode
        if open_it:
            self.open()

        if len(options) > 0:
            for k, v in options.items():
                setattr(self, k, v)

    @staticmethod
    def fileexts() -> list[str]:
        """Return file extensions."""
        raise NotImplementedError

    def reset(self) -> None:
        """Reset file."""
        self.close()
        self.open()

    def open(self) -> None:
        """Open codec file object."""
        raise NotImplementedError

    def fileobj(self) -> typing.IO[Any]:
        """Return file object."""
        if self._fileobj is None:
            raise ValueError("File object is not initialized")
        return self._fileobj

    def close(self) -> None:
        """Close codec. Not implemented by default."""
        raise NotImplementedError

    def __enter__(self) -> BaseCodec:
        """Context manager entry."""
        if self._fileobj is None and self.filename is not None:
            self.open()
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        """Context manager exit."""
        self.close()

    def textIO(self, encoding: str = "utf8") -> io.TextIOWrapper:
        """Return text wrapper over binary stream."""
        return io.TextIOWrapper(self.fileobj(), encoding=encoding, write_through=False)
