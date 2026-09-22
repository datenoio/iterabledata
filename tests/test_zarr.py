"""Tests for the Zarr v2/v3 datatype.

Committed golden fixtures (tests/fixtures/zarr_v2.zarr, zarr_v3.zarr) each hold
three tiny arrays: ``values`` (1-D int64, 6 rows of 0,10,...,50, chunks 3),
``records`` (structured id/name, 6 rows) and ``matrix`` (3x2 float64, chunks
(2, 2)). Large/chunked stores are generated under tmp_path instead.
"""

from types import SimpleNamespace

import pytest

zarr = pytest.importorskip("zarr")
np = pytest.importorskip("numpy")

from pathlib import Path  # noqa: E402

from iterable import open_iterable  # noqa: E402
from iterable.datatypes.zarr import ZarrIterable  # noqa: E402

FIXTURES = Path(__file__).parent / "fixtures"
STORE_VERSIONS = ["zarr_v2.zarr", "zarr_v3.zarr"]

VALUES = [0, 10, 20, 30, 40, 50]
RECORDS = [{"id": i, "name": f"row-{i}"} for i in range(6)]
MATRIX = [[0.0, 1.0], [2.0, 3.0], [4.0, 5.0]]


@pytest.fixture(params=STORE_VERSIONS)
def store(request):
    return str(FIXTURES / request.param)


# ---------------------------------------------------------------------------
# Read behavior and row mappings
# ---------------------------------------------------------------------------


class TestRead:
    def test_read_dense_1d_row_mapping(self, store):
        with ZarrIterable(store, array="values") as source:
            assert source.read() == {"index": 0, "value": 0}
            assert source.read() == {"index": 1, "value": 10}

    def test_read_bulk_partial_then_empty(self, store):
        with ZarrIterable(store, array="values") as source:
            assert source.read_bulk(4) == [{"index": i, "value": v} for i, v in enumerate(VALUES[:4])]
            assert source.read_bulk(4) == [{"index": i + 4, "value": v} for i, v in enumerate(VALUES[4:])]
            assert source.read_bulk(4) == []

    def test_read_exhaustion_raises_stop_iteration(self, store):
        with ZarrIterable(store, array="values") as source:
            for _ in range(6):
                source.read()
            with pytest.raises(StopIteration):
                source.read()

    def test_reset_replays(self, store):
        with ZarrIterable(store, array="values") as source:
            first = [row["value"] for row in source.read_bulk(3)]
            source.reset()
            assert [row["value"] for row in source.read_bulk(6)] == VALUES
            assert first == VALUES[:3]

    def test_totals(self, store):
        with ZarrIterable(store, array="values") as source:
            assert source.totals() == 6

    def test_interleaved_read_and_bulk_share_cursor(self, store):
        with ZarrIterable(store, array="values") as source:
            rows = [source.read()]
            rows.extend(source.read_bulk(2))
            rows.append(source.read())
            rows.extend(source.read_bulk(100))
            assert [row["index"] for row in rows] == list(range(6))
            assert [row["value"] for row in rows] == VALUES

    def test_dense_2d_row_mapping(self, store):
        with ZarrIterable(store, array="matrix") as source:
            rows = source.read_bulk(10)
            assert rows == [{"index": i, "values": MATRIX[i]} for i in range(3)]

    def test_structured_row_mapping(self, store):
        with ZarrIterable(store, array="records") as source:
            assert source.read_bulk(10) == RECORDS

    def test_scalar_array_yields_single_record(self, tmp_path):
        path = str(tmp_path / "scalar.zarr")
        group = zarr.open_group(path, mode="a")
        group.create_array("answer", shape=(), dtype="i8")[()] = 42
        with ZarrIterable(path, array="answer") as source:
            assert source.totals() == 1
            assert source.read() == {"value": 42}
            with pytest.raises(StopIteration):
                source.read()

    def test_array_mode_numpy(self, store):
        with ZarrIterable(store, array="matrix", array_mode="numpy") as source:
            row = source.read()
            assert isinstance(row["values"], np.ndarray)
            assert row["values"].tolist() == MATRIX[0]


