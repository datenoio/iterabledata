from __future__ import annotations

import importlib
from typing import Literal, TypedDict

import chardet

from ..base import BaseCodec, BaseIterable

# Database driver registry helpers. Imported at module level (the db package is
# lightweight; heavy driver imports are internally guarded) so they can be
# patched as ``iterable.helpers.detect.get_driver`` / ``is_database_engine``.
from ..db import get_driver, is_database_engine

# Re-exported so callers/tests can reference and patch them as
# ``iterable.helpers.detect.<Driver>``; the heavy driver dependencies are guarded
# inside these modules, so importing the classes here is cheap and safe.
from ..db.clickhouse import ClickHouseDriver  # noqa: F401
from ..db.postgres import PostgresDriver  # noqa: F401
from ..exceptions import IterableDataError
from ..types import CodecArgs, IterableArgs
from .debug import file_io_logger, format_detection_logger, is_debug_enabled


def _load_symbol(module_path: str, symbol: str):
    """
    Lazy-load a datatype/codec class to avoid importing all optional dependencies at import time.
    """
    try:
        module = importlib.import_module(module_path)
        return getattr(module, symbol)
    except ImportError as e:
        raise ImportError(
            f"Failed to import '{symbol}' from '{module_path}'. "
            f"This format/codec likely requires an optional dependency. "
            f"Install the needed extras (for now: `pip install iterabledata[dev]` or `pip install iterabledata`)."
        ) from e


# Plugin discovery flag
_plugins_discovered = False


def _ensure_plugins_discovered() -> None:
    """Ensure plugins are discovered (lazy discovery)."""
    global _plugins_discovered
    if not _plugins_discovered:
        try:
            from ..plugins import discover_plugins

            discover_plugins()
        except Exception:
            # Silently fail if plugin system not available
            pass
        _plugins_discovered = True


def _get_format_registry() -> dict[str, tuple[str, str]]:
    """Get merged format registry (built-in + plugins).

    Built-in formats take precedence over plugins.
    """
    _ensure_plugins_discovered()

    # Start with built-in formats (take precedence)
    merged = DATATYPE_REGISTRY.copy()

    # Add plugin formats (don't override built-in)
    try:
        from ..plugins import get_plugin_registry

        registry = get_plugin_registry()
        for format_id, value in registry._formats.items():
            if format_id not in merged:
                merged[format_id] = value
    except Exception:
        # Silently fail if plugin system not available
        pass

    return merged


def _get_codec_registry() -> dict[str, tuple[str, str]]:
    """Get merged codec registry (built-in + plugins).

    Built-in codecs take precedence over plugins.
    """
    _ensure_plugins_discovered()

    # Start with built-in codecs (take precedence)
    merged = CODEC_REGISTRY.copy()

    # Add plugin codecs (don't override built-in)
    try:
        from ..plugins import get_plugin_registry

        registry = get_plugin_registry()
        for codec_id, value in registry._codecs.items():
            if codec_id not in merged:
                merged[codec_id] = value
    except Exception:
        # Silently fail if plugin system not available
        pass

    return merged


