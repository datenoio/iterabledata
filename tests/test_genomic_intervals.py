"""Tests for BED and GFF3/GTF genomic interval formats.

Committed fixtures (see tests/create_bio_fixtures.py):

- ``fixtures/sample.bed`` / ``.gz``: browser + track + comment headers, then
  BED3/4/6/9/12 rows and one row with two extra trailing columns.
- ``fixtures/sample.gff3`` / ``.gz``: ``##gff-version``/``##sequence-region``
  directives, a comment, six features.
- ``fixtures/sample.gtf`` / ``.gz``: a comment plus six features.
- ``fixtures/sample_fasta_tail.gff3``: two features followed by a ``##FASTA``
  section, exercising the documented stop policy.
"""

from __future__ import annotations

import tracemalloc
from io import StringIO
from pathlib import Path

import pytest

from iterable.datatypes.bed import BEDIterable
from iterable.datatypes.genomic_intervals import GFF3Iterable, GTFIterable
from iterable.helpers.detect import open_iterable

FIXTURES = Path(__file__).parent / "fixtures"
BED_FIXTURE = FIXTURES / "sample.bed"
GFF3_FIXTURE = FIXTURES / "sample.gff3"
GTF_FIXTURE = FIXTURES / "sample.gtf"
GFF3_FASTA_FIXTURE = FIXTURES / "sample_fasta_tail.gff3"


def _read_all(source) -> list[dict]:
    rows = []
    while True:
        try:
            rows.append(source.read())
        except StopIteration:
            return rows


# ---------------------------------------------------------------------------
# BED
# ---------------------------------------------------------------------------


class TestBEDReading:
    def test_bed_coordinates_and_blocks(self):
        source = BEDIterable.from_stream(StringIO("track name=x\nchr1\t0\t10\tgene\t0\t+\t0\t10\t0\t1\t10\t0,\n"))
        row = source.read()
        assert row["start"] == 0 and row["end"] == 10
        assert row["block_sizes"] == [10]

    def test_fixture_rows_cover_bed3_through_bed12_and_extra(self):
        with BEDIterable(str(BED_FIXTURE)) as source:
            rows = _read_all(source)
        assert len(rows) == 6
        assert rows[0] == {"chrom": "chr1", "start": 0, "end": 150}
        assert rows[1]["name"] == "feature-1"
        assert rows[2]["score"] == 42 and rows[2]["strand"] == "+"
        assert rows[3]["item_rgb"] == "255,0,0" and rows[3]["thick_start"] == 600
        assert rows[4]["block_count"] == 2
        assert rows[4]["block_sizes"] == [100, 60]
        assert rows[4]["block_starts"] == [0, 100]
        assert rows[5]["extra"] == ["extra-a", "extra-b"]

    def test_headers_browser_track_lines_collected_not_yielded(self):
        with BEDIterable(str(BED_FIXTURE)) as source:
            rows = _read_all(source)
            headers = list(source.headers)
        assert len(rows) == 6
        assert headers == [
            "browser position chr1:1-2000",
            'track name=sample description="Sample BED fixture" visibility=full',
            "# committed fixture for extend-bioinformatics-formats",
        ]

    def test_compressed_gzip_fixture(self):
        with open_iterable(str(FIXTURES / "sample.bed.gz")) as source:
            assert isinstance(source, BEDIterable)
            rows = _read_all(source)
        assert len(rows) == 6
        assert rows[4]["block_count"] == 2

    def test_empty_file(self, tmp_path):
        empty = tmp_path / "empty.bed"
        empty.write_text("", encoding="utf-8")
        with BEDIterable(str(empty)) as source:
            assert source.read_bulk(10) == []
            with pytest.raises(StopIteration):
                source.read()

    def test_headers_only_file(self, tmp_path):
        path = tmp_path / "headers.bed"
        path.write_text("track name=only\n# nothing else\n", encoding="utf-8")
        with BEDIterable(str(path)) as source:
            assert _read_all(source) == []
            assert source.headers == ["track name=only", "# nothing else"]


