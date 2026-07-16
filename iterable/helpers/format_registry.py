"""Declarative format metadata registry (single source of truth)."""

from __future__ import annotations

from collections.abc import Iterator
from dataclasses import dataclass, replace
from typing import Any, Literal

from .format_descriptions import description_for, doc_url_for


@dataclass(frozen=True)
class FormatDescriptor:
    """Metadata for a built-in data format."""

    id: str
    module: str
    cls: str
    aliases: tuple[str, ...] = ()
    text: bool = False
    flat: bool = False
    writable: bool = True
    extra: str | None = None
    magic: tuple[bytes, ...] = ()
    description: str | None = None
    example_args: dict[str, Any] | None = None
    limitations: tuple[str, ...] = ()
    doc_url: str | None = None
    # Extended capability declarations. ``None`` is deliberate: an unknown
    # backend-dependent value is safer than optimistic runtime inference.
    maturity: Literal["stable", "experimental", "partial"] = "stable"
    read_memory: Literal["bounded", "whole_input", "backend_defined", "unknown"] = "unknown"
    write_memory: Literal["bounded", "whole_output", "backend_defined", "unknown"] = "unknown"
    native_bulk_read: bool | None = None
    native_bulk_write: bool | None = None
    selection: tuple[str, ...] = ()
    codec_support: tuple[str, ...] = ()
    source_constraints: tuple[str, ...] = ()


def _fmt(
    id: str,
    module: str,
    cls: str,
    *,
    aliases: tuple[str, ...] = (),
    text: bool = False,
    flat: bool = False,
    writable: bool = True,
    extra: str | None = None,
    magic: tuple[bytes, ...] = (),
    description: str | None = None,
    example_args: dict[str, Any] | None = None,
    limitations: tuple[str, ...] = (),
    doc_url: str | None = None,
    maturity: Literal["stable", "experimental", "partial"] = "stable",
    read_memory: Literal["bounded", "whole_input", "backend_defined", "unknown"] = "unknown",
    write_memory: Literal["bounded", "whole_output", "backend_defined", "unknown"] = "unknown",
    native_bulk_read: bool | None = None,
    native_bulk_write: bool | None = None,
    selection: tuple[str, ...] = (),
    codec_support: tuple[str, ...] = (),
    source_constraints: tuple[str, ...] = (),
) -> FormatDescriptor:
    return FormatDescriptor(
        id=id,
        module=module,
        cls=cls,
        aliases=aliases,
        text=text,
        flat=flat,
        writable=writable,
        extra=extra,
        magic=magic,
        description=description,
        example_args=example_args,
        limitations=limitations,
        doc_url=doc_url,
        maturity=maturity,
        read_memory=read_memory,
        write_memory=write_memory,
        native_bulk_read=native_bulk_read,
        native_bulk_write=native_bulk_write,
        selection=selection,
        codec_support=codec_support,
        source_constraints=source_constraints,
    )


_DOCS_BASE = "docs/docs/formats"

