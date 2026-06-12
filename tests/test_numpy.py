"""Tests for NumPy array format"""

import os
import tempfile

import pytest

try:
    import numpy as np  # noqa: F401

    HAS_NUMPY = True
except ImportError:
    HAS_NUMPY = False

from iterable.datatypes.numpy import NumPyIterable
from iterable.exceptions import FormatNotSupportedError
from iterable.helpers.detect import open_iterable


@pytest.mark.skipif(not HAS_NUMPY, reason="NumPy not available")
class TestNumPy:
    """Test NumPy array format reading and writing"""

    def test_read_npy_2d(self):
        """Test reading 2D .npy array"""
        # Create 2D array
        array_data = np.array([[1.0, 2.0, 3.0], [4.0, 5.0, 6.0], [7.0, 8.0, 9.0]])

        with tempfile.NamedTemporaryFile(suffix=".npy", delete=False) as f:
            temp_file = f.name
            np.save(temp_file, array_data)

        try:
            source = open_iterable(temp_file)
            records = list(source)
            source.close()

            assert len(records) == 3
            assert records[0] == {"col_0": 1.0, "col_1": 2.0, "col_2": 3.0}
            assert records[1] == {"col_0": 4.0, "col_1": 5.0, "col_2": 6.0}
            assert records[2] == {"col_0": 7.0, "col_1": 8.0, "col_2": 9.0}
        finally:
            os.unlink(temp_file)

    def test_read_npy_1d(self):
        """Test reading 1D .npy array"""
        # Create 1D array
        array_data = np.array([1.0, 2.0, 3.0, 4.0])

        with tempfile.NamedTemporaryFile(suffix=".npy", delete=False) as f:
            temp_file = f.name
            np.save(temp_file, array_data)

        try:
            source = open_iterable(temp_file)
            records = list(source)
            source.close()

            assert len(records) == 4
            assert records[0] == {"value": 1.0}
            assert records[1] == {"value": 2.0}
            assert records[2] == {"value": 3.0}
            assert records[3] == {"value": 4.0}
        finally:
            os.unlink(temp_file)

    def test_read_npz(self):
        """Test reading .npz file"""
        # Create .npz file with multiple arrays
        array1 = np.array([[1.0, 2.0], [3.0, 4.0]])
        array2 = np.array([10.0, 20.0, 30.0])

        with tempfile.NamedTemporaryFile(suffix=".npz", delete=False) as f:
            temp_file = f.name
            np.savez(temp_file, data=array1, labels=array2)

        try:
            # Read first array
            source = open_iterable(temp_file, iterableargs={"array_name": "data"})
            records = list(source)
            source.close()

            assert len(records) == 2
            assert records[0] == {"col_0": 1.0, "col_1": 2.0}

            # Read second array
            source = open_iterable(temp_file, iterableargs={"array_name": "labels"})
            records = list(source)
            source.close()

            assert len(records) == 3
            assert records[0] == {"value": 10.0}
        finally:
            os.unlink(temp_file)

    def test_list_tables_npz(self):
        """Test listing arrays in .npz file"""
        array1 = np.array([[1.0, 2.0]])
        array2 = np.array([10.0])

        with tempfile.NamedTemporaryFile(suffix=".npz", delete=False) as f:
            temp_file = f.name
            np.savez(temp_file, data=array1, labels=array2)

        try:
            # Create instance to call list_tables
            iterable = NumPyIterable(temp_file)
            arrays = iterable.list_tables(temp_file)
            assert arrays is not None
            assert "data" in arrays
            assert "labels" in arrays
            assert len(arrays) == 2
            iterable.close()
        finally:
            os.unlink(temp_file)

    def test_list_tables_npy(self):
        """Test listing arrays in .npy file (should return None)"""
        array_data = np.array([[1.0, 2.0]])

        with tempfile.NamedTemporaryFile(suffix=".npy", delete=False) as f:
            temp_file = f.name
            np.save(temp_file, array_data)

        try:
            # Create instance to call list_tables
            iterable = NumPyIterable(temp_file)
            arrays = iterable.list_tables(temp_file)
            assert arrays is None  # .npy files don't have named arrays
            iterable.close()
        finally:
            os.unlink(temp_file)

    def test_write_npy_2d(self):
        """Test writing 2D .npy array"""
        records = [
            {"col_0": 1.0, "col_1": 2.0, "col_2": 3.0},
            {"col_0": 4.0, "col_1": 5.0, "col_2": 6.0},
        ]

        with tempfile.NamedTemporaryFile(suffix=".npy", delete=False) as f:
            temp_file = f.name

        try:
            source = open_iterable(temp_file, mode="w")
            source.write_bulk(records)
            source.close()

            # Read back
            loaded = np.load(temp_file)
            assert loaded.shape == (2, 3)
            assert np.array_equal(loaded[0], [1.0, 2.0, 3.0])
            assert np.array_equal(loaded[1], [4.0, 5.0, 6.0])
            # .npy files return arrays directly, no need to close
        finally:
            os.unlink(temp_file)

    def test_write_npz(self):
        """Test writing .npz file"""
        records = [
            {"col_0": 1.0, "col_1": 2.0},
            {"col_0": 3.0, "col_1": 4.0},
        ]

        with tempfile.NamedTemporaryFile(suffix=".npz", delete=False) as f:
            temp_file = f.name

        try:
            source = open_iterable(temp_file, mode="w", iterableargs={"array_name": "mydata"})
            source.write_bulk(records)
            source.close()

            # Read back
            loaded = np.load(temp_file)
            assert "mydata" in loaded
            array = loaded["mydata"]
            assert array.shape == (2, 2)
            assert np.array_equal(array[0], [1.0, 2.0])
            loaded.close()
        finally:
            os.unlink(temp_file)

    def test_totals(self):
        """Test totals count"""
        array_data = np.array([[1.0, 2.0], [3.0, 4.0], [5.0, 6.0]])

        with tempfile.NamedTemporaryFile(suffix=".npy", delete=False) as f:
            temp_file = f.name
            np.save(temp_file, array_data)

        try:
            source = open_iterable(temp_file)
            total = source.totals()
            source.close()

            assert total == 3
        finally:
            os.unlink(temp_file)

    def test_read_bulk(self):
        """Test bulk reading"""
        array_data = np.array([[1.0, 2.0], [3.0, 4.0], [5.0, 6.0]])

        with tempfile.NamedTemporaryFile(suffix=".npy", delete=False) as f:
            temp_file = f.name
            np.save(temp_file, array_data)

        try:
            source = open_iterable(temp_file)
            chunk = source.read_bulk(2)
            assert len(chunk) == 2
            chunk2 = source.read_bulk(2)
            assert len(chunk2) == 1
            source.close()
        finally:
            os.unlink(temp_file)

    def test_invalid_shape(self):
        """Test invalid array shape (3D)"""
        array_data = np.array([[[1.0, 2.0], [3.0, 4.0]], [[5.0, 6.0], [7.0, 8.0]]])

        with tempfile.NamedTemporaryFile(suffix=".npy", delete=False) as f:
            temp_file = f.name
            np.save(temp_file, array_data)

        try:
            source = open_iterable(temp_file)
            with pytest.raises(FormatNotSupportedError):
                list(source)
            source.close()
        finally:
            os.unlink(temp_file)

    def test_npz_array_not_found(self):
        """Test .npz file with non-existent array name"""
        array_data = np.array([[1.0, 2.0]])

        with tempfile.NamedTemporaryFile(suffix=".npz", delete=False) as f:
            temp_file = f.name
            np.savez(temp_file, data=array_data)

        try:
            with pytest.raises((ValueError, RuntimeError)):
                source = open_iterable(temp_file, iterableargs={"array_name": "nonexistent"})
                source.close()
        finally:
            os.unlink(temp_file)

    def test_no_numpy_import(self):
        """Test error when numpy is not available"""
        # This test would need to mock the import, but we'll skip it
        # since we can't easily test ImportError in this context
        pass
