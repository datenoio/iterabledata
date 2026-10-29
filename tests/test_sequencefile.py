"""Hadoop SequenceFile round trips, header layout and malformed input."""

from __future__ import annotations

import gzip
import struct

import pytest

from iterable import open_iterable
from iterable.datatypes.sequencefile import SequenceFileIterable
from iterable.exceptions import FormatParseError

TEXT = "org.apache.hadoop.io.Text"
SYNC = bytes(range(16))
SYNC_ESCAPE = struct.pack(">i", -1)

ROWS = [
    {"key": "k1", "value": "plain text"},
    {"key": "k2", "value": {"id": 2, "name": "naïve 日本", "tags": ["a", "b"]}},
    {"key": "k3", "value": [1, 2.5, None, True]},
    {"key": "k4", "value": {"nested": {"deep": {"x": 1}}}},
]


def _text(value: str | bytes) -> bytes:
    """Serialize a short value as Hadoop Text (single-byte vint length)."""
    data = value.encode("utf-8") if isinstance(value, str) else value
    assert len(data) < 128
    return bytes([len(data)]) + data


def _record(key: bytes, value: bytes) -> bytes:
    return struct.pack(">ii", len(key) + len(value), len(key)) + key + value


def _hadoop_header(key_class=TEXT, value_class=TEXT, *, version=6, flags=b"\x00\x00", metadata=()) -> bytes:
    """Build a header the way Hadoop's uncompressed writer lays it out."""
    header = b"SEQ" + bytes([version]) + _text(key_class) + _text(value_class) + flags
    if version >= 6:
        header += struct.pack(">i", len(metadata)) + b"".join(_text(k) + _text(v) for k, v in metadata)
    return header + SYNC


def _read_bytes(tmp_path, raw: bytes, **kwargs) -> list[dict]:
    path = tmp_path / "input.seq"
    path.write_bytes(raw)
    with SequenceFileIterable(str(path), **kwargs) as source:
        return list(source)


class TestSequenceFileRoundTrip:
    @pytest.mark.parametrize("suffix", [".seq", ".seq.gz", ".seq.bz2"])
    def test_open_iterable_round_trip(self, tmp_path, suffix):
        path = tmp_path / f"data{suffix}"
        with open_iterable(str(path), mode="w") as dest:
            for row in ROWS:
                dest.write(row)
        with open_iterable(str(path)) as source:
            assert list(source) == ROWS

    def test_write_bulk_round_trip_with_custom_field_names(self, tmp_path):
        path = tmp_path / "data.seq"
        rows = [{"id": row["key"], "doc": row["value"]} for row in ROWS]
        options = {"key_name": "id", "value_name": "doc"}
        with SequenceFileIterable(str(path), mode="w", options=dict(options)) as dest:
            dest.write_bulk(rows)
        with SequenceFileIterable(str(path), options=dict(options)) as source:
            assert source.read_bulk(10) == rows

    def test_record_without_key_and_value_is_stored_as_json_value(self, tmp_path):
        path = tmp_path / "data.seq"
        record = {"a": 1, "b": "two", "c": [3]}
        with SequenceFileIterable(str(path), mode="w") as dest:
            dest.write(record)
        with SequenceFileIterable(str(path)) as source:
            (row,) = list(source)
        assert row["value"] == record

    def test_reset_rereads_from_first_record(self, tmp_path):
        path = tmp_path / "data.seq"
        with SequenceFileIterable(str(path), mode="w") as dest:
            dest.write_bulk(ROWS)
        with SequenceFileIterable(str(path)) as source:
            assert source.read() == ROWS[0]
            source.reset()
            assert list(source) == ROWS

    def test_file_without_records_is_a_valid_header(self, tmp_path):
        path = tmp_path / "empty.seq"
        with SequenceFileIterable(str(path), mode="w"):
            pass
        assert path.read_bytes().startswith(b"SEQ\x06")
        with SequenceFileIterable(str(path)) as source:
            assert list(source) == []

    def test_sync_escapes_between_records_round_trip(self, tmp_path):
        path = tmp_path / "data.seq"
        rows = [{"key": f"k{i}", "value": {"n": i, "pad": "x" * 20}} for i in range(50)]
        with SequenceFileIterable(str(path), mode="w") as dest:
            dest.sync_interval = 64
            sync_marker = dest.sync_marker
            dest.write_bulk(rows)
        assert path.read_bytes().count(SYNC_ESCAPE + sync_marker) > 10
        with SequenceFileIterable(str(path)) as source:
            assert list(source) == rows

    def test_codec_writer_reset_keeps_a_single_header(self, tmp_path):
        # Pipelines reset their destination before writing; a codec stream cannot rewind.
        path = tmp_path / "data.seq.gz"
        with open_iterable(str(path), mode="w") as dest:
            dest.reset()
            dest.write_bulk(ROWS)
        assert gzip.decompress(path.read_bytes()).count(b"SEQ\x06") == 1
        with open_iterable(str(path)) as source:
            assert list(source) == ROWS