# Lazy registries: extension -> (module_path, class_name)
DATATYPE_REGISTRY: dict[str, tuple[str, str]] = {
    "avro": ("iterable.datatypes.avro", "AVROIterable"),
    "bson": ("iterable.datatypes.bsonf", "BSONIterable"),
    "csv": ("iterable.datatypes.csv", "CSVIterable"),
    "tsv": ("iterable.datatypes.csv", "CSVIterable"),
    "dbf": ("iterable.datatypes.dbf", "DBFIterable"),
    "json": ("iterable.datatypes.json", "JSONIterable"),
    "jsonl": ("iterable.datatypes.jsonl", "JSONLinesIterable"),
    "ndjson": ("iterable.datatypes.jsonl", "JSONLinesIterable"),
    "jsonld": ("iterable.datatypes.jsonld", "JSONLDIterable"),
    "parquet": ("iterable.datatypes.parquet", "ParquetIterable"),
    "pickle": ("iterable.datatypes.picklef", "PickleIterable"),
    "orc": ("iterable.datatypes.orc", "ORCIterable"),
    "xls": ("iterable.datatypes.xls", "XLSIterable"),
    "xlsx": ("iterable.datatypes.xlsx", "XLSXIterable"),
    "xml": ("iterable.datatypes.xml", "XMLIterable"),
    "arrow": ("iterable.datatypes.arrow", "ArrowIterable"),
    "feather": ("iterable.datatypes.arrow", "ArrowIterable"),
    "msgpack": ("iterable.datatypes.msgpack", "MessagePackIterable"),
    "mp": ("iterable.datatypes.msgpack", "MessagePackIterable"),
    "fwf": ("iterable.datatypes.fwf", "FixedWidthIterable"),
    "fixed": ("iterable.datatypes.fwf", "FixedWidthIterable"),
    "yaml": ("iterable.datatypes.yaml", "YAMLIterable"),
    "yml": ("iterable.datatypes.yaml", "YAMLIterable"),
    "sas7bdat": ("iterable.datatypes.sas", "SASIterable"),
    "sas": ("iterable.datatypes.sas", "SASIterable"),
    "dta": ("iterable.datatypes.stata", "StataIterable"),
    "stata": ("iterable.datatypes.stata", "StataIterable"),
    "sav": ("iterable.datatypes.spss", "SPSSIterable"),
    "spss": ("iterable.datatypes.spss", "SPSSIterable"),
    "protobuf": ("iterable.datatypes.protobuf", "ProtobufIterable"),
    "pb": ("iterable.datatypes.protobuf", "ProtobufIterable"),
    "ion": ("iterable.datatypes.ion", "IonIterable"),
    "hdf5": ("iterable.datatypes.hdf5", "HDF5Iterable"),
    "h5": ("iterable.datatypes.hdf5", "HDF5Iterable"),
    "geojson": ("iterable.datatypes.geojson", "GeoJSONIterable"),
    "toml": ("iterable.datatypes.toml", "TOMLIterable"),
    "delta": ("iterable.datatypes.delta", "DeltaIterable"),
    "cbor": ("iterable.datatypes.cbor", "CBORIterable"),
    "cbors": ("iterable.datatypes.cbor", "CBORIterable"),
    "cdf": ("iterable.datatypes.cdf", "CDFIterable"),
    "ods": ("iterable.datatypes.ods", "ODSIterable"),
    "sqlite": ("iterable.datatypes.sqlite", "SQLiteIterable"),
    "db": ("iterable.datatypes.sqlite", "SQLiteIterable"),
    "duckdb": ("iterable.datatypes.duckdb", "DuckDBIterable"),
    "ddb": ("iterable.datatypes.duckdb", "DuckDBIterable"),
    "psv": ("iterable.datatypes.psv", "PSVIterable"),
    "ssv": ("iterable.datatypes.psv", "SSVIterable"),
    "ubjson": ("iterable.datatypes.ubjson", "UBJSONIterable"),
    "ubj": ("iterable.datatypes.ubjson", "UBJSONIterable"),
    "capnp": ("iterable.datatypes.capnp", "CapnpIterable"),
    "iceberg": ("iterable.datatypes.iceberg", "IcebergIterable"),
    "turtle": ("iterable.datatypes.turtle", "TurtleIterable"),
    "ttl": ("iterable.datatypes.turtle", "TurtleIterable"),
    "flatbuffers": ("iterable.datatypes.flatbuffers", "FlatBuffersIterable"),
    "fbs": ("iterable.datatypes.flatbuffers", "FlatBuffersIterable"),
    "thrift": ("iterable.datatypes.thrift", "ThriftIterable"),
    "txt": ("iterable.datatypes.txt", "TxtIterable"),
    "text": ("iterable.datatypes.txt", "TxtIterable"),
    "hudi": ("iterable.datatypes.hudi", "HudiIterable"),
    "apachelog": ("iterable.datatypes.apachelog", "ApacheLogIterable"),
    "access.log": ("iterable.datatypes.apachelog", "ApacheLogIterable"),
    "log": ("iterable.datatypes.apachelog", "ApacheLogIterable"),
    "tfrecord": ("iterable.datatypes.tfrecord", "TFRecordIterable"),
    "tfrecords": ("iterable.datatypes.tfrecord", "TFRecordIterable"),
    "sequencefile": ("iterable.datatypes.sequencefile", "SequenceFileIterable"),
    "seq": ("iterable.datatypes.sequencefile", "SequenceFileIterable"),
    "gelf": ("iterable.datatypes.gelf", "GELIterable"),
    "cef": ("iterable.datatypes.cef", "CEFIterable"),
    "ntriples": ("iterable.datatypes.ntriples", "NTriplesIterable"),
    "nt": ("iterable.datatypes.ntriples", "NTriplesIterable"),
    "nquads": ("iterable.datatypes.nquads", "NQuadsIterable"),
    "nq": ("iterable.datatypes.nquads", "NQuadsIterable"),
    "kafka": ("iterable.datatypes.kafka", "KafkaIterable"),
    "pulsar": ("iterable.datatypes.pulsar", "PulsarIterable"),
    "flink": ("iterable.datatypes.flink", "FlinkIterable"),
    "ckpt": ("iterable.datatypes.flink", "FlinkIterable"),
    "beam": ("iterable.datatypes.beam", "BeamIterable"),
    "recordio": ("iterable.datatypes.recordio", "RecordIOIterable"),
    "rio": ("iterable.datatypes.recordio", "RecordIOIterable"),
    "rdfxml": ("iterable.datatypes.rdfxml", "RDFXMLIterable"),
    "rdf": ("iterable.datatypes.rdfxml", "RDFXMLIterable"),
    "ilp": ("iterable.datatypes.ilp", "ILPIterable"),
    "annotatedcsv": ("iterable.datatypes.annotatedcsv", "AnnotatedCSVIterable"),
    "cdx": ("iterable.datatypes.cdx", "CDXIterable"),
    "warc": ("iterable.datatypes.warc", "WARCIterable"),
    "arc": ("iterable.datatypes.warc", "WARCIterable"),
    "ldif": ("iterable.datatypes.ldif", "LDIFIterable"),
    "mbox": ("iterable.datatypes.mbox", "MBOXIterable"),
    "ini": ("iterable.datatypes.ini", "INIIterable"),
    "properties": ("iterable.datatypes.ini", "INIIterable"),
    "conf": ("iterable.datatypes.ini", "INIIterable"),
    "edn": ("iterable.datatypes.edn", "EDNIterable"),
    "smile": ("iterable.datatypes.smile", "SMILEIterable"),
    "bencode": ("iterable.datatypes.bencode", "BencodeIterable"),
    "torrent": ("iterable.datatypes.bencode", "BencodeIterable"),
    "vcf": ("iterable.datatypes.vcf", "VCFIterable"),
    "vcard": ("iterable.datatypes.vcf", "VCFIterable"),
    "ical": ("iterable.datatypes.ical", "ICALIterable"),
    "ics": ("iterable.datatypes.ical", "ICALIterable"),
    "eml": ("iterable.datatypes.eml", "EMLIterable"),
    "mysqldump": ("iterable.datatypes.mysqldump", "MySQLDumpIterable"),
    "sql": ("iterable.datatypes.mysqldump", "MySQLDumpIterable"),
    "pgcopy": ("iterable.datatypes.pgcopy", "PGCopyIterable"),
    "copy": ("iterable.datatypes.pgcopy", "PGCopyIterable"),
    "hocon": ("iterable.datatypes.hocon", "HOCONIterable"),
    "flexbuffers": ("iterable.datatypes.flexbuffers", "FlexBuffersIterable"),
    "flexbuf": ("iterable.datatypes.flexbuffers", "FlexBuffersIterable"),
    "asn1": ("iterable.datatypes.asn1", "ASN1Iterable"),
    "der": ("iterable.datatypes.asn1", "ASN1Iterable"),
    "mhtml": ("iterable.datatypes.mhtml", "MHTMLIterable"),
    "mht": ("iterable.datatypes.mhtml", "MHTMLIterable"),
    "ltsv": ("iterable.datatypes.ltsv", "LTSVIterable"),
    "px": ("iterable.datatypes.px", "PXIterable"),
    "kml": ("iterable.datatypes.kml", "KMLIterable"),
    "kmz": ("iterable.datatypes.kmz", "KMZIterable"),
    "gpx": ("iterable.datatypes.gpx", "GPXIterable"),
    "gml": ("iterable.datatypes.gml", "GMLIterable"),
    "shapefile": ("iterable.datatypes.shapefile", "ShapefileIterable"),
    "shp": ("iterable.datatypes.shapefile", "ShapefileIterable"),
    "geopackage": ("iterable.datatypes.geopackage", "GeoPackageIterable"),
    "gpkg": ("iterable.datatypes.geopackage", "GeoPackageIterable"),
    "csvw": ("iterable.datatypes.csvw", "CSVWIterable"),
    "rdata": ("iterable.datatypes.rdata", "RDataIterable"),
    "rda": ("iterable.datatypes.rdata", "RDataIterable"),
    "rds": ("iterable.datatypes.rds", "RDSIterable"),
    "lance": ("iterable.datatypes.lance", "LanceIterable"),
    "pcap": ("iterable.datatypes.pcap", "PCAPIterable"),
    "pcapng": ("iterable.datatypes.pcap", "PCAPIterable"),
    "nc": ("iterable.datatypes.netcdf", "NetCDFIterable"),
    "netcdf": ("iterable.datatypes.netcdf", "NetCDFIterable"),
    "mvt": ("iterable.datatypes.mvt", "MVTIterable"),
    "pbf": ("iterable.datatypes.mvt", "MVTIterable"),
    "topojson": ("iterable.datatypes.topojson", "TopoJSONIterable"),
    "feed": ("iterable.datatypes.feed", "FeedIterable"),
    "atom": ("iterable.datatypes.feed", "FeedIterable"),
    "rss": ("iterable.datatypes.feed", "FeedIterable"),
    "dxf": ("iterable.datatypes.dxf", "DXFIterable"),
    "libsvm": ("iterable.datatypes.libsvm", "LIBSVMIterable"),
    "npy": ("iterable.datatypes.numpy", "NumPyIterable"),
    "npz": ("iterable.datatypes.numpy", "NumPyIterable"),
    "html": ("iterable.datatypes.html", "HTMLIterable"),
    "htm": ("iterable.datatypes.html", "HTMLIterable"),
    "arff": ("iterable.datatypes.arff", "ARFFIterable"),
    "trig": ("iterable.datatypes.trig", "TriGIterable"),
    "n3": ("iterable.datatypes.n3", "N3Iterable"),
    "trix": ("iterable.datatypes.trix", "TriXIterable"),
    "xlsb": ("iterable.datatypes.xlsb", "XLSBIterable"),
    "fasta": ("iterable.datatypes.fasta", "FASTAIterable"),
    "fa": ("iterable.datatypes.fasta", "FASTAIterable"),
    "fna": ("iterable.datatypes.fasta", "FASTAIterable"),
    "faa": ("iterable.datatypes.fasta", "FASTAIterable"),
    "fastq": ("iterable.datatypes.fastq", "FASTQIterable"),
    "fq": ("iterable.datatypes.fastq", "FASTQIterable"),
    "graphml": ("iterable.datatypes.graphml", "GraphMLIterable"),
    "gexf": ("iterable.datatypes.gexf", "GEXFIterable"),
    "dot": ("iterable.datatypes.dot", "DOTIterable"),
    "gv": ("iterable.datatypes.dot", "DOTIterable"),
    "bam": ("iterable.datatypes.bam", "BAMIterable"),
    "sam": ("iterable.datatypes.sam", "SAMIterable"),
    "vortex": ("iterable.datatypes.vortex", "VortexIterable"),
    "vtx": ("iterable.datatypes.vortex", "VortexIterable"),
    # Usable via explicit format override: iterableargs={"format": "zipxml", "tagname": ...}
    "zipxml": ("iterable.datatypes.zipxml", "ZIPXMLSource"),
}