class TestBEDMalformed:
    def test_too_few_columns(self, tmp_path):
        path = tmp_path / "bad.bed"
        path.write_text("chr1\t0\t10\nchr1\t20\n", encoding="utf-8")
        with BEDIterable(str(path)) as source:
            source.read()
            with pytest.raises(ValueError, match=r"bad\.bed:line 2: BED requires at least chrom"):
                source.read()

    def test_non_integer_coordinate(self):
        source = BEDIterable.from_stream(StringIO("chr1\tZERO\t10\n"))
        with pytest.raises(ValueError, match=r"line 1:"):
            source.read()

    def test_end_before_start(self):
        source = BEDIterable.from_stream(StringIO("chr1\t10\t5\n"))
        with pytest.raises(ValueError, match=r"0-based with end >= start"):
            source.read()

    def test_negative_start(self):
        source = BEDIterable.from_stream(StringIO("chr1\t-1\t5\n"))
        with pytest.raises(ValueError, match=r"0-based with end >= start"):
            source.read()

    def test_block_count_mismatch(self):
        source = BEDIterable.from_stream(StringIO("chr1\t0\t10\tg\t0\t+\t0\t10\t0\t2\t10,\t0,\n"))
        with pytest.raises(ValueError, match=r"block_count does not match"):
            source.read()


class TestBEDRoundTrip:
    def test_round_trip_with_headers_blocks_and_extra(self, tmp_path):
        with BEDIterable(str(BED_FIXTURE)) as source:
            rows = _read_all(source)
            headers = list(source.headers)

        out = tmp_path / "roundtrip.bed"
        with BEDIterable(str(out), mode="w", headers=headers) as dest:
            dest.write(rows[0])
            dest.write_bulk(rows[1:])

        with BEDIterable(str(out)) as reopened:
            reread = _read_all(reopened)
            assert reopened.headers == headers
        assert reread == rows

    def test_write_requires_core_columns(self, tmp_path):
        out = tmp_path / "x.bed"
        with BEDIterable(str(out), mode="w") as dest:
            with pytest.raises(ValueError, match="chrom, start, and end"):
                dest.write({"chrom": "chr1", "start": 0})

    def test_round_trip_via_open_iterable(self, tmp_path):
        out = tmp_path / "peaks.bed"
        rows = [{"chrom": "chr2", "start": i * 10, "end": i * 10 + 5, "name": f"p{i}"} for i in range(3)]
        with open_iterable(str(out), mode="w") as dest:
            dest.write_bulk(rows)
        with open_iterable(str(out)) as source:
            assert isinstance(source, BEDIterable)
            assert _read_all(source) == rows


class TestBEDLargeStream:
    def test_large_stream_bounded_memory(self, tmp_path):
        path = tmp_path / "large.bed"
        count = 50_000
        with path.open("w", encoding="utf-8") as handle:
            for index in range(count):
                handle.write(f"chr1\t{index * 10}\t{index * 10 + 5}\tfeat-{index}\n")
        assert path.stat().st_size > 1_000_000  # multi-MB input
        tracemalloc.start()
        try:
            seen = 0
            with BEDIterable(str(path)) as source:
                while True:
                    chunk = source.read_bulk(1000)
                    if not chunk:
                        break
                    seen += len(chunk)
            _current, peak = tracemalloc.get_traced_memory()
        finally:
            tracemalloc.stop()
        assert seen == count
        assert peak < 10_000_000, f"peak memory {peak} bytes for {count} streamed rows"


# ---------------------------------------------------------------------------
# GFF3 / GTF
# ---------------------------------------------------------------------------