# ---------------------------------------------------------------------------
# Table discovery and array selection
# ---------------------------------------------------------------------------


class TestTables:
    def test_list_tables_sorted(self, store):
        with ZarrIterable(store, array="values") as source:
            assert source.list_tables() == ["matrix", "records", "values"]

    def test_ambiguous_store_requires_array(self, store):
        with pytest.raises(ValueError, match="multiple arrays"):
            ZarrIterable(store)

    def test_missing_array_names_available(self, store):
        with pytest.raises(KeyError, match="nope"):
            ZarrIterable(store, array="nope")

    def test_single_array_store_auto_selects(self, tmp_path):
        path = str(tmp_path / "single.zarr")
        group = zarr.open_group(path, mode="a")
        group.create_array("only", shape=(2,), dtype="i8")[:] = [7, 8]
        with ZarrIterable(path) as source:
            assert [row["value"] for row in source.read_bulk(10)] == [7, 8]

    def test_has_tables(self):
        assert ZarrIterable.has_tables() is True


# ---------------------------------------------------------------------------
# Selection: axis, slice, fields, chunk-aware reads
# ---------------------------------------------------------------------------


class TestSelection:
    def test_slice_window(self, store):
        with ZarrIterable(store, array="values", slice=(2, 5)) as source:
            assert source.totals() == 3
            rows = source.read_bulk(10)
            assert [row["index"] for row in rows] == [2, 3, 4]
            assert [row["value"] for row in rows] == [20, 30, 40]

    def test_slice_step(self, store):
        with ZarrIterable(store, array="values", slice=(0, 6, 2)) as source:
            assert source.totals() == 3
            assert [row["value"] for row in source.read_bulk(10)] == [0, 20, 40]

    def test_slice_open_ends(self, store):
        with ZarrIterable(store, array="values", slice=(None, None, 3)) as source:
            assert [row["index"] for row in source.read_bulk(10)] == [0, 3]

    def test_slice_negative_rejected(self, store):
        with pytest.raises(ValueError, match="Negative"):
            ZarrIterable(store, array="values", slice=(-2, 4))

    def test_slice_zero_step_rejected(self, store):
        with pytest.raises(ValueError, match="step"):
            ZarrIterable(store, array="values", slice=(0, 6, 0))

    def test_axis_iteration(self, store):
        with ZarrIterable(store, array="matrix", axis=1) as source:
            assert source.totals() == 2
            rows = source.read_bulk(10)
            assert rows == [
                {"index": 0, "values": [0.0, 2.0, 4.0]},
                {"index": 1, "values": [1.0, 3.0, 5.0]},
            ]

    def test_axis_out_of_range(self, store):
        with pytest.raises(ValueError, match="axis"):
            ZarrIterable(store, array="matrix", axis=5)

    def test_fields_projection(self, store):
        with ZarrIterable(store, array="records", fields=["name"]) as source:
            assert source.read_bulk(2) == [{"name": "row-0"}, {"name": "row-1"}]

    def test_fields_unknown_field(self, store):
        with pytest.raises(KeyError, match="unknown"):
            ZarrIterable(store, array="records", fields=["unknown"])

    def test_fields_on_dense_array_rejected(self, store):
        with pytest.raises(ValueError, match="structured"):
            ZarrIterable(store, array="values", fields=["value"])

    def test_chunk_aligned_reads_cross_boundaries(self, tmp_path):
        # chunks of 3 along axis 0 with a bulk size that is not a chunk multiple
        path = str(tmp_path / "chunked.zarr")
        group = zarr.open_group(path, mode="a")
        data = np.arange(1000, dtype="i8")
        group.create_array("values", shape=data.shape, chunks=(3,), dtype="i8")[:] = data
        with ZarrIterable(path, array="values") as source:
            rows = []
            while True:
                batch = source.read_bulk(7)
                if not batch:
                    break
                rows.extend(batch)
            assert [row["value"] for row in rows] == data.tolist()

    def test_iterableargs_plumbing(self, store):
        with open_iterable(
            store,
            iterableargs={"format": "zarr", "array": "values", "slice": (1, 4), "columns": None},
        ) as source:
            rows = source.read_bulk(10)
            assert [row["value"] for row in rows] == [10, 20, 30]

    def test_open_iterable_auto_detects_zarr_directory(self, store):
        with open_iterable(store, iterableargs={"array": "values"}) as source:
            assert source.id() == "zarr"
            assert source.totals() == 6


