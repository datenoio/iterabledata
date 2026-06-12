"""Tests for FASTA format."""

import os
import tempfile

from iterable.datatypes.fasta import FASTAIterable
from iterable.helpers.detect import open_iterable


class TestFASTA:
    def test_fasta_id(self):
        assert FASTAIterable.id() == "fasta"

    def test_fasta_flatonly(self):
        assert FASTAIterable.is_flatonly()

    def test_fasta_read_single_sequence(self):
        content = ">seq1\nACGT\n"
        with tempfile.NamedTemporaryFile(mode="w", suffix=".fa", delete=False, encoding="utf-8") as f:
            f.write(content)
            path = f.name
        try:
            it = FASTAIterable(path, mode="r")
            row = it.read()
            it.close()
            assert row["id"] == "seq1"
            assert row["sequence"] == "ACGT"
            assert "description" in row
        finally:
            os.unlink(path)

    def test_fasta_read_multiple_sequences(self):
        content = ">s1 desc1\nAAA\n>s2\nTTT\n"
        with tempfile.NamedTemporaryFile(mode="w", suffix=".fasta", delete=False, encoding="utf-8") as f:
            f.write(content)
            path = f.name
        try:
            it = FASTAIterable(path, mode="r")
            rows = list(it)
            it.close()
            assert len(rows) == 2
            assert rows[0]["id"] == "s1" and rows[0]["description"] == "desc1" and rows[0]["sequence"] == "AAA"
            assert rows[1]["id"] == "s2" and rows[1]["sequence"] == "TTT"
        finally:
            os.unlink(path)

    def test_fasta_open_iterable_detection(self):
        content = ">id1\nACGT\n"
        with tempfile.NamedTemporaryFile(mode="w", suffix=".fasta", delete=False, encoding="utf-8") as f:
            f.write(content)
            path = f.name
        try:
            with open_iterable(path) as src:
                rows = list(src)
            assert len(rows) == 1
            assert rows[0]["id"] == "id1"
        finally:
            os.unlink(path)

    def test_fasta_read_bulk(self):
        content = ">a\nA\n>b\nB\n>c\nC\n"
        with tempfile.NamedTemporaryFile(mode="w", suffix=".fna", delete=False, encoding="utf-8") as f:
            f.write(content)
            path = f.name
        try:
            it = FASTAIterable(path, mode="r")
            chunk = it.read_bulk(2)
            it.close()
            assert len(chunk) == 2
            assert chunk[0]["id"] == "a" and chunk[1]["id"] == "b"
        finally:
            os.unlink(path)

    def test_fasta_empty_file(self):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".fa", delete=False, encoding="utf-8") as f:
            path = f.name
        try:
            it = FASTAIterable(path, mode="r")
            rows = list(it)
            it.close()
            assert len(rows) == 0
        finally:
            os.unlink(path)
