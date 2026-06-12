"""Tests for FASTQ format."""

import os
import tempfile

from iterable.datatypes.fastq import FASTQIterable
from iterable.helpers.detect import open_iterable


class TestFASTQ:
    def test_fastq_id(self):
        assert FASTQIterable.id() == "fastq"

    def test_fastq_flatonly(self):
        assert FASTQIterable.is_flatonly()

    def test_fastq_read_one_record(self):
        content = "@read1\nACGT\n+\nIIII\n"
        with tempfile.NamedTemporaryFile(mode="w", suffix=".fq", delete=False, encoding="utf-8") as f:
            f.write(content)
            path = f.name
        try:
            it = FASTQIterable(path, mode="r")
            row = it.read()
            it.close()
            assert row["id"] == "read1"
            assert row["sequence"] == "ACGT"
            assert row["quality"] == "IIII"
        finally:
            os.unlink(path)

    def test_fastq_read_multiple_records(self):
        content = "@r1\nAA\n+\n!!\n@r2\nTT\n+\n@@\n"
        with tempfile.NamedTemporaryFile(mode="w", suffix=".fastq", delete=False, encoding="utf-8") as f:
            f.write(content)
            path = f.name
        try:
            it = FASTQIterable(path, mode="r")
            rows = list(it)
            it.close()
            assert len(rows) == 2
            assert rows[0]["id"] == "r1" and rows[0]["sequence"] == "AA" and rows[0]["quality"] == "!!"
            assert rows[1]["id"] == "r2" and rows[1]["sequence"] == "TT"
        finally:
            os.unlink(path)

    def test_fastq_open_iterable_detection(self):
        content = "@x\nG\n+\n#\n"
        with tempfile.NamedTemporaryFile(mode="w", suffix=".fastq", delete=False, encoding="utf-8") as f:
            f.write(content)
            path = f.name
        try:
            with open_iterable(path) as src:
                rows = list(src)
            assert len(rows) == 1
            assert rows[0]["id"] == "x"
        finally:
            os.unlink(path)

    def test_fastq_read_bulk(self):
        content = '@a\nA\n+\n!\n@b\nB\n+\n"\n@c\nC\n+\n#\n'
        with tempfile.NamedTemporaryFile(mode="w", suffix=".fq", delete=False, encoding="utf-8") as f:
            f.write(content)
            path = f.name
        try:
            it = FASTQIterable(path, mode="r")
            chunk = it.read_bulk(2)
            it.close()
            assert len(chunk) == 2
        finally:
            os.unlink(path)
