"""
Tests for async/await support (Phase 1: Foundation).
"""

import asyncio
import os
import tempfile

import pytest

from iterable.async_base import AsyncBaseFileIterable, AsyncBaseIterable
from iterable.datatypes.csv import CSVIterable
from iterable.helpers.async_detect import aopen_iterable
from iterable.types import Row


class TestAsyncBaseIterable:
    """Test AsyncBaseIterable base class."""

    def test_async_base_iterable_abstract(self):
        """Test that AsyncBaseIterable is abstract."""
        with pytest.raises(TypeError):
            AsyncBaseIterable()  # type: ignore

    def test_async_base_iterable_context_manager(self):
        """Test async context manager protocol."""

        class ConcreteAsyncIterable(AsyncBaseIterable):
            async def aread(self, skip_empty: bool = True) -> Row:
                raise StopAsyncIteration

        async def test():
            async with ConcreteAsyncIterable() as source:
                assert source is not None

        asyncio.run(test())

    def test_async_base_iterable_iterator(self):
        """Test async iterator protocol."""

        class ConcreteAsyncIterable(AsyncBaseIterable):
            def __init__(self):
                super().__init__()
                self._count = 0

            async def aread(self, skip_empty: bool = True) -> Row:
                if self._count >= 3:
                    raise StopAsyncIteration
                self._count += 1
                return {"id": self._count}

        async def test():
            source = ConcreteAsyncIterable()
            rows = []
            async for row in source:
                rows.append(row)
            assert len(rows) == 3

        asyncio.run(test())


class TestAsyncBaseFileIterable:
    """Test AsyncBaseFileIterable wrapper."""

    def test_async_wrapper_creation(self):
        """Test creating async wrapper from sync iterable."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
            f.write("col1,col2\n")
            temp_filename = f.name

        try:
            sync_iterable = CSVIterable(filename=temp_filename)
            async_iterable = AsyncBaseFileIterable(sync_iterable=sync_iterable)
            assert async_iterable._sync == sync_iterable
        finally:
            os.unlink(temp_filename)

    def test_async_wrapper_context_manager(self):
        """Test async wrapper context manager."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
            f.write("col1,col2\n")
            f.write("val1,val2\n")
            temp_filename = f.name

        try:

            async def test():
                sync_iterable = CSVIterable(filename=temp_filename)
                async_iterable = AsyncBaseFileIterable(sync_iterable=sync_iterable)
                async with async_iterable:
                    assert async_iterable._sync is not None

            asyncio.run(test())
        finally:
            os.unlink(temp_filename)

    def test_async_read(self):
        """Test async read operation."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
            f.write("col1,col2\n")
            f.write("val1,val2\n")
            temp_filename = f.name

        try:

            async def test():
                sync_iterable = CSVIterable(filename=temp_filename)
                sync_iterable.open()
                async_iterable = AsyncBaseFileIterable(sync_iterable=sync_iterable)
                row = await async_iterable.aread()
                assert row == {"col1": "val1", "col2": "val2"}

            asyncio.run(test())
        finally:
            os.unlink(temp_filename)

    def test_async_read_bulk(self):
        """Test async bulk read operation."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
            f.write("col1,col2\n")
            f.write("val1,val2\n")
            f.write("val3,val4\n")
            temp_filename = f.name

        try:

            async def test():
                sync_iterable = CSVIterable(filename=temp_filename)
                sync_iterable.open()
                async_iterable = AsyncBaseFileIterable(sync_iterable=sync_iterable)
                rows = await async_iterable.aread_bulk(10)
                assert len(rows) == 2
                assert rows[0] == {"col1": "val1", "col2": "val2"}

            asyncio.run(test())
        finally:
            os.unlink(temp_filename)

    def test_async_iterator(self):
        """Test async iterator protocol."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
            f.write("col1,col2\n")
            f.write("val1,val2\n")
            f.write("val3,val4\n")
            temp_filename = f.name

        try:

            async def test():
                sync_iterable = CSVIterable(filename=temp_filename)
                sync_iterable.open()
                async_iterable = AsyncBaseFileIterable(sync_iterable=sync_iterable)
                rows = []
                async for row in async_iterable:
                    rows.append(row)
                assert len(rows) == 2

            asyncio.run(test())
        finally:
            os.unlink(temp_filename)


class TestAOpenIterable:
    """Test aopen_iterable() function."""

    def test_aopen_iterable_basic(self):
        """Test basic aopen_iterable usage."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
            f.write("col1,col2\n")
            f.write("val1,val2\n")
            temp_filename = f.name

        try:

            async def test():
                source = await aopen_iterable(temp_filename)
                async with source:
                    rows = []
                    async for row in source:
                        rows.append(row)
                    assert len(rows) == 1
                    assert rows[0] == {"col1": "val1", "col2": "val2"}

            asyncio.run(test())
        finally:
            os.unlink(temp_filename)

    def test_aopen_iterable_bulk_read(self):
        """Test aopen_iterable with bulk read."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
            f.write("col1,col2\n")
            f.write("val1,val2\n")
            f.write("val3,val4\n")
            temp_filename = f.name

        try:

            async def test():
                source = await aopen_iterable(temp_filename)
                async with source:
                    rows = await source.aread_bulk(10)
                    assert len(rows) == 2

            asyncio.run(test())
        finally:
            os.unlink(temp_filename)

    def test_aopen_iterable_concurrent(self):
        """Test concurrent file processing with aopen_iterable."""
        files_data = [
            ("col1\nval1\nval2\n",),
            ("col1\nval3\nval4\n",),
        ]

        temp_files = []
        try:
            for data in files_data:
                f = tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False)
                f.write(data[0])
                f.close()
                temp_files.append(f.name)

            async def process_file(filename: str) -> list[Row]:
                rows = []
                source = await aopen_iterable(filename)
                async with source:
                    async for row in source:
                        rows.append(row)
                return rows

            async def test():
                results = await asyncio.gather(*[process_file(f) for f in temp_files])
                assert len(results) == 2
                assert len(results[0]) == 2
                assert len(results[1]) == 2

            asyncio.run(test())
        finally:
            for f in temp_files:
                os.unlink(f)
