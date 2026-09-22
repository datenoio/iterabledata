"""Regenerate the committed bioinformatics fixtures under ``tests/fixtures/``.

Produces small, deterministic fixtures for the CRAM / BED / GFF3 / GTF
datatypes (``extend-bioinformatics-formats`` change):

- ``sample.reference.fa`` (+ ``.fai``): 1 kb chr1 reference used to build the CRAM.
- ``sample.cram`` (+ ``.crai``): six reads, written with ``embed_ref=1`` so the
  file decodes without any external reference (deterministic offline). Tests
  still exercise explicit ``reference_filename`` against the committed FASTA.
- ``sample.bed`` / ``sample.bed.gz``: browser/track/comment headers plus
  BED3/4/6/9/12 rows and one row with extra trailing columns.
- ``sample.gff3`` / ``sample.gff3.gz``: directives, a comment, six features.
- ``sample.gtf`` / ``sample.gtf.gz``: a comment plus six features.
- ``sample_fasta_tail.gff3``: two features followed by a ``##FASTA`` tail.

Run with the project venv (requires pysam)::

    .venv/bin/python tests/create_bio_fixtures.py
"""

from __future__ import annotations

import gzip
import shutil
from pathlib import Path

import pysam

FIXTURES = Path(__file__).parent / "fixtures"

REFERENCE_NAME = "sample.reference.fa"
REFERENCE_SEQ = "ACGT" * 250  # 1000 bp chr1

BED_TEXT = """\
browser position chr1:1-2000
track name=sample description="Sample BED fixture" visibility=full
# committed fixture for extend-bioinformatics-formats
chr1\t0\t150
chr1\t200\t360\tfeature-1
chr1\t400\t560\tfeature-2\t42\t+
chr1\t600\t760\tfeature-3\t10\t-\t600\t760\t255,0,0
chr1\t800\t960\tfeature-4\t99\t+\t800\t960\t0\t2\t100,60,\t0,100,
chr1\t1000\t1160\tfeature-5\t7\t+\t1000\t1160\t0\t1\t160,\t0,\textra-a\textra-b
"""

GFF3_TEXT = """\
##gff-version 3
##sequence-region chr1 1 2000
# committed fixture for extend-bioinformatics-formats
chr1\tsrc\tgene\t100\t400\t.\t+\t.\tID=gene1;Name=GeneOne
chr1\tsrc\tmRNA\t100\t400\t.\t+\t.\tID=tx1;Parent=gene1
chr1\tsrc\texon\t100\t200\t.\t+\t.\tID=ex1;Parent=tx1
chr1\tsrc\texon\t300\t400\t.\t+\t.\tID=ex2;Parent=tx1
chr1\tsrc\tCDS\t150\t200\t0.5\t+\t0\tID=cds1;Parent=tx1
chr1\tsrc\tgene\t900\t1200\t.\t-\t.\tID=gene2;Name=GeneTwo;Note=stress%20induced
"""

GTF_TEXT = """\
# committed fixture for extend-bioinformatics-formats
chr1\tsrc\tgene\t100\t400\t.\t+\t.\tgene_id "g1"; gene_name "GeneOne";
chr1\tsrc\ttranscript\t100\t400\t.\t+\t.\tgene_id "g1"; transcript_id "t1"; gene_name "GeneOne";
chr1\tsrc\texon\t100\t200\t.\t+\t.\tgene_id "g1"; transcript_id "t1"; exon_number "1";
chr1\tsrc\texon\t300\t400\t.\t+\t.\tgene_id "g1"; transcript_id "t1"; exon_number "2";
chr1\tsrc\tCDS\t150\t200\t.\t+\t0\tgene_id "g1"; transcript_id "t1";
chr1\tsrc\tgene\t900\t1200\t.\t-\t.\tgene_id "g2"; gene_name "GeneTwo";
"""

GFF3_FASTA_TAIL_TEXT = """\
##gff-version 3
chr1\tsrc\tgene\t100\t400\t.\t+\t.\tID=gene1
chr1\tsrc\tgene\t900\t1200\t.\t-\t.\tID=gene2
##FASTA
>chr1
ACGTACGTACGT
ACGT
"""


def _write_text(name: str, content: str, compress: bool = False) -> None:
    path = FIXTURES / name
    path.write_text(content, encoding="utf-8")
    if compress:
        with path.open("rb") as source, gzip.GzipFile(str(path) + ".gz", "wb", mtime=0) as dest:
            shutil.copyfileobj(source, dest)


def _write_cram() -> None:
    reference = FIXTURES / REFERENCE_NAME
    reference.write_text(f">chr1\n{REFERENCE_SEQ}\n", encoding="utf-8")
    pysam.faidx(str(reference))

    cram_path = FIXTURES / "sample.cram"
    header = {"HD": {"VN": "1.6", "SO": "coordinate"}, "SQ": [{"LN": len(REFERENCE_SEQ), "SN": "chr1"}]}
    with pysam.AlignmentFile(
        str(cram_path),
        "wc",
        header=header,
        reference_filename=str(reference),
        format_options=["embed_ref=1"],
    ) as output:
        for index in range(6):
            segment = pysam.AlignedSegment()
            segment.query_name = f"read-{index}"
            segment.query_sequence = "ACGTACGTAC"
            segment.flag = 0
            segment.reference_id = 0
            segment.reference_start = index * 100
            segment.mapping_quality = 60
            segment.cigar = ((0, 10),)
            output.write(segment)
    pysam.index(str(cram_path))


def main() -> None:
    FIXTURES.mkdir(exist_ok=True)
    _write_cram()
    _write_text("sample.bed", BED_TEXT, compress=True)
    _write_text("sample.gff3", GFF3_TEXT, compress=True)
    _write_text("sample.gtf", GTF_TEXT, compress=True)
    _write_text("sample_fasta_tail.gff3", GFF3_FASTA_TAIL_TEXT)
    for path in sorted(FIXTURES.glob("sample*")):
        print(f"{path.name}\t{path.stat().st_size} bytes")


if __name__ == "__main__":
    main()
