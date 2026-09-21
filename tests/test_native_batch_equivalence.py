"""Native-versus-row equivalence tests for the opt-in batch conversion path.

For every native-capable source the batch path (``read_batches`` with a
:class:`BatchSelection`) must produce exactly the rows the documented row
fallback produces (row iteration plus row-wise selection). End-to-end
``convert()`` runs must likewise match whether or not the native transfer is
negotiated. Covered: nulls, nested data, dates/timestamps, schema alignment,
projection, predicate pushdown, and row windows including slice steps.
"""

import datetime
import json

import pytest

pyarrow = pytest.importorskip("pyarrow")
pyarrow_parquet = pytest.importorskip("pyarrow.parquet")
pyarrow_ipc = pytest.importorskip("pyarrow.ipc")

from iterable.convert import BatchSelection, convert  # noqa: E402
from iterable.convert.batch import select_rows  # noqa: E402
from iterable.datatypes.arrow import ArrowIterable  # noqa: E402
from iterable.datatypes.numpy import NumPyIterable  # noqa: E402
from iterable.datatypes.orc import HAS_PYARROW_ORC, ORCIterable  # noqa: E402
from iterable.datatypes.parquet import ParquetIterable  # noqa: E402

np = pytest.importorskip("numpy")  # noqa: E402

NUM_ROWS = 20


def _rows():
    """Mixed-type rows: nulls, nested lists/structs, dates and timestamps."""
    return [
        {
            "id": i,
            "name": f"n{i % 3}",
            "value": None if i % 4 == 0 else i * 1.5,
            "day": datetime.date(2024, 1, 1) + datetime.timedelta(days=i),
            "ts": datetime.datetime(2024, 1, 1, 12, 0) + datetime.timedelta(minutes=i),
            "tags": [f"t{i}", f"u{i % 2}"] if i % 2 else [],
            "meta": {"a": i, "b": None} if i % 3 else None,
        }
        for i in range(NUM_ROWS)
    ]


def _concrete_nested_rows():
    """Variant without all-None nested fields.

    ORC and Iceberg v2 reject columns/fields inferred as the Arrow *null
    type* (a struct field that is None in every row); keep the nested
    struct but give ``b`` a concrete type.
    """
    rows = _rows()
    for row in rows:
        if row["meta"] is not None:
            row["meta"] = {"a": row["meta"]["a"], "b": row["id"] % 2}
    return rows


def _flat_rows():
    """Flat primitive rows for writers with limited schema inference."""
    return [{"id": row["id"], "name": row["name"], "value": row["value"]} for row in _rows()]


@pytest.fixture
def parquet_source(tmp_path):
    path = tmp_path / "source.parquet"
    pyarrow_parquet.write_table(pyarrow.Table.from_pylist(_rows()), path)
    return str(path)


@pytest.fixture
def arrow_source(tmp_path):
    path = tmp_path / "source.arrow"
    table = pyarrow.Table.from_pylist(_rows())
    with pyarrow_ipc.new_file(str(path), table.schema) as writer:
        writer.write_table(table)
    return str(path)


@pytest.fixture
def orc_source(tmp_path):
    if not HAS_PYARROW_ORC:
        pytest.skip("pyarrow.orc backend not available")
    path = str(tmp_path / "source.orc")
    with ORCIterable(path, mode="w", backend="pyarrow") as it:
        it.write_bulk(_concrete_nested_rows())
    return str(tmp_path / "source.orc")


@pytest.fixture
def npz_source(tmp_path):
    path = tmp_path / "source.npz"
    grid = (np.arange(NUM_ROWS * 3).reshape(NUM_ROWS, 3) * 0.5).astype(float)
    np.savez_compressed(path, data=grid, other=np.ones((4, 2)))
    return str(path)


