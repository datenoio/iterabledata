"""Unit tests for the extracted entry-point helpers.

Covers the staged helpers behind ``open_iterable()`` (detection, input
normalization, engine validation) and ``convert()``/``bulk_convert()``
(schema scan, output args, atomic targets, per-file aggregation).
"""

import io
import os
import pathlib

import pytest

from iterable.convert.core import (
    _build_output_args,
    _BulkMetrics,
    _close_quietly,
    _ConvertMetrics,
    _ensure_dest_dir,
    _generate_output_filename,
    _prepare_atomic_target,
    _progress_estimates,
    _record_file_result,
    _resolve_workers,
    _scan_schema_keys,
    _validate_convert_args,
)
from iterable.helpers.open_iterable import (
    _apply_explicit_format,
    _get_cloud_backend,
    _is_cloud_storage_uri,
    _looks_like_stream,
    _normalize_open_inputs,
    _resolve_type_and_codec,
    _validate_engine_support,
)
from iterable.types import ConversionResult


class TestLooksLikeStream:
    def test_file_like_object_is_stream(self):
        assert _looks_like_stream(io.BytesIO(b"data")) is True
        assert _looks_like_stream(io.StringIO("data")) is True

    def test_str_bytes_path_are_not_streams(self):
        assert _looks_like_stream("file.csv") is False
        assert _looks_like_stream(b"file.csv") is False
        assert _looks_like_stream(pathlib.Path("file.csv")) is False
        assert _looks_like_stream(None) is False


class TestNormalizeOpenInputs:
    def test_options_merge_overrides_iterableargs(self):
        _, _, args = _normalize_open_inputs("f.csv", None, {"a": 1, "b": 2}, {"b": 3}, None)
        assert args == {"a": 1, "b": 3}

    def test_stream_passed_as_filename_is_swapped(self):
        stream = io.BytesIO(b"data")
        filename, out_stream, _ = _normalize_open_inputs(stream, None, None, None, None)
        assert filename is None
        assert out_stream is stream

    def test_format_injected_into_args(self):
        _, _, args = _normalize_open_inputs("f.dat", None, None, None, "csv")
        assert args["format"] == "csv"

    def test_pathlike_coerced_to_str(self):
        filename, _, _ = _normalize_open_inputs(pathlib.Path("dir") / "f.csv", None, None, None, None)
        assert filename == os.path.join("dir", "f.csv")

    def test_defaults(self):
        filename, stream, args = _normalize_open_inputs(None, None, None, None, None)
        assert filename is None
        assert stream is None
        assert args == {}


class TestResolveTypeAndCodec:
    def test_explicit_format_wins(self):
        result = {"detection_method": "explicit"}
        assert _resolve_type_and_codec("f.bin", result, {"format": "CSV"}) == ("csv", None)

    def test_simple_extension(self):
        assert _resolve_type_and_codec("data.csv", {}, {}) == ("csv", None)

    def test_extension_with_codec(self):
        filetype, codec = _resolve_type_and_codec("data.csv.gz", {}, {})
        assert filetype == "csv"
        assert codec == "gz"

    def test_double_extension_without_codec(self):
        filetype, codec = _resolve_type_and_codec("data.backup.csv", {}, {})
        assert filetype == "csv"
        assert codec is None

    def test_no_extension(self):
        assert _resolve_type_and_codec("data", {}, {}) == (None, None)


class TestValidateEngineSupport:
    def test_internal_engine_accepts_anything(self):
        _validate_engine_support("internal", "xlsx", "lzo")

    def test_duckdb_rejects_unsupported_type(self):
        with pytest.raises(ValueError, match="does not support file type"):
            _validate_engine_support("duckdb", "xlsx", None)

    def test_duckdb_rejects_unsupported_codec(self):
        with pytest.raises(ValueError, match="does not support compression codec"):
            _validate_engine_support("duckdb", "csv", "lzo")

    def test_duckdb_accepts_csv_gzip(self):
        _validate_engine_support("duckdb", "csv", "gz")


class TestApplyExplicitFormat:
    def test_known_format_populates_result(self):
        result = {"success": False, "datatype": None, "codec": None, "confidence": 0.0}
        _apply_explicit_format(result, {"format": "csv"})
        assert result["success"] is True
        assert result["datatype"] is not None
        assert result["confidence"] == 1.0

    def test_no_format_hint_is_noop(self):
        result = {"success": False, "datatype": None}
        _apply_explicit_format(result, {})
        assert result["success"] is False

    def test_explicit_format_overrides_existing_detection(self):
        from iterable.datatypes.csv import CSVIterable
        from iterable.datatypes.ducklake import DuckLakeIterable

        result = {
            "success": True,
            "datatype": CSVIterable,
            "codec": None,
            "confidence": 1.0,
            "detection_method": "filename",
        }
        _apply_explicit_format(result, {"format": "ducklake"})
        assert result["datatype"] is DuckLakeIterable
        assert result["detection_method"] == "explicit"


class TestCloudURIHelpers:
    def test_cloud_uri_detection(self):
        assert _is_cloud_storage_uri("s3://bucket/key.csv") is True
        assert _is_cloud_storage_uri("/local/path.csv") is False
        assert _is_cloud_storage_uri("") is False

    def test_cloud_backend_resolution(self):
        assert _get_cloud_backend("s3://bucket/key.csv") == "s3fs"
        assert _get_cloud_backend("/local/path.csv") is None


