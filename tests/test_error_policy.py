"""Tests for the centralized error-policy contract.

Covers the "No Silent Empty Reads" requirement (malformed non-empty input
must not read as a valid zero-row dataset under the default
``on_error="raise"`` policy) and the ``on_error="skip"|"warn"`` behavior for
formats migrated to the centralized ``_handle_error()`` mechanism (SMILE,
VCF/vCard, Parquet), plus typed errors at the ``open_iterable()`` boundary.
"""

import importlib
import io
import json
import sys
import types
import warnings

import pytest

from iterable.exceptions import FormatParseError, IterableDataError, ReadError, WriteError
from iterable.helpers.detect import open_iterable


@pytest.fixture
def smile_module():
    """Provide a SMILE iterable backed by a stub codec when the real one is absent.

    The real ``smile-json`` package is not installable from PyPI, so these
    tests substitute a minimal JSON-backed stand-in that mimics its
    ``loads``/``dumps`` API (raising on undecodable input) and reload the
    datatype module against it.
    """
    import iterable.datatypes.smile as smile_datatype

    if smile_datatype.HAS_SMILE:
        yield smile_datatype
        return

    stub = types.ModuleType("smile")
    stub.loads = lambda content: json.loads(content.decode("utf-8"))
    stub.dumps = lambda record: json.dumps(record).encode("utf-8")
    sys.modules["smile"] = stub
    try:
        importlib.reload(smile_datatype)
        yield smile_datatype
    finally:
        del sys.modules["smile"]
        importlib.reload(smile_datatype)


class TestSMILEErrorPolicy:
    @pytest.fixture
    def malformed_smile(self, tmp_path):
        path = tmp_path / "broken.smile"
        path.write_bytes(b"\x00\x01\x02 definitely not smile data \xff\xfe")
        return str(path)

    def test_malformed_raises_by_default(self, smile_module, malformed_smile):
        with pytest.raises(FormatParseError) as excinfo:
            smile_module.SMILEIterable(filename=malformed_smile)
        assert excinfo.value.format_id == "smile"
        assert excinfo.value.filename is not None

    def test_malformed_skip_yields_zero_rows(self, smile_module, malformed_smile):
        with smile_module.SMILEIterable(filename=malformed_smile, options={"on_error": "skip"}) as source:
            assert list(source) == []

    def test_malformed_warn_yields_zero_rows_with_warning(self, smile_module, malformed_smile):
        with pytest.warns(UserWarning, match="Parse error"):
            with smile_module.SMILEIterable(filename=malformed_smile, options={"on_error": "warn"}) as source:
                assert list(source) == []

    def test_empty_file_reads_empty_without_error(self, smile_module, tmp_path):
        path = tmp_path / "empty.smile"
        path.write_bytes(b"")
        with smile_module.SMILEIterable(filename=str(path)) as source:
            assert list(source) == []

    def test_valid_content_still_reads(self, smile_module, tmp_path):
        path = tmp_path / "ok.smile"
        path.write_bytes(smile_module.smile.dumps([{"a": 1}, {"a": 2}]))
        with smile_module.SMILEIterable(filename=str(path)) as source:
            rows = list(source)
        assert rows == [{"a": 1}, {"a": 2}]


class TestVCFErrorPolicy:
    @pytest.fixture(autouse=True)
    def _require_vobject(self):
        pytest.importorskip("vobject", reason="VCF support requires 'vobject'")

    @pytest.fixture
    def malformed_vcf(self, tmp_path):
        path = tmp_path / "broken.vcf"
        # Non-empty content with no parseable key:value structure at all.
        path.write_text("complete garbage without any colon separated lines\nat all\n")
        return str(path)

    @pytest.fixture
    def mixed_vcf(self, tmp_path):
        path = tmp_path / "mixed.vcf"
        path.write_text(
            "BEGIN:VCARD\nVERSION:3.0\nFN:Alice\nEND:VCARD\n"
            "BEGIN:VCARD\ngarbage without structure\nEND:VCARD\n"
            "BEGIN:VCARD\nVERSION:3.0\nFN:Bob\nEND:VCARD\n"
        )
        return str(path)

    def test_malformed_raises_by_default(self, malformed_vcf):
        with pytest.raises(FormatParseError) as excinfo:
            open_iterable(malformed_vcf)
        assert excinfo.value.format_id == "vcf"

    def test_malformed_skip_yields_zero_rows(self, malformed_vcf):
        with open_iterable(malformed_vcf, iterableargs={"on_error": "skip"}) as source:
            assert list(source) == []

    def test_skip_keeps_valid_entries(self, mixed_vcf):
        with open_iterable(mixed_vcf, iterableargs={"on_error": "skip"}) as source:
            rows = list(source)
        names = [r.get("fn") for r in rows if r.get("fn")]
        assert "Alice" in names
        assert "Bob" in names

    def test_valid_vcf_still_reads(self, tmp_path):
        path = tmp_path / "ok.vcf"
        path.write_text("BEGIN:VCARD\nVERSION:3.0\nFN:Carol\nEND:VCARD\n")
        with open_iterable(str(path)) as source:
            rows = list(source)
        assert len(rows) == 1
        assert rows[0]["fn"] == "Carol"


class TestParquetErrorPolicy:
    @pytest.fixture(autouse=True)
    def _require_pyarrow(self):
        pytest.importorskip("pyarrow", reason="Parquet support requires 'pyarrow'")

    def test_malformed_parquet_raises_typed_error(self, tmp_path):
        path = tmp_path / "broken.parquet"
        path.write_bytes(b"PAR1 this is not a real parquet file PAR1")
        with pytest.raises(IterableDataError):
            open_iterable(str(path))

    def test_write_alignment_failure_surfaces(self, tmp_path):
        from iterable.datatypes.parquet import ParquetIterable

        path = tmp_path / "out.parquet"
        it = ParquetIterable(filename=str(path), mode="w")
        try:
            it.write_bulk([{"a": 1, "b": "x"}])
            it.flush()
            # Records with a type the established schema cannot represent
            # must raise WriteError, not buffer silently.
            with pytest.raises(WriteError, match="aligned to the existing Parquet schema"):
                it.write_bulk([{"a": {"nested": "dict"}, "b": object()}])
        finally:
            try:
                it.close()
            except Exception:
                pass


class TestOpenIterableTypedErrors:
    def test_stream_detection_fallback_warns(self):
        stream = io.BytesIO(b"\x00\x01\x02\x03 unrecognizable binary content \xff")
        with pytest.warns(UserWarning, match="assuming CSV"):
            source = open_iterable(stream)
        source.close()

    def test_explicit_stream_format_does_not_warn(self):
        stream = io.StringIO("a,b\n1,2\n")
        with warnings.catch_warnings():
            warnings.simplefilter("error", UserWarning)
            source = open_iterable(stream, iterableargs={"format": "csv"})
        assert source.read() == {"a": "1", "b": "2"}
        source.close()

    def test_read_error_is_iterabledataerror(self):
        assert issubclass(ReadError, IterableDataError)
