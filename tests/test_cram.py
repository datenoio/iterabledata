"""Tests for CRAM alignment reading (pysam-backed, explicit reference configuration).

Committed fixtures (see tests/create_bio_fixtures.py):

- ``fixtures/sample.cram``: six reads written with ``embed_ref=1`` so the file
  decodes without any external reference (deterministic, offline-safe).
- ``fixtures/sample.cram.crai``: its CRAI index.
- ``fixtures/sample.reference.fa`` (+ ``.fai``): the 1 kb reference the CRAM was
  built against, for explicit ``reference_filename`` coverage.

Reference-missing coverage builds a *non-embedded* CRAM in a tmp dir, hides the
reference, and scrubs ``REF_PATH``/``REF_CACHE`` so htslib cannot fall back to a
network lookup — proving the failure is a clear local error, never a download.
"""

from __future__ import annotations

import shutil
import tracemalloc
from pathlib import Path

import pytest

pysam = pytest.importorskip("pysam", reason="pysam is required for CRAM support")

from iterable.datatypes.cram import CRAMIterable  # noqa: E402
from iterable.helpers.detect import open_iterable  # noqa: E402

FIXTURES = Path(__file__).parent / "fixtures"
CRAM_FIXTURE = FIXTURES / "sample.cram"
REFERENCE_FIXTURE = FIXTURES / "sample.reference.fa"

EXPECTED_NAMES = [f"read-{index}" for index in range(6)]
EXPECTED_STARTS = [index * 100 for index in range(6)]


@pytest.fixture(autouse=True)
def _no_reference_network_fallback(monkeypatch, tmp_path):
    """Keep htslib reference lookup local and empty: no cache, no EBI download.

    REF_PATH replaces htslib's default search path (which includes the EBI CRAM
    reference registry URL), so pointing it at a nonexistent local pattern makes
    any reference lookup fail fast and offline.
    """
    monkeypatch.setenv("REF_PATH", str(tmp_path / "no-such-dir" / "%s"))
    monkeypatch.setenv("REF_CACHE", str(tmp_path / "no-such-cache"))


def _write_tmp_cram(tmp_path: Path, *, embed_ref: bool, count: int = 6) -> tuple[Path, Path]:
    """Write a small CRAM plus its reference in tmp_path (interleave-builder style)."""
    reference = tmp_path / "ref.fa"
    reference.write_text(">chr1\n" + "ACGT" * 250 + "\n", encoding="utf-8")
    pysam.faidx(str(reference))
    cram_path = tmp_path / ("embed.cram" if embed_ref else "rows.cram")
    header = {"HD": {"VN": "1.6", "SO": "coordinate"}, "SQ": [{"LN": 1000, "SN": "chr1"}]}
    format_options = ["embed_ref=1"] if embed_ref else None
    with pysam.AlignmentFile(
        str(cram_path), "wc", header=header, reference_filename=str(reference), format_options=format_options
    ) as output:
        for index in range(count):
            segment = pysam.AlignedSegment()
            segment.query_name = f"read-{index}"
            segment.query_sequence = "ACGTACGTAC"
            segment.flag = 0
            segment.reference_id = 0
            segment.reference_start = index * 100
            segment.mapping_quality = 60
            segment.cigar = ((0, 10),)
            output.write(segment)
    return cram_path, reference


def _read_names(source) -> list[str]:
    names = []
    while True:
        try:
            names.append(source.read()["query_name"])
        except StopIteration:
            return names


class TestCRAMBasics:
    def test_id_and_flatonly(self):
        assert CRAMIterable.id() == "cram"
        assert CRAMIterable.is_flatonly()

    def test_requires_filename(self):
        with pytest.raises(ValueError, match="filename"):
            CRAMIterable(filename=None, mode="r")

    def test_open_iterable_detection(self):
        with open_iterable(str(CRAM_FIXTURE)) as source:
            assert isinstance(source, CRAMIterable)
            assert source.read()["query_name"] == "read-0"