# Curated LLM-oriented metadata for high-traffic and argument-heavy formats.
_LLM_METADATA: dict[str, dict[str, Any]] = {
    "csv": {
        "description": "Comma-separated values; flat tabular text format for spreadsheets and ETL.",
        "doc_url": f"{_DOCS_BASE}/csv.md",
        "limitations": ("Delimiter/encoding may need detection for non-standard files",),
    },
    "json": {
        "description": "JSON array or object stream; nested structures, common for APIs.",
        "doc_url": f"{_DOCS_BASE}/json.md",
    },
    "jsonl": {
        "description": "JSON Lines (one JSON object per line); streaming-friendly. Also known as ndjson.",
        "doc_url": f"{_DOCS_BASE}/jsonl.md",
    },
    "parquet": {
        "description": "Columnar binary format optimized for analytics and compression.",
        "doc_url": f"{_DOCS_BASE}/parquet.md",
        "limitations": ("Requires pyarrow",),
    },
    "geoparquet": {
        "description": "GeoParquet profile preserving geometry metadata and WKB columns.",
        "doc_url": f"{_DOCS_BASE}/geoparquet.md",
        "limitations": ("Requires pyarrow; geometry is raw WKB by default",),
    },
    "flatgeobuf": {
        "description": "Streaming FlatGeobuf geospatial features through Fiona/GDAL.",
        "doc_url": f"{_DOCS_BASE}/geoparquet.md",
        "limitations": ("Read-only; requires Fiona/GDAL",),
    },
    "zarr": {
        "description": "Chunked Zarr v2/v3 array stores exposed as bounded rows.",
        "doc_url": f"{_DOCS_BASE}/zarr.md",
        "limitations": ("Requires zarr and numpy; explicit array selection for multi-array stores",),
    },
    "xml": {
        "description": "XML documents; requires the record element tag name.",
        "doc_url": f"{_DOCS_BASE}/xml.md",
        "example_args": {"tagname": "item"},
        "limitations": ("Read-only", "Requires tagname iterablearg"),
    },
    "xlsx": {
        "description": "Excel Open XML workbook; flat sheets, read-only in IterableData.",
        "doc_url": f"{_DOCS_BASE}/xlsx.md",
        "limitations": ("Read-only", "Requires openpyxl"),
    },
    "avro": {
        "description": "Apache Avro binary row format with embedded schema.",
        "doc_url": f"{_DOCS_BASE}/avro.md",
        "limitations": ("Requires avro package",),
    },
    "orc": {
        "description": "Optimized Row Columnar format for Hive/Spark workloads.",
        "doc_url": f"{_DOCS_BASE}/orc.md",
        "limitations": ("Requires pyorc",),
    },
    "delta": {
        "description": "Delta Lake table format; directory-based lakehouse storage.",
        "doc_url": f"{_DOCS_BASE}/delta.md",
        "limitations": ("Read-only", "Path is table root directory"),
    },
    "iceberg": {
        "description": "Apache Iceberg tables via catalog configuration.",
        "doc_url": f"{_DOCS_BASE}/iceberg.md",
        "example_args": {"catalog_name": "my_catalog", "table_name": "my_table"},
        "limitations": ("Read-only", "Requires catalog_name and table_name"),
    },
    "pb": {
        "description": "Protocol Buffers binary messages.",
        "doc_url": f"{_DOCS_BASE}/protobuf.md",
        "example_args": {"message_class": "mymodule.MyMessage"},
        "limitations": ("Requires message_class parameter",),
    },
    "otlp-json": {
        "description": "OpenTelemetry traces, logs, and metrics in OTLP JSON envelopes.",
        "doc_url": f"{_DOCS_BASE}/otlp.md",
        "limitations": ("Signal-specific JSON documents are bounded by max_message_bytes",),
    },
    "otlp-protobuf": {
        "description": "OpenTelemetry ExportRequest protobuf profile with explicit message classes.",
        "doc_url": f"{_DOCS_BASE}/otlp.md",
        "limitations": ("Requires generated OpenTelemetry protobuf message_class",),
    },
    "cram": {
        "description": "CRAM binary sequence alignments with explicit reference configuration.",
        "doc_url": f"{_DOCS_BASE}/genomic-intervals.md",
        "limitations": ("Requires pysam and, for some files, reference_filename",),
    },
    "bed": {
        "description": "BED3-BED12 genomic intervals with 0-based half-open coordinates.",
        "doc_url": f"{_DOCS_BASE}/genomic-intervals.md",
    },
    "gff3": {
        "description": "GFF3 genomic annotations with directives and ordered attributes.",
        "doc_url": f"{_DOCS_BASE}/genomic-intervals.md",
    },
    "gtf": {
        "description": "GTF genomic annotations with quoted attributes and 1-based coordinates.",
        "doc_url": f"{_DOCS_BASE}/genomic-intervals.md",
    },
    "arrow": {
        "description": "Apache Arrow/Feather columnar in-memory format.",
        "doc_url": f"{_DOCS_BASE}/arrow.md",
    },
    "yaml": {
        "description": "YAML text configuration and data files.",
        "doc_url": f"{_DOCS_BASE}/yaml.md",
    },
    "bam": {
        "description": "Binary Alignment Map for genomic sequence alignments.",
        "doc_url": f"{_DOCS_BASE}/bam.md",
        "limitations": ("Read-only", "Requires pysam"),
    },
    "fa": {
        "description": "FASTA biological sequence format.",
        "doc_url": f"{_DOCS_BASE}/fa.md",
        "limitations": ("Read-only",),
    },
    "fq": {
        "description": "FASTQ biological sequences with quality scores.",
        "doc_url": f"{_DOCS_BASE}/fq.md",
        "limitations": ("Read-only",),
    },
    "gexf": {
        "description": "Graph Exchange XML Format for network graphs.",
        "doc_url": f"{_DOCS_BASE}/gexf.md",
        "limitations": ("Read-only",),
    },
    "graphml": {
        "description": "XML-based graph markup language.",
        "doc_url": f"{_DOCS_BASE}/graphml.md",
        "limitations": ("Read-only",),
    },
    "gpx": {
        "description": "GPS Exchange Format for geographic tracks and waypoints.",
        "doc_url": f"{_DOCS_BASE}/gpx.md",
    },
    "zipxml": {
        "description": "XML inside ZIP archives; requires record tag name.",
        "doc_url": f"{_DOCS_BASE}/zipxml.md",
        "example_args": {"tagname": "item"},
        "limitations": ("Read-only", "Requires tagname"),
    },
    "fbs": {
        "description": "FlatBuffers binary serialization; schema-dependent.",
        "doc_url": f"{_DOCS_BASE}/flatbuffers.md",
        "example_args": {"schema_file": "schema.fbs", "root_type": "MyTable"},
        "limitations": ("Partial support", "Requires schema_file and root_type"),
    },
    "hudi": {
        "description": "Apache Hudi data lake tables; table-path dependent.",
        "doc_url": f"{_DOCS_BASE}/hudi.md",
        "example_args": {"table_path": "/path/to/hudi/table"},
        "limitations": ("Partial support", "Requires table_path"),
    },
    "lance": {
        "description": "Lance columnar format for ML workloads.",
        "doc_url": f"{_DOCS_BASE}/lance.md",
        "limitations": ("Partial support", "Requires pylance package (not PyPI lance)"),
    },
    "capnp": {
        "description": "Cap'n Proto binary messages; schema-dependent.",
        "doc_url": f"{_DOCS_BASE}/capnp.md",
        "example_args": {"schema_file": "schema.capnp", "schema_name": "MyMessage"},
        "limitations": ("Requires schema_file and schema_name",),
    },
    "thrift": {
        "description": "Apache Thrift binary messages; schema-dependent.",
        "doc_url": f"{_DOCS_BASE}/thrift.md",
        "limitations": ("Schema-dependent", "Requires generated Thrift types"),
    },
    "ubj": {
        "description": "UBJSON (Universal Binary JSON) format.",
        "doc_url": f"{_DOCS_BASE}/ubjson.md",
        "limitations": ("Optional dependency py-ubjson",),
    },
}