SELECTIONS = {
    "full": BatchSelection(),
    "projection": BatchSelection(columns=("id", "value")),
    "predicate": BatchSelection(predicate=("id", ">=", 7)),
    "predicate_multi": BatchSelection(predicate=[("id", ">=", 3), ("value", "<", 10.0)]),
    "row_range": BatchSelection(row_range=(4, 12)),
    "slice_step": BatchSelection(slice=(1, 18, 3)),
    "combo": BatchSelection(columns=("id", "day"), predicate=("id", "<", 15), slice=(2, 14, 2)),
}

# NumPy arrays only carry numeric col_N keys, so text/date predicates and
# projections over other fields do not apply there.
NUMPY_SELECTIONS = {
    "full": BatchSelection(),
    "projection": BatchSelection(columns=("col_0", "col_2")),
    "row_range": BatchSelection(row_range=(4, 12)),
    "slice_step": BatchSelection(slice=(1, 18, 3)),
}


def _native_batches(iterable, selection):
    return [row for batch in iterable.read_batches(selection) for row in batch]


def _row_fallback(iterable, selection):
    return list(select_rows(iter(iterable), selection))


def _assert_native_equals_row(open_reader, selection):
    """Compare batch-path rows with row-fallback rows on fresh readers."""
    with open_reader() as reader:
        native = _native_batches(reader, selection)
    with open_reader() as reader:
        fallback = _row_fallback(reader, selection)
    assert native == fallback


def _force_row_fallback(monkeypatch):
    """Make convert() negotiate the documented row/bulk fallback path."""
    monkeypatch.setattr("iterable.convert.core.native_batch_supported", lambda reader, writer: False)


def _read_parquet(path):
    return pyarrow_parquet.read_table(str(path)).to_pylist()


def _read_arrow(path):
    with pyarrow_ipc.open_file(str(path)) as reader:
        return reader.read_all().to_pylist()


class TestReaderLevelEquivalence:
    """read_batches(selection) must equal row iteration + row-wise selection."""

    @pytest.mark.parametrize("selection", SELECTIONS.values(), ids=SELECTIONS.keys())
    def test_parquet(self, parquet_source, selection):
        _assert_native_equals_row(lambda: ParquetIterable(parquet_source, mode="r"), selection)

    @pytest.mark.parametrize("selection", SELECTIONS.values(), ids=SELECTIONS.keys())
    def test_arrow_ipc(self, arrow_source, selection):
        if selection.predicate is not None:
            pytest.skip("Arrow IPC adapter does not support predicates")
        _assert_native_equals_row(lambda: ArrowIterable(arrow_source, mode="r"), selection)

    @pytest.mark.parametrize("selection", SELECTIONS.values(), ids=SELECTIONS.keys())
    def test_orc_pyarrow_backend(self, orc_source, selection):
        _assert_native_equals_row(lambda: ORCIterable(orc_source, mode="r", backend="pyarrow"), selection)

    @pytest.mark.parametrize("selection", NUMPY_SELECTIONS.values(), ids=NUMPY_SELECTIONS.keys())
    def test_numpy_npz(self, npz_source, selection):
        _assert_native_equals_row(lambda: NumPyIterable(npz_source, mode="r"), selection)

    def test_numpy_table_selection(self, npz_source):
        """Table pushdown picks the named array inside an .npz archive."""
        selection = BatchSelection(table="other")
        with NumPyIterable(npz_source, mode="r") as reader:
            native = _native_batches(reader, selection)
        with NumPyIterable(npz_source, mode="r", array_name="other") as reader:
            fallback = _row_fallback(reader, BatchSelection())
        assert native == fallback
        assert len(native) == 4