# ---------------------------------------------------------------------------
# Malformed stores and dependency errors
# ---------------------------------------------------------------------------


class TestErrors:
    def test_missing_store(self, tmp_path):
        with pytest.raises(FileNotFoundError, match="not found"):
            ZarrIterable(str(tmp_path / "absent.zarr"))

    def test_plain_directory_is_not_a_store(self, tmp_path):
        path = tmp_path / "plain.zarr"
        path.mkdir()
        with pytest.raises(ValueError, match="not a valid Zarr store"):
            ZarrIterable(str(path))

    def test_file_instead_of_directory(self, tmp_path):
        path = tmp_path / "file.zarr"
        path.write_text("not a store", encoding="utf-8")
        with pytest.raises(FileNotFoundError, match="not found"):
            ZarrIterable(str(path))

    def test_stream_rejected(self):
        import io

        with pytest.raises(ValueError, match="stream"):
            ZarrIterable(stream=io.BytesIO(b""))

    def test_missing_dependency_message(self, monkeypatch, tmp_path):
        import iterable.datatypes.zarr as zarr_module

        monkeypatch.setattr(zarr_module, "zarr", None)
        with pytest.raises(ImportError, match=r"iterabledata\[zarr\]"):
            ZarrIterable(str(tmp_path / "x.zarr"))

    def test_object_array_read_requires_opt_in(self, store):
        # zarr 3 itself cannot parse object-dtype metadata, so exercise the
        # guard with a stand-in array carrying an object dtype (zarr 2 stores).
        with ZarrIterable(store, array="values") as source:
            source._array = SimpleNamespace(dtype=np.dtype(object), shape=(2,))
            with pytest.raises(ValueError, match="allow_object"):
                source._configure_selection()


# ---------------------------------------------------------------------------
# Write behavior
# ---------------------------------------------------------------------------