def _enrich_descriptor(desc: FormatDescriptor) -> FormatDescriptor:
    meta = _LLM_METADATA.get(desc.id)
    description = desc.description
    example_args = desc.example_args
    limitations = desc.limitations
    doc_url = desc.doc_url

    if meta is not None:
        description = meta.get("description", description)
        example_args = meta.get("example_args", example_args)
        meta_limitations = meta.get("limitations", ())
        if isinstance(meta_limitations, list):
            meta_limitations = tuple(meta_limitations)
        if meta_limitations:
            limitations = meta_limitations
        doc_url = meta.get("doc_url", doc_url)

    if description is None:
        description = description_for(desc.id)
    if doc_url is None:
        doc_url = doc_url_for(desc.id)

    return replace(
        desc,
        description=description,
        example_args=example_args,
        limitations=limitations,
        doc_url=doc_url,
    )


_RAW_FORMAT_DESCRIPTORS: tuple[FormatDescriptor, ...] = (
    _fmt(id="avro", module="iterable.datatypes.avro", cls="AVROIterable", flat=True),
    _fmt(id="bson", module="iterable.datatypes.bsonf", cls="BSONIterable"),
    _fmt(
        id="csv",
        module="iterable.datatypes.csv",
        cls="CSVIterable",
        aliases=("tsv",),
        text=True,
        flat=True,
        read_memory="bounded",
        write_memory="bounded",
        native_bulk_read=False,
        native_bulk_write=True,
        codec_support=("gzip", "bz2", "xz", "zstd"),
    ),
    _fmt(id="dbf", module="iterable.datatypes.dbf", cls="DBFIterable", flat=True, writable=False),
    _fmt(id="json", module="iterable.datatypes.json", cls="JSONIterable", text=True),
    _fmt(
        id="jsonl",
        module="iterable.datatypes.jsonl",
        cls="JSONLinesIterable",
        aliases=("ndjson",),
        text=True,
        read_memory="bounded",
        write_memory="bounded",
        native_bulk_read=False,
        native_bulk_write=True,
        codec_support=("gzip", "bz2", "xz", "zstd"),
    ),
    _fmt(id="jsonld", module="iterable.datatypes.jsonld", cls="JSONLDIterable", text=True),
    _fmt(
        id="parquet",
        module="iterable.datatypes.parquet",
        cls="ParquetIterable",
        read_memory="bounded",
        write_memory="bounded",
        native_bulk_read=True,
        native_bulk_write=True,
        selection=("columns", "row_groups"),
        codec_support=("snappy", "gzip", "brotli", "zstd", "lz4"),
    ),
    _fmt(
        id="geoparquet",
        module="iterable.datatypes.geoparquet",
        cls="GeoParquetIterable",
        aliases=("geo.parquet",),
        flat=True,
        extra="parquet",
        read_memory="bounded",
        write_memory="bounded",
        native_bulk_read=True,
        native_bulk_write=True,
        selection=("columns", "row_groups", "bbox"),
        source_constraints=("geometry_column",),
    ),
    _fmt(id="pickle", module="iterable.datatypes.picklef", cls="PickleIterable"),
    _fmt(id="orc", module="iterable.datatypes.orc", cls="ORCIterable"),
    _fmt(id="xls", module="iterable.datatypes.xls", cls="XLSIterable", flat=True, writable=False),
    _fmt(id="xlsx", module="iterable.datatypes.xlsx", cls="XLSXIterable", flat=True, writable=False),
    _fmt(id="xml", module="iterable.datatypes.xml", cls="XMLIterable", text=True, writable=False),
    _fmt(
        id="arrow",
        module="iterable.datatypes.arrow",
        cls="ArrowIterable",
        aliases=("feather",),
        read_memory="bounded",
        write_memory="bounded",
        native_bulk_read=True,
        native_bulk_write=True,
        selection=("columns",),
        codec_support=(),
    ),
    _fmt(id="mp", module="iterable.datatypes.msgpack", cls="MessagePackIterable", aliases=("msgpack",)),
    _fmt(id="fwf", module="iterable.datatypes.fwf", cls="FixedWidthIterable", aliases=("fixed",), text=True, flat=True),
    _fmt(id="yml", module="iterable.datatypes.yaml", cls="YAMLIterable", aliases=("yaml",), text=True),
    _fmt(
        id="sas", module="iterable.datatypes.sas", cls="SASIterable", aliases=("sas7bdat",), flat=True, writable=False
    ),
    _fmt(
        id="dta", module="iterable.datatypes.stata", cls="StataIterable", aliases=("stata",), flat=True, writable=False
    ),
    _fmt(id="sav", module="iterable.datatypes.spss", cls="SPSSIterable", aliases=("spss",), flat=True, writable=False),
    _fmt(id="pb", module="iterable.datatypes.protobuf", cls="ProtobufIterable", aliases=("protobuf",)),
    _fmt(
        id="otlp-json",
        module="iterable.datatypes.otlp",
        cls="OTLPJSONIterable",
        aliases=("otlp", "otlpjson"),
        text=True,
        extra="otlp",
        maturity="experimental",
        read_memory="whole_input",
        write_memory="whole_output",
        native_bulk_read=True,
        native_bulk_write=True,
        selection=("item_key",),
    ),
    _fmt(
        id="otlp-protobuf",
        module="iterable.datatypes.otlp",
        cls="OTLPProtobufIterable",
        aliases=("otlp.pb", "otlp-proto"),
        extra="otlp",
        maturity="experimental",
        read_memory="whole_input",
        write_memory="whole_output",
        native_bulk_read=True,
        native_bulk_write=True,
        source_constraints=("message_class",),
    ),
    _fmt(id="ion", module="iterable.datatypes.ion", cls="IonIterable"),
    _fmt(id="h5", module="iterable.datatypes.hdf5", cls="HDF5Iterable", aliases=("hdf5",), flat=True, writable=False),
    _fmt(id="geojson", module="iterable.datatypes.geojson", cls="GeoJSONIterable", text=True),
    _fmt(
        id="geojsonseq",
        module="iterable.datatypes.geojsonseq",
        cls="GeoJSONSeqIterable",
        aliases=("geojsonl", "geojsons"),
        text=True,
    ),
    _fmt(id="toml", module="iterable.datatypes.toml", cls="TOMLIterable", text=True),
    _fmt(id="tar", module="iterable.datatypes.tar", cls="TARIterable", aliases=("tgz",), writable=False),
    _fmt(id="delta", module="iterable.datatypes.delta", cls="DeltaIterable", flat=True, writable=False),
    _fmt(id="cbor", module="iterable.datatypes.cbor", cls="CBORIterable", aliases=("cbors",)),
    _fmt(id="cdf", module="iterable.datatypes.cdf", cls="CDFIterable", writable=False),
    _fmt(id="ods", module="iterable.datatypes.ods", cls="ODSIterable", flat=True, writable=False),
    _fmt(id="db", module="iterable.datatypes.sqlite", cls="SQLiteIterable", aliases=("sqlite",), flat=True),
    _fmt(id="ddb", module="iterable.datatypes.duckdb", cls="DuckDBIterable", aliases=("duckdb",), flat=True),
    _fmt(id="psv", module="iterable.datatypes.psv", cls="PSVIterable", text=True, flat=True, writable=False),
    _fmt(id="ssv", module="iterable.datatypes.psv", cls="SSVIterable", text=True, flat=True),
    _fmt(id="ubj", module="iterable.datatypes.ubjson", cls="UBJSONIterable", aliases=("ubjson",)),
    _fmt(id="capnp", module="iterable.datatypes.capnp", cls="CapnpIterable"),
    _fmt(id="iceberg", module="iterable.datatypes.iceberg", cls="IcebergIterable", flat=True, writable=False),
    _fmt(id="ttl", module="iterable.datatypes.turtle", cls="TurtleIterable", aliases=("turtle",), text=True),
    _fmt(
        id="fbs",
        module="iterable.datatypes.flatbuffers",
        cls="FlatBuffersIterable",
        aliases=("flatbuffers",),
        writable=False,
    ),
    _fmt(id="thrift", module="iterable.datatypes.thrift", cls="ThriftIterable"),
    _fmt(id="txt", module="iterable.datatypes.txt", cls="TxtIterable", aliases=("text",), text=True),
    _fmt(id="hudi", module="iterable.datatypes.hudi", cls="HudiIterable", flat=True, writable=False),
    _fmt(
        id="log",
        module="iterable.datatypes.apachelog",
        cls="ApacheLogIterable",
        aliases=("apachelog", "access.log"),
        text=True,
        flat=True,
    ),
    _fmt(id="tfrecord", module="iterable.datatypes.tfrecord", cls="TFRecordIterable", aliases=("tfrecords",)),
    _fmt(id="seq", module="iterable.datatypes.sequencefile", cls="SequenceFileIterable", aliases=("sequencefile",)),
    _fmt(id="gelf", module="iterable.datatypes.gelf", cls="GELIterable", text=True),
    _fmt(id="cef", module="iterable.datatypes.cef", cls="CEFIterable", text=True, flat=True),
    _fmt(
        id="nt",
        module="iterable.datatypes.ntriples",
        cls="NTriplesIterable",
        aliases=("ntriples",),
        text=True,
        flat=True,
    ),
    _fmt(id="nq", module="iterable.datatypes.nquads", cls="NQuadsIterable", aliases=("nquads",), text=True, flat=True),
    _fmt(id="kafka", module="iterable.datatypes.kafka", cls="KafkaIterable"),
    _fmt(id="pulsar", module="iterable.datatypes.pulsar", cls="PulsarIterable"),
    _fmt(id="ckpt", module="iterable.datatypes.flink", cls="FlinkIterable", aliases=("flink",)),
    _fmt(id="beam", module="iterable.datatypes.beam", cls="BeamIterable"),
    _fmt(id="rio", module="iterable.datatypes.recordio", cls="RecordIOIterable", aliases=("recordio",)),
    _fmt(id="rdf", module="iterable.datatypes.rdfxml", cls="RDFXMLIterable", aliases=("rdfxml",), text=True),
    _fmt(id="ilp", module="iterable.datatypes.ilp", cls="ILPIterable", text=True),
    _fmt(id="annotatedcsv", module="iterable.datatypes.annotatedcsv", cls="AnnotatedCSVIterable", text=True, flat=True),
    _fmt(id="cdx", module="iterable.datatypes.cdx", cls="CDXIterable", text=True, flat=True),
    _fmt(id="arc", module="iterable.datatypes.warc", cls="WARCIterable", aliases=("warc",)),
    _fmt(id="ldif", module="iterable.datatypes.ldif", cls="LDIFIterable", text=True),
    _fmt(id="mbox", module="iterable.datatypes.mbox", cls="MBOXIterable", text=True),
    _fmt(
        id="ini",
        module="iterable.datatypes.ini",
        cls="INIIterable",
        aliases=("properties", "conf"),
        text=True,
        flat=True,
    ),
    _fmt(id="edn", module="iterable.datatypes.edn", cls="EDNIterable", text=True),
    _fmt(id="smile", module="iterable.datatypes.smile", cls="SMILEIterable"),
    _fmt(id="bencode", module="iterable.datatypes.bencode", cls="BencodeIterable", aliases=("torrent",)),
    _fmt(id="vcf", module="iterable.datatypes.vcf", cls="VCFIterable", aliases=("vcard",), text=True),
    _fmt(
        id="genomic_vcf",
        module="iterable.datatypes.genomic_vcf",
        cls="GenomicVCFIterable",
        aliases=("bcf",),
        text=True,
        extra="bio",
        writable=False,
    ),
    _fmt(
        id="cram",
        module="iterable.datatypes.cram",
        cls="CRAMIterable",
        extra="alignment",
        flat=True,
        writable=False,
        read_memory="bounded",
        native_bulk_read=False,
        source_constraints=("filename", "reference_filename"),
    ),
    _fmt(
        id="bed",
        module="iterable.datatypes.bed",
        cls="BEDIterable",
        aliases=("bed3", "bed6", "bed12"),
        text=True,
        flat=True,
        read_memory="bounded",
        write_memory="bounded",
        native_bulk_read=False,
        native_bulk_write=True,
    ),
    _fmt(
        id="gff3",
        module="iterable.datatypes.genomic_intervals",
        cls="GFF3Iterable",
        aliases=("gff",),
        text=True,
        flat=True,
        read_memory="bounded",
        write_memory="bounded",
        native_bulk_read=False,
        native_bulk_write=True,
    ),
    _fmt(
        id="gtf",
        module="iterable.datatypes.genomic_intervals",
        cls="GTFIterable",
        text=True,
        flat=True,
        read_memory="bounded",
        write_memory="bounded",
        native_bulk_read=False,
        native_bulk_write=True,
    ),
    _fmt(id="ics", module="iterable.datatypes.ical", cls="ICALIterable", aliases=("ical",), text=True),
    _fmt(id="eml", module="iterable.datatypes.eml", cls="EMLIterable", text=True),
    _fmt(
        id="sql",
        module="iterable.datatypes.mysqldump",
        cls="MySQLDumpIterable",
        aliases=("mysqldump",),
        text=True,
        flat=True,
    ),
    _fmt(
        id="copy", module="iterable.datatypes.pgcopy", cls="PGCopyIterable", aliases=("pgcopy",), text=True, flat=True
    ),
    _fmt(id="hocon", module="iterable.datatypes.hocon", cls="HOCONIterable", text=True),
    _fmt(id="flexbuf", module="iterable.datatypes.flexbuffers", cls="FlexBuffersIterable", aliases=("flexbuffers",)),
    _fmt(id="der", module="iterable.datatypes.asn1", cls="ASN1Iterable", aliases=("asn1",)),
    _fmt(id="mht", module="iterable.datatypes.mhtml", cls="MHTMLIterable", aliases=("mhtml",), text=True),
    _fmt(id="ltsv", module="iterable.datatypes.ltsv", cls="LTSVIterable", text=True),
    _fmt(id="px", module="iterable.datatypes.px", cls="PXIterable", text=True, flat=True, writable=False),
    _fmt(id="kml", module="iterable.datatypes.kml", cls="KMLIterable", text=True),
    _fmt(id="kmz", module="iterable.datatypes.kmz", cls="KMZIterable", text=True, writable=False),
    _fmt(id="gpx", module="iterable.datatypes.gpx", cls="GPXIterable", text=True, writable=False),
    _fmt(id="gml", module="iterable.datatypes.gml", cls="GMLIterable", text=True),
    _fmt(id="shp", module="iterable.datatypes.shapefile", cls="ShapefileIterable", aliases=("shapefile",)),
    _fmt(id="gpkg", module="iterable.datatypes.geopackage", cls="GeoPackageIterable", aliases=("geopackage",)),
    _fmt(
        id="flatgeobuf",
        module="iterable.datatypes.flatgeobuf",
        cls="FlatGeobufIterable",
        aliases=("fgb",),
        extra="geospatial",
        writable=False,
        read_memory="bounded",
        native_bulk_read=True,
        selection=("bbox",),
        source_constraints=("filename",),
    ),
    _fmt(id="csvw", module="iterable.datatypes.csvw", cls="CSVWIterable", text=True, flat=True),
    _fmt(
        id="rda", module="iterable.datatypes.rdata", cls="RDataIterable", aliases=("rdata",), flat=True, writable=False
    ),
    _fmt(id="rds", module="iterable.datatypes.rds", cls="RDSIterable", flat=True, writable=False),
    _fmt(
        id="lance",
        module="iterable.datatypes.lance",
        cls="LanceIterable",
        flat=True,
        maturity="partial",
        read_memory="bounded",
        write_memory="bounded",
        native_bulk_read=True,
        native_bulk_write=True,
        selection=("columns", "filter"),
        source_constraints=("directory",),
    ),
    _fmt(id="pcap", module="iterable.datatypes.pcap", cls="PCAPIterable", aliases=("pcapng",), writable=False),
    _fmt(id="nc", module="iterable.datatypes.netcdf", cls="NetCDFIterable", aliases=("netcdf",), writable=False),
    _fmt(id="mvt", module="iterable.datatypes.mvt", cls="MVTIterable", aliases=("pbf",), writable=False),
    _fmt(id="topojson", module="iterable.datatypes.topojson", cls="TopoJSONIterable"),
    _fmt(id="rss", module="iterable.datatypes.feed", cls="FeedIterable", aliases=("feed", "atom"), writable=False),
    _fmt(id="dxf", module="iterable.datatypes.dxf", cls="DXFIterable", writable=False),
    _fmt(id="libsvm", module="iterable.datatypes.libsvm", cls="LIBSVMIterable", flat=True),
    _fmt(id="npy", module="iterable.datatypes.numpy", cls="NumPyIterable", aliases=("npz",), flat=True),
    _fmt(
        id="htm",
        module="iterable.datatypes.html",
        cls="HTMLIterable",
        aliases=("html",),
        text=True,
        flat=True,
        writable=False,
    ),
    _fmt(id="arff", module="iterable.datatypes.arff", cls="ARFFIterable", text=True, flat=True, writable=False),
    _fmt(id="trig", module="iterable.datatypes.trig", cls="TriGIterable", text=True, writable=False),
    _fmt(id="n3", module="iterable.datatypes.n3", cls="N3Iterable", text=True, writable=False),
    _fmt(id="trix", module="iterable.datatypes.trix", cls="TriXIterable", text=True, writable=False),
    _fmt(id="xlsb", module="iterable.datatypes.xlsb", cls="XLSBIterable", flat=True, writable=False),
    _fmt(
        id="fa",
        module="iterable.datatypes.fasta",
        cls="FASTAIterable",
        aliases=("fasta", "fna", "faa"),
        text=True,
        flat=True,
        writable=False,
    ),
    _fmt(
        id="fq",
        module="iterable.datatypes.fastq",
        cls="FASTQIterable",
        aliases=("fastq",),
        text=True,
        flat=True,
        writable=False,
    ),
    _fmt(id="graphml", module="iterable.datatypes.graphml", cls="GraphMLIterable", text=True, writable=False),
    _fmt(id="gexf", module="iterable.datatypes.gexf", cls="GEXFIterable", text=True, writable=False),
    _fmt(id="gv", module="iterable.datatypes.dot", cls="DOTIterable", aliases=("dot",), text=True, writable=False),
    _fmt(id="bam", module="iterable.datatypes.bam", cls="BAMIterable", flat=True, writable=False),
    _fmt(id="sam", module="iterable.datatypes.sam", cls="SAMIterable", text=True, flat=True, writable=False),
    _fmt(
        id="zarr",
        module="iterable.datatypes.zarr",
        cls="ZarrIterable",
        flat=True,
        extra="zarr",
        maturity="experimental",
        read_memory="bounded",
        write_memory="bounded",
        native_bulk_read=True,
        native_bulk_write=True,
        selection=("array", "slice", "chunks"),
        source_constraints=("directory",),
    ),
    _fmt(
        id="vtx",
        module="iterable.datatypes.vortex",
        cls="VortexIterable",
        aliases=("vortex",),
        flat=True,
        maturity="partial",
        read_memory="bounded",
        write_memory="whole_output",
        native_bulk_read=True,
        native_bulk_write=False,
        source_constraints=("filename",),
    ),
    _fmt(id="zipxml", module="iterable.datatypes.zipxml", cls="ZIPXMLSource", writable=False),
)