CODEC_REGISTRY: dict[str, tuple[str, str]] = {
    "bz2": ("iterable.codecs.bz2codec", "BZIP2Codec"),
    "gz": ("iterable.codecs.gzipcodec", "GZIPCodec"),
    "lz4": ("iterable.codecs.lz4codec", "LZ4Codec"),
    "xz": ("iterable.codecs.lzmacodec", "LZMACodec"),
    "lzma": ("iterable.codecs.lzmacodec", "LZMACodec"),
    "zip": ("iterable.codecs.zipcodec", "ZIPCodec"),
    "br": ("iterable.codecs.brotlicodec", "BrotliCodec"),
    "zstd": ("iterable.codecs.zstdcodec", "ZSTDCodec"),
    "zst": ("iterable.codecs.zstdcodec", "ZSTDCodec"),
    "snappy": ("iterable.codecs.snappycodec", "SnappyCodec"),
    "sz": ("iterable.codecs.snappycodec", "SnappyCodec"),
    "lzo": ("iterable.codecs.lzocodec", "LZOCodec"),
    "lzop": ("iterable.codecs.lzocodec", "LZOCodec"),
}

# Formats that are read-only (do not support write operations)
# This set includes formats that explicitly raise WriteNotSupportedError
# or use the base class default (which also raises WriteNotSupportedError)
READ_ONLY_FORMATS: set[str] = {
    # Formats that explicitly raise WriteNotSupportedError
    "arff",
    "delta",
    "feed",
    "atom",  # alias for feed
    "rss",  # alias for feed
    "flatbuffers",
    "hdf5",
    "html",
    "htm",  # alias for html
    "hudi",
    "iceberg",
    "ods",
    "pcap",
    "px",
    "rdata",
    "rds",
    "sas",
    "sas7bdat",  # alias for sas
    "spss",
    "sav",  # alias for spss
    "stata",
    "dta",  # alias for stata
    # Formats that use base class default (raises WriteNotSupportedError)
    "avro",
    "dbf",
    "dxf",
    "mvt",
    "pbf",  # alias for mvt
    "netcdf",
    "cdf",
    "nc",  # alias for netcdf
    "psv",
    "xls",
    "xlsx",
    "xml",
    "zipped",
    "zipxml",
    "kmz",
    "gpx",
    # Bioinformatics formats (read-only)
    "fasta",
    "fa",  # alias for fasta
    "fna",  # alias for fasta
    "faa",  # alias for fasta
    "fastq",
    "fq",  # alias for fastq
    "bam",
    "sam",
    # RDF formats (read-only)
    "trig",
    "n3",
    "trix",
    # Graph formats (read-only)
    "graphml",
    "gexf",
    "dot",
    "gv",  # alias for dot
    # Spreadsheet formats (read-only)
    "xlsb",
}


