"""BAG (Bathymetric Attributed Grid) reader via h5py."""

from __future__ import annotations

import typing
from typing import Any

try:
    import h5py

    HAS_H5PY = True
except ImportError:
    HAS_H5PY = False

from ..base import DEFAULT_BULK_NUMBER, BaseCodec, BaseFileIterable
from ..exceptions import ReadError, WriteNotSupportedError
from ..types import Row


class BAGIterable(BaseFileIterable):
    """Read BAG bathymetric HDF5 products.

    ``list_tables()`` returns dataset paths under ``/BAG_root`` when present,
    otherwise top-level datasets. Elevation samples stream as
    ``{row, col, value}`` one cell at a time (row-major). Select a dataset with
    ``options["table"]`` or ``options["dataset"]``.
    """

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
        if not HAS_H5PY:
            raise ImportError("BAG support requires 'h5py'. Install with: pip install iterabledata[hdf5]")
        if mode not in ("r",):
            raise WriteNotSupportedError("bag", "BAG is read-only")

        self.dataset_path = options.get("table") or options.get("dataset")
        self._h5file = None
        self._dataset = None
        self._iterator: typing.Iterator[Row] | None = None
        super().__init__(
            filename,
            stream,
            codec=codec,
            mode=mode,
            binary=True,
            noopen=True,
            options=options,
        )
        self.reset()

    def reset(self) -> None:
        super().reset()
        self.pos = 0
        if self._h5file is not None:
            try:
                self._h5file.close()
            except Exception:
                pass
            self._h5file = None
            self._dataset = None

        if self.filename is None:
            raise ReadError(
                "BAG requires a file path; stream and codec are not supported.",
                filename=None,
                error_code="RESOURCE_REQUIREMENT_NOT_MET",
            )

        self._h5file = h5py.File(self.filename, "r")
        path = self.dataset_path or self._default_elevation_path()
        if path not in self._h5file:
            raise ValueError(f"BAG dataset not found: {path}")
        self._dataset = self._h5file[path]
        self._iterator = self._sample_iterator()

    def _default_elevation_path(self) -> str:
        tables = self.list_tables() or []
        for candidate in (
            "/BAG_root/elevation",
            "/BAG_root/Elevation",
            "BAG_root/elevation",
        ):
            if candidate in tables or (self._h5file is not None and candidate in self._h5file):
                return candidate if candidate.startswith("/") else f"/{candidate}"
        # Prefer any path ending with elevation
        for t in tables:
            if t.rstrip("/").lower().endswith("elevation"):
                return t
        if tables:
            return tables[0]
        raise ValueError("No datasets found in BAG file")

    @staticmethod
    def _list_datasets(group: Any, prefix: str = "") -> list[str]:
        datasets: list[str] = []
        for key in group.keys():
            item = group[key]
            path = f"{prefix}/{key}" if prefix else f"/{key}"
            if isinstance(item, h5py.Dataset):
                datasets.append(path)
            elif isinstance(item, h5py.Group):
                datasets.extend(BAGIterable._list_datasets(item, path))
        return datasets

    def list_tables(self, filename: str | None = None) -> list[str] | None:
        """List dataset paths under ``/BAG_root`` if present, else top-level."""
        if filename is None and self._h5file is not None:
            root = self._h5file
            if "BAG_root" in root:
                return self._list_datasets(root["BAG_root"], "/BAG_root")
            return self._list_datasets(root)

        target = filename if filename is not None else self.filename
        if target is None:
            return None
        with h5py.File(target, "r") as h5file:
            if "BAG_root" in h5file:
                return self._list_datasets(h5file["BAG_root"], "/BAG_root")
            return self._list_datasets(h5file)

    def _sample_iterator(self) -> typing.Iterator[Row]:
        assert self._dataset is not None
        ds = self._dataset
        if len(ds.shape) == 1:
            for col in range(ds.shape[0]):
                yield {"row": 0, "col": col, "value": ds[col].item() if hasattr(ds[col], "item") else ds[col]}
            return
        if len(ds.shape) >= 2:
            nrows, ncols = int(ds.shape[0]), int(ds.shape[1])
            for row in range(nrows):
                row_data = ds[row, :]
                for col in range(ncols):
                    val = row_data[col]
                    yield {
                        "row": row,
                        "col": col,
                        "value": val.item() if hasattr(val, "item") else val,
                    }
            return
        raise ValueError(f"Unsupported BAG dataset shape: {ds.shape}")

    @staticmethod
    def id() -> str:
        return "bag"

    @staticmethod
    def is_flatonly() -> bool:
        return True

    @staticmethod
    def has_tables() -> bool:
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
        raise WriteNotSupportedError("bag", "BAG is read-only")

    def write_bulk(self, records: list[Row]) -> None:
        raise WriteNotSupportedError("bag", "BAG is read-only")

    def close(self) -> None:
        if self._h5file is not None:
            self._h5file.close()
            self._h5file = None
            self._dataset = None
        super().close()