FORMAT_DESCRIPTORS: tuple[FormatDescriptor, ...] = tuple(_enrich_descriptor(d) for d in _RAW_FORMAT_DESCRIPTORS)

# Preserve legacy list order; membership is validated against descriptor flags.
_TEXT_TYPE_ORDER: tuple[str, ...] = (
    "xml",
    "csv",
    "tsv",
    "jsonl",
    "ndjson",
    "json",
    "jsonld",
    "yaml",
    "yml",
    "fwf",
    "fixed",
    "geojson",
    "toml",
    "psv",
    "ssv",
    "turtle",
    "ttl",
    "apachelog",
    "log",
    "access.log",
    "gelf",
    "cef",
    "nt",
    "nq",
    "ntriples",
    "nquads",
    "rdf",
    "rdf.xml",
    "ilp",
    "annotatedcsv",
    "cdx",
    "ldif",
    "mbox",
    "ini",
    "properties",
    "conf",
    "edn",
    "vcf",
    "ical",
    "ics",
    "eml",
    "sql",
    "mysqldump",
    "pgcopy",
    "copy",
    "hocon",
    "mhtml",
    "mht",
    "txt",
    "text",
    "ltsv",
    "px",
    "kml",
    "kmz",
    "gpx",
    "gml",
    "csvw",
    "html",
    "htm",
    "arff",
    "trig",
    "n3",
    "trix",
    "fasta",
    "fa",
    "fna",
    "faa",
    "fastq",
    "fq",
    "graphml",
    "gexf",
    "dot",
    "gv",
    "sam",
)
_FLAT_TYPE_ORDER: tuple[str, ...] = (
    "csv",
    "tsv",
    "xls",
    "xlsx",
    "dbf",
    "fwf",
    "fixed",
    "sas7bdat",
    "sas",
    "dta",
    "stata",
    "sav",
    "spss",
    "hdf5",
    "h5",
    "delta",
    "ods",
    "sqlite",
    "db",
    "duckdb",
    "ddb",
    "psv",
    "ssv",
    "iceberg",
    "hudi",
    "apachelog",
    "log",
    "access.log",
    "cef",
    "nt",
    "nq",
    "ntriples",
    "nquads",
    "annotatedcsv",
    "cdx",
    "ini",
    "properties",
    "conf",
    "mysqldump",
    "sql",
    "pgcopy",
    "copy",
    "px",
    "csvw",
    "rdata",
    "rda",
    "rds",
    "lance",
    "libsvm",
    "npy",
    "npz",
    "html",
    "htm",
    "arff",
    "xlsb",
    "fasta",
    "fa",
    "fastq",
    "fq",
    "bam",
    "sam",
    "vortex",
    "vtx",
)
# Legacy read-only membership (exact set previously maintained by hand in detect.py).
# Canonical ids with writable=False on their descriptor; aliases listed explicitly.
_READONLY_MEMBERS: frozenset[str] = frozenset(
    {
        "arff",
        "atom",
        "bam",
        "cdf",
        "dbf",
        "delta",
        "dot",
        "dta",
        "dxf",
        "fa",
        "faa",
        "fasta",
        "fastq",
        "feed",
        "flatbuffers",
        "fna",
        "fq",
        "bcf",
        "genomic_vcf",
        "gexf",
        "gpx",
        "graphml",
        "gv",
        "hdf5",
        "htm",
        "html",
        "hudi",
        "iceberg",
        "kmz",
        "mvt",
        "n3",
        "nc",
        "netcdf",
        "ods",
        "pbf",
        "pcap",
        "psv",
        "px",
        "rdata",
        "rds",
        "rss",
        "sam",
        "sas",
        "sas7bdat",
        "sav",
        "spss",
        "stata",
        "tar",
        "tgz",
        "trig",
        "trix",
        "xls",
        "xlsb",
        "xlsx",
        "xml",
        "zipxml",
    }
)
_EXTRA_READ_ONLY: frozenset[str] = frozenset({"zipped"})

