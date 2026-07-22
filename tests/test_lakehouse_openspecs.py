"""Tests for DuckLake, Paimon tables, Delta/Iceberg writes, and Hudi deferral."""

from __future__ import annotations

import importlib.util

import pytest

from iterable.helpers.detect import open_iterable
from iterable.helpers.format_registry import get_descriptor, install_extra_hint

RECORDS = [
    {"id": 1, "name": "Alice"},
    {"id": 2, "name": "Bob"},
    {"id": 3, "name": "Carol"},
]


def _has(module: str) -> bool:
    return importlib.util.find_spec(module) is not None


def _iceberg_catalog(tmp_path):
    warehouse = tmp_path / "warehouse"
    warehouse.mkdir(exist_ok=True)
    catalog_db = tmp_path / "cat.db"
    catalog = {
        "type": "sql",
        "uri": f"sqlite:///{catalog_db}",
        "warehouse": f"file://{warehouse}",
    }
    return warehouse, catalog


class TestDescriptors:
    def test_ducklake_descriptor(self):
        desc = get_descriptor("ducklake")
        assert desc is not None
        assert desc.cls == "DuckLakeIterable"
        assert desc.writable is True
        assert desc.maturity == "experimental"
        assert install_extra_hint("iterable.datatypes.ducklake") == "ducklake"

    def test_paimon_table_descriptor(self):
        desc = get_descriptor("paimon")
        assert desc is not None
        assert desc.cls == "PaimonTableIterable"
        assert desc.id == "paimon"
        assert get_descriptor("paimon_row").cls == "PaimonRowIterable"
        assert get_descriptor("paimon_mosaic").cls == "PaimonMosaicIterable"
        assert install_extra_hint("iterable.datatypes.paimon") == "paimon-table"

    def test_lakehouse_write_capabilities(self):
        assert get_descriptor("delta").writable is True
        assert get_descriptor("iceberg").writable is True
        assert get_descriptor("hudi").writable is False
        assert get_descriptor("ducklake").writable is True
        assert get_descriptor("paimon").writable is True


class TestLakehouseWriteHelpers:
    def test_records_to_arrow_and_infer(self):
        pytest.importorskip("pyarrow")
        from iterable.helpers.lakehouse_write import infer_arrow_schema, records_to_arrow_table

        schema = infer_arrow_schema(RECORDS)
        table = records_to_arrow_table(RECORDS, schema=schema)
        assert table.num_rows == 3
        assert table.column_names == ["id", "name"]
        empty = records_to_arrow_table([], schema=schema)
        assert empty.num_rows == 0

    def test_infer_empty_raises(self):
        pytest.importorskip("pyarrow")
        from iterable.helpers.lakehouse_write import infer_arrow_schema

        with pytest.raises(ValueError, match="empty"):
            infer_arrow_schema([])

    def test_require_pyarrow_missing(self, monkeypatch):
        import iterable.helpers.lakehouse_write as mod

        monkeypatch.setattr(mod, "HAS_PYARROW", False)
        with pytest.raises(ImportError, match="pyarrow"):
            mod.require_pyarrow()