class TestWrite:
    def test_round_trip_dense(self, tmp_path):
        path = str(tmp_path / "out.zarr")
        with ZarrIterable(path, mode="w", chunks=2, array="value") as output:
            output.write_bulk([{"value": 1}, {"value": 2}, {"value": 3}])
        with ZarrIterable(path, array="value") as source:
            assert source.read() == {"index": 0, "value": 1}
            assert source.read_bulk(2) == [{"index": 1, "value": 2}, {"index": 2, "value": 3}]

    def test_write_flushes_by_chunks(self, tmp_path):
        path = str(tmp_path / "chunks.zarr")
        with ZarrIterable(path, mode="w", chunks=2, array="value") as output:
            for i in range(5):
                output.write({"value": i})
        array = zarr.open_group(path, mode="r")["value"]
        assert array.shape == (5,)
        assert array.chunks == (2,)
        assert array[:].tolist() == [0, 1, 2, 3, 4]

    def test_structured_inference_round_trip(self, tmp_path):
        path = str(tmp_path / "structured.zarr")
        with ZarrIterable(path, mode="w", chunks=4) as output:
            for row in RECORDS:
                output.write(dict(row))
        with ZarrIterable(path) as source:
            assert source.list_tables() == ["records"]
            assert source.read_bulk(10) == RECORDS

    def test_explicit_dtype(self, tmp_path):
        path = str(tmp_path / "dtype.zarr")
        with ZarrIterable(path, mode="w", array="value", dtype="f8") as output:
            output.write_bulk([{"value": 1}, {"value": 2}])
        array = zarr.open_group(path, mode="r")["value"]
        assert array.dtype == np.dtype("f8")
        assert array[:].tolist() == [1.0, 2.0]

    def test_explicit_structured_dtype(self, tmp_path):
        path = str(tmp_path / "schema.zarr")
        dtype = [("id", "i8"), ("name", "U32")]
        with ZarrIterable(path, mode="w", array="recs", dtype=dtype) as output:
            output.write_bulk(RECORDS[:2])
        with ZarrIterable(path, array="recs") as source:
            assert source.read_bulk(10) == RECORDS[:2]

    def test_dtype_mismatch_fails_without_silent_coercion(self, tmp_path):
        path = str(tmp_path / "mismatch.zarr")
        with pytest.raises(ValueError, match="dtype mismatch"):
            with ZarrIterable(path, mode="w", chunks=1, array="value") as output:
                output.write_bulk([{"value": 1}])
                output.write_bulk([{"value": 1.5}])  # float into int64 array

    def test_string_truncation_fails(self, tmp_path):
        path = str(tmp_path / "strings.zarr")
        with pytest.raises(ValueError, match="dtype mismatch"):
            with ZarrIterable(path, mode="w", chunks=1) as output:
                output.write({"name": "ab"})
                output.write({"name": "much-longer-name"})

    def test_shape_mismatch_fails(self, tmp_path):
        path = str(tmp_path / "shape.zarr")
        with pytest.raises(ValueError, match="shape mismatch"):
            with ZarrIterable(path, mode="w", chunks=1, array="value") as output:
                output.write_bulk([{"value": [1, 2]}])
                output.write_bulk([{"value": [1, 2, 3]}])

    def test_structured_schema_mismatch_fails(self, tmp_path):
        path = str(tmp_path / "schema-mismatch.zarr")
        with pytest.raises(ValueError, match="schema mismatch"):
            with ZarrIterable(path, mode="w", chunks=2) as output:
                output.write_bulk([{"id": 1, "name": "a"}, {"id": 2, "name": "b"}])
                output.write_bulk([{"id": 3, "extra": 1}])

    def test_inconsistent_batch_fields_fail(self, tmp_path):
        path = str(tmp_path / "batch.zarr")
        with pytest.raises(ValueError, match="same field set"):
            with ZarrIterable(path, mode="w", chunks=10) as output:
                output.write_bulk([{"id": 1}, {"id": 2, "name": "b"}])

    def test_object_dtype_write_blocked_by_default(self, tmp_path):
        path = str(tmp_path / "object.zarr")
        with pytest.raises(ValueError, match="allow_object"):
            with ZarrIterable(path, mode="w", array="value") as output:
                output.write({"value": {"nested": "dict"}})

    def test_missing_field_keyerror(self, tmp_path):
        path = str(tmp_path / "field.zarr")
        with pytest.raises(KeyError, match="value"):
            with ZarrIterable(path, mode="w", array="value") as output:
                output.write({"other": 1})

    def test_multi_field_record_with_array_extracts_field(self, tmp_path):
        path = str(tmp_path / "extract.zarr")
        with ZarrIterable(path, mode="w", array="value") as output:
            output.write_bulk([{"index": 0, "value": 5}, {"index": 1, "value": 6}])
        with ZarrIterable(path, array="value") as source:
            assert [row["value"] for row in source.read_bulk(10)] == [5, 6]

    def test_mode_w_truncates_existing_array(self, tmp_path):
        path = str(tmp_path / "truncate.zarr")
        for values in ([1, 2, 3], [9]):
            with ZarrIterable(path, mode="w", array="value") as output:
                output.write_bulk([{"value": v} for v in values])
        with ZarrIterable(path, array="value") as source:
            assert source.totals() == 1

    def test_write_zarr_format_v2(self, tmp_path):
        path = str(tmp_path / "v2write.zarr")
        with ZarrIterable(path, mode="w", array="value", zarr_format=2) as output:
            output.write_bulk([{"value": 1}, {"value": 2}])
        assert (tmp_path / "v2write.zarr" / ".zgroup").exists()
        with ZarrIterable(path, array="value") as source:
            assert [row["value"] for row in source.read_bulk(10)] == [1, 2]

    def test_invalid_zarr_format(self, tmp_path):
        with pytest.raises(ValueError, match="zarr_format"):
            ZarrIterable(str(tmp_path / "x.zarr"), mode="w", zarr_format=7)

    def test_non_dict_record_rejected(self, tmp_path):
        path = str(tmp_path / "types.zarr")
        with pytest.raises(TypeError):
            with ZarrIterable(path, mode="w", array="value", chunks=1) as output:
                output.write_bulk([42])

    def test_totals_while_writing(self, tmp_path):
        path = str(tmp_path / "totals.zarr")
        with ZarrIterable(path, mode="w", chunks=2, array="value") as output:
            output.write_bulk([{"value": 1}, {"value": 2}])  # flushed
            output.write({"value": 3})  # buffered
            assert output.totals() == 3

    def test_open_iterable_write_round_trip(self, tmp_path):
        path = str(tmp_path / "via-open.zarr")
        with open_iterable(path, mode="w", iterableargs={"format": "zarr", "array": "value", "chunks": 2}) as output:
            output.write_bulk([{"value": 1}, {"value": 2}, {"value": 3}])
        with open_iterable(path, iterableargs={"array": "value"}) as source:
            assert [row["value"] for row in source.read_bulk(10)] == [1, 2, 3]


