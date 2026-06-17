from __future__ import annotations

import typing

import numpy as np

try:
    import netCDF4

    HAS_NETCDF = True
except ImportError:
    HAS_NETCDF = False

from typing import Any

from ..base import BaseCodec, BaseFileIterable
from ..exceptions import ReadError, WriteNotSupportedError


class NetCDFIterable(BaseFileIterable):
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
        if not HAS_NETCDF:
            raise ImportError("NetCDF support requires 'netCDF4' package")

        self.options = options
        super().__init__(filename, stream, codec=codec, binary=True, mode=mode, options=options)
        self.reset()

    def reset(self):
        """Reset iterable"""
        super().reset()
        self.pos = 0
        if self.mode == "r":
            if self.filename:
                self.nc_dataset = netCDF4.Dataset(self.filename, "r")
            elif hasattr(self.fobj, "read") and hasattr(self.fobj, "name"):
                # netCDF4 requires a filename or memory mapping, but from python 3 file obj it's tricky without a name.
                # If it has a name, we use it.
                self.nc_dataset = netCDF4.Dataset(self.fobj.name, "r")
            else:
                # If we have a stream of bytes but no filename, netCDF4 can read from memory if we pass the bytes.
                # But BaseFileIterable usually gives us a stream.
                # For now, let's require a filename or a named stream.
                raise ReadError(
                    "NetCDF reading currently requires a filename or a file object with a name attribute",
                    filename=None,
                    error_code="RESOURCE_REQUIREMENT_NOT_MET",
                )

            self.iterator = self.__iterator()
        else:
            raise WriteNotSupportedError("netcdf", "NetCDF writing is not yet implemented")

    def __iterator(self):
        """Iterator for reading NetCDF dataset"""
        # Strategy:
        # 1. Identify the iteration dimension.
        #    - If 'dimension' is in options, use it.
        #    - Else look for the unlimited dimension.
        #    - Else pick the first dimension found.
        # 2. Iterate over that dimension index.
        # 3. For each index, extract values from all variables that depend on that dimension.

        dims = self.nc_dataset.dimensions
        if not dims:
            # No dimensions, maybe just scalar variables?
            variables = self.nc_dataset.variables
            if variables:
                yield {name: var[:] for name, var in variables.items()}
            return

        target_dim_name = self.options.get("dimension")
        if not target_dim_name:
            # Try to find unlimited dimension
            for name, dim in dims.items():
                if dim.isunlimited():
                    target_dim_name = name
                    break

            # If no unlimited, just pick the first one (often time or similar)
            if not target_dim_name and len(dims) > 0:
                target_dim_name = list(dims.keys())[0]

        if not target_dim_name:
            # Should be covered by "if not dims" check but safety first
            return

        target_dim = dims[target_dim_name]
        size = target_dim.size

        # Pre-select variables that use this dimension
        # If a variable doesn't use the dimension, should we emit it every time?
        # Usually metadata variables (scalars) are emitted once or repeated.
        # Let's include everything for now, handling shape.

        variables = self.nc_dataset.variables
        # Optim optimization: separate variables into "sliced" and "scalar/other"
        sliced_vars = []
        other_vars = []

        for name, var in variables.items():
            if target_dim_name in var.dimensions:
                # We need to find WHICH axis corresponds to target_dim
                axis_idx = var.dimensions.index(target_dim_name)
                sliced_vars.append((name, var, axis_idx))
            else:
                other_vars.append((name, var))

        for i in range(size):
            record = {}
            for name, var, axis_idx in sliced_vars:
                # Determine slice
                # We want var[..., i, ...] where i is at axis_idx
                # dynamic slicing construction
                slicer = [slice(None)] * var.ndim
                slicer[axis_idx] = i
                val = var[tuple(slicer)]

                # Convert numpy types to python native types if it's a scalar result
                # masked arrays need handling
                if np.ma.is_masked(val):
                    val = None
                elif isinstance(val, np.generic):
                    val = val.item()
                elif isinstance(val, bytes):
                    # decode chars/strings
                    val = val.decode("utf-8", "ignore")

                record[name] = val

            # Add other vars (repeated)
            # CAUTION: This might be heavy if there are large static arrays.
            # But standard CSV/JSONL logic implies full record.
            # Maybe we should only include scalars for 'other_vars'
            for name, var in other_vars:
                val = var[:]
                if np.ma.is_masked(val):
                    if val.size == 1:
                        val = None
                    else:
                        val = val.tolist()
                elif isinstance(val, np.generic):
                    val = val.item()

                # Optimization: if it's a byte string (char array), decode
                if hasattr(val, "decode"):
                    val = val.decode("utf-8", "ignore")

                record[name] = val

            yield record

    @staticmethod
    def id() -> str:
        return "netcdf"

    @staticmethod
    def is_flatonly() -> bool:
        return False

    @staticmethod
    def has_tables() -> bool:
        """Indicates if this format supports multiple tables/variables."""
        return True

    def list_tables(self, filename: str | None = None) -> list[str] | None:
        """List available variable names in the NetCDF file.

        Args:
            filename: Optional filename. If None, uses instance's filename and reuses open dataset.

        Returns:
            list[str]: List of variable names, or empty list if no variables.
        """
        # If dataset is already open, reuse it
        if filename is None and hasattr(self, "nc_dataset") and self.nc_dataset is not None:
            return list(self.nc_dataset.variables.keys())

        # Otherwise, open temporarily
        target_filename = filename if filename is not None else self.filename
        if target_filename is None:
            return None

        nc_dataset = netCDF4.Dataset(target_filename, "r")
        try:
            return list(nc_dataset.variables.keys())
        finally:
            nc_dataset.close()

    @staticmethod
    def has_totals() -> bool:
        return True

    def totals(self):
        # Return size of target dimension if possible
        if hasattr(self, "nc_dataset"):
            # Logic duplicate from __iterator roughly
            dims = self.nc_dataset.dimensions
            target_dim_name = self.options.get("dimension")
            if not target_dim_name:
                for name, dim in dims.items():
                    if dim.isunlimited():
                        target_dim_name = name
                        break
                if not target_dim_name and len(dims) > 0:
                    target_dim_name = list(dims.keys())[0]

            if target_dim_name and target_dim_name in dims:
                return dims[target_dim_name].size
        return 0

    def close(self):
        if hasattr(self, "nc_dataset"):
            self.nc_dataset.close()
        super().close()

    def read(self, skip_empty: bool = True) -> dict:
        row = next(self.iterator)
        self.pos += 1
        return row
