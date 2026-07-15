"""TAR multi-file container.

Iterates the data members of a TAR archive (``.tar``, ``.tar.gz``/``.tgz``,
``.tar.bz2``, ``.tar.xz``; ``.tar.zst`` via the ZStandard codec layer). Each
member's format is detected from its name and delegated to that format's
reader, and every yielded record is tagged with the originating member name.

Members are read as in-memory streams directly from the archive; nothing is
ever extracted to disk. Members with absolute paths or ``..`` traversal
components are skipped. Read-only.
"""

from __future__ import annotations

import fnmatch
import io
import logging
import posixpath
import tarfile
import typing
from typing import Any

from ..base import BaseCodec, BaseFileIterable
from ..exceptions import WriteNotSupportedError
from ..types import Row

logger = logging.getLogger(__name__)

DEFAULT_MEMBER_KEY = "_member"


def _member_binary_stream(raw: typing.IO[bytes]) -> typing.IO[bytes]:
    """Return a well-behaved binary stream for a tar member.

    Members of seekable archives (``r:*``) are proper buffered readers and are
    passed through. In stream mode (``r|*``, used for non-seekable sources such
    as ``.tar.zst`` codec streams) the member object sits on tarfile's internal
    ``_Stream``, which breaks ``seekable()``/``TextIOWrapper`` and cannot be
    reset by format readers, so the member is buffered in memory. The archive
    itself is still processed one member at a time.
    """
    try:
        if raw.seekable():
            return raw
    except (AttributeError, OSError):
        pass
    return io.BytesIO(raw.read())


class TARIterable(BaseFileIterable):
    """Read-only container that iterates records of the files inside a TAR archive."""

    datamode = "binary"

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
        if mode not in ("r", "rb"):
            raise WriteNotSupportedError("tar", "TAR container is read-only")

        # Member selection: exact name, glob pattern, or list of either.
        members = options.pop("members", None) or options.pop("member", None)
        if isinstance(members, str):
            members = [members]
        self._member_patterns: list[str] | None = members

        # Key used to tag records with the member name; None disables tagging.
        self._member_key = options.pop("member_key", DEFAULT_MEMBER_KEY)

        self._tar: tarfile.TarFile | None = None
        self._members_iter: typing.Iterator[tarfile.TarInfo] | None = None
        self._current: BaseFileIterable | None = None
        self._current_name: str | None = None

        super().__init__(
            filename=filename,
            stream=stream,
            codec=codec,
            binary=True,
            mode="r",
            encoding=encoding,
            options=options,
        )
        self._open_archive()

    @staticmethod
    def id() -> str:
        return "tar"

    @staticmethod
    def is_flatonly() -> bool:
        return False

    def is_streaming(self) -> bool:
        """Members are streamed one by one; records stream within each member."""
        return True

    def _open_archive(self) -> None:
        fobj = self.fobj
        if fobj is None:
            raise ValueError("TARIterable requires a filename, stream, or codec")
        seekable = bool(getattr(fobj, "seekable", lambda: False)())
        # "r:*" needs a seekable file; "r|*" reads strictly forward, which is
        # all this container needs (members are visited in archive order).
        tar_mode = "r:*" if seekable else "r|*"
        self._tar = tarfile.open(fileobj=fobj, mode=tar_mode)  # noqa: S202 - members are never extracted
        self._members_iter = iter(self._tar)
        self._current = None
        self._current_name = None

    @staticmethod
    def _is_safe_member(member: tarfile.TarInfo) -> bool:
        """Reject absolute paths and `..` traversal components."""
        name = member.name
        if name.startswith(("/", "\\")) or (len(name) > 1 and name[1] == ":"):
            return False
        parts = posixpath.normpath(name.replace("\\", "/")).split("/")
        return ".." not in parts

    def _member_selected(self, name: str) -> bool:
        if self._member_patterns is None:
            return True
        return any(fnmatch.fnmatch(name, pattern) or name == pattern for pattern in self._member_patterns)

    def _open_member(self, member: tarfile.TarInfo) -> BaseFileIterable | None:
        """Open a member as an iterable, or return None to skip it."""
        from ..helpers.detect import detect_file_type

        if not member.isfile():
            return None
        if not self._is_safe_member(member):
            logger.warning("tar: skipping unsafe member path %r (absolute or traversal)", member.name)
            return None
        if not self._member_selected(member.name):
            return None

        result = detect_file_type(member.name)
        if not result.get("success") or result.get("datatype") is None:
            logger.debug("tar: skipping member %r (format not detected)", member.name)
            return None
        datatype_cls = result["datatype"]
        codec_cls = result["codec"]

        assert self._tar is not None
        raw = self._tar.extractfile(member)
        if raw is None:
            return None

        member_fobj = _member_binary_stream(raw)
        try:
            if codec_cls is not None:
                codec = codec_cls(fileobj=member_fobj, mode="r")
                return datatype_cls(codec=codec, mode="r", encoding=self.encoding)
            if getattr(datatype_cls, "datamode", "text") == "binary":
                return datatype_cls(stream=member_fobj, mode="r")
            text = io.TextIOWrapper(member_fobj, encoding=self.encoding)
            return datatype_cls(stream=text, mode="r", encoding=self.encoding)
        except ImportError as e:
            logger.warning("tar: skipping member %r (missing dependency: %s)", member.name, e)
            return None

    def _advance_member(self) -> None:
        """Move to the next readable member or raise StopIteration."""
        assert self._members_iter is not None
        while True:
            member = next(self._members_iter)  # StopIteration ends the container
            iterable = self._open_member(member)
            if iterable is not None:
                self._current = iterable
                self._current_name = member.name
                return

    def read(self, skip_empty: bool = True) -> Row:
        """Read a single record from the current member, advancing members as needed."""
        while True:
            if self._current is None:
                self._advance_member()
            try:
                row = self._current.read(skip_empty=skip_empty)
            except StopIteration:
                self._current.close()
                self._current = None
                self._current_name = None
                continue
            if isinstance(row, dict) and self._member_key:
                row = dict(row)
                row[self._member_key] = self._current_name
            return row

    def reset(self) -> None:
        """Reset to the first member of the archive."""
        if self._current is not None:
            self._current.close()
            self._current = None
            self._current_name = None
        if self._tar is not None:
            self._tar.close()
            self._tar = None
        fobj = self.fobj
        if fobj is not None and getattr(fobj, "seekable", lambda: False)():
            fobj.seek(0)
        else:
            super().reset()
        self._open_archive()

    def close(self) -> None:
        if getattr(self, "_closed", False):
            return
        if self._current is not None:
            self._current.close()
            self._current = None
        if self._tar is not None:
            self._tar.close()
            self._tar = None
        super().close()

    def list_members(self) -> list[str]:
        """Return the names of safe, regular-file members (seekable archives only)."""
        assert self._tar is not None
        return [m.name for m in self._tar.getmembers() if m.isfile() and self._is_safe_member(m)]

    def write(self, record: Row) -> None:
        raise WriteNotSupportedError("tar", "TAR container is read-only")

    def write_bulk(self, records: list[Row]) -> None:
        raise WriteNotSupportedError("tar", "TAR container is read-only")