@pytest.mark.skipif(not _has("pyducklake"), reason="pyducklake not installed")
class TestDuckLake:
    def test_round_trip_and_list(self, tmp_path):
        meta = tmp_path / "meta.duckdb"
        data = tmp_path / "data"
        data.mkdir()
        with open_iterable(
            str(meta),
            mode="w",
            iterableargs={
                "format": "ducklake",
                "table": "events",
                "data_path": str(data),
                "create_table": True,
            },
        ) as dest:
            assert dest.id() == "ducklake"
            dest.write_bulk(RECORDS)
        with open_iterable(
            str(meta),
            iterableargs={"format": "ducklake", "table": "events", "data_path": str(data)},
        ) as source:
            assert source.totals() == 3
            rows = list(source)
            tables = source.list_tables()
        assert [r["name"] for r in rows] == ["Alice", "Bob", "Carol"]
        assert any(t == "main.events" or t.endswith(".events") or t == "events" for t in tables)

    def test_top_level_format_overrides_duckdb_extension(self, tmp_path):
        meta = tmp_path / "meta.duckdb"
        data = tmp_path / "data"
        data.mkdir()
        with open_iterable(
            str(meta),
            mode="w",
            format="ducklake",
            iterableargs={"table": "people", "data_path": str(data), "create_table": True},
        ) as dest:
            assert dest.id() == "ducklake"
            dest.write({"id": 1, "name": "Zed"})
        with open_iterable(
            str(meta),
            format="ducklake",
            iterableargs={"table": "people", "data_path": str(data)},
        ) as source:
            assert list(source) == [{"id": 1, "name": "Zed"}]

    def test_single_table_auto_select(self, tmp_path):
        meta = tmp_path / "meta.duckdb"
        data = tmp_path / "data"
        data.mkdir()
        with open_iterable(
            str(meta),
            mode="w",
            iterableargs={
                "format": "ducklake",
                "table": "only",
                "data_path": str(data),
                "create_table": True,
            },
        ) as dest:
            dest.write_bulk(RECORDS[:1])
        with open_iterable(str(meta), iterableargs={"format": "ducklake", "data_path": str(data)}) as source:
            assert source.totals() == 1
            assert source.read()["name"] == "Alice"

    def test_ambiguous_tables(self, tmp_path):
        from pyducklake import Catalog, IntegerType, Schema, StringType, optional, required

        from iterable.exceptions import ReadError

        meta = tmp_path / "meta.duckdb"
        data = tmp_path / "data"
        data.mkdir()
        cat = Catalog("lake", str(meta), data_path=str(data))
        schema = Schema.of(required("id", IntegerType()), optional("name", StringType()))
        cat.create_table("t1", schema)
        cat.create_table("t2", schema)
        cat.close()
        with pytest.raises(ReadError, match="multiple tables"):
            open_iterable(str(meta), iterableargs={"format": "ducklake", "data_path": str(data)})

    def test_missing_table_raises(self, tmp_path):
        from iterable.exceptions import ReadError

        meta = tmp_path / "meta.duckdb"
        data = tmp_path / "data"
        data.mkdir()
        with open_iterable(
            str(meta),
            mode="w",
            iterableargs={
                "format": "ducklake",
                "table": "events",
                "data_path": str(data),
                "create_table": True,
            },
        ) as dest:
            dest.write_bulk(RECORDS[:1])
        with pytest.raises(ReadError, match="not found"):
            open_iterable(
                str(meta),
                iterableargs={"format": "ducklake", "table": "missing", "data_path": str(data)},
            )

    def test_write_requires_create_table(self, tmp_path):
        from iterable.exceptions import ReadError

        meta = tmp_path / "meta.duckdb"
        data = tmp_path / "data"
        data.mkdir()
        with pytest.raises(ReadError, match="not found|create_table"):
            open_iterable(
                str(meta),
                mode="w",
                iterableargs={"format": "ducklake", "table": "events", "data_path": str(data)},
            )

    def test_append_and_reset_read_bulk(self, tmp_path):
        meta = tmp_path / "meta.duckdb"
        data = tmp_path / "data"
        data.mkdir()
        args = {"format": "ducklake", "table": "events", "data_path": str(data), "create_table": True}
        with open_iterable(str(meta), mode="w", iterableargs=args) as dest:
            dest.write_bulk(RECORDS[:2])
        with open_iterable(
            str(meta),
            mode="w",
            iterableargs={"format": "ducklake", "table": "events", "data_path": str(data)},
        ) as dest:
            dest.write_bulk(RECORDS[2:])
        with open_iterable(
            str(meta),
            iterableargs={"format": "ducklake", "table": "events", "data_path": str(data)},
        ) as source:
            assert source.totals() == 3
            first = source.read()
            bulk = source.read_bulk(10)
            source.reset()
            again = list(source)
        assert first["name"] == "Alice"
        assert [r["name"] for r in bulk] == ["Bob", "Carol"]
        assert [r["name"] for r in again] == ["Alice", "Bob", "Carol"]

    def test_batch_size_flush(self, tmp_path):
        meta = tmp_path / "meta.duckdb"
        data = tmp_path / "data"
        data.mkdir()
        with open_iterable(
            str(meta),
            mode="w",
            iterableargs={
                "format": "ducklake",
                "table": "events",
                "data_path": str(data),
                "create_table": True,
                "batch_size": 2,
            },
        ) as dest:
            dest.write_bulk(RECORDS)
        with open_iterable(
            str(meta),
            iterableargs={"format": "ducklake", "table": "events", "data_path": str(data)},
        ) as source:
            assert source.totals() == 3

    def test_stream_rejected(self):
        import io

        from iterable.datatypes.ducklake import DuckLakeIterable
        from iterable.exceptions import ReadError

        with pytest.raises(ReadError, match="not a stream"):
            DuckLakeIterable(stream=io.BytesIO(b""), mode="r", table="t")

    def test_invalid_write_mode(self, tmp_path):
        meta = tmp_path / "meta.duckdb"
        data = tmp_path / "data"
        data.mkdir()
        with pytest.raises(ValueError, match="write_mode"):
            open_iterable(
                str(meta),
                mode="w",
                iterableargs={
                    "format": "ducklake",
                    "table": "events",
                    "data_path": str(data),
                    "create_table": True,
                    "write_mode": "merge",
                },
            )

    def test_missing_dependency(self, monkeypatch):
        import iterable.datatypes.ducklake as mod

        monkeypatch.setattr(mod, "HAS_PYDUCKLAKE", False)
        with pytest.raises(ImportError, match="ducklake"):
            mod.DuckLakeIterable(filename="x.duckdb", mode="r", table="t")


