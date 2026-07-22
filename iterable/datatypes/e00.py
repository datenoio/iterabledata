"""Experimental ArcInfo Interchange (``.e00``) text export reader."""

from __future__ import annotations

import typing
from typing import Any

from ..base import DEFAULT_BULK_NUMBER, BaseCodec, BaseFileIterable
from ..exceptions import WriteNotSupportedError
from ..types import Row

# Recognizable coverage section keywords (best-effort subset).
_SUPPORTED_SECTIONS = {"ARC", "PAL", "LAB"}
_KNOWN_SECTIONS = {
    "ARC",
    "PAL",
    "LAB",
    "CNT",
    "TOL",
    "SIN",
    "LOG",
    "PRJ",
    "TX6",
    "TX7",
    "RXP",
    "RPL",
    "IFO",
    "MTD",
    "BND",
    "TIC",
    "LNK",
}
_END_MARKERS = {"EOA", "EOP", "EOL", "EOI", "EOS", "EOT", "EOD", "EOX"}


class E00Iterable(BaseFileIterable):
    """Best-effort reader for simple ARC/INFO E00 text exports.

    Yields records for recognizable ``ARC`` / ``PAL`` / ``LAB`` sections as
    dicts with a ``type`` field and section-specific fields. Unsupported
    coverage constructs raise ``ValueError`` with a clear message.
    """

    datamode = "text"

    def __init__(
        self,
        filename: str | None = None,
        stream: typing.IO[Any] | None = None,
        codec: BaseCodec | None = None,
        mode: str = "r",
        encoding: str = "utf-8",
        options: dict[str, Any] | None = None,
    ):
        if options is None:
            options = {}
        if mode not in ("r",):
            raise WriteNotSupportedError("e00", "E00 is read-only")
        self._iterator: typing.Iterator[Row] | None = None
        super().__init__(
            filename,
            stream,
            codec=codec,
            binary=False,
            mode=mode,
            encoding=encoding,
            options=options,
        )
        self.reset()

    def reset(self) -> None:
        super().reset()
        self.pos = 0
        if self.mode == "r":
            self._iterator = self._parse()
        else:
            self._iterator = iter([])

    def _lines(self) -> typing.Iterator[str]:
        if self.fobj is not None:
            if hasattr(self.fobj, "seek"):
                self.fobj.seek(0)
            for line in self.fobj:
                yield line.rstrip("\r\n")
        elif self.filename is not None:
            with open(self.filename, encoding=self.encoding) as f:
                for line in f:
                    yield line.rstrip("\r\n")
        else:
            raise ValueError("E00 requires a filename or stream")

    @staticmethod
    def _section_name(line: str) -> str | None:
        parts = line.strip().split()
        if not parts:
            return None
        token = parts[0].upper()
        if token in _KNOWN_SECTIONS:
            return token
        return None

    def _parse(self) -> typing.Iterator[Row]:
        lines = list(self._lines())
        if not lines:
            raise ValueError("Empty or unsupported E00 file")

        # Require a recognizable interchange header or section.
        first = lines[0].strip().upper()
        if not (first.startswith("EXP") or first.startswith("ARC") or "E00" in first):
            # Still allow files that jump straight into a known section.
            if self._section_name(lines[0]) is None and not any(
                self._section_name(ln) in _SUPPORTED_SECTIONS for ln in lines
            ):
                raise ValueError("Unsupported E00 content: expected EXP header or ARC/PAL/LAB sections")

        i = 0
        found_supported = False
        while i < len(lines):
            line = lines[i]
            section = self._section_name(line)
            if section is None:
                i += 1
                continue
            if section not in _SUPPORTED_SECTIONS:
                raise ValueError(
                    f"Unsupported E00 section '{section}': only ARC, PAL, and LAB "
                    "are handled by this experimental reader"
                )
            found_supported = True
            i += 1
            body: list[str] = []
            while i < len(lines):
                cur = lines[i]
                end_tok = cur.strip().split()[0].upper() if cur.strip() else ""
                if end_tok in _END_MARKERS or self._section_name(cur) is not None:
                    break
                if cur.strip():
                    body.append(cur)
                i += 1
            yield from self._emit_section(section, body)
            # Skip end marker if present
            if i < len(lines):
                end_tok = lines[i].strip().split()[0].upper() if lines[i].strip() else ""
                if end_tok in _END_MARKERS:
                    i += 1

        if not found_supported:
            raise ValueError("Unsupported E00 file: no recognizable ARC/PAL/LAB sections found")

    def _emit_section(self, section: str, body: list[str]) -> typing.Iterator[Row]:
        if section == "ARC":
            yield from self._emit_arcs(body)
        elif section == "PAL":
            yield from self._emit_pals(body)
        elif section == "LAB":
            yield from self._emit_labs(body)

    def _emit_arcs(self, body: list[str]) -> typing.Iterator[Row]:
        """Parse ARC records: header ints then coordinate pairs."""
        i = 0
        while i < len(body):
            parts = body[i].split()
            # Arc header typically: cover-id from to left right npoints ...
            ints: list[int] = []
            try:
                ints = [int(float(p)) for p in parts]
            except ValueError:
                # Unexpected non-integer line — treat remainder as unsupported.
                raise ValueError(f"Unsupported E00 ARC construct near: {body[i]!r}") from None
            if len(ints) < 1:
                i += 1
                continue
            npoints = ints[6] if len(ints) > 6 else (ints[-1] if ints else 0)
            arc_id = ints[0]
            i += 1
            coords: list[list[float]] = []
            while i < len(body) and len(coords) < max(npoints, 0):
                nums = body[i].split()
                floats: list[float] = []
                try:
                    floats = [float(p) for p in nums]
                except ValueError:
                    break
                # Coordinates come as x y pairs (possibly multiple per line)
                for j in range(0, len(floats) - 1, 2):
                    coords.append([floats[j], floats[j + 1]])
                i += 1
                if npoints and len(coords) >= npoints:
                    break
            yield {
                "type": "ARC",
                "id": arc_id,
                "from_node": ints[1] if len(ints) > 1 else None,
                "to_node": ints[2] if len(ints) > 2 else None,
                "left_poly": ints[3] if len(ints) > 3 else None,
                "right_poly": ints[4] if len(ints) > 4 else None,
                "npoints": npoints,
                "coordinates": coords,
                "fields": ints,
            }

    def _emit_pals(self, body: list[str]) -> typing.Iterator[Row]:
        for line in body:
            parts = line.split()
            if not parts:
                continue
            try:
                nums = [float(p) for p in parts]
            except ValueError:
                raise ValueError(f"Unsupported E00 PAL construct near: {line!r}") from None
            yield {
                "type": "PAL",
                "fields": nums,
                "id": int(nums[0]) if nums else None,
            }

    def _emit_labs(self, body: list[str]) -> typing.Iterator[Row]:
        i = 0
        while i < len(body):
            parts = body[i].split()
            try:
                nums = [float(p) for p in parts]
            except ValueError:
                raise ValueError(f"Unsupported E00 LAB construct near: {body[i]!r}") from None
            lab_id = int(nums[0]) if nums else None
            # LAB often: id poly-id  then next line x y
            x = y = None
            if len(nums) >= 3:
                x, y = nums[-2], nums[-1]
            elif i + 1 < len(body):
                nxt = body[i + 1].split()
                try:
                    floats = [float(p) for p in nxt]
                    if len(floats) >= 2:
                        x, y = floats[0], floats[1]
                        i += 1
                except ValueError:
                    pass
            yield {"type": "LAB", "id": lab_id, "x": x, "y": y, "fields": nums}
            i += 1

    @staticmethod
    def id() -> str:
        return "e00"

    @staticmethod
    def is_flatonly() -> bool:
        return True

    def is_streaming(self) -> bool:
        return True

    def read(self, skip_empty: bool = True) -> Row:
        assert self._iterator is not None
        row = next(self._iterator)
        self.pos += 1
        return row

    def read_bulk(self, num: int = DEFAULT_BULK_NUMBER) -> list[Row]:
        rows: list[Row] = []
        for _ in range(num):
            try:
                rows.append(self.read())
            except StopIteration:
                break
        return rows

    def write(self, record: Row) -> None:
        raise WriteNotSupportedError("e00", "E00 is read-only")

    def write_bulk(self, records: list[Row]) -> None:
        raise WriteNotSupportedError("e00", "E00 is read-only")