# Orphan text ids present in _TEXT_TYPE_ORDER but not in DATATYPE_REGISTRY.
_TEXT_ORPHANS: frozenset[str] = frozenset({"rdf.xml"})


_LOOKUP: dict[str, FormatDescriptor] | None = None


def _build_lookup() -> dict[str, FormatDescriptor]:
    lookup: dict[str, FormatDescriptor] = {}
    for desc in FORMAT_DESCRIPTORS:
        lookup[desc.id] = desc
        for alias in desc.aliases:
            lookup[alias] = desc
    return lookup


def get_descriptor(format_id: str) -> FormatDescriptor | None:
    """Return the descriptor for a canonical id or alias, or None if unknown."""
    global _LOOKUP
    if _LOOKUP is None:
        _LOOKUP = _build_lookup()
    return _LOOKUP.get(format_id)


# Maps datatype/codec module paths to ``pyproject.toml`` optional-extra names.
_MODULE_INSTALL_EXTRAS: dict[str, str] = {
    "iterable.datatypes.parquet": "parquet",
    "iterable.datatypes.geoparquet": "parquet",
    "iterable.datatypes.orc": "orc",
    "iterable.datatypes.arrow": "parquet",
    "iterable.datatypes.xls": "excel",
    "iterable.datatypes.xlsx": "excel",
    "iterable.datatypes.xlsb": "xlsb",
    "iterable.datatypes.xml": "xml",
    "iterable.datatypes.bsonf": "bson",
    "iterable.datatypes.dbf": "dbf",
    "iterable.datatypes.warc": "warc",
    "iterable.datatypes.duckdb": "duckdb",
    "iterable.datatypes.sas": "stats",
    "iterable.datatypes.stata": "stats",
    "iterable.datatypes.spss": "stats",
    "iterable.datatypes.protobuf": "protobuf",
    "iterable.datatypes.otlp": "otlp",
    "iterable.datatypes.ion": "ion",
    "iterable.datatypes.hdf5": "hdf5",
    "iterable.datatypes.geojson": "geospatial",
    "iterable.datatypes.shapefile": "geospatial",
    "iterable.datatypes.geopackage": "geospatial",
    "iterable.datatypes.flatgeobuf": "geospatial",
    "iterable.datatypes.mvt": "mvt",
    "iterable.datatypes.topojson": "topojson",
    "iterable.datatypes.kml": "geospatial",
    "iterable.datatypes.kmz": "geospatial",
    "iterable.datatypes.gml": "geospatial",
    "iterable.datatypes.toml": "toml",
    "iterable.datatypes.msgpack": "msgpack",
    "iterable.datatypes.yaml": "yaml",
    "iterable.datatypes.pcap": "pcap",
    "iterable.datatypes.netcdf": "netcdf",
    "iterable.datatypes.cbor": "cbor",
    "iterable.datatypes.cdf": "cdf",
    "iterable.datatypes.feed": "feed",
    "iterable.datatypes.dxf": "dxf",
    "iterable.datatypes.html": "html",
    "iterable.datatypes.arff": "arff",
    "iterable.datatypes.json": "json",
    "iterable.datatypes.vortex": "vortex",
    "iterable.datatypes.zarr": "zarr",
    "iterable.datatypes.trig": "rdf",
    "iterable.datatypes.n3": "rdf",
    "iterable.datatypes.trix": "rdf",
    "iterable.datatypes.turtle": "rdf",
    "iterable.datatypes.graphml": "graph",
    "iterable.datatypes.gexf": "graph",
    "iterable.datatypes.dot": "graph",
    "iterable.datatypes.bam": "alignment",
    "iterable.datatypes.sam": "alignment",
    "iterable.datatypes.genomic_vcf": "bio",
    "iterable.datatypes.cram": "alignment",
    "iterable.datatypes.bed": "bio",
    "iterable.datatypes.genomic_intervals": "bio",
    "iterable.datatypes.lance": "lakehouse",
    "iterable.datatypes.delta": "lakehouse",
    "iterable.datatypes.iceberg": "lakehouse",
    "iterable.datatypes.hudi": "lakehouse",
    "iterable.datatypes.avro": "avro",
    "iterable.datatypes.numpy": "npy",
    "iterable.datatypes.ubjson": "ubj",
    "iterable.datatypes.vcf": "vcf",
    "iterable.datatypes.ods": "ods",
    "iterable.datatypes.rdata": "rdata",
    "iterable.datatypes.rds": "rdata",
    "iterable.datatypes.capnp": "capnp",
    "iterable.datatypes.thrift": "thrift",
    "iterable.datatypes.flatbuffers": "fbs",
    "iterable.datatypes.edn": "edn",
    "iterable.datatypes.hocon": "hocon",
    "iterable.datatypes.asn1": "der",
    "iterable.datatypes.bencode": "bencode",
    "iterable.datatypes.gpx": "xml",
    "iterable.datatypes.ical": "ics",
    "iterable.datatypes.ldif": "ldif",
    "iterable.codecs.lz4codec": "compression",
    "iterable.codecs.snappycodec": "compression",
    "iterable.codecs.lzocodec": "compression",
    "iterable.codecs.brotlicodec": "compression",
    "iterable.codecs.zstdcodec": "compression",
    "iterable.codecs.szipcodec": "compression",
}

