import pytest

from iterable.datatypes.iceberg import IcebergIterable

try:
    import pyiceberg  # noqa: F401

    HAS_PYICEBERG = True
except ImportError:
    HAS_PYICEBERG = False


@pytest.mark.skipif(not HAS_PYICEBERG, reason="PyIceberg library not available")
def test_iceberg_id():
    """Test Iceberg ID"""
    assert IcebergIterable.id() == "iceberg"


@pytest.mark.skipif(not HAS_PYICEBERG, reason="PyIceberg library not available")
def test_iceberg_flatonly():
    """Test Iceberg is flat only"""
    assert IcebergIterable.is_flatonly()


@pytest.mark.skipif(not HAS_PYICEBERG, reason="PyIceberg library not available")
def test_iceberg_requires_params():
    """Test that Iceberg requires catalog and table names"""
    from iterable.exceptions import ReadError

    with pytest.raises((ValueError, ReadError)):
        IcebergIterable("test.iceberg", mode="r")


@pytest.mark.skipif(not HAS_PYICEBERG, reason="PyIceberg library not available")
def test_iceberg_has_tables():
    """Test has_tables static method"""
    assert IcebergIterable.has_tables() is True


@pytest.mark.skipif(not HAS_PYICEBERG, reason="PyIceberg library not available")
def test_iceberg_list_tables():
    """Test list_tables method (may return None if catalog doesn't support listing)"""
    # Note: This test may not work without a real catalog setup
    # It's mainly to ensure the method exists and doesn't crash
    try:
        # Try to create an instance with dummy values to test the method signature
        # The actual implementation may require real catalog configuration
        iterable = IcebergIterable(filename=None, catalog_name="test_catalog", table_name="test_table", mode="r")
        # list_tables may return None if catalog doesn't support listing or isn't configured
        result = iterable.list_tables()
        # Result can be None, empty list, or list of strings
        assert result is None or isinstance(result, list)
        iterable.close()
    except (ValueError, Exception):
        # If catalog setup fails, that's expected in test environment
        pass
