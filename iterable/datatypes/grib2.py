"""GRIB2 meteorological message reader.

Prefers ``cfgrib`` + ``xarray`` when available; falls back to ``pygrib`` or
``eccodes``. Yields one dict per message with keys such as ``shortName`` and
``values`` when possible.

Install examples::

    pip install cfgrib xarray
    # or
    pip install pygrib

Read-only. Format id: ``grib2``.
"""

from __future__ import annotations

import typing
from typing import Any

from ..base import BaseCodec, BaseFileIterable
from ..exceptions import ReadError, WriteNotSupportedError
from ..types import Row

_BACKEND: str | None = None

try:
    import cfgrib  # type: ignore[import-untyped]  # noqa: F401
    import xarray  # type: ignore[import-untyped]  # noqa: F401

    _BACKEND = "cfgrib"
except ImportError:
    try:
        import pygrib  # type: ignore[import-untyped]  # noqa: F401

        _BACKEND = "pygrib"
    except ImportError:
        try:
            import eccodes  # type: ignore[import-untyped]  # noqa: F401

            _BACKEND = "eccodes"
        except ImportError:
            _BACKEND = None

HAS_GRIB = _BACKEND is not None

_IMPORT_ERROR = (
    "GRIB2 support requires 'cfgrib'+'xarray', 'pygrib', or 'eccodes'. "
    "Install with: pip install cfgrib xarray  (or pip install iterabledata[grib] when configured)"
)


class GRIB2Iterable(BaseFileIterable):
    """Read-only GRIB2 message iterable."""

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
        if not HAS_GRIB:
            raise ImportError(_IMPORT_ERROR)
        if mode not in ("r", "rb"):
            raise WriteNotSupportedError("grib2", "GRIB2 is read-only")
        if filename is None:
            raise ReadError(
                "GRIB2 reading requires a filename",
                filename=None,
                error_code="RESOURCE_REQUIREMENT_NOT_MET",
            )
        if stream is not None or codec is not None:
            raise ReadError(
                "GRIB2 reading requires a filename, not a stream or codec",
                filename=None,
                error_code="RESOURCE_REQUIREMENT_NOT_MET",
            )
        super().__init__(
            filename=filename,
            stream=None,
            codec=None,
            binary=True,
            mode="r",
            noopen=True,
            options=options,
        )
        self._messages: list[dict[str, Any]] = []
        self._iterator: typing.Iterator[dict[str, Any]] | None = None
        self.reset()

    @staticmethod
    def id() -> str:
        return "grib2"

    @staticmethod
    def is_flatonly() -> bool:
        return True

    def is_streaming(self) -> bool:
        return False

    def _load_cfgrib(self, path: str) -> list[dict[str, Any]]:
        import cfgrib

        datasets = cfgrib.open_datasets(path)
        messages: list[dict[str, Any]] = []
        for ds in datasets:
            for var_name, da in ds.data_vars.items():
                values = da.values
                record: dict[str, Any] = {
                    "shortName": var_name,
                    "values": values.tolist() if hasattr(values, "tolist") else values,
                }
                for coord in ("time", "step", "level", "isobaricInhPa", "latitude", "longitude"):
                    if coord in ds.coords:
                        val = ds.coords[coord].values
                        record[coord] = val.tolist() if hasattr(val, "tolist") else val
                # Prefer GRIB shortName attribute when present
                short = da.attrs.get("GRIB_shortName") or da.attrs.get("shortName")
                if short:
                    record["shortName"] = short
                messages.append(record)
            ds.close()
        return messages

    def _load_pygrib(self, path: str) -> list[dict[str, Any]]:
        import pygrib

        messages: list[dict[str, Any]] = []
        with pygrib.open(path) as grbs:
            for grb in grbs:
                values = grb.values
                messages.append(
                    {
                        "shortName": getattr(grb, "shortName", None) or getattr(grb, "name", None),
                        "values": values.tolist() if hasattr(values, "tolist") else list(values),
                        "level": getattr(grb, "level", None),
                        "typeOfLevel": getattr(grb, "typeOfLevel", None),
                        "validDate": str(getattr(grb, "validDate", "")),
                    }
                )
        return messages

    def _load_eccodes(self, path: str) -> list[dict[str, Any]]:
        import eccodes

        messages: list[dict[str, Any]] = []
        with open(path, "rb") as f:
            while True:
                gid = eccodes.codes_grib_new_from_file(f)
                if gid is None:
                    break
                try:
                    short = None
                    try:
                        short = eccodes.codes_get(gid, "shortName")
                    except Exception:
                        try:
                            short = eccodes.codes_get(gid, "name")
                        except Exception:
                            short = None
                    values = eccodes.codes_get_values(gid)
                    messages.append(
                        {
                            "shortName": short,
                            "values": values.tolist() if hasattr(values, "tolist") else list(values),
                        }
                    )
                finally:
                    eccodes.codes_release(gid)
        return messages

    def reset(self) -> None:
        self.pos = 0
        assert self.filename is not None
        if _BACKEND == "cfgrib":
            self._messages = self._load_cfgrib(self.filename)
        elif _BACKEND == "pygrib":
            self._messages = self._load_pygrib(self.filename)
        elif _BACKEND == "eccodes":
            self._messages = self._load_eccodes(self.filename)
        else:
            raise ImportError(_IMPORT_ERROR)
        self._iterator = iter(self._messages)

    def read(self, skip_empty: bool = True) -> Row:
        if self._iterator is None:
            raise StopIteration
        row = next(self._iterator)
        self.pos += 1
        return row

    def write(self, record: Row) -> None:
        raise WriteNotSupportedError("grib2", "GRIB2 is read-only")

    def write_bulk(self, records: list[Row]) -> None:
        raise WriteNotSupportedError("grib2", "GRIB2 is read-only")
