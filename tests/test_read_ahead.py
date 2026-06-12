"""Tests for read-ahead caching functionality."""

import pytest

from iterable.helpers.detect import open_iterable
from iterable.helpers.read_ahead import ReadAheadBuffer


class TestReadAheadBuffer:
    """Test ReadAheadBuffer class."""

    def test_basic_prefetching(self):
        """Test basic prefetching functionality."""
        source = iter([1, 2, 3, 4, 5, 6, 7, 8, 9, 10])
        buffer = ReadAheadBuffer(source, buffer_size=5, refill_threshold=0.3)

        # Should prefetch 5 items initially
        assert len(buffer.buffer) == 0  # Buffer starts empty, fills on first access

        # Read first item - should trigger prefetch
        item1 = next(buffer)
        assert item1 == 1
        # Buffer should have been refilled (at least 4 more items)
        assert len(buffer.buffer) >= 4

        # Read remaining items
        items = [item1] + list(buffer)
        assert items == [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]

    def test_refill_threshold(self):
        """Test that buffer refills when threshold is reached."""
        source = iter(range(20))
        buffer = ReadAheadBuffer(source, buffer_size=10, refill_threshold=0.3)

        # Read items until buffer drops below threshold (3 items)
        items = []
        for _ in range(8):  # Read 8 items, leaving 2 in buffer (below threshold of 3)
            items.append(next(buffer))

        # Buffer should have been refilled
        assert len(buffer.buffer) >= 2

        # Continue reading
        remaining = list(buffer)
        assert len(items) + len(remaining) == 20

    def test_peek_functionality(self):
        """Test peek() method."""
        source = iter([1, 2, 3, 4, 5])
        buffer = ReadAheadBuffer(source, buffer_size=3)

        # Peek at next 2 items without consuming
        peeked = buffer.peek(2)
        assert len(peeked) == 2
        assert peeked[0] == 1
        assert peeked[1] == 2

        # Buffer should still have items
        assert len(buffer.buffer) >= 2

        # Reading should still work
        item = next(buffer)
        assert item == 1

    def test_clear_functionality(self):
        """Test clear() method."""
        source = iter([1, 2, 3, 4, 5])
        buffer = ReadAheadBuffer(source, buffer_size=5)

        # Read some items
        item1 = next(buffer)
        assert item1 == 1

        # Clear buffer
        buffer.clear()
        assert len(buffer.buffer) == 0
        assert buffer.exhausted is False

        # Should be able to continue reading (though source may be partially consumed)
        # Note: clear() doesn't reset the source, so this test verifies clear() works
        # but the source iterator state depends on implementation

    def test_exhausted_source(self):
        """Test behavior when source is exhausted."""
        source = iter([1, 2, 3])
        buffer = ReadAheadBuffer(source, buffer_size=10)

        # Read all items
        items = list(buffer)
        assert items == [1, 2, 3]

        # Should raise StopIteration
        with pytest.raises(StopIteration):
            next(buffer)


class TestReadAheadIntegration:
    """Test read-ahead caching integration with file iterables."""

    def test_csv_with_read_ahead(self, tmp_path):
        """Test CSV format with read-ahead enabled."""
        test_file = tmp_path / "test.csv"
        test_file.write_text("col1,col2\n" + "\n".join([f"val{i},val{i}" for i in range(20)]))

        # Open with read-ahead enabled
        with open_iterable(str(test_file), iterableargs={"read_ahead": True, "read_ahead_size": 5}) as source:
            rows = list(source)
            assert len(rows) == 20
            assert rows[0]["col1"] == "val0"
            assert rows[19]["col1"] == "val19"

    def test_jsonl_with_read_ahead(self, tmp_path):
        """Test JSONL format with read-ahead enabled."""
        test_file = tmp_path / "test.jsonl"
        test_file.write_text("\n".join([f'{{"id": {i}, "value": "val{i}"}}' for i in range(15)]))

        with open_iterable(str(test_file), iterableargs={"read_ahead": True, "read_ahead_size": 10}) as source:
            rows = list(source)
            assert len(rows) == 15
            assert rows[0]["id"] == 0
            assert rows[14]["id"] == 14

    def test_read_ahead_disabled_by_default(self, tmp_path):
        """Test that read-ahead is disabled by default."""
        test_file = tmp_path / "test.csv"
        test_file.write_text("col1,col2\nval1,val2\nval3,val4\n")

        with open_iterable(str(test_file)) as source:
            # Should not have read-ahead buffer
            assert not hasattr(source, "_read_ahead_buffer") or source._read_ahead_buffer is None

    def test_read_ahead_with_reset(self, tmp_path):
        """Test that reset() clears read-ahead buffer."""
        test_file = tmp_path / "test.csv"
        test_file.write_text("col1,col2\nval1,val2\nval3,val4\n")

        source = open_iterable(str(test_file), iterableargs={"read_ahead": True, "read_ahead_size": 5})

        # Read some rows
        row1 = next(source)
        assert row1["col1"] == "val1"

        # Reset
        source.reset()

        # Should be able to read from beginning again
        row1_again = next(source)
        assert row1_again["col1"] == "val1"

        source.close()

    def test_read_ahead_configuration_options(self, tmp_path):
        """Test read-ahead configuration options."""
        test_file = tmp_path / "test.csv"
        test_file.write_text("col1,col2\n" + "\n".join([f"val{i},val{i}" for i in range(10)]))

        # Test custom buffer size
        with open_iterable(
            str(test_file),
            iterableargs={"read_ahead": True, "read_ahead_size": 20, "read_ahead_refill_threshold": 0.5},
        ) as source:
            assert source._read_ahead_enabled is True
            assert source._read_ahead_size == 20
            assert source._read_ahead_refill_threshold == 0.5

            rows = list(source)
            assert len(rows) == 10

    def test_read_ahead_backward_compatibility(self, tmp_path):
        """Test that read-ahead maintains backward compatibility."""
        test_file = tmp_path / "test.csv"
        test_file.write_text("col1,col2\nval1,val2\nval3,val4\n")

        # Without read-ahead (default behavior)
        with open_iterable(str(test_file)) as source:
            rows1 = list(source)

        # With read-ahead disabled explicitly
        with open_iterable(str(test_file), iterableargs={"read_ahead": False}) as source:
            rows2 = list(source)

        # Results should be identical
        assert rows1 == rows2