class TestValidateConvertArgs:
    def test_valid_args_pass(self):
        _validate_convert_args(100, 1000)
        _validate_convert_args(None, 1)

    def test_negative_scan_limit_rejected(self):
        with pytest.raises(ValueError, match="scan_limit"):
            _validate_convert_args(-1, 1000)

    def test_non_positive_batch_size_rejected(self):
        with pytest.raises(ValueError, match="batch_size"):
            _validate_convert_args(100, 0)


class TestPrepareAtomicTarget:
    def test_non_atomic_returns_target_unchanged(self):
        assert _prepare_atomic_target("out.csv", atomic=False) == ("out.csv", None)

    def test_atomic_returns_temp_path(self, tmp_path):
        target = str(tmp_path / "out.csv")
        actual, temp = _prepare_atomic_target(target, atomic=True)
        assert actual == temp == target + ".tmp"

    def test_atomic_removes_stale_temp_file(self, tmp_path):
        target = str(tmp_path / "out.csv")
        stale = target + ".tmp"
        with open(stale, "w") as f:
            f.write("stale")
        _prepare_atomic_target(target, atomic=True)
        assert not os.path.exists(stale)


class TestScanSchemaKeys:
    def test_nested_keys_collected(self):
        rows = [{"a": 1, "b": {"c": 2}}, {"a": 3, "d": 4}]
        keys = _scan_schema_keys(rows, scan_limit=None, is_flatten=False, silent=True)
        assert "a" in keys
        assert "b.c" in keys
        assert "d" in keys

    def test_flatten_mode_uses_flat_keys(self):
        rows = [{"a": 1, "b": {"c": 2}}]
        keys = _scan_schema_keys(rows, scan_limit=None, is_flatten=True, silent=True)
        # make_flat() stringifies nested values under the top-level key
        assert keys == {"a", "b"}

    def test_scan_limit_bounds_rows(self):
        rows = [{"a": 1}, {"b": 2}, {"c": 3}]
        keys = _scan_schema_keys(rows, scan_limit=1, is_flatten=False, silent=True)
        assert keys == {"a"}


class TestBuildOutputArgs:
    def test_flat_output_gets_keys(self):
        args = _build_output_args("out.csv", "out.csv", True, ["a", "b"], {})
        assert args["keys"] == ["a", "b"]

    def test_user_args_merged(self):
        args = _build_output_args("out.csv", "out.csv", True, ["a"], {"delimiter": ";"})
        assert args["delimiter"] == ";"

    def test_atomic_temp_target_carries_format(self):
        args = _build_output_args("out.parquet", "out.parquet.tmp", False, [], {})
        assert args["format"] == "parquet"

    def test_explicit_format_not_overridden(self):
        args = _build_output_args("out.parquet", "out.parquet.tmp", False, [], {"format": "jsonl"})
        assert args["format"] == "jsonl"


class TestProgressEstimates:
    def test_no_total_returns_nones(self):
        metrics = _ConvertMetrics(start_time=0.0, rows_read=10)
        assert _progress_estimates(metrics, None, 1.0) == (None, None)

    def test_percent_and_eta_computed(self):
        metrics = _ConvertMetrics(start_time=0.0, rows_read=50)
        percent, eta = _progress_estimates(metrics, 100, 5.0)
        assert percent == 50.0
        assert eta == pytest.approx(5.0)


class TestCloseQuietly:
    def test_none_is_noop(self):
        errors: list[Exception] = []
        _close_quietly(None, "msg", errors)
        assert errors == []

    def test_close_error_recorded_not_raised(self):
        class Broken:
            def close(self):
                raise RuntimeError("boom")

        errors: list[Exception] = []
        _close_quietly(Broken(), "msg", errors)
        assert len(errors) == 1
        assert isinstance(errors[0], RuntimeError)


class TestBulkHelpers:
    def test_resolve_workers_default_bounded(self):
        assert 1 <= _resolve_workers(None) <= 4

    def test_resolve_workers_explicit(self):
        assert _resolve_workers(7) == 7

    def test_ensure_dest_dir_creates_missing(self, tmp_path):
        dest = tmp_path / "sub" / "dir"
        _ensure_dest_dir(str(dest))
        assert dest.is_dir()

    def test_ensure_dest_dir_rejects_file(self, tmp_path):
        target = tmp_path / "afile"
        target.write_text("x")
        with pytest.raises(ValueError, match="not a directory"):
            _ensure_dest_dir(str(target))

    def test_generate_output_filename_with_pattern(self):
        out = _generate_output_filename("data/raw/input.csv", "out", pattern="{stem}.parquet")
        assert out == os.path.join("out", "input.parquet")

    def test_generate_output_filename_with_to_ext(self):
        out = _generate_output_filename("data/input.csv", "out", to_ext="parquet")
        assert out == os.path.join("out", "input.parquet")

    def test_record_file_result_success(self):
        metrics = _BulkMetrics(start_time=0.0, total_files=1)
        result = ConversionResult(
            rows_in=10, rows_out=10, elapsed_seconds=0.1, bytes_read=None, bytes_written=None, errors=[]
        )
        _record_file_result(metrics, "a.csv", "a.parquet", result, None)
        assert metrics.successful_files == 1
        assert metrics.failed_files == 0
        assert metrics.total_rows_in == 10
        assert len(metrics.file_results) == 1

    def test_record_file_result_failure(self):
        metrics = _BulkMetrics(start_time=0.0, total_files=1)
        err = RuntimeError("boom")
        _record_file_result(metrics, "a.csv", "a.parquet", None, err)
        assert metrics.failed_files == 1
        assert metrics.errors == [err]
        assert metrics.file_results[0].error is err