@pytest.mark.skipif(not _has("pypaimon"), reason="pypaimon not installed")
class TestPaimonTable:
    def test_round_trip_and_list(self, tmp_path):
        warehouse = tmp_path / "warehouse"
        warehouse.mkdir()
        with open_iterable(
            str(warehouse),
            mode="w",
            iterableargs={
                "format": "paimon",
                "database": "demo",
                "table": "people",
                "create_table": True,
            },
        ) as dest:
            assert dest.id() == "paimon"
            dest.write_bulk(RECORDS)
        with open_iterable(
            str(warehouse),
            iterableargs={"format": "paimon", "database": "demo", "table": "people"},
        ) as source:
            assert source.totals() == 3
            rows = list(source)
            tables = source.list_tables()
        assert [r["name"] for r in rows] == ["Alice", "Bob", "Carol"]
        assert "demo.people" in tables

    def test_append_and_reset(self, tmp_path):
        warehouse = tmp_path / "warehouse"
        warehouse.mkdir()
        args = {"format": "paimon", "database": "demo", "table": "people", "create_table": True}
        with open_iterable(str(warehouse), mode="w", iterableargs=args) as dest:
            dest.write_bulk(RECORDS[:2])
        with open_iterable(
            str(warehouse),
            mode="w",
            iterableargs={"format": "paimon", "database": "demo", "table": "people"},
        ) as dest:
            dest.write(RECORDS[2])
        with open_iterable(
            str(warehouse),
            iterableargs={"format": "paimon", "database": "demo", "table": "people"},
        ) as source:
            names = [r["name"] for r in source]
            source.reset()
            assert source.totals() == 3
            assert [r["name"] for r in source] == names
        assert names == ["Alice", "Bob", "Carol"]

    def test_column_projection(self, tmp_path):
        warehouse = tmp_path / "warehouse"
        warehouse.mkdir()
        with open_iterable(
            str(warehouse),
            mode="w",
            iterableargs={
                "format": "paimon",
                "database": "demo",
                "table": "people",
                "create_table": True,
            },
        ) as dest:
            dest.write_bulk(RECORDS)
        with open_iterable(
            str(warehouse),
            iterableargs={
                "format": "paimon",
                "database": "demo",
                "table": "people",
                "columns": ["name"],
            },
        ) as source:
            rows = list(source)
        assert all(set(r.keys()) == {"name"} or "name" in r for r in rows)
        assert [r["name"] for r in rows] == ["Alice", "Bob", "Carol"]

    def test_write_requires_create_table(self, tmp_path):
        from iterable.exceptions import ReadError

        warehouse = tmp_path / "warehouse"
        warehouse.mkdir()
        with pytest.raises(ReadError, match="create_table"):
            open_iterable(
                str(warehouse),
                mode="w",
                iterableargs={"format": "paimon", "database": "demo", "table": "people"},
            )

    def test_missing_table_coords(self):
        from iterable.exceptions import ReadError

        with pytest.raises(ReadError):
            open_iterable("/tmp/nope", iterableargs={"format": "paimon"})

    def test_stream_rejected(self):
        import io

        from iterable.datatypes.paimon import PaimonTableIterable
        from iterable.exceptions import ReadError

        with pytest.raises(ReadError, match="not a stream"):
            PaimonTableIterable(stream=io.BytesIO(b""), mode="r", table="t")

    def test_file_formats_unchanged(self, tmp_path):
        path = tmp_path / "x.row"
        schema = [("id", "bigint"), ("name", "string")]
        with open_iterable(str(path), mode="w", iterableargs={"schema": schema}) as dest:
            dest.write({"id": 1, "name": "a"})
        with open_iterable(str(path), iterableargs={"schema": schema}) as source:
            assert source.id() == "paimon_row"

    def test_missing_dependency(self, monkeypatch):
        import iterable.datatypes.paimon as mod

        monkeypatch.setattr(mod, "HAS_PYPAIMON", False)
        with pytest.raises(ImportError, match="paimon-table"):
            mod.PaimonTableIterable(filename="/tmp/w", mode="r", table="t")