# Module basename -> extra when the module path is not listed above.
_BASENAME_INSTALL_EXTRAS: dict[str, str] = {
    "parquet": "parquet",
    "orc": "orc",
    "xml": "xml",
    "toml": "toml",
    "yaml": "yaml",
    "msgpack": "msgpack",
    "cbor": "cbor",
    "protobuf": "protobuf",
    "vortex": "vortex",
}


def install_extra_hint(module_path: str) -> str | None:
    """Return the ``pyproject.toml`` optional-extra name for a module, if known."""
    if module_path in _MODULE_INSTALL_EXTRAS:
        return _MODULE_INSTALL_EXTRAS[module_path]
    desc = get_descriptor_by_module(module_path)
    if desc is not None and desc.extra:
        return desc.extra
    basename = module_path.rsplit(".", 1)[-1]
    return _BASENAME_INSTALL_EXTRAS.get(basename)


def get_descriptor_by_module(module_path: str) -> FormatDescriptor | None:
    """Return the descriptor whose ``module`` matches ``module_path``."""
    for desc in FORMAT_DESCRIPTORS:
        if desc.module == module_path:
            return desc
    return None


def iter_descriptors() -> Iterator[FormatDescriptor]:
    """Yield each built-in format descriptor once (canonical ids only)."""
    yield from FORMAT_DESCRIPTORS


