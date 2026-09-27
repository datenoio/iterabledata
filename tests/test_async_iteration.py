"""Tests for genuine async iteration (OpenSpec add-genuine-async-iteration)."""

import asyncio
import importlib.util

import iterable
from iterable import aopen_iterable, open_iterable


def _write_csv(path, records):
    with open_iterable(str(path), mode="w") as target:
        target.write_bulk(records)


class TestAsyncIteration:
    def test_root_export(self):
        assert iterable.aopen_iterable is aopen_iterable
        assert "aopen_iterable" in iterable.__all__

    def test_csv_parity_with_sync(self, tmp_path):
        path = tmp_path / "data.csv"
        expected = [{"n": str(i), "s": f"x{i}"} for i in range(20)]
        _write_csv(path, [{"n": i, "s": f"x{i}"} for i in range(20)])

        async def run():
            async with await aopen_iterable(str(path)) as source:
                return [row async for row in source]

        assert asyncio.run(run()) == expected

    def test_jsonl_parity_with_sync(self, tmp_path):
        path = tmp_path / "data.jsonl"
        records = [{"n": i, "nested": {"k": i}} for i in range(10)]
        with open_iterable(str(path), mode="w") as target:
            target.write_bulk(records)

        async def run():
            async with await aopen_iterable(str(path)) as source:
                return [row async for row in source]

        assert asyncio.run(run()) == records

    def test_concurrent_reads_interleave(self, tmp_path):
        path_a = tmp_path / "a.csv"
        path_b = tmp_path / "b.csv"
        _write_csv(path_a, [{"n": i} for i in range(50)])
        _write_csv(path_b, [{"n": i} for i in range(50)])
        order = []

        async def read_all(path, tag):
            async with await aopen_iterable(str(path)) as source:
                async for _row in source:
                    order.append(tag)

        async def run():
            await asyncio.gather(read_all(path_a, "a"), read_all(path_b, "b"))

        asyncio.run(run())
        # A blocked event loop would drain one source fully before the other.
        assert "a" in order[:10] and "b" in order[:10]
        assert len(order) == 100

    def test_aread_bulk_parity(self, tmp_path):
        path = tmp_path / "bulk.jsonl"
        records = [{"n": i} for i in range(25)]
        with open_iterable(str(path), mode="w") as target:
            target.write_bulk(records)

        async def run():
            chunks = []
            async with await aopen_iterable(str(path)) as source:
                while True:
                    chunk = await source.aread_bulk(10)
                    if not chunk:
                        break
                    chunks.append(chunk)
            return chunks

        chunks = asyncio.run(run())
        assert [row for chunk in chunks for row in chunk] == records
        assert [len(c) for c in chunks] == [10, 10, 5]

    def test_parquet_parity_with_sync(self, tmp_path):
        if importlib.util.find_spec("pyarrow") is None:
            import pytest

            pytest.skip("pyarrow not installed")
        path = tmp_path / "data.parquet"
        records = [{"n": i, "s": f"x{i}"} for i in range(15)]
        with open_iterable(str(path), mode="w") as target:
            target.write_bulk(records)

        async def run():
            async with await aopen_iterable(str(path)) as source:
                return [row async for row in source]

        assert asyncio.run(run()) == records
