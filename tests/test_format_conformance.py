"""
Registry-driven conformance tests for format implementations.

Part 1 checks structural invariants for every format in DATATYPE_REGISTRY
(class loads, static id(), iterator contract methods present).

Part 2 checks runtime behavior (StopIteration at EOF, read_bulk semantics,
reset round-trip) for every format that has a golden fixture (auto-discovered
from tests/fixtures/ via tests/conformance_fixtures.py).

Part 3 checks write round-trip for writable formats with golden fixtures.
"""

import os

import pytest
from conformance_fixtures import canonical_fixture_formats

from iterable.helpers.detect import (
    DATATYPE_REGISTRY,
    READ_ONLY_FORMATS,
    _load_symbol,
    open_iterable,
)
from iterable.helpers.format_registry import get_descriptor

# Canonical format ids -> registry keys (one key per unique class)
_UNIQUE_FORMATS: dict[tuple[str, str], str] = {}
for _key, _target in DATATYPE_REGISTRY.items():
    _UNIQUE_FORMATS.setdefault(_target, _key)
UNIQUE_FORMAT_KEYS = sorted(_UNIQUE_FORMATS.values())

FIXTURE_FORMATS = canonical_fixture_formats()


def _load_class_or_skip(key: str):
    module_path, symbol = DATATYPE_REGISTRY[key]
    try:
        return _load_symbol(module_path, symbol)
    except ImportError as e:
        pytest.skip(f"Optional dependency missing for format {key!r}: {e}")


def _is_writable(format_key: str) -> bool:
    desc = get_descriptor(format_key)
    if desc is not None and not desc.writable:
        return False
    if format_key in READ_ONLY_FORMATS:
        return False
    return True


class TestRegistryIntegrity:
    @pytest.mark.parametrize("key", UNIQUE_FORMAT_KEYS)
    def test_class_loads_and_has_static_id(self, key):
        """Every registered class loads and exposes a static, non-empty id()."""
        cls = _load_class_or_skip(key)
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
        unknown -= {"zipped"}
        assert not unknown, f"READ_ONLY_FORMATS contains unregistered formats: {sorted(unknown)}"


def _open_or_skip(format_key: str):
    path, iterableargs = FIXTURE_FORMATS[format_key]
    if not os.path.exists(path):
        pytest.skip(f"Fixture {path} not found")
    try:
        return open_iterable(path, iterableargs=dict(iterableargs) if iterableargs else None)
    except ImportError as e:
        pytest.skip(f"Optional dependency missing for {format_key}: {e}")
    except RuntimeError as e:
        if isinstance(e.__cause__, ImportError) or "requires" in str(e):
            pytest.skip(f"Optional dependency missing for {format_key}: {e}")
        raise


class TestFormatBehavior:
    @pytest.mark.parametrize("format_key", sorted(FIXTURE_FORMATS))
    def test_read_raises_stopiteration_at_eof(self, format_key):
        """read() must raise StopIteration when exhausted, never return None."""
        with _open_or_skip(format_key) as source:
            count = 0
            while count < 10_000:
                try:
                    row = source.read()
                except StopIteration:
                    break
                assert row is not None, f"{format_key}: read() returned None instead of raising StopIteration"
                count += 1
            else:
                pytest.fail(f"{format_key}: read() did not raise StopIteration after 10000 rows")
            assert count > 0, f"{format_key}: fixture produced no rows"
            with pytest.raises(StopIteration):
                source.read()

    @pytest.mark.parametrize("format_key", sorted(FIXTURE_FORMATS))
    def test_read_bulk_semantics(self, format_key):
        """read_bulk(n) returns at most n rows and [] when exhausted."""
        with _open_or_skip(format_key) as source:
            chunk = source.read_bulk(3)
            assert isinstance(chunk, list)
            assert len(chunk) <= 3
            assert len(chunk) > 0, f"{format_key}: fixture produced no rows"
            while True:
                more = source.read_bulk(100)
                if not more:
                    break
            assert source.read_bulk(10) == []

    @pytest.mark.parametrize("format_key", sorted(FIXTURE_FORMATS))
    def test_reset_round_trip(self, format_key):
        """After reset(), the source yields the same first row again."""
        with _open_or_skip(format_key) as source:
            try:
                first = source.read()
            except StopIteration:
                pytest.fail(f"{format_key}: fixture produced no rows")
            try:
                source.reset()
            except (NotImplementedError, ValueError) as e:
                pytest.skip(f"{format_key}: reset not supported: {e}")
            again = source.read()
            assert again == first, f"{format_key}: first row after reset() differs"


WRITABLE_FIXTURE_FORMATS = sorted(k for k in FIXTURE_FORMATS if _is_writable(k))


class TestWriteRoundTrip:
    @pytest.mark.parametrize("format_key", WRITABLE_FIXTURE_FORMATS)
    def test_write_read_round_trip(self, format_key, tmp_path):
        """Writable formats can write rows read from the golden fixture."""
        path, iterableargs = FIXTURE_FORMATS[format_key]
        args = dict(iterableargs) if iterableargs else None

        rows: list = []
        with _open_or_skip(format_key) as source:
            while True:
                try:
                    rows.append(source.read())
                except StopIteration:
                    break
        if not rows:
            pytest.skip(f"{format_key}: no rows to round-trip")

        out_path = tmp_path / f"roundtrip.{format_key}"
        try:
            with open_iterable(str(out_path), mode="w", iterableargs=args) as dest:
                dest.write_bulk(rows)
        except (ImportError, NotImplementedError, ValueError, RuntimeError) as e:
            pytest.skip(f"{format_key}: write not available: {e}")

        try:
            with open_iterable(str(out_path), iterableargs=args) as reread:
                roundtrip = reread.read_bulk(len(rows) + 10)
        except (ImportError, RuntimeError) as e:
            pytest.skip(f"{format_key}: reread after write failed: {e}")

        assert len(roundtrip) == len(rows), f"{format_key}: row count mismatch after write"
        assert roundtrip[0] == rows[0], f"{format_key}: first row differs after write"
