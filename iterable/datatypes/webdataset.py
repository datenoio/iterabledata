"""WebDataset TAR shard reader.

Groups TAR members that share a key (basename without the final extension) into
one sample dict per key. Unlike :class:`~iterable.datatypes.tar.TARIterable`,
this does not delegate members to other format readers — payloads stay as
bytes (with optional JSON/text decoding).

Example sample::

    {"__key__": "0001", "jpg": b"...", "json": {"label": "cat"}, "txt": "cat"}

Options:
    decode_json (bool): Decode ``.json`` members to dicts (default True).
    partial_group ("error"|"yield"): Behavior when the last sample group is
        incomplete at end of shard (default ``"error"``).

Read-only. Format id: ``webdataset``. Does not change default TAR behavior.
"""

from __future__ import annotations

import json
import posixpath
import tarfile
import typing
from collections import Counter
from typing import Any

from ..base import BaseCodec, BaseFileIterable
from ..exceptions import FormatParseError, WriteNotSupportedError
from ..types import Row

_TEXT_SUFFIXES = frozenset({"txt", "text", "cls", "caption", "url", "uri", "html", "xml", "csv", "tsv", "md"})


def _sample_key_and_suffix(member_name: str) -> tuple[str, str]:
    """Return (key, suffix) for a WebDataset member path."""
    base = posixpath.basename(member_name.replace("\\", "/"))
    if "." in base:
        key, suffix = base.rsplit(".", 1)
        return key, suffix.lower()
    return base, ""


def _is_safe_member(name: str) -> bool:
    if name.startswith(("/", "\\")) or (len(name) > 1 and name[1] == ":"):
        return False
    parts = posixpath.normpath(name.replace("\\", "/")).split("/")
    return ".." not in parts


class WebDatasetIterable(BaseFileIterable):
    """Read-only WebDataset sample iterable over a TAR shard."""

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
            raise WriteNotSupportedError("webdataset", "WebDataset is read-only")
        self._decode_json = bool(options.pop("decode_json", True))
        partial = options.pop("partial_group", "error")
        if partial not in ("error", "yield"):
            raise ValueError('partial_group must be "error" or "yield"')
        self._partial_group = partial
        self._tar: tarfile.TarFile | None = None
        self._samples: list[dict[str, Any]] = []
        self._iterator: typing.Iterator[dict[str, Any]] | None = None
        super().__init__(
            filename=filename,
            stream=stream,
            codec=codec,
            binary=True,
            mode="r",
            encoding=encoding,
            options=options,
        )
        self.reset()

    @staticmethod
    def id() -> str:
        return "webdataset"

    @staticmethod
    def is_flatonly() -> bool:
        return False

    def is_streaming(self) -> bool:
        return False

    def _open_tar(self) -> tarfile.TarFile:
        fobj = self.fobj
        if fobj is None:
            raise ValueError("WebDatasetIterable requires a filename, stream, or codec")
        seekable = bool(getattr(fobj, "seekable", lambda: False)())
        tar_mode = "r:*" if seekable else "r|*"
        return tarfile.open(fileobj=fobj, mode=tar_mode)  # noqa: S202

    def _decode_payload(self, suffix: str, raw: bytes) -> Any:
        if suffix == "json" and self._decode_json:
            return json.loads(raw.decode(self.encoding))
        if suffix in _TEXT_SUFFIXES:
            return raw.decode(self.encoding, errors="replace")
        return raw

    def _build_samples(self) -> list[dict[str, Any]]:
        assert self._tar is not None
        groups: dict[str, dict[str, Any]] = {}
        order: list[str] = []

        for member in self._tar:
            if not member.isfile():
                continue
            if not _is_safe_member(member.name):
                continue
            key, suffix = _sample_key_and_suffix(member.name)
            if not suffix:
                continue
            extracted = self._tar.extractfile(member)
            if extracted is None:
                continue
            raw = extracted.read()
            payload = self._decode_payload(suffix, raw)
            if key not in groups:
                groups[key] = {"__key__": key}
                order.append(key)
            groups[key][suffix] = payload

        samples = [groups[k] for k in order]
        if not samples:
            return samples

        # Partial trailing group: WebDataset shards ideally contain complete
        # samples. We treat a group with only __key__ as incomplete (shouldn't
        # happen). More usefully, callers may expect every sample to have more
        # than one suffix; we flag incompleteness when the last sample has
        # fewer suffixes than the modal count among prior samples.
        if len(samples) >= 2:
            counts = [len(s) - 1 for s in samples[:-1]]  # exclude __key__
            if counts:
                expected = Counter(counts).most_common(1)[0][0]
                last_count = len(samples[-1]) - 1
                if last_count < expected and expected > 0:
                    if self._partial_group == "error":
                        raise FormatParseError(
                            "webdataset",
                            f"Incomplete trailing WebDataset sample group "
                            f"{samples[-1].get('__key__')!r} "
                            f"(has {last_count} suffixes, expected {expected})",
                        )
                    # yield: keep partial sample
        return samples

    def reset(self) -> None:
        if self._tar is not None:
            try:
                self._tar.close()
            except Exception:
                pass
            self._tar = None
        super().reset()
        self.pos = 0
        # After super().reset(), fobj is rewound / reopened
        self._tar = self._open_tar()
        self._samples = self._build_samples()
        self._iterator = iter(self._samples)

    def close(self) -> None:
        if getattr(self, "_closed", False):
            return
        if self._tar is not None:
            try:
                self._tar.close()
            except Exception:
                pass
            self._tar = None
        super().close()

    def read(self, skip_empty: bool = True) -> Row:
        if self._iterator is None:
            raise StopIteration
        row = next(self._iterator)
        self.pos += 1
        return row

    def write(self, record: Row) -> None:
        raise WriteNotSupportedError("webdataset", "WebDataset is read-only")

    def write_bulk(self, records: list[Row]) -> None:
        raise WriteNotSupportedError("webdataset", "WebDataset is read-only")