def _datatype_class(ext: str) -> type[BaseIterable]:
    """Get datatype class for extension (with plugin support)."""
    registry = _get_format_registry()
    if ext not in registry:
        raise ValueError(f"Unknown format: {ext}")
    module_path, symbol = registry[ext]
    return _load_symbol(module_path, symbol)


def _codec_class(ext: str) -> type[BaseCodec]:
    """Get codec class for extension (with plugin support)."""
    registry = _get_codec_registry()
    if ext not in registry:
        raise ValueError(f"Unknown codec: {ext}")
    module_path, symbol = registry[ext]
    return _load_symbol(module_path, symbol)


class FileTypeResult(TypedDict, total=False):
    """Result of file type detection"""

    filename: str
    success: bool
    codec: type[BaseCodec] | None
    datatype: type[BaseIterable] | None
    confidence: float  # Confidence score 0.0-1.0, higher is more confident
    detection_method: str  # "filename", "magic_number", or "heuristic"


class CompressionResult(TypedDict):
    """Result of compression detection"""

    filename: str
    success: bool
    compression: type[BaseCodec] | None
    codec: type[BaseCodec] | None
    datatype: type[BaseIterable] | None


TEXT_DATA_TYPES = [
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
]


FLAT_TYPES = [
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
]

ENGINES = ["internal", "duckdb"]

# DuckDB engine can read many file formats directly via DuckDB, but we keep this
# allowlist conservative and aligned with tests/docs.
DUCKDB_SUPPORTED_TYPES = ["csv", "jsonl", "ndjson", "json", "parquet"]
DUCKDB_SUPPORTED_CODECS = ["gz", "zstd", "zst"]


def is_flat(filename: str | None = None, filetype: str | None = None) -> bool:
    """Returns True if file is flat data file"""
    if filetype is not None:
        if filetype in FLAT_TYPES:
            return True
    elif filename is not None:
        parts = filename.lower().rsplit(".", 2)
        if len(parts) == 2:
            if parts[1] in FLAT_TYPES:
                return True
        elif len(parts) > 2:
            if parts[1] in FLAT_TYPES:
                return True
    return False