class TestCRAMReferencePresent:
    def test_read_with_explicit_reference(self):
        with CRAMIterable(str(CRAM_FIXTURE), reference_filename=str(REFERENCE_FIXTURE)) as source:
            rows = list(source)
        assert [row["query_name"] for row in rows] == EXPECTED_NAMES
        assert [row["reference_start"] for row in rows] == EXPECTED_STARTS

    def test_rows_match_sam_bam_shape(self):
        with CRAMIterable(str(CRAM_FIXTURE), reference_filename=str(REFERENCE_FIXTURE)) as source:
            row = source.read()
        for key in (
            "query_name",
            "flag",
            "reference_id",
            "reference_start",
            "mapping_quality",
            "cigarstring",
            "next_reference_id",
            "next_reference_start",
            "template_length",
            "query_sequence",
            "query_qualities",
        ):
            assert key in row, f"missing alignment field {key!r}"
        assert row["query_sequence"] == "ACGTACGTAC"
        assert row["cigarstring"] == "10M"
        assert row["mapping_quality"] == 60

    def test_embedded_reference_reads_without_reference_filename(self, tmp_path):
        """An embed_ref CRAM decodes with no reference at all (proven with a
        dangling UR: tmp reference deleted before reading)."""
        cram_path, reference = _write_tmp_cram(tmp_path, embed_ref=True)
        reference.unlink()
        reference.with_suffix(".fa.fai").unlink()
        with CRAMIterable(str(cram_path)) as source:
            assert _read_names(source) == EXPECTED_NAMES

    def test_read_bulk_and_reset(self):
        with CRAMIterable(str(CRAM_FIXTURE), reference_filename=str(REFERENCE_FIXTURE)) as source:
            chunk = source.read_bulk(4)
            assert [row["query_name"] for row in chunk] == EXPECTED_NAMES[:4]
            source.reset()
            assert _read_names(source) == EXPECTED_NAMES


class TestCRAMReferenceMissing:
    def test_missing_reference_is_clear_error_not_download(self, tmp_path):
        """A CRAM that needs an unavailable reference fails fast with a clear
        error naming the reference requirement; no download is attempted
        (REF_PATH/REF_CACHE scrubbed by the autouse fixture)."""
        cram_path, reference = _write_tmp_cram(tmp_path, embed_ref=False)
        reference.unlink()
        reference.with_suffix(".fa.fai").unlink()
        with CRAMIterable(str(cram_path)) as source:
            with pytest.raises(ValueError, match=r"[Rr]eference"):
                source.read()

    def test_reference_filename_fixes_the_failure(self, tmp_path):
        """Same file, explicit reference: reading succeeds — the error above is
        specifically the missing-reference scenario."""
        cram_path, reference = _write_tmp_cram(tmp_path, embed_ref=False)
        with CRAMIterable(str(cram_path), reference_filename=str(reference)) as source:
            assert _read_names(source) == EXPECTED_NAMES


class TestCRAMIndex:
    def test_indexed_fixture_reads_sequentially(self):
        """The committed .crai sits next to the fixture; sequential iteration is unaffected."""
        assert (FIXTURES / "sample.cram.crai").exists()
        with CRAMIterable(str(CRAM_FIXTURE), reference_filename=str(REFERENCE_FIXTURE)) as source:
            assert _read_names(source) == EXPECTED_NAMES

    def test_unindexed_copy_reads_sequentially(self, tmp_path):
        """Without a .crai, sequential iteration still yields every record in order."""
        unindexed = tmp_path / "sample.cram"
        shutil.copy(CRAM_FIXTURE, unindexed)
        with CRAMIterable(str(unindexed), reference_filename=str(REFERENCE_FIXTURE)) as source:
            assert _read_names(source) == EXPECTED_NAMES


class TestCRAMTruncated:
    def test_truncated_file_raises_clear_error(self, tmp_path):
        truncated = tmp_path / "truncated.cram"
        data = CRAM_FIXTURE.read_bytes()
        truncated.write_bytes(data[: len(data) // 2])
        with CRAMIterable(str(truncated)) as source:
            with pytest.raises(ValueError, match=r"truncated|corrupt|reference"):
                while True:
                    source.read()

    def test_empty_file_is_clear_error(self, tmp_path):
        empty = tmp_path / "empty.cram"
        empty.write_bytes(b"")
        with pytest.raises(ValueError, match=r"Unable to open CRAM"):
            CRAMIterable(str(empty))


class TestCRAMBoundedMemory:
    def test_large_cram_streams_in_bounded_memory(self, tmp_path):
        """20k reads decoded one at a time must not materialize the file."""
        cram_path, _reference = _write_tmp_cram(tmp_path, embed_ref=True, count=20_000)
        tracemalloc.start()
        try:
            count = 0
            with CRAMIterable(str(cram_path)) as source:
                while True:
                    try:
                        source.read()
                        count += 1
                    except StopIteration:
                        break
            _current, peak = tracemalloc.get_traced_memory()
        finally:
            tracemalloc.stop()
        assert count == 20_000
        assert peak < 10_000_000, f"peak memory {peak} bytes for 20k streamed reads"