class TestConvertEndToEndEquivalence:
    """convert() native path and row fallback must write identical rows."""

    @pytest.mark.parametrize("selection", SELECTIONS.values(), ids=SELECTIONS.keys())
    def test_parquet_to_parquet(self, tmp_path, parquet_source, selection, monkeypatch):
        native_dst = tmp_path / "native.parquet"
        convert(parquet_source, str(native_dst), use_native_batch=True, selection=selection)

        _force_row_fallback(monkeypatch)
        row_dst = tmp_path / "row.parquet"
        convert(parquet_source, str(row_dst), use_native_batch=True, selection=selection)

        native_table = pyarrow_parquet.read_table(str(native_dst))
        row_table = pyarrow_parquet.read_table(str(row_dst))
        assert native_table.to_pylist() == row_table.to_pylist()
        # Schema alignment: identical field names in identical order.
        assert native_table.schema.names == row_table.schema.names

    @pytest.mark.parametrize("selection", SELECTIONS.values(), ids=SELECTIONS.keys())
    def test_orc_to_parquet(self, tmp_path, orc_source, selection, monkeypatch):
        args = {"backend": "pyarrow"}
        native_dst = tmp_path / "native.parquet"
        convert(orc_source, str(native_dst), iterableargs=args, use_native_batch=True, selection=selection)

        _force_row_fallback(monkeypatch)
        row_dst = tmp_path / "row.parquet"
        convert(orc_source, str(row_dst), iterableargs=args, use_native_batch=True, selection=selection)

        assert _read_parquet(native_dst) == _read_parquet(row_dst)

    def test_parquet_to_arrow(self, tmp_path, parquet_source, monkeypatch):
        selection = BatchSelection(columns=("id", "value"), predicate=("id", "!=", 3))
        native_dst = tmp_path / "native.arrow"
        convert(parquet_source, str(native_dst), use_native_batch=True, selection=selection)

        _force_row_fallback(monkeypatch)
        row_dst = tmp_path / "row.arrow"
        convert(parquet_source, str(row_dst), use_native_batch=True, selection=selection)

        assert _read_arrow(native_dst) == _read_arrow(row_dst)

    def test_numpy_to_parquet_with_table_and_step(self, tmp_path, npz_source, monkeypatch):
        selection = BatchSelection(table="data", columns=("col_1",), slice=(1, 18, 4))
        native_dst = tmp_path / "native.parquet"
        convert(npz_source, str(native_dst), use_native_batch=True, selection=selection)

        _force_row_fallback(monkeypatch)
        row_dst = tmp_path / "row.parquet"
        convert(npz_source, str(row_dst), use_native_batch=True, selection=selection)

        native_rows = _read_parquet(native_dst)
        assert native_rows == _read_parquet(row_dst)
        # grid row i is [3i, 3i+1, 3i+2] * 0.5; col_1 of rows 1,5,9,13,17.
        assert [row["col_1"] for row in native_rows] == [(3 * i + 1) * 0.5 for i in (1, 5, 9, 13, 17)]

    def test_unsupported_predicate_falls_back_with_identical_rows(self, tmp_path, arrow_source):
        """Arrow IPC cannot push predicates: fallback must still apply them."""
        selection = BatchSelection(predicate=("id", ">=", 7))
        dst = tmp_path / "out.parquet"
        result = convert(arrow_source, str(dst), use_native_batch=True, selection=selection)
        assert result.errors == []
        expected = [row for row in _rows() if row["id"] >= 7]
        assert _read_parquet(dst) == expected

    def test_unsupported_predicate_strict_mode_raises(self, tmp_path, arrow_source):
        selection = BatchSelection(predicate=("id", ">=", 7))
        with pytest.raises(NotImplementedError, match="Arrow native batches"):
            convert(
                arrow_source,
                str(tmp_path / "out.parquet"),
                use_native_batch=True,
                selection=selection,
                strict_native=True,
            )

    def test_selection_applies_for_row_only_destination(self, tmp_path, parquet_source):
        """JSONL has no native writer; the row path applies the selection."""
        selection = BatchSelection(columns=("id",), predicate=("id", "<", 3))
        dst = tmp_path / "out.jsonl"
        convert(parquet_source, str(dst), selection=selection)
        rows = [json.loads(line) for line in dst.read_text(encoding="utf-8").splitlines()]
        assert rows == [{"id": 0}, {"id": 1}, {"id": 2}]

    def test_nested_null_date_values_preserved(self, tmp_path, parquet_source, monkeypatch):
        """Nulls, nested values, dates and timestamps survive both paths."""
        native_dst = tmp_path / "native.parquet"
        convert(parquet_source, str(native_dst), use_native_batch=True)

        _force_row_fallback(monkeypatch)
        row_dst = tmp_path / "row.parquet"
        convert(parquet_source, str(row_dst), use_native_batch=True)

        native_rows = _read_parquet(native_dst)
        row_rows = _read_parquet(row_dst)
        assert native_rows == row_rows
        sample = native_rows[1]
        assert sample["tags"] == ["t1", "u1"]
        assert sample["meta"] == {"a": 1, "b": None}
        assert sample["day"] == datetime.date(2024, 1, 2)
        assert sample["ts"] == datetime.datetime(2024, 1, 1, 12, 1)
        assert native_rows[0]["value"] is None