# ---------------------------------------------------------------------------
# fsspec / cloud-style stores (no live credentials)
# ---------------------------------------------------------------------------


class TestFsspecStores:
    def test_memory_store_round_trip(self):
        url = "memory://iterabledata-tests/roundtrip.zarr"
        with ZarrIterable(url, mode="w", chunks=2, array="value") as output:
            output.write_bulk([{"value": i} for i in range(5)])
        with ZarrIterable(url, array="value") as source:
            assert source.totals() == 5
            assert [row["value"] for row in source.read_bulk(10)] == list(range(5))

    def test_memory_store_structured_and_slice(self):
        url = "memory://iterabledata-tests/structured.zarr"
        with ZarrIterable(url, mode="w", chunks=4) as output:
            for row in RECORDS:
                output.write(dict(row))
        with ZarrIterable(url, array="records", fields=["name"], slice=(2, 4)) as source:
            assert source.read_bulk(10) == [{"name": "row-2"}, {"name": "row-3"}]

    def test_memory_store_via_open_iterable_write(self):
        url = "memory://iterabledata-tests/open.zarr"
        with open_iterable(url, mode="w", iterableargs={"format": "zarr", "array": "value"}) as output:
            output.write_bulk([{"value": 42}])
        with ZarrIterable(url, array="value") as source:
            assert source.read() == {"index": 0, "value": 42}

    def test_memory_store_missing_is_clear_error(self):
        with pytest.raises(ValueError, match="not a valid Zarr store"):
            ZarrIterable("memory://iterabledata-tests/definitely-absent.zarr")


# ---------------------------------------------------------------------------
# Bounded memory
# ---------------------------------------------------------------------------


class TestBoundedMemory:
    def test_large_chunked_tmp_store_streams(self, tmp_path):
        # Generated large/chunked fixture: 50k x 4 float64 (~1.6 MB) with
        # unaligned chunking; full pass must stay far below whole-array memory.
        import tracemalloc

        path = str(tmp_path / "large.zarr")
        group = zarr.open_group(path, mode="a")
        rows, cols = 50_000, 4
        array = group.create_array("values", shape=(rows, cols), chunks=(997, cols), dtype="f8")
        for start in range(0, rows, 5000):
            array[start : start + 5000] = np.arange(5000 * cols, dtype="f8").reshape(5000, cols) + start

        with ZarrIterable(path, array="values") as source:
            assert source.totals() == rows
            tracemalloc.start()
            count = 0
            while True:
                batch = source.read_bulk(256)
                if not batch:
                    break
                count += len(batch)
            _, peak = tracemalloc.get_traced_memory()
            tracemalloc.stop()
            assert count == rows
            # Peak stays batch/chunk bounded, far below the ~1.6 MB array.
            assert peak < 1_000_000, f"peak memory {peak} bytes"