def detect_file_type_from_content(fileobj, peek_size: int = 8192) -> tuple[str, float, str] | None:
    """Detect file type from content (magic numbers and heuristics).

    Args:
        fileobj: File-like object to read from
        peek_size: Number of bytes to read for detection

    Returns:
        Tuple of (format_id, confidence, method) if detected, None otherwise
        - format_id: Format identifier string
        - confidence: Confidence score (0.0-1.0), higher is more confident
        - method: Detection method ("magic_number" or "heuristic")
    """
    try:
        # Save current position
        original_pos = fileobj.tell()
        peek = fileobj.read(peek_size)
        fileobj.seek(original_pos)

        if len(peek) == 0:
            return None

        # Binary format detection (magic numbers) - High confidence (0.95-0.99)
        # Parquet
        if peek.startswith(b"PAR1"):
            return ("parquet", 0.99, "magic_number")

        # ORC
        if peek.startswith(b"ORC"):
            return ("orc", 0.99, "magic_number")

        # Vortex
        if peek.startswith(b"VTXF"):
            return ("vortex", 0.99, "magic_number")

        # PCAP/PCAPNG
        if len(peek) >= 4:
            # Standard PCAP: magic number can be big-endian (0xa1b2c3d4) or little-endian (0xd4c3b2a1)
            if peek[:4] == b"\xa1\xb2\xc3\xd4" or peek[:4] == b"\xd4\xc3\xb2\xa1":
                return ("pcap", 0.99, "magic_number")
            # PCAPNG: section header block starts with 0x0a0d0d0a
            if peek[:4] == b"\x0a\x0d\x0d\x0a":
                return ("pcapng", 0.99, "magic_number")

        # ZIP-based formats (XLSX, DOCX, etc.)
        if peek.startswith(b"PK\x03\x04"):
            # Check for specific ZIP-based formats
            if b"xl/" in peek[:100] or b"[Content_Types].xml" in peek[:200]:
                return ("xlsx", 0.95, "magic_number")  # Slightly lower - ZIP structure analysis
            if b"word/" in peek[:100]:
                return ("docx", 0.95, "magic_number")  # Not in registry, but detectable
            # Generic ZIP - could be many formats
            return ("zip", 0.90, "magic_number")  # Lower confidence - generic ZIP

        # Arrow/Feather
        if peek.startswith(b"ARROW1"):
            return ("arrow", 0.99, "magic_number")

        # Text format detection (heuristics)
        try:
            # Try to decode as UTF-8
            text = peek.decode("utf-8", errors="ignore")
            text_stripped = text.strip()

            # JSON detection - Medium-high confidence (0.85-0.90)
            if text_stripped.startswith("{") or text_stripped.startswith("["):
                # Try to parse as JSON to confirm
                try:
                    import json

                    json.loads(text_stripped[:1000])  # Try parsing first part
                    return ("json", 0.90, "heuristic")  # High confidence - valid JSON parsed
                except (ValueError, json.JSONDecodeError):
                    # Might be JSONL - check if first line is valid JSON
                    first_line = text_stripped.split("\n")[0].strip()
                    if first_line.startswith("{") or first_line.startswith("["):
                        try:
                            json.loads(first_line)
                            return ("jsonl", 0.80, "heuristic")  # Medium confidence - single line
                        except (ValueError, json.JSONDecodeError):
                            pass

            # CSV detection (heuristics) - Medium confidence (0.75-0.85)
            if "," in text[:100] or "\t" in text[:100]:
                # Check if it looks like CSV (has consistent delimiter)
                lines = text.split("\n")[:5]
                if len(lines) >= 2:
                    # Check if delimiter is consistent
                    delimiters = [",", "\t", "|", ";"]
                    for delim in delimiters:
                        if delim in lines[0] and delim in lines[1]:
                            counts_0 = lines[0].count(delim)
                            counts_1 = lines[1].count(delim)
                            # Allow some variance (headers might have different structure)
                            if abs(counts_0 - counts_1) <= 2 and counts_0 > 0:
                                format_id = "csv" if delim == "," else "tsv" if delim == "\t" else "psv"
                                # Higher confidence if delimiter is very consistent
                                confidence = 0.85 if abs(counts_0 - counts_1) == 0 else 0.75
                                return (format_id, confidence, "heuristic")

            # JSONL detection (each line is JSON) - Medium-high confidence (0.80-0.90)
            lines = text.split("\n")[:10]
            jsonl_count = 0
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                try:
                    import json

                    json.loads(line)
                    jsonl_count += 1
                except (ValueError, json.JSONDecodeError):
                    break
            if jsonl_count >= 3:  # At least 3 valid JSON lines
                # Higher confidence with more valid lines
                confidence = min(0.90, 0.70 + (jsonl_count * 0.05))
                return ("jsonl", confidence, "heuristic")

        except UnicodeDecodeError:
            # Binary format, already checked above
            pass

        return None
    except Exception:
        # If anything fails, return None (fallback to filename detection)
        return None


def detect_file_type(filename: str, fileobj=None, debug: bool = False) -> FileTypeResult:
    """Detects file type and compression codec from filename and/or content

    Args:
        filename: Path to the file to detect
        fileobj: Optional file-like object for content-based detection
        debug: If True, enable verbose debug logging

    Returns:
        FileTypeResult dictionary with detection results

    Raises:
        ValueError: If filename is empty or invalid
    """
    if not filename:
        raise ValueError("Filename cannot be empty")

    if debug or is_debug_enabled():
        format_detection_logger.debug(f"Detecting file type for: {filename}")

    result: FileTypeResult = {
        "filename": filename,
        "success": False,
        "codec": None,
        "datatype": None,
        "confidence": 0.0,
        "detection_method": "none",
    }

    # First, try filename-based detection - High confidence (1.0)
    parts = filename.lower().rsplit(".", 2)
    if debug or is_debug_enabled():
        format_detection_logger.debug(f"File extension parts: {parts}")

    format_registry = _get_format_registry()
    codec_registry = _get_codec_registry()

    if len(parts) == 2:
        if parts[-1] in format_registry:
            result["datatype"] = _datatype_class(parts[-1])
            result["success"] = True
            result["confidence"] = 1.0
            result["detection_method"] = "filename"
            if debug or is_debug_enabled():
                format_detection_logger.debug(
                    f"Detected format from extension: {parts[-1]} (confidence: 1.0, method: filename)"
                )
    elif len(parts) > 2:
        if parts[-2] in format_registry and parts[-1] in codec_registry:
            result["datatype"] = _datatype_class(parts[-2])
            result["success"] = True
            result["codec"] = _codec_class(parts[-1])
            result["confidence"] = 1.0
            result["detection_method"] = "filename"
            if debug or is_debug_enabled():
                format_detection_logger.debug(
                    f"Detected format from extension: {parts[-2]} with codec {parts[-1]} "
                    f"(confidence: 1.0, method: filename)"
                )
        elif parts[-1] in format_registry:
            result["datatype"] = _datatype_class(parts[-1])
            result["success"] = True
            result["confidence"] = 1.0
            result["detection_method"] = "filename"
            if debug or is_debug_enabled():
                format_detection_logger.debug(
                    f"Detected format from extension: {parts[-1]} (confidence: 1.0, method: filename)"
                )

    # If filename detection failed and we have a file object, try content-based detection
    if not result["success"] and fileobj is not None:
        if debug or is_debug_enabled():
            format_detection_logger.debug("Extension detection failed, trying content-based detection")
        detection_result = detect_file_type_from_content(fileobj)
        if detection_result:
            detected_format, confidence, method = detection_result
            format_registry = _get_format_registry()
            if detected_format and detected_format in format_registry:
                result["datatype"] = _datatype_class(detected_format)
                result["success"] = True
                result["confidence"] = confidence
                result["detection_method"] = method
                if debug or is_debug_enabled():
                    format_detection_logger.debug(
                        f"Content-based detection: {detected_format} (confidence: {confidence:.2f}, method: {method})"
                    )

    if debug or is_debug_enabled():
        if result["success"]:
            format_detection_logger.debug(
                f"Detection successful: format={result['datatype'].__name__ if result['datatype'] else None}, "
                f"codec={result['codec'].__name__ if result['codec'] else None}, "
                f"confidence={result['confidence']:.2f}, method={result['detection_method']}"
            )
        else:
            format_detection_logger.debug("Detection failed: no matching format found")

    return result