deltalake = pytest.importorskip("deltalake", reason="deltalake not installed")


class TestDeltaEquivalence:
    """Delta Lake scanner pushdown matches the sequential row path."""

    @pytest.fixture
    def delta_source(self, tmp_path):
        from iterable.datatypes.delta import DeltaIterable

        path = str(tmp_path / "delta_table")
        with DeltaIterable(path, mode="w", batch_size=4) as it:
            it.write_bulk(_rows())
        return path

    def test_reader_equivalence(self, delta_source):
        from iterable.datatypes.delta import DeltaIterable

        selection = BatchSelection(columns=("id", "value"), predicate=("id", ">=", 7))
        _assert_native_equals_row(lambda: DeltaIterable(delta_source, mode="r"), selection)

    def test_convert_equivalence(self, tmp_path, delta_source, monkeypatch):
        args = {"format": "delta"}
        selection = BatchSelection(columns=("id", "value"), predicate=("id", ">=", 7))
        native_dst = tmp_path / "native.parquet"
        convert(delta_source, str(native_dst), iterableargs=args, use_native_batch=True, selection=selection)

        _force_row_fallback(monkeypatch)
        row_dst = tmp_path / "row.parquet"
        convert(delta_source, str(row_dst), iterableargs=args, use_native_batch=True, selection=selection)

        assert _read_parquet(native_dst) == _read_parquet(row_dst)


pyiceberg = pytest.importorskip("pyiceberg", reason="pyiceberg not installed")


class TestIcebergEquivalence:
    """Iceberg scan pushdown matches the sequential row path."""

    @pytest.fixture
    def iceberg_args(self, tmp_path):
        from iterable.datatypes.iceberg import IcebergIterable

        warehouse = tmp_path / "warehouse"
        warehouse.mkdir()
        catalog = {
            "type": "sql",
            "uri": f"sqlite:///{tmp_path / 'catalog.db'}",
            "warehouse": f"file://{warehouse}",
        }
        options = {"catalog": catalog, "create_table": True}
        with IcebergIterable(
            str(warehouse), mode="w", catalog_name="default", table_name="ns.equiv", options=options
        ) as it:
            it.write_bulk(_flat_rows())
        return str(warehouse), {"format": "iceberg", "catalog": catalog, "table_name": "ns.equiv"}

    def test_convert_equivalence(self, tmp_path, iceberg_args, monkeypatch):
        warehouse, args = iceberg_args
        selection = BatchSelection(columns=("id", "value"), predicate=("id", ">=", 7))
        native_dst = tmp_path / "native.parquet"
        convert(warehouse, str(native_dst), iterableargs=args, use_native_batch=True, selection=selection)

        _force_row_fallback(monkeypatch)
        row_dst = tmp_path / "row.parquet"
        convert(warehouse, str(row_dst), iterableargs=args, use_native_batch=True, selection=selection)

        assert _read_parquet(native_dst) == _read_parquet(row_dst)
