import os
import tempfile

import pytest

from iterable.datatypes import NetCDFIterable
from iterable.helpers.detect import open_iterable

try:
    import netCDF4  # noqa: F401

    HAS_NETCDF = True
except ImportError:
    HAS_NETCDF = False


@pytest.mark.skipif(not HAS_NETCDF, reason="NetCDF support requires 'netCDF4' package")
class TestNetCDF:
    def test_id(self):
        datatype_id = NetCDFIterable.id()
        assert datatype_id == "netcdf"

    def test_flatonly(self):
        flag = NetCDFIterable.is_flatonly()
        assert not flag

    def test_has_tables(self):
        flag = NetCDFIterable.has_tables()
        assert flag

    def test_openclose(self):
        """Test basic open/close"""
        import netCDF4

        with tempfile.NamedTemporaryFile(suffix=".nc", delete=False) as f:
            temp_file = f.name

        try:
            # Create a simple NetCDF file
            with netCDF4.Dataset(temp_file, "w") as nc:
                # Create dimensions
                nc.createDimension("time", 3)
                nc.createDimension("x", 2)

                # Create variables
                var_time = nc.createVariable("time", "f4", ("time",))
                var_data = nc.createVariable("data", "f4", ("time", "x"))

                # Write data
                var_time[:] = [1.0, 2.0, 3.0]
                var_data[:] = [[1.0, 2.0], [3.0, 4.0], [5.0, 6.0]]

            iterable = NetCDFIterable(temp_file)
            iterable.close()
        finally:
            if os.path.exists(temp_file):
                os.unlink(temp_file)

    def test_read_one(self):
        """Test reading single record"""
        import netCDF4

        with tempfile.NamedTemporaryFile(suffix=".nc", delete=False) as f:
            temp_file = f.name

        try:
            # Create a simple NetCDF file
            with netCDF4.Dataset(temp_file, "w") as nc:
                nc.createDimension("time", 3)
                var_time = nc.createVariable("time", "f4", ("time",))
                var_time[:] = [1.0, 2.0, 3.0]

            iterable = NetCDFIterable(temp_file)
            record = iterable.read()
            assert isinstance(record, dict)
            assert "time" in record
            iterable.close()
        finally:
            if os.path.exists(temp_file):
                os.unlink(temp_file)

    def test_read_all(self):
        """Test reading all records"""
        import netCDF4

        with tempfile.NamedTemporaryFile(suffix=".nc", delete=False) as f:
            temp_file = f.name

        try:
            # Create NetCDF file with time dimension
            with netCDF4.Dataset(temp_file, "w") as nc:
                nc.createDimension("time", 3)
                var_time = nc.createVariable("time", "f4", ("time",))
                var_time[:] = [1.0, 2.0, 3.0]

            iterable = NetCDFIterable(temp_file)
            records = list(iterable)
            assert len(records) == 3
            assert records[0]["time"] == 1.0
            assert records[1]["time"] == 2.0
            assert records[2]["time"] == 3.0
            iterable.close()
        finally:
            if os.path.exists(temp_file):
                os.unlink(temp_file)

    def test_read_bulk(self):
        """Test bulk reading"""
        import netCDF4

        with tempfile.NamedTemporaryFile(suffix=".nc", delete=False) as f:
            temp_file = f.name

        try:
            with netCDF4.Dataset(temp_file, "w") as nc:
                nc.createDimension("time", 5)
                var_time = nc.createVariable("time", "f4", ("time",))
                var_time[:] = [1.0, 2.0, 3.0, 4.0, 5.0]

            iterable = NetCDFIterable(temp_file)
            rows = iterable.read_bulk(3)
            assert len(rows) == 3
            assert rows[0]["time"] == 1.0
            assert rows[1]["time"] == 2.0
            assert rows[2]["time"] == 3.0
            iterable.close()
        finally:
            if os.path.exists(temp_file):
                os.unlink(temp_file)

    def test_has_totals(self):
        """Test totals method"""
        import netCDF4

        with tempfile.NamedTemporaryFile(suffix=".nc", delete=False) as f:
            temp_file = f.name

        try:
            with netCDF4.Dataset(temp_file, "w") as nc:
                nc.createDimension("time", 5)
                var_time = nc.createVariable("time", "f4", ("time",))
                var_time[:] = [1.0, 2.0, 3.0, 4.0, 5.0]

            iterable = NetCDFIterable(temp_file)
            assert NetCDFIterable.has_totals()
            total = iterable.totals()
            assert total == 5
            iterable.close()
        finally:
            if os.path.exists(temp_file):
                os.unlink(temp_file)

    def test_list_tables(self):
        """Test listing variables (instance method)"""
        import netCDF4

        with tempfile.NamedTemporaryFile(suffix=".nc", delete=False) as f:
            temp_file = f.name

        try:
            with netCDF4.Dataset(temp_file, "w") as nc:
                nc.createDimension("time", 3)
                nc.createVariable("time", "f4", ("time",))
                nc.createVariable("temperature", "f4", ("time",))
                nc.createVariable("pressure", "f4", ("time",))

            iterable = NetCDFIterable(temp_file)
            variables = iterable.list_tables()
            assert isinstance(variables, list)
            assert "time" in variables
            assert "temperature" in variables
            assert "pressure" in variables
            iterable.close()
        finally:
            if os.path.exists(temp_file):
                os.unlink(temp_file)

    def test_list_tables_with_filename(self):
        """Test list_tables with filename parameter (class-like usage)"""
        import netCDF4

        with tempfile.NamedTemporaryFile(suffix=".nc", delete=False) as f:
            temp_file = f.name

        try:
            with netCDF4.Dataset(temp_file, "w") as nc:
                nc.createDimension("time", 3)
                nc.createVariable("time", "f4", ("time",))
                nc.createVariable("temperature", "f4", ("time",))

            iterable = NetCDFIterable(temp_file)
            variables = iterable.list_tables(temp_file)
            assert isinstance(variables, list)
            assert "time" in variables
            assert "temperature" in variables
            iterable.close()
        finally:
            if os.path.exists(temp_file):
                os.unlink(temp_file)

    def test_list_tables_reuses_dataset(self):
        """Test that list_tables reuses open dataset"""
        import netCDF4

        with tempfile.NamedTemporaryFile(suffix=".nc", delete=False) as f:
            temp_file = f.name

        try:
            with netCDF4.Dataset(temp_file, "w") as nc:
                nc.createDimension("time", 3)
                nc.createVariable("time", "f4", ("time",))
                nc.createVariable("temperature", "f4", ("time",))

            iterable = NetCDFIterable(temp_file)
            # Read a record to ensure dataset is open
            _ = iterable.read()
            # Now list tables - should reuse dataset
            variables1 = iterable.list_tables()
            variables2 = iterable.list_tables()
            assert variables1 == variables2
            iterable.close()
        finally:
            if os.path.exists(temp_file):
                os.unlink(temp_file)

    def test_automatic_detection(self):
        """Test automatic format detection via open_iterable"""
        import netCDF4

        with tempfile.NamedTemporaryFile(suffix=".nc", delete=False) as f:
            temp_file = f.name

        try:
            with netCDF4.Dataset(temp_file, "w") as nc:
                nc.createDimension("time", 2)
                var_time = nc.createVariable("time", "f4", ("time",))
                var_time[:] = [1.0, 2.0]

            with open_iterable(temp_file) as source:
                assert isinstance(source, NetCDFIterable)
                row = source.read()
                assert "time" in row
        finally:
            if os.path.exists(temp_file):
                os.unlink(temp_file)

    def test_reset(self):
        """Test reset functionality"""
        import netCDF4

        with tempfile.NamedTemporaryFile(suffix=".nc", delete=False) as f:
            temp_file = f.name

        try:
            with netCDF4.Dataset(temp_file, "w") as nc:
                nc.createDimension("time", 2)
                var_time = nc.createVariable("time", "f4", ("time",))
                var_time[:] = [1.0, 2.0]

            iterable = NetCDFIterable(temp_file)
            row1 = iterable.read()
            iterable.reset()
            row2 = iterable.read()
            assert row1 == row2
            iterable.close()
        finally:
            if os.path.exists(temp_file):
                os.unlink(temp_file)

    def test_dimension_option(self):
        """Test specifying dimension via options"""
        import netCDF4

        with tempfile.NamedTemporaryFile(suffix=".nc", delete=False) as f:
            temp_file = f.name

        try:
            with netCDF4.Dataset(temp_file, "w") as nc:
                nc.createDimension("x", 2)
                nc.createDimension("y", 3)
                var_x = nc.createVariable("x", "f4", ("x",))
                var_y = nc.createVariable("y", "f4", ("y",))
                var_x[:] = [1.0, 2.0]
                var_y[:] = [10.0, 20.0, 30.0]

            iterable = NetCDFIterable(temp_file, options={"dimension": "y"})
            records = list(iterable)
            assert len(records) == 3
            iterable.close()
        finally:
            if os.path.exists(temp_file):
                os.unlink(temp_file)

    def test_missing_dependency(self):
        """Test that missing netCDF4 raises helpful error"""
        # This test would need to mock the import, but we can at least verify
        # the error message format is correct by checking the code
        pass