class TestGFF3Reading:
    def test_gff3_and_gtf_attributes(self):
        gff = GFF3Iterable.from_stream(StringIO("##gff-version 3\nchr1\tsrc\tgene\t1\t4\t.\t+\t.\tID=g1;Name=Gene\n"))
        assert gff.read()["attributes"]["ID"] == "g1"

        gtf = GTFIterable.from_stream(StringIO('chr1\tsrc\tgene\t1\t4\t.\t+\t.\tgene_id "g1";\n'))
        assert gtf.read()["attributes"]["gene_id"] == "g1"

    def test_fixture_rows_and_directive_metadata(self):
        with GFF3Iterable(str(GFF3_FIXTURE)) as source:
            rows = _read_all(source)
            metadata = list(source.metadata)
        assert len(rows) == 6
        assert metadata == [
            "##gff-version 3",
            "##sequence-region chr1 1 2000",
            "# committed fixture for extend-bioinformatics-formats",
        ]
        assert rows[0]["seqid"] == "chr1"
        assert rows[0]["start"] == 100 and rows[0]["end"] == 400  # 1-based closed, unchanged
        assert rows[0]["attributes"] == {"ID": "gene1", "Name": "GeneOne"}
        assert rows[4]["score"] == "0.5" and rows[4]["phase"] == "0"
        assert rows[5]["attributes"]["Note"] == "stress%20induced"  # no implicit unescaping

    def test_include_comments_yields_directive_records(self):
        with GFF3Iterable(str(GFF3_FIXTURE), include_comments=True) as source:
            first = source.read()
        assert first == {"record_type": "directive", "value": "##gff-version 3"}

    def test_compressed_gzip_fixtures(self):
        with open_iterable(str(FIXTURES / "sample.gff3.gz")) as source:
            assert isinstance(source, GFF3Iterable)
            assert len(_read_all(source)) == 6
        with open_iterable(str(FIXTURES / "sample.gtf.gz")) as source:
            assert isinstance(source, GTFIterable)
            rows = _read_all(source)
        assert len(rows) == 6
        assert rows[1]["attributes"]["transcript_id"] == "t1"

    def test_lossless_mode_keeps_raw_attributes(self):
        with GFF3Iterable(str(GFF3_FIXTURE), attribute_mode="lossless") as source:
            row = source.read()
        assert row["attributes_raw"] == "ID=gene1;Name=GeneOne"
        assert row["attributes"]["Name"] == "GeneOne"

    def test_invalid_attribute_mode_rejected(self):
        with pytest.raises(ValueError, match="attribute_mode"):
            GFF3Iterable(stream=StringIO(""), attribute_mode="bogus")


class TestGFF3Malformed:
    def test_malformed_attribute_raises_with_location(self, tmp_path):
        path = tmp_path / "bad.gff3"
        lines = (
            "##gff-version 3\nchr1\tsrc\tgene\t1\t4\t.\t+\t.\tID=g1;Name=Ok\nchr1\tsrc\tgene\t5\t9\t.\t+\t.\tBareAttr\n"
        )
        path.write_text(lines, encoding="utf-8")
        with GFF3Iterable(str(path)) as source:
            source.read()
            with pytest.raises(ValueError, match=r"bad\.gff3:line 3: Malformed GFF3 attribute 'BareAttr'"):
                source.read()

    def test_wrong_column_count(self):
        source = GFF3Iterable.from_stream(StringIO("chr1\tsrc\tgene\n"))
        with pytest.raises(ValueError, match=r"line 1: GFF3 records require nine"):
            source.read()

    def test_non_integer_coordinates(self):
        source = GFF3Iterable.from_stream(StringIO("chr1\tsrc\tgene\tx\t4\t.\t+\t.\tID=g1\n"))
        with pytest.raises(ValueError, match=r"Invalid GFF3 coordinates"):
            source.read()

    def test_zero_start_violates_one_based_closed(self):
        source = GFF3Iterable.from_stream(StringIO("chr1\tsrc\tgene\t0\t4\t.\t+\t.\tID=g1\n"))
        with pytest.raises(ValueError, match=r"1-based, closed"):
            source.read()

    def test_end_before_start(self):
        source = GTFIterable.from_stream(StringIO('chr1\tsrc\tgene\t9\t4\t.\t+\t.\tgene_id "g1";\n'))
        with pytest.raises(ValueError, match=r"1-based, closed"):
            source.read()

    def test_gtf_unquoted_attribute_is_lenient_but_coordinates_still_checked(self):
        # GTF profile: fragments outside `key "value";` shape are skipped,
        # while structural errors still raise with line context.
        gtf = GTFIterable.from_stream(StringIO("chr1\tsrc\tgene\t1\t4\t.\t+\t.\tgene_id g1;\n"))
        assert gtf.read()["attributes"] == {}


