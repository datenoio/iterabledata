"""convert()/bulk_convert() parameter parity: codec arguments and per-file selection options."""

import gzip
import inspect
import json
from unittest import mock

import pytest

from iterable.convert import bulk_convert, convert
from iterable.convert import core as convert_core

# Byte 8 of a gzip member header (XFL): 2 = maximum compression, 4 = fastest.
GZIP_XFL_OFFSET = 8
XFL_BEST, XFL_FAST = 2, 4


def _write_jsonl(path, rows):
    path.write_text("".join(json.dumps(r) + "\n" for r in rows), encoding="utf-8")


def _read_jsonl(path):
    opener = gzip.open if str(path).endswith(".gz") else open
    with opener(path, "rt", encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def _rows(n=3000):
    return [{"id": i, "name": f"name-{i * 7919 % 10007}", "group": i % 13} for i in range(n)]


@pytest.fixture
def source_dir(tmp_path):
    src = tmp_path / "in"
    src.mkdir()
    for part in range(2):
        _write_jsonl(src / f"part{part}.jsonl", _rows(500))
    return src


def test_tocodecargs_sets_output_compression_level(tmp_path):
    src = tmp_path / "rows.jsonl"
    _write_jsonl(src, _rows())
    fast, best = tmp_path / "fast.jsonl.gz", tmp_path / "best.jsonl.gz"

    convert(str(src), str(fast), tocodecargs={"compression_level": 1})
    convert(str(src), str(best), tocodecargs={"compression_level": 9})

    assert fast.read_bytes()[GZIP_XFL_OFFSET] == XFL_FAST
    assert best.read_bytes()[GZIP_XFL_OFFSET] == XFL_BEST
    assert best.stat().st_size < fast.stat().st_size
    assert _read_jsonl(fast) == _read_jsonl(best) == _rows()


def test_codec_args_reach_reader_and_writer(tmp_path):
    src = tmp_path / "rows.jsonl.gz"
    with gzip.open(src, "wt", encoding="utf-8") as f:
        f.writelines(json.dumps(r) + "\n" for r in _rows(10))
    out = tmp_path / "rows.csv.gz"
    reader_args, writer_args = {"profile": "fast"}, {"compression_level": 1}

    with mock.patch.object(convert_core, "open_iterable", wraps=convert_core.open_iterable) as opened:
        result = convert(str(src), str(out), codecargs=reader_args, tocodecargs=writer_args)

    by_mode = {c.kwargs["mode"]: c.kwargs["codecargs"] for c in opened.call_args_list}
    assert by_mode == {"r": reader_args, "w": writer_args}
    assert result.rows_out == 10


def test_codec_args_ignored_for_uncompressed_files(tmp_path):
    src = tmp_path / "rows.jsonl"
    _write_jsonl(src, _rows(5))
    out = tmp_path / "rows.csv"
    result = convert(str(src), str(out), codecargs={"compression_level": 1}, tocodecargs={"compression_level": 1})
    assert result.rows_out == 5


@pytest.mark.parametrize("parallel", [False, True])
def test_bulk_convert_forwards_tocodecargs(source_dir, tmp_path, parallel):
    dest = tmp_path / "out"
    result = bulk_convert(
        str(source_dir / "*.jsonl"),
        str(dest),
        to_ext="jsonl.gz",
        tocodecargs={"compression_level": 9},
        parallel=parallel,
    )
    assert result.successful_files == 2
    outputs = sorted(dest.glob("*.jsonl.gz"))
    assert [p.read_bytes()[GZIP_XFL_OFFSET] for p in outputs] == [XFL_BEST, XFL_BEST]


@pytest.mark.parametrize("parallel", [False, True])
def test_bulk_convert_applies_selection(source_dir, tmp_path, parallel):
    dest = tmp_path / "out"
    result = bulk_convert(
        str(source_dir / "*.jsonl"),
        str(dest),
        to_ext="jsonl",
        selection={"columns": ["id"], "row_range": [0, 3]},
        parallel=parallel,
    )
    assert result.successful_files == 2
    for output in sorted(dest.glob("*.jsonl")):
        assert _read_jsonl(output) == [{"id": 0}, {"id": 1}, {"id": 2}]


def test_bulk_convert_selection_from_parquet(tmp_path):
    pytest.importorskip("pyarrow")
    from iterable.helpers.detect import open_iterable

    src = tmp_path / "in"
    src.mkdir()
    for part in range(2):
        with open_iterable(str(src / f"part{part}.parquet"), mode="w") as dest:
            dest.write_bulk(_rows(20))

    result = bulk_convert(str(src / "*.parquet"), str(tmp_path / "out"), to_ext="jsonl", selection={"columns": ["id"]})

    assert result.successful_files == 2
    for output in sorted((tmp_path / "out").glob("*.jsonl")):
        assert _read_jsonl(output) == [{"id": i} for i in range(20)]


def test_bulk_convert_forwards_strict_native(source_dir, tmp_path):
    # JSON Lines has no native batch path, so strict_native fails every file.
    result = bulk_convert(
        str(source_dir / "*.jsonl"), str(tmp_path / "out"), to_ext="jsonl", use_native_batch=True, strict_native=True
    )
    assert result.failed_files == 2
    assert all("Native batch conversion is unsupported" in str(e) for e in result.errors)


def test_bulk_convert_accepts_every_convert_parameter():
    per_file = set(inspect.signature(convert).parameters) - {"fromfile", "tofile"}
    assert per_file <= set(inspect.signature(bulk_convert).parameters)