def build_datatype_registry() -> dict[str, tuple[str, str]]:
    """Build extension/id -> (module, class) mapping including aliases."""
    registry: dict[str, tuple[str, str]] = {}
    for desc in FORMAT_DESCRIPTORS:
        target = (desc.module, desc.cls)
        registry[desc.id] = target
        for alias in desc.aliases:
            registry[alias] = target
    return registry


def build_read_only_formats() -> set[str]:
    """Build the set of format ids and aliases that do not support writing."""
    return set(_READONLY_MEMBERS) | set(_EXTRA_READ_ONLY)


def _membership_lookup() -> dict[str, FormatDescriptor]:
    global _LOOKUP
    if _LOOKUP is None:
        _LOOKUP = _build_lookup()
    return _LOOKUP


def build_text_data_types() -> list[str]:
    """Build ordered text-format id list preserving legacy order."""
    lookup = _membership_lookup()
    result: list[str] = []
    for item in _TEXT_TYPE_ORDER:
        if item in _TEXT_ORPHANS:
            result.append(item)
            continue
        desc = lookup.get(item)
        if desc is not None and desc.text:
            result.append(item)
    return result


def build_flat_types() -> list[str]:
    """Build ordered flat-format id list preserving legacy order."""
    lookup = _membership_lookup()
    result: list[str] = []
    for item in _FLAT_TYPE_ORDER:
        desc = lookup.get(item)
        if desc is not None and desc.flat:
            result.append(item)
    return result