def detect_compression(filename: str) -> CompressionResult:
    """Detects compression codec from filename

    Args:
        filename: Path to the file to detect compression for

    Returns:
        CompressionResult dictionary with detection results

    Raises:
        ValueError: If filename is empty or invalid
    """
    if not filename:
        raise ValueError("Filename cannot be empty")

    result: CompressionResult = {
        "filename": filename,
        "success": False,
        "compression": None,
        "codec": None,
        "datatype": None,
    }
    parts = filename.lower().rsplit(".", 2)
    codec_registry = _get_codec_registry()
    if len(parts) == 2:
        if parts[-1] in codec_registry:
            result["compression"] = _codec_class(parts[-1])
            result["success"] = True
    elif len(parts) > 2:
        if parts[-1] in codec_registry:
            result["compression"] = _codec_class(parts[-1])
            result["success"] = True
    return result


def detect_encoding_any(filename: str, limit: int = 1000000) -> dict:
    """Detects encoding of any data file including compressed

    Args:
        filename: Path to the file to detect encoding for
        limit: Maximum bytes to read for detection (default: 1000000)

    Returns:
        Dictionary with encoding detection results from chardet containing:
        - 'encoding': Detected encoding name
        - 'confidence': Confidence score (0.0 to 1.0)
        - 'language': Detected language (if available)

    Raises:
        FileNotFoundError: If file does not exist
        ValueError: If filename is empty
        IOError: If file cannot be read
    """
    if not filename:
        raise ValueError("Filename cannot be empty")

    import os

    if not os.path.exists(filename):
        raise FileNotFoundError(
            f"File not found: '{filename}'. Please check that the file exists and the path is correct."
        )

    result = detect_file_type(filename)
    fileobj = None
    codec = None

    try:
        if result["success"]:
            if result["codec"] is not None:
                try:
                    codec = result["codec"](filename, open_it=True)
                    fileobj = codec.fileobj()
                except Exception as e:
                    raise OSError(
                        f"Failed to open compressed file '{filename}' with codec '{result['codec']}'. Error: {str(e)}"
                    ) from e
        if fileobj is None:
            try:
                fileobj = open(filename, "rb")
            except OSError as e:
                raise OSError(
                    f"Cannot read file '{filename}'. "
                    f"Please check file permissions and that the file is not corrupted. "
                    f"Error: {str(e)}"
                ) from e

        chunk = fileobj.read(limit)
        if not chunk:
            raise ValueError(f"File '{filename}' appears to be empty")

        detected = chardet.detect(chunk)
        if not detected or detected.get("encoding") is None:
            raise ValueError(
                f"Could not detect encoding for file '{filename}'. "
                f"The file may be binary or use an unsupported encoding."
            )

        return detected
    finally:
        if codec is not None:
            try:
                codec.close()
            except Exception:
                pass
        elif fileobj is not None:
            try:
                fileobj.close()
            except Exception:
                pass


# Cloud storage URI schemes supported
CLOUD_STORAGE_SCHEMES = {
    "s3": "s3fs",  # Amazon S3
    "s3a": "s3fs",  # Amazon S3 (alternative)
    "gs": "gcsfs",  # Google Cloud Storage
    "gcs": "gcsfs",  # Google Cloud Storage (alternative)
    "az": "adlfs",  # Azure Blob Storage
    "abfs": "adlfs",  # Azure Blob File System
    "abfss": "adlfs",  # Azure Blob File System (secure)
}


def _is_cloud_storage_uri(filename: str) -> bool:
    """Check if filename is a cloud storage URI.

    Args:
        filename: File path or URI to check

    Returns:
        True if filename is a cloud storage URI, False otherwise
    """
    if not filename or not isinstance(filename, str):
        return False
    # Check if it starts with a known cloud storage scheme
    for scheme in CLOUD_STORAGE_SCHEMES.keys():
        if filename.startswith(f"{scheme}://"):
            return True
    return False


def _get_cloud_backend(filename: str) -> str | None:
    """Get the required backend package for a cloud storage URI.

    Args:
        filename: Cloud storage URI

    Returns:
        Backend package name (e.g., 's3fs', 'gcsfs', 'adlfs') or None if not a cloud URI
    """
    if not _is_cloud_storage_uri(filename):
        return None
    for scheme, backend in CLOUD_STORAGE_SCHEMES.items():
        if filename.startswith(f"{scheme}://"):
            return backend
    return None


