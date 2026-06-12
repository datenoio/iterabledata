"""
Registry-driven conformance tests for format implementations.

Part 1 checks structural invariants for every format in DATATYPE_REGISTRY
(class loads, static id(), iterator contract methods present).

Part 2 checks runtime behavior (StopIteration at EOF, read_bulk semantics,
reset round-trip) for every format that has a shared fixture file.
"""

import os

import pytest

from iterable.helpers.detect import (
    DATATYPE_REGISTRY,
    READ_ONLY_FORMATS,
    _load_symbol,
    open_iterable,
)

# Canonical format ids -> registry keys (one key per unique class)
_UNIQUE_FORMATS: dict[tuple[str, str], str] = {}
for _key, _target in DATATYPE_REGISTRY.items():
    _UNIQUE_FORMATS.setdefault(_target, _key)
UNIQUE_FORMAT_KEYS = sorted(_UNIQUE_FORMATS.values())

# Fixture-backed formats: extension -> (fixture filename, iterableargs)
# Paths are relative to tests/ (cwd is tests/ via conftest)
FIXTURE_FILES = {
    "csv": ("fixtures/2cols6rows.csv", None),
    "parquet": ("fixtures/2cols6rows.parquet", None),
    "arrow": ("fixtures/2cols6rows.arrow", None),
    "orc": ("fixtures/2cols6rows.orc", None),
    "xlsx": ("fixtures/2cols6rows.xlsx", None),
    "xls": ("fixtures/2cols6rows.xls", None),
    "toml": ("fixtures/2cols6rows.toml", None),
    "ltsv": ("fixtures/2cols6rows.ltsv", None),
    "fwf": ("fixtures/2cols6rows.fwf", {"widths": [3, 10], "names": ["id", "name"]}),
    "geojson": ("fixtures/2cols6rows.geojson", None),
    "gml": ("fixtures/2cols6rows.gml", None),
    "kml": ("fixtures/2cols6rows.kml", None),
    "px": ("fixtures/2cols6rows.px", None),
    "dbf": ("fixtures/2cols6rows.dbf", None),
    "avro": ("fixtures/2cols6rows.avro", None),
    "jsonl": ("fixtures/2cols6rows.jsonl", None),
}


def _load_class_or_skip(key: str):
    module_path, symbol = DATATYPE_REGISTRY[key]
    try:
        return _load_symbol(module_path, symbol)
    except ImportError as e:
        pytest.skip(f"Optional dependency missing for format {key!r}: {e}")


class TestRegistryIntegrity:
    @pytest.mark.parametrize("key", UNIQUE_FORMAT_KEYS)
    def test_class_loads_and_has_static_id(self, key):
        """Every registered class loads and exposes a static, non-empty id()."""
        cls = _load_class_or_skip(key)
        # id() must be callable on the class itself (no instance required)
        format_id = cls.id()
        assert isinstance(format_id, str) and format_id, f"{cls.__name__}.id() must return a non-empty string"

    @pytest.mark.parametrize("key", UNIQUE_FORMAT_KEYS)
    def test_iterator_contract_methods_present(self, key):
        """Every registered class defines or inherits read/read_bulk/reset."""
        cls = _load_class_or_skip(key)
        for method in ("read", "read_bulk", "reset"):
            assert callable(getattr(cls, method, None)), f"{cls.__name__} missing {method}()"

    def test_read_only_formats_are_registered(self):
        """READ_ONLY_FORMATS must not reference unknown format keys."""
        unknown = {f for f in READ_ONLY_FORMATS if f not in DATATYPE_REGISTRY}
        # "zipped" is a wrapper class without its own registry entry
        unknown -= {"zipped"}
        assert not unknown, f"READ_ONLY_FORMATS contains unregistered formats: {sorted(unknown)}"


def _open_or_skip(ext: str):
    path, iterableargs = FIXTURE_FILES[ext]
    if not os.path.exists(path):
        pytest.skip(f"Fixture {path} not found")
    try:
        return open_iterable(path, iterableargs=dict(iterableargs) if iterableargs else None)
    except ImportError as e:
        pytest.skip(f"Optional dependency missing for {ext}: {e}")
    except RuntimeError as e:
        # open_iterable wraps constructor failures; skip when the underlying
        # cause is a missing optional dependency
        if isinstance(e.__cause__, ImportError) or "requires" in str(e):
            pytest.skip(f"Optional dependency missing for {ext}: {e}")
        raise


class TestFormatBehavior:
    @pytest.mark.parametrize("ext", sorted(FIXTURE_FILES))
    def test_read_raises_stopiteration_at_eof(self, ext):
        """read() must raise StopIteration when exhausted, never return None."""
        with _open_or_skip(ext) as source:
            count = 0
            while count < 10_000:
                try:
                    row = source.read()
                except StopIteration:
                    break
                assert row is not None, f"{ext}: read() returned None instead of raising StopIteration"
                count += 1
            else:
                pytest.fail(f"{ext}: read() did not raise StopIteration after 10000 rows")
            assert count > 0, f"{ext}: fixture produced no rows"
            # Subsequent reads must keep raising StopIteration
            with pytest.raises(StopIteration):
                source.read()

    @pytest.mark.parametrize("ext", sorted(FIXTURE_FILES))
    def test_read_bulk_semantics(self, ext):
        """read_bulk(n) returns at most n rows and [] when exhausted."""
        with _open_or_skip(ext) as source:
            chunk = source.read_bulk(3)
            assert isinstance(chunk, list)
            assert len(chunk) <= 3
            assert len(chunk) > 0, f"{ext}: fixture produced no rows"
            # Drain and verify empty list at EOF (no StopIteration)
            while True:
                more = source.read_bulk(100)
                if not more:
                    break
            assert source.read_bulk(10) == []

    @pytest.mark.parametrize("ext", sorted(FIXTURE_FILES))
    def test_reset_round_trip(self, ext):
        """After reset(), the source yields the same first row again."""
        with _open_or_skip(ext) as source:
            try:
                first = source.read()
            except StopIteration:
                pytest.fail(f"{ext}: fixture produced no rows")
            try:
                source.reset()
            except (NotImplementedError, ValueError) as e:
                pytest.skip(f"{ext}: reset not supported: {e}")
            again = source.read()
            assert again == first, f"{ext}: first row after reset() differs"