@dataclass(frozen=True)
class MagicMatch:
    """A content-detection signature matched against file leading bytes."""

    format_id: str
    prefix: bytes
    confidence: float = 0.99
    # When set, peek must also contain this substring (ZIP-based formats).
    contains: bytes | None = None


# Ordered longest-prefix-first is handled at match time.
MAGIC_SIGNATURES: tuple[MagicMatch, ...] = (
    MagicMatch("parquet", b"PAR1", 0.99),
    MagicMatch("orc", b"ORC", 0.99),
    MagicMatch("vortex", b"VTXF", 0.99),
    MagicMatch("pcap", b"\xa1\xb2\xc3\xd4", 0.99),
    MagicMatch("pcap", b"\xd4\xc3\xb2\xa1", 0.99),
    MagicMatch("pcapng", b"\x0a\x0d\x0d\x0a", 0.99),
    MagicMatch("xlsx", b"PK\x03\x04", 0.95, contains=b"xl/"),
    MagicMatch("xlsx", b"PK\x03\x04", 0.95, contains=b"[Content_Types].xml"),
    MagicMatch("arrow", b"ARROW1", 0.99),
)


def match_magic_prefix(peek: bytes) -> tuple[str, float, str] | None:
    """Match leading bytes against registered magic signatures."""
    if not peek:
        return None
    # PCAP signatures require at least 4 bytes.
    if len(peek) >= 4:
        for sig in MAGIC_SIGNATURES:
            if sig.format_id in ("pcap", "pcapng") and peek.startswith(sig.prefix):
                return (sig.format_id, sig.confidence, "magic_number")
    for sig in MAGIC_SIGNATURES:
        if sig.format_id in ("pcap", "pcapng"):
            continue
        if not peek.startswith(sig.prefix):
            continue
        if sig.contains is not None and sig.contains not in peek[:200]:
            continue
        return (sig.format_id, sig.confidence, "magic_number")
    # Generic ZIP fallback (after specific ZIP-based checks).
    if peek.startswith(b"PK\x03\x04"):
        if b"word/" in peek[:100]:
            return ("docx", 0.95, "magic_number")
        return ("zip", 0.90, "magic_number")
    return None
