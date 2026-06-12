"""Tests for BAM/SAM alignment formats (pysam)."""

import os
import tempfile

import pytest

try:
    import pysam  # noqa: F401

    HAS_PYSAM = True
except ImportError:
    HAS_PYSAM = False

from iterable.datatypes.bam import BAMIterable
from iterable.datatypes.sam import SAMIterable
from iterable.helpers.detect import open_iterable

# Minimal valid SAM: header + one alignment line
MINIMAL_SAM = """@HD\tVN:1.6\tSO:coordinate
@SQ\tSN:ref\tLN:100
read1\t0\tref\t1\t60\t4M\t*\t0\t0\tACGT\tIIII
"""


@pytest.mark.skipif(not HAS_PYSAM, reason="pysam not installed")
class TestSAM:
    def test_sam_id(self):
        assert SAMIterable.id() == "sam"

    def test_sam_flatonly(self):
        assert SAMIterable.is_flatonly()

    def test_sam_read(self):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".sam", delete=False, encoding="utf-8") as f:
            f.write(MINIMAL_SAM)
            path = f.name
        try:
            it = SAMIterable(path, mode="r")
            row = it.read()
            it.close()
            assert "query_name" in row
            assert row["query_name"] == "read1"
            assert row.get("query_sequence") == "ACGT"
        finally:
            os.unlink(path)

    def test_sam_open_iterable_detection(self):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".sam", delete=False, encoding="utf-8") as f:
            f.write(MINIMAL_SAM)
            path = f.name
        try:
            with open_iterable(path) as src:
                rows = list(src)
            assert len(rows) >= 1
            assert rows[0].get("query_name") == "read1"
        finally:
            os.unlink(path)

    def test_sam_read_bulk(self):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".sam", delete=False, encoding="utf-8") as f:
            f.write(MINIMAL_SAM)
            path = f.name
        try:
            it = SAMIterable(path, mode="r")
            chunk = it.read_bulk(10)
            it.close()
            assert len(chunk) >= 1
        finally:
            os.unlink(path)


@pytest.mark.skipif(not HAS_PYSAM, reason="pysam not installed")
class TestBAM:
    def test_bam_id(self):
        assert BAMIterable.id() == "bam"

    def test_bam_flatonly(self):
        assert BAMIterable.is_flatonly()

    def test_bam_requires_filename(self):
        """BAM requires filename (no stream support in pysam for our usage)."""
        with pytest.raises(ValueError) as exc_info:
            BAMIterable(filename=None, mode="r")
        assert "filename" in str(exc_info.value).lower()


@pytest.mark.skipif(HAS_PYSAM, reason="only run when pysam is not installed")
def test_sam_import_error_without_pysam():
    """Without pysam, SAMIterable raises ImportError with install hint."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".sam", delete=False) as f:
        f.write("@HD\tVN:1.6\n")
        path = f.name
    try:
        with pytest.raises(ImportError) as exc_info:
            SAMIterable(path, mode="r")
        assert "iterabledata[alignment]" in str(exc_info.value) or "pysam" in str(exc_info.value).lower()
    finally:
        os.unlink(path)
