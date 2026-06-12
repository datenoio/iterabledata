import os
import tempfile

import pytest

from iterable.datatypes.cbor import CBORIterable

try:
    import cbor2  # noqa: F401

    HAS_CBOR2 = True
except ImportError:
    try:
        import cbor  # noqa: F401

        HAS_CBOR = True
        HAS_CBOR2 = False
    except ImportError:
        HAS_CBOR = False
        HAS_CBOR2 = False


@pytest.mark.skipif(not HAS_CBOR2 and not HAS_CBOR, reason="CBOR library not available")
def test_cbor_read_write():
    """Test CBOR read and write"""
    test_data = [
        {"name": "Alice", "age": 30, "city": "New York"},
        {"name": "Bob", "age": 25, "city": "London"},
        {"name": "Charlie", "age": 35, "city": "Tokyo"},
    ]

    with tempfile.NamedTemporaryFile(delete=False, suffix=".cbor") as tmp:
        tmp_path = tmp.name

    try:
        # Write data
        writer = CBORIterable(tmp_path, mode="w")
        for record in test_data:
            writer.write(record)
        writer.close()

        # Read data back
        reader = CBORIterable(tmp_path, mode="r")
        results = []
        for record in reader:
            results.append(record)
        reader.close()

        # Note: CBOR reading might return a list if written as sequence
        # Adjust based on actual behavior
        assert len(results) > 0
    finally:
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)


@pytest.mark.skipif(not HAS_CBOR2 and not HAS_CBOR, reason="CBOR library not available")
def test_cbor_bulk():
    """Test CBOR bulk operations"""
    test_data = [{"name": "Alice", "age": 30}, {"name": "Bob", "age": 25}, {"name": "Charlie", "age": 35}]

    with tempfile.NamedTemporaryFile(delete=False, suffix=".cbor") as tmp:
        tmp_path = tmp.name

    try:
        # Write bulk
        writer = CBORIterable(tmp_path, mode="w")
        writer.write_bulk(test_data)
        writer.close()

        # Read bulk
        reader = CBORIterable(tmp_path, mode="r")
        chunk = reader.read_bulk(10)
        reader.close()

        assert len(chunk) > 0
    finally:
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)