class TestSequenceFileHadoopLayout:
    def test_writer_emits_hadoop_version_6_header_and_records(self, tmp_path):
        path = tmp_path / "data.seq"
        with SequenceFileIterable(str(path), mode="w") as dest:
            dest.write({"key": "k1", "value": "v1"})
        raw = path.read_bytes()

        header = b"SEQ\x06" + _text(TEXT) + _text(TEXT) + b"\x00\x00" + struct.pack(">i", 0)
        assert raw.startswith(header)
        body = raw[len(header) + 16 :]
        assert body == _record(_text("k1"), _text("v1"))

    @pytest.mark.parametrize(
        ("key_class", "key", "expected"),
        [
            ("org.apache.hadoop.io.LongWritable", struct.pack(">q", -5), -5),
            ("org.apache.hadoop.io.IntWritable", struct.pack(">i", 7), 7),
            ("org.apache.hadoop.io.NullWritable", b"", None),
            ("org.apache.hadoop.io.BytesWritable", struct.pack(">i", 3) + b"abc", "abc"),
            ("org.apache.hadoop.io.BytesWritable", struct.pack(">i", 2) + b"\xff\x00", "/wA="),
            (TEXT, _text("1.5"), 1.5),
            ("com.example.CustomWritable", b"raw", "raw"),
        ],
    )
    def test_reads_common_writable_classes(self, tmp_path, key_class, key, expected):
        raw = _hadoop_header(key_class) + _record(key, _text('{"a": 1}'))
        assert _read_bytes(tmp_path, raw) == [{"key": expected, "value": {"a": 1}}]

    @pytest.mark.parametrize("version", [4, 5, 6])
    def test_reads_supported_versions_with_metadata(self, tmp_path, version):
        raw = _hadoop_header(version=version, metadata=[("created-by", "test")])
        raw += _record(_text("k1"), _text("v1")) + _record(_text("k2"), _text("v2"))
        assert _read_bytes(tmp_path, raw) == [{"key": "k1", "value": "v1"}, {"key": "k2", "value": "v2"}]

    def test_reads_sync_escape_between_records(self, tmp_path):
        raw = _hadoop_header() + _record(_text("k1"), _text("v1")) + SYNC_ESCAPE + SYNC
        raw += _record(_text("k2"), _text("v2")) + SYNC_ESCAPE + SYNC
        assert _read_bytes(tmp_path, raw) == [{"key": "k1", "value": "v1"}, {"key": "k2", "value": "v2"}]

    def test_reads_multi_byte_vint_lengths(self, tmp_path):
        value = "x" * 300
        rows = [{"key": "k1", "value": value}]
        path = tmp_path / "data.seq"
        with SequenceFileIterable(str(path), mode="w") as dest:
            dest.write_bulk(rows)
        # Hadoop vint for 300: marker -114 (two value bytes), then 0x012c
        assert b"\x8e\x01\x2c" + value.encode() in path.read_bytes()
        with SequenceFileIterable(str(path)) as source:
            assert list(source) == rows


class TestSequenceFileHeaderlessLayout:
    def test_reads_records_written_by_earlier_releases(self, tmp_path):
        records = [(b"k1", b'{"id": 1}'), (b"k2", b"text")]
        raw = b"".join(struct.pack(">II", len(k), len(v)) + k + v for k, v in records)
        assert _read_bytes(tmp_path, raw) == [{"key": "k1", "value": {"id": 1}}, {"key": "k2", "value": "text"}]

    def test_empty_file_reads_no_rows(self, tmp_path):
        assert _read_bytes(tmp_path, b"") == []


class TestSequenceFileMalformedInput:
    @pytest.mark.parametrize(
        ("raw", "message"),
        [
            (b"SEQ\x06" + _text(TEXT)[:5], "Truncated SequenceFile key class name"),
            (b"SEQ\x03" + _text(TEXT) + _text(TEXT), "Unsupported SequenceFile version 3"),
            (b"SEQ\x07" + _text(TEXT) + _text(TEXT), "Unsupported SequenceFile version 7"),
            (_hadoop_header(flags=b"\x01\x00"), "Record-compressed SequenceFiles are not supported"),
            (_hadoop_header(flags=b"\x01\x01"), "Block-compressed SequenceFiles are not supported"),
            (_hadoop_header()[:-4], "Truncated SequenceFile sync marker"),
            (
                _hadoop_header() + SYNC_ESCAPE + bytes(16) + _record(_text("k1"), _text("v1")),
                "sync marker does not match",
            ),
            (_hadoop_header() + _record(_text("k1"), _text("value"))[:-2], "Truncated SequenceFile value"),
            (_hadoop_header() + struct.pack(">ii", 2, 5) + b"k1", "Invalid SequenceFile record lengths"),
            (_hadoop_header() + _record(b"\x05k1", _text("v1")), "Text length 5 does not match 2"),
            (struct.pack(">II", 2, 10) + b"k1short", "Truncated SequenceFile value"),
        ],
    )
    def test_raises_format_parse_error(self, tmp_path, raw, message):
        with pytest.raises(FormatParseError, match=message):
            _read_bytes(tmp_path, raw)

    def test_truncated_record_keeps_rows_read_before_it(self, tmp_path):
        path = tmp_path / "input.seq"
        path.write_bytes(_hadoop_header() + _record(_text("k1"), _text("v1")) + b"\x00\x00")
        with SequenceFileIterable(str(path)) as source:
            assert source.read() == {"key": "k1", "value": "v1"}
            with pytest.raises(FormatParseError, match="Truncated SequenceFile record length") as excinfo:
                source.read()
        assert excinfo.value.row_number == 2
