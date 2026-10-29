"""CSV dialect options through open_iterable, TSV defaults, and codecs with an explicit format."""

import gzip
import io
import zipfile

import pytest

from iterable import open_iterable
from iterable.convert import convert


def _read(path, **iterableargs):
    with open_iterable(str(path), iterableargs=iterableargs or None) as it:
        return list(it)


def _write(path, rows, **iterableargs):
    with open_iterable(str(path), mode="w", iterableargs=iterableargs or None) as it:
        it.write_bulk(rows)


def test_read_delimiter_from_iterableargs(tmp_path):
    path = tmp_path / "a.csv"
    path.write_text("a;b\n1;2\n", encoding="utf-8")
    assert _read(path, delimiter=";") == [{"a": "1", "b": "2"}]


def test_read_quotechar_from_iterableargs(tmp_path):
    path = tmp_path / "q.csv"
    path.write_text("a,b\n'x,y',2\n", encoding="utf-8")
    assert _read(path, quotechar="'") == [{"a": "x,y", "b": "2"}]


def test_read_autodetect_from_iterableargs(tmp_path):
    path = tmp_path / "s.csv"
    path.write_text("a|b\n1|2\n", encoding="utf-8")
    assert _read(path, autodetect=True) == [{"a": "1", "b": "2"}]


def test_write_delimiter_from_iterableargs(tmp_path):
    path = tmp_path / "o.csv"
    _write(path, [{"a": 1, "b": 2}], delimiter="\t")
    assert path.read_text(encoding="utf-8").splitlines() == ["a\tb", "1\t2"]


def test_escapechar_and_doublequote_round_trip(tmp_path):
    path = tmp_path / "e.csv"
    dialect = {"escapechar": "\\", "doublequote": False}
    _write(path, [{"a": 'x"y'}], **dialect)
    assert path.read_text(encoding="utf-8").splitlines() == ["a", 'x\\"y']
    assert _read(path, **dialect) == [{"a": 'x"y'}]


def test_tsv_read_default(tmp_path):
    path = tmp_path / "t.tsv"
    path.write_text("a,b\tc\n1,2\t3\n", encoding="utf-8")
    assert _read(path) == [{"a,b": "1,2", "c": "3"}]


def test_tsv_explicit_delimiter_wins(tmp_path):
    path = tmp_path / "t.tsv"
    path.write_text("a;b\n1;2\n", encoding="utf-8")
    assert _read(path, delimiter=";") == [{"a": "1", "b": "2"}]


def test_tsv_write_default(tmp_path):
    path = tmp_path / "o.tsv"
    _write(path, [{"a": 1, "b": 2}])
    assert path.read_text(encoding="utf-8").splitlines() == ["a\tb", "1\t2"]


def test_compressed_tsv_write_and_read(tmp_path):
    path = tmp_path / "o.tsv.gz"
    _write(path, [{"a": "x,y", "b": 2}])
    with gzip.open(path, "rt", encoding="utf-8") as f:
        assert f.read().splitlines() == ["a\tb", "x,y\t2"]
    assert _read(path) == [{"a": "x,y", "b": "2"}]


def test_convert_honors_writer_delimiter(tmp_path):
    src = tmp_path / "in.jsonl"
    src.write_text('{"a": 1, "b": 2}\n', encoding="utf-8")
    out = tmp_path / "out.csv"
    convert(str(src), str(out), toiterableargs={"delimiter": "|"})
    assert out.read_text(encoding="utf-8").splitlines() == ["a|b", "1|2"]


def test_convert_csv_to_tsv(tmp_path):
    src = tmp_path / "in.csv"
    src.write_text("a,b\n1,2\n", encoding="utf-8")
    out = tmp_path / "out.tsv"
    convert(str(src), str(out))
    assert out.read_text(encoding="utf-8").splitlines() == ["a\tb", "1\t2"]


def test_explicit_format_keeps_gzip(tmp_path):
    path = tmp_path / "x.csv.gz"
    with gzip.open(path, "wt", encoding="utf-8") as f:
        f.write("a,b\n1,2\n")
    assert _read(path, format="csv") == [{"a": "1", "b": "2"}]


def test_explicit_format_on_zip_without_inner_format(tmp_path):
    path = tmp_path / "data.zip"
    with zipfile.ZipFile(path, "w") as z:
        z.writestr("data.jsonl", '{"a": 1}\n')
    assert _read(path, format="jsonl") == [{"a": 1}]


@pytest.mark.parametrize("hint", ["gz", "gzip"])
def test_explicit_codec_hint(tmp_path, hint):
    path = tmp_path / "data.bin"
    path.write_bytes(gzip.compress(b'{"a": 1}\n'))
    assert _read(path, format="jsonl", codec=hint) == [{"a": 1}]


def test_codec_hint_on_stream():
    stream = io.BytesIO(gzip.compress(b'{"a": 1}\n{"a": 2}\n'))
    with open_iterable(stream, iterableargs={"format": "jsonl", "codec": "gz"}) as it:
        assert list(it) == [{"a": 1}, {"a": 2}]


def test_unknown_codec_hint(tmp_path):
    path = tmp_path / "data.bin"
    path.write_bytes(b"a\n")
    with pytest.raises(ValueError, match="Unknown codec"):
        open_iterable(str(path), iterableargs={"format": "csv", "codec": "nope"})


def test_csv_totals_exclude_header(tmp_path):
    path = tmp_path / "a.csv"
    path.write_text("a,b\n1,2\n3,4\n", encoding="utf-8")
    with open_iterable(str(path)) as it:
        assert it.totals() == 2


def test_compressed_csv_totals_exclude_header(tmp_path):
    path = tmp_path / "a.csv.gz"
    with gzip.open(path, "wt", encoding="utf-8") as f:
        f.write("a,b\n1,2\n3,4\n")
    with open_iterable(str(path)) as it:
        assert it.totals() == 2
        assert len(list(it)) == 2


def test_csv_totals_overestimate_quoted_newlines(tmp_path):
    path = tmp_path / "m.csv"
    path.write_text('a,b\n1,"x\ny"\n', encoding="utf-8")
    with open_iterable(str(path)) as it:
        assert it.totals() >= len(list(it))