class TestGFF3FastaTail:
    def test_fasta_tail_stops_iteration_and_skips_sequences(self):
        with GFF3Iterable(str(GFF3_FASTA_FIXTURE)) as source:
            rows = _read_all(source)
            metadata = list(source.metadata)
        assert [row["attributes"]["ID"] for row in rows] == ["gene1", "gene2"]
        assert metadata == ["##gff-version 3", "##FASTA"]
        # Sequence lines (>chr1, ACGT...) are never parsed as feature rows.
        assert all("seqid" in row for row in rows)

    def test_fasta_tail_with_include_comments(self):
        with GFF3Iterable(str(GFF3_FASTA_FIXTURE), include_comments=True) as source:
            records = _read_all(source)
        assert records[0] == {"record_type": "directive", "value": "##gff-version 3"}
        assert records[3] == {"record_type": "directive", "value": "##FASTA"}
        assert len(records) == 4  # 2 directives + 2 features; nothing after ##FASTA

    def test_fasta_tail_reset_replays(self):
        with GFF3Iterable(str(GFF3_FASTA_FIXTURE)) as source:
            first_pass = _read_all(source)
            source.reset()
            assert _read_all(source) == first_pass
            assert source.metadata == ["##gff-version 3", "##FASTA"]


class TestGFFGTFRoundTrip:
    def test_gff3_parsed_round_trip(self, tmp_path):
        with GFF3Iterable(str(GFF3_FIXTURE)) as source:
            rows = _read_all(source)
        out = tmp_path / "roundtrip.gff3"
        with GFF3Iterable(str(out), mode="w") as dest:
            dest.write_bulk(rows)
        with GFF3Iterable(str(out)) as reopened:
            assert _read_all(reopened) == rows

    def test_gff3_lossless_round_trip_preserves_attribute_text(self, tmp_path):
        with GFF3Iterable(str(GFF3_FIXTURE), attribute_mode="lossless") as source:
            rows = _read_all(source)
        out = tmp_path / "lossless.gff3"
        with GFF3Iterable(str(out), mode="w", attribute_mode="lossless") as dest:
            dest.write_bulk(rows)
        original_features = [
            line for line in GFF3_FIXTURE.read_text(encoding="utf-8").splitlines() if not line.startswith("#")
        ]
        assert out.read_text(encoding="utf-8").splitlines() == original_features

    def test_gtf_round_trip(self, tmp_path):
        with GTFIterable(str(GTF_FIXTURE)) as source:
            rows = _read_all(source)
        out = tmp_path / "roundtrip.gtf"
        with GTFIterable(str(out), mode="w") as dest:
            for row in rows:
                dest.write(row)
        with GTFIterable(str(out)) as reopened:
            reread = _read_all(reopened)
        assert reread == rows
        # GTF attribute serialization keeps the `key "value";` profile.
        text = out.read_text(encoding="utf-8")
        assert 'gene_id "g1";' in text

    def test_round_trip_via_open_iterable(self, tmp_path):
        out = tmp_path / "genes.gff3"
        row = {
            "seqid": "chr1",
            "source": "src",
            "type": "gene",
            "start": 1,
            "end": 9,
            "strand": "+",
            "attributes": {"ID": "g1"},
        }
        with open_iterable(str(out), mode="w") as dest:
            dest.write(row)
        with open_iterable(str(out)) as source:
            assert isinstance(source, GFF3Iterable)
            reread = source.read()
        assert reread["start"] == 1 and reread["attributes"] == {"ID": "g1"}


class TestGFFBoundedMemory:
    def test_large_gff3_streams_in_bounded_memory(self, tmp_path):
        path = tmp_path / "large.gff3"
        count = 50_000
        with path.open("w", encoding="utf-8") as handle:
            handle.write("##gff-version 3\n")
            for index in range(count):
                handle.write(f"chr1\tsrc\tgene\t{index + 1}\t{index + 1}\t.\t+\t.\tID=g{index}\n")
        assert path.stat().st_size > 1_000_000  # multi-MB input
        tracemalloc.start()
        try:
            seen = 0
            with GFF3Iterable(str(path)) as source:
                while True:
                    try:
                        source.read()
                        seen += 1
                    except StopIteration:
                        break
            _current, peak = tracemalloc.get_traced_memory()
        finally:
            tracemalloc.stop()
        assert seen == count
        assert peak < 10_000_000, f"peak memory {peak} bytes for {count} streamed rows"
