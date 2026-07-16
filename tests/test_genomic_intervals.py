from io import StringIO

from iterable.datatypes.bed import BEDIterable
from iterable.datatypes.genomic_intervals import GFF3Iterable, GTFIterable


def test_bed_coordinates_and_blocks():
    source = BEDIterable.from_stream(StringIO("track name=x\nchr1\t0\t10\tgene\t0\t+\t0\t10\t0\t1\t10\t0,\n"))
    row = source.read()
    assert row["start"] == 0 and row["end"] == 10
    assert row["block_sizes"] == [10]


def test_gff3_and_gtf_attributes():
    gff = GFF3Iterable.from_stream(StringIO("##gff-version 3\nchr1\tsrc\tgene\t1\t4\t.\t+\t.\tID=g1;Name=Gene\n"))
    assert gff.read()["attributes"]["ID"] == "g1"

    gtf = GTFIterable.from_stream(StringIO('chr1\tsrc\tgene\t1\t4\t.\t+\t.\tgene_id "g1";\n'))
    assert gtf.read()["attributes"]["gene_id"] == "g1"