def open_iterable(
    filename: str,
    mode: Literal["r", "w", "rb", "wb"] = "r",
    engine: str = "internal",
    codecargs: CodecArgs | None = None,
    iterableargs: IterableArgs | None = None,
    debug: bool = False,
) -> BaseIterable:
    """Opens file and returns iterable object.

    Args:
        filename: Path to the file to open
        mode: File mode ('r' for read, 'w' for write, 'rb'/'wb' for binary)
        engine: Processing engine ('internal' or 'duckdb')
        codecargs: Dictionary with arguments for codec initialization
        iterableargs: Dictionary with arguments for iterable initialization
        debug: If True, enable verbose debug logging

    Returns:
        Iterable object for the detected file type

    Raises:
        ValueError: If engine is invalid, filename is empty, or DuckDB engine doesn't support the format/codec
        FileNotFoundError: If file does not exist (in read mode)
        RuntimeError: If file type cannot be detected or format is not supported

    Example:
        >>> source = open_iterable('data.csv.gz')  # doctest: +SKIP
        >>> with source:  # doctest: +SKIP
        ...     for row in source:  # doctest: +SKIP
        ...         print(row)  # doctest: +SKIP
    """
    import os

    # Normalize path-like (e.g. pathlib.Path) to str for .lower() and path checks
    if not isinstance(filename, str):
        filename = os.fspath(filename) if hasattr(filename, "__fspath__") else str(filename)

    if debug or is_debug_enabled():
        file_io_logger.debug(f"Opening file: {filename} (mode: {mode}, engine: {engine})")

    if not filename:
        raise ValueError("Filename cannot be empty")

    # Enable debug mode if requested
    if debug:
        from .debug import enable_debug_mode

        enable_debug_mode()

    # Pass debug flag to iterableargs for downstream use
    if iterableargs is None:
        iterableargs = {}
    iterableargs["_debug"] = debug or is_debug_enabled()

    # Validate the error policy early (before any file I/O) so an invalid value
    # is reported regardless of whether the target file exists.
    on_error = iterableargs.get("on_error", "raise")
    if on_error not in ("raise", "skip", "warn"):
        raise ValueError(
            f"Invalid 'on_error' value: '{on_error}'. Valid values are: 'raise', 'skip', 'warn'"
        )

    # Check if this is a database engine
    try:
        from ..db.iterable import DatabaseIterable

        if is_database_engine(engine):
            # This is a database engine - handle it separately
            driver_class = get_driver(engine)
            if driver_class is None:
                raise ValueError(f"Database engine '{engine}' is not available. Install the required driver.")

            # Create driver instance
            # For databases, filename is the connection string/URL
            driver = driver_class(source=filename, **iterableargs)

            # Wrap driver in DatabaseIterable
            return DatabaseIterable(driver)

    except ImportError:
        # Database module not available - continue with file-based logic
        pass

    if engine not in ["internal", "duckdb"]:
        raise ValueError(f"Engine must be 'internal', 'duckdb', or a registered database engine, got '{engine}'")

    # Normalize mode: 'rb' -> 'r', 'wb' -> 'w' for text-based formats
    normalized_mode = "r" if mode in ["r", "rb"] else "w"

    if codecargs is None:
        codecargs = {}
    if iterableargs is None:
        iterableargs = {}

    # Check if this is a cloud storage URI
    is_cloud_uri = _is_cloud_storage_uri(filename)
    cloud_stream = None
    storage_options = iterableargs.get("storage_options", {})

    # Handle cloud storage URIs
    if is_cloud_uri:
        try:
            import fsspec
        except ImportError:
            raise ImportError("Cloud storage support requires 'fsspec'. Install it with: pip install fsspec") from None

        # Check for specific backend if needed
        backend = _get_cloud_backend(filename)
        if backend:
            try:
                __import__(backend)
            except ImportError:
                raise ImportError(
                    f"Cloud storage URI '{filename}' requires '{backend}'. Install it with: pip install {backend}"
                ) from None

        # Open cloud storage file via fsspec
        try:
            # Determine binary mode for fsspec
            fsspec_mode = "rb" if mode in ["r", "rb"] else "wb"
            cloud_stream = fsspec.open(filename, mode=fsspec_mode, **storage_options)
            # Open the file-like object
            cloud_stream = cloud_stream.open()
        except Exception as e:
            if "NoCredentialsError" in str(type(e).__name__) or "credentials" in str(e).lower():
                raise RuntimeError(
                    f"Authentication failed for cloud storage URI '{filename}'. "
                    f"Please configure credentials via environment variables or storage_options. "
                    f"Error: {str(e)}"
                ) from e
            elif "NoSuchKey" in str(type(e).__name__) or "not found" in str(e).lower():
                raise FileNotFoundError(
                    f"File not found in cloud storage: '{filename}'. "
                    f"Please check that the file exists and the path is correct."
                ) from e
            else:
                raise RuntimeError(f"Failed to open cloud storage URI '{filename}': {str(e)}") from e

    # Check file existence for read mode (only for local files)
    elif normalized_mode == "r" and not os.path.exists(filename):
        raise FileNotFoundError(
            f"File not found: '{filename}'. Please check that the file exists and the path is correct."
        )

    # Try filename-based detection first
    result = detect_file_type(filename, debug=debug or is_debug_enabled())

    # If filename detection failed, try content-based detection
    if not result["success"] and normalized_mode == "r":
        if debug or is_debug_enabled():
            format_detection_logger.debug("Filename detection failed, attempting content-based detection")
        try:
            if is_cloud_uri and cloud_stream is not None:
                # For cloud storage, use the already-opened stream
                # Note: we need to read from the stream, but also need to reset it
                # For now, we'll try to detect from the stream if possible
                # Some cloud backends may not support seek, so we'll be careful
                try:
                    if hasattr(cloud_stream, "seekable") and cloud_stream.seekable():
                        pos = cloud_stream.tell()
                        result = detect_file_type(filename, fileobj=cloud_stream, debug=debug or is_debug_enabled())
                        cloud_stream.seek(pos)
                    else:
                        # Can't seek, skip content-based detection for cloud
                        pass
                except Exception:
                    # If seeking fails, skip content-based detection
                    pass
            else:
                with open(filename, "rb") as f:
                    result = detect_file_type(filename, fileobj=f, debug=debug or is_debug_enabled())
        except OSError:
            # Can't read file, fall through to error
            pass

    if not result["success"]:
        # Allow explicit format override (e.g. for atomic write temp files like .tmp)
        explicit_format = iterableargs.get("format")
        if explicit_format:
            format_id = explicit_format.lower()
            format_registry = _get_format_registry()
            if format_id in format_registry:
                result["datatype"] = _datatype_class(format_id)
                result["success"] = True
                result["codec"] = None
                result["confidence"] = 1.0
                result["detection_method"] = "explicit"

        if not result["success"]:
            from ..exceptions import FormatDetectionError

            raise FormatDetectionError(
                filename=filename,
                reason=f"Could not detect file type from filename or content. "
                f"Supported formats: {', '.join(sorted(set(DATATYPE_REGISTRY.keys())))}",
            )

    # Extract file type from filename for DuckDB validation (or from explicit format)
    if result.get("detection_method") == "explicit":
        detected_filetype = iterableargs.get("format", "").lower() or None
        detected_codec = None
    else:
        parts = filename.lower().rsplit(".", 2)
        detected_filetype = None
        detected_codec = None
        codec_registry = _get_codec_registry()
        if len(parts) == 2:
            detected_filetype = parts[-1]
        elif len(parts) > 2:
            detected_filetype = parts[-2] if parts[-1] in codec_registry else parts[-1]
            detected_codec = parts[-1] if parts[-1] in codec_registry else None

    # Validate DuckDB engine support
    if engine == "duckdb":
        if detected_filetype not in DUCKDB_SUPPORTED_TYPES:
            raise ValueError(
                f"DuckDB engine does not support file type '{detected_filetype}'. "
                f"Supported types: {', '.join(DUCKDB_SUPPORTED_TYPES)}. "
                f"Use engine='internal' for this file type."
            )
        if detected_codec is not None and detected_codec not in DUCKDB_SUPPORTED_CODECS:
            raise ValueError(
                f"DuckDB engine does not support compression codec '{detected_codec}'. "
                f"Supported codecs: {', '.join(DUCKDB_SUPPORTED_CODECS)}. "
                f"Use engine='internal' for this compression codec."
            )

    # Get datatype class name for better error messages
    datatype_name = result["datatype"].__name__ if result["datatype"] else "unknown"

    if debug or is_debug_enabled():
        codec_name = result["codec"].__name__ if result["codec"] else "none"
        file_io_logger.debug(f"Creating iterable: format={datatype_name}, codec={codec_name}, engine={engine}")

    try:
        # If we have a cloud storage stream, pass it appropriately
        if is_cloud_uri and cloud_stream is not None:
            if result["codec"] is not None and engine != "duckdb":
                # For codecs with cloud storage, pass the stream as fileobj
                # Codecs support fileobj parameter in their __init__
                codec = result["codec"](filename=filename, fileobj=cloud_stream, mode=mode, options=codecargs)
                iterable = result["datatype"](codec=codec, mode=normalized_mode, options=iterableargs)
            elif engine == "duckdb":
                # DuckDB engine does not support cloud storage directly
                raise ValueError(
                    "DuckDB engine does not support cloud storage URIs. Use engine='internal' for cloud storage files."
                )
            else:
                # Pass the stream directly to the datatype
                iterable = result["datatype"](stream=cloud_stream, mode=normalized_mode, options=iterableargs)
        elif result["codec"] is not None and engine != "duckdb":
            codec = result["codec"](filename=filename, mode=mode, options=codecargs)
            iterable = result["datatype"](codec=codec, mode=normalized_mode, options=iterableargs)
        elif engine == "duckdb":
            try:
                from ..engines.duckdb import DuckDBEngineIterable
            except ImportError as e:
                raise ImportError(
                    "DuckDB engine requires the 'duckdb' dependency. Install it with: pip install duckdb"
                ) from e
            iterable = DuckDBEngineIterable(filename=filename, mode=normalized_mode, options=iterableargs)
        else:
            iterable = result["datatype"](filename=filename, mode=normalized_mode, options=iterableargs)
    except FileNotFoundError as e:
        raise FileNotFoundError(
            f"File not found: '{filename}'. Please check that the file exists and the path is correct."
        ) from e
    except IterableDataError:
        # Library exceptions (e.g. ReadError for query validation, FormatParseError)
        # carry typed context and error codes; let them propagate unwrapped rather
        # than masking them behind a generic RuntimeError.
        raise
    except Exception as e:
        if debug or is_debug_enabled():
            file_io_logger.error(f"Failed to open file '{filename}': {e}", exc_info=True)
        raise RuntimeError(
            f"Failed to open file '{filename}' with format '{datatype_name}' "
            f"(detected type: '{detected_filetype}', codec: '{detected_codec or 'none'}'). "
            f"Error: {str(e)}"
        ) from e

    if debug or is_debug_enabled():
        file_io_logger.debug(f"Successfully opened file: {filename}")

    return iterable


# Convenience exports for easier imports
from ..convert.core import bulk_convert, convert  # noqa: E402

__all__ = ["open_iterable", "detect_file_type", "convert", "bulk_convert"]
