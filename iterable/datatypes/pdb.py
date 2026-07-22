"""PDB Protein Data Bank format (stdlib-only)."""

from __future__ import annotations

import typing
from typing import Any

from ..base import BaseCodec, BaseFileIterable
from ..types import Row


def _safe_int(text: str, default: int | None = None) -> int | None:
    text = text.strip()
    if not text:
        return default
    try:
        return int(text)
    except ValueError:
        return default


def _safe_float(text: str, default: float | None = None) -> float | None:
    text = text.strip()
    if not text:
        return default
    try:
        return float(text)
    except ValueError:
        return default


class PDBIterable(BaseFileIterable):
    """PDB reader/writer for ATOM/HETATM coordinate records.

    Yields ``{record_type, serial, name, resName, chainID, resSeq, x, y, z,
    element, model}``. Multi-model files track MODEL/ENDMDL; pass
    ``options={"model": N}`` to filter a single model.
    """

    datamode = "text"

    def __init__(
        self,
        filename: str | None = None,
        stream: typing.IO[Any] | None = None,
        codec: BaseCodec | None = None,
        mode: str = "r",
        encoding: str = "utf-8",
        model: int | None = None,
        options: dict[str, Any] | None = None,
    ):
        if options is None:
            options = {}
        self.model_filter = options.get("model", model)
        if self.model_filter is not None:
            self.model_filter = int(self.model_filter)
        super().__init__(
            filename,
            stream,
            codec=codec,
            binary=False,
            mode=mode,
            encoding=encoding,
            options=options,
        )
        self._iterator: typing.Iterator[Row] | None = None
        self.pos = 0
        self.reset()

    def reset(self) -> None:
        """Reset and (re)build ATOM/HETATM iterator."""
        super().reset()
        self.pos = 0
        if self.mode != "r":
            self._iterator = iter([])
            return
        self._iterator = self._yield_atoms()

    def _iter_lines(self) -> typing.Iterator[str]:
        if self.fobj is not None:
            if hasattr(self.fobj, "seek"):
                try:
                    self.fobj.seek(0)
                except OSError:
                    pass
            for line in self.fobj:
                yield line.rstrip("\r\n")
        elif self.filename is not None:
            with open(self.filename, encoding=self.encoding) as f:
                for line in f:
                    yield line.rstrip("\r\n")

    def _yield_atoms(self) -> typing.Iterator[Row]:
        current_model = 1
        for line in self._iter_lines():
            if not line:
                continue
            record = line[:6].strip()
            if record == "MODEL":
                current_model = _safe_int(line[6:14], 1) or 1
                continue
            if record == "ENDMDL":
                continue
            if record not in ("ATOM", "HETATM"):
                continue
            if self.model_filter is not None and current_model != self.model_filter:
                continue
            # Pad short lines to fixed-column width
            padded = line.ljust(80)
            name = padded[12:16].strip()
            element = padded[76:78].strip()
            if not element and name:
                # Infer element from atom name (leading letters)
                element = "".join(ch for ch in name if ch.isalpha())[:2]
            yield {
                "record_type": record,
                "serial": _safe_int(padded[6:11]),
                "name": name,
                "resName": padded[17:20].strip(),
                "chainID": padded[21:22].strip(),
                "resSeq": _safe_int(padded[22:26]),
                "x": _safe_float(padded[30:38]),
                "y": _safe_float(padded[38:46]),
                "z": _safe_float(padded[46:54]),
                "element": element,
                "model": current_model,
            }

    @staticmethod
    def id() -> str:
        return "pdb"

    @staticmethod
    def is_flatonly() -> bool:
        return True

    def is_streaming(self) -> bool:
        return True

    def read(self, skip_empty: bool = True) -> Row:
        """Read a single ATOM/HETATM record."""
        try:
            row = next(self._iterator)  # type: ignore[arg-type]
            self.pos += 1
            return row
        except (StopIteration, TypeError):
            raise StopIteration from None

    def write(self, record: Row) -> None:
        """Write a basic ATOM (or HETATM) line."""
        self.write_bulk([record])

    def write_bulk(self, records: list[Row]) -> None:
        """Write basic ATOM/HETATM lines."""
        for record in records:
            self.fobj.write(self._format_atom_line(record))

    @staticmethod
    def _format_atom_line(record: Row) -> str:
        record_type = str(record.get("record_type", "ATOM"))
        if record_type not in ("ATOM", "HETATM"):
            record_type = "ATOM"
        serial = int(record.get("serial") or 0)
        name = str(record.get("name") or "CA")
        # Atom name: right-align in 4 cols if length < 4 and no leading space convention
        if len(name) < 4:
            name_field = f" {name:<3}"[:4]
        else:
            name_field = f"{name:4}"[:4]
        res_name = f"{str(record.get('resName') or 'UNK'):>3}"[:3]
        chain = str(record.get("chainID") or "A")[:1]
        res_seq = int(record.get("resSeq") or 1)
        x = float(record.get("x") or 0.0)
        y = float(record.get("y") or 0.0)
        z = float(record.get("z") or 0.0)
        element = str(record.get("element") or "")[:2]
        # Classic PDB fixed-width ATOM line
        line = (
            f"{record_type:<6}"
            f"{serial:5d} "
            f"{name_field}"
            f" "
            f"{res_name}"
            f" "
            f"{chain}"
            f"{res_seq:4d}"
            f"    "
            f"{x:8.3f}{y:8.3f}{z:8.3f}"
            f"{1.00:6.2f}{0.00:6.2f}"
            f"          "
            f"{element:>2}"
            f"  "
        )
        return line[:80].rstrip() + "\n"