@pytest.mark.skipif(not _has("deltalake"), reason="deltalake not installed")
class TestDeltaWrites:
    def test_round_trip(self, tmp_path):
        path = tmp_path / "delta_table"
        with open_iterable(str(path), mode="w", iterableargs={"format": "delta", "write_mode": "overwrite"}) as dest:
            assert dest.id() == "delta"
            dest.write_bulk(RECORDS)
        with open_iterable(str(path), iterableargs={"format": "delta"}) as source:
            assert source.totals() == 3
            assert [r["name"] for r in source] == ["Alice", "Bob", "Carol"]

    def test_append_and_overwrite(self, tmp_path):
        path = tmp_path / "delta_modes"
        with open_iterable(str(path), mode="w", iterableargs={"format": "delta", "write_mode": "overwrite"}) as dest:
            dest.write_bulk(RECORDS[:2])
        with open_iterable(str(path), mode="w", iterableargs={"format": "delta", "write_mode": "append"}) as dest:
            dest.write_bulk(RECORDS[2:])
        with open_iterable(str(path), iterableargs={"format": "delta"}) as source:
            assert source.totals() == 3
        with open_iterable(str(path), mode="w", iterableargs={"format": "delta", "write_mode": "overwrite"}) as dest:
            dest.write_bulk(RECORDS[:1])
        with open_iterable(str(path), iterableargs={"format": "delta"}) as source:
            assert [r["name"] for r in source] == ["Alice"]

    def test_reset_and_read_bulk(self, tmp_path):
        path = tmp_path / "delta_bulk"
        with open_iterable(str(path), mode="w", iterableargs={"format": "delta", "write_mode": "overwrite"}) as dest:
            dest.write_bulk(RECORDS)
        with open_iterable(str(path), iterableargs={"format": "delta"}) as source:
            assert source.read()["name"] == "Alice"
            bulk = source.read_bulk(10)
            source.reset()
            assert source.totals() == 3
            assert list(source)[0]["name"] == "Alice"
        assert [r["name"] for r in bulk] == ["Bob", "Carol"]

    def test_batch_size_flush(self, tmp_path):
        path = tmp_path / "delta_batch"
        with open_iterable(
            str(path),
            mode="w",
            iterableargs={"format": "delta", "write_mode": "overwrite", "batch_size": 2},
        ) as dest:
            dest.write_bulk(RECORDS)
        with open_iterable(str(path), iterableargs={"format": "delta"}) as source:
            assert source.totals() == 3

    def test_schema_mismatch_on_append(self, tmp_path):
        from deltalake.exceptions import SchemaMismatchError

        path = tmp_path / "delta_schema"
        with open_iterable(str(path), mode="w", iterableargs={"format": "delta", "write_mode": "overwrite"}) as dest:
            dest.write_bulk(RECORDS)
        with pytest.raises(SchemaMismatchError, match="extra"):
            with open_iterable(str(path), mode="w", iterableargs={"format": "delta", "write_mode": "append"}) as dest:
                dest.write_bulk([{"id": 4, "extra": "nope"}])

    def test_invalid_write_mode(self, tmp_path):
        path = tmp_path / "delta_bad_mode"
        with pytest.raises(ValueError, match="write_mode"):
            open_iterable(str(path), mode="w", iterableargs={"format": "delta", "write_mode": "merge"})

    def test_list_tables_single_directory(self, tmp_path):
        path = tmp_path / "delta_list"
        with open_iterable(str(path), mode="w", iterableargs={"format": "delta", "write_mode": "overwrite"}) as dest:
            dest.write_bulk(RECORDS[:1])
        with open_iterable(str(path), iterableargs={"format": "delta"}) as source:
            assert source.list_tables() is None

    def test_missing_dependency(self, monkeypatch):
        import iterable.datatypes.delta as mod

        monkeypatch.setattr(mod, "HAS_DELTALAKE", False)
        with pytest.raises(ImportError, match="deltalake"):
            mod.DeltaIterable(filename="/tmp/delta", mode="r")


@pytest.mark.skipif(
    not (_has("pyiceberg") and _has("sqlalchemy")),
    reason="pyiceberg/sqlalchemy not installed",
)
class TestIcebergWrites:
    def test_round_trip(self, tmp_path):
        warehouse, catalog = _iceberg_catalog(tmp_path)
        with open_iterable(
            str(warehouse),
            mode="w",
            iterableargs={
                "format": "iceberg",
                "catalog_name": "default",
                "table_name": "demo.people",
                "catalog": catalog,
                "create_table": True,
            },
        ) as dest:
            assert dest.id() == "iceberg"
            dest.write_bulk(RECORDS)
        with open_iterable(
            str(warehouse),
            iterableargs={
                "format": "iceberg",
                "catalog_name": "default",
                "table_name": "demo.people",
                "catalog": catalog,
            },
        ) as source:
            assert source.totals() == 3
            assert [r["name"] for r in source] == ["Alice", "Bob", "Carol"]

    def test_append_and_list_tables(self, tmp_path):
        warehouse, catalog = _iceberg_catalog(tmp_path)
        args = {
            "format": "iceberg",
            "catalog_name": "default",
            "table_name": "demo.people",
            "catalog": catalog,
            "create_table": True,
        }
        with open_iterable(str(warehouse), mode="w", iterableargs=args) as dest:
            dest.write_bulk(RECORDS[:2])
        with open_iterable(
            str(warehouse),
            mode="w",
            iterableargs={
                "format": "iceberg",
                "catalog_name": "default",
                "table_name": "demo.people",
                "catalog": catalog,
            },
        ) as dest:
            dest.write_bulk(RECORDS[2:])
        with open_iterable(
            str(warehouse),
            iterableargs={
                "format": "iceberg",
                "catalog_name": "default",
                "table_name": "demo.people",
                "catalog": catalog,
            },
        ) as source:
            assert source.totals() == 3
            tables = source.list_tables()
            source.reset()
            names = sorted(r["name"] for r in source)
        assert names == ["Alice", "Bob", "Carol"]
        assert tables is not None
        assert any("people" in str(t) for t in tables)

    def test_write_requires_create_table(self, tmp_path):
        from iterable.exceptions import ReadError

        warehouse, catalog = _iceberg_catalog(tmp_path)
        with pytest.raises(ReadError, match="create_table"):
            open_iterable(
                str(warehouse),
                mode="w",
                iterableargs={
                    "format": "iceberg",
                    "catalog_name": "default",
                    "table_name": "demo.missing",
                    "catalog": catalog,
                },
            )

    def test_missing_table_name(self, tmp_path):
        from iterable.exceptions import ReadError

        warehouse, catalog = _iceberg_catalog(tmp_path)
        with pytest.raises(ReadError, match="table_name"):
            open_iterable(
                str(warehouse),
                iterableargs={"format": "iceberg", "catalog_name": "default", "catalog": catalog},
            )

    def test_stream_rejected(self):
        import io

        from iterable.datatypes.iceberg import IcebergIterable
        from iterable.exceptions import ReadError

        with pytest.raises(ReadError, match="not a stream"):
            IcebergIterable(stream=io.BytesIO(b""), mode="r", table_name="demo.t")

    def test_missing_dependency(self, monkeypatch):
        import iterable.datatypes.iceberg as mod

        monkeypatch.setattr(mod, "HAS_PYICEBERG", False)
        with pytest.raises(ImportError, match="pyiceberg"):
            mod.IcebergIterable(filename="/tmp/w", mode="r", table_name="demo.t")


class TestHudiWriteDeferred:
    def test_descriptor_not_writable(self):
        assert get_descriptor("hudi").writable is False

    def test_write_raises_without_optional_import(self, monkeypatch):
        import iterable.datatypes.hudi as mod
        from iterable.exceptions import WriteNotSupportedError

        monkeypatch.setattr(mod, "HAS_PYHUDI", True)
        monkeypatch.setattr(mod, "HAS_HUDI", False)
        with pytest.raises(WriteNotSupportedError, match="deferred"):
            mod.HudiIterable(filename="/tmp/hudi", mode="w")

    def test_write_methods_raise(self, monkeypatch):
        import iterable.datatypes.hudi as mod
        from iterable.exceptions import WriteNotSupportedError

        monkeypatch.setattr(mod, "HAS_PYHUDI", True)
        monkeypatch.setattr(mod, "HAS_HUDI", False)

        # Bypass reset write-mode check by constructing in read mode then switching
        it = object.__new__(mod.HudiIterable)
        with pytest.raises(WriteNotSupportedError, match="deferred"):
            mod.HudiIterable.write(it, {"id": 1})
        with pytest.raises(WriteNotSupportedError, match="deferred"):
            mod.HudiIterable.write_bulk(it, [{"id": 1}])
