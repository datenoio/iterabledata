"""Curated one-line descriptions and doc URLs for all built-in formats."""

# ruff: noqa: E501
from __future__ import annotations

# Registry id -> doc filename when they differ (mirrors dev/scripts/generate_format_doc_stubs.py)
DOC_FILENAMES: dict[str, str] = {
    "arc": "warc.md",
    "ckpt": "flink.md",
    "copy": "pgcopy.md",
    "db": "sqlite.md",
    "ddb": "duckdb.md",
    "der": "asn1.md",
    "fa": "fa.md",
    "fbs": "flatbuffers.md",
    "flexbuf": "flexbuffers.md",
    "fq": "fq.md",
    "gpkg": "geopackage.md",
    "gv": "gv.md",
    "h5": "hdf5.md",
    "htm": "html.md",
    "ics": "ical.md",
    "log": "apachelog.md",
    "mp": "msgpack.md",
    "pb": "protobuf.md",
    "rdf": "rdfxml.md",
    "rio": "recordio.md",
    "seq": "sequencefile.md",
    "shp": "shapefile.md",
    "sql": "mysqldump.md",
    "ttl": "turtle.md",
    "ubj": "ubjson.md",
    "yml": "yaml.md",
}

DOCS_BASE = "docs/docs/formats"

FORMAT_DESCRIPTIONS: dict[str, str] = {
    "annotatedcsv": "Annotated CSV is a format used by InfluxDB for exporting time series data.",
    "arc": "WARC (Web ARChive) is a format for storing web archive data.",
    "arff": "ARFF (Attribute-Relation File Format) for machine learning datasets with typed attributes and relations.",
    "beam": "Apache Beam is a unified programming model for batch and streaming data processing.",
    "bencode": 'Bencode (pronounced "B-encode") is the encoding format used by the BitTorrent protocol.',
    "bson": "BSON (Binary JSON) is a binary-encoded serialization of JSON-like documents.",
    "capnp": "Cap'n Proto is a fast data interchange format and capability-based RPC system.",
    "cbor": "CBOR (Concise Binary Object Representation) is a binary data format inspired by JSON.",
    "cdf": "NASA Common Data Format for self-describing scientific array and metadata storage.",
    "cdx": "CDX (Capture inDeX) is a text format used for indexing web archive files (WARC/ARC).",
    "cef": "CEF (Common Event Format) is a standard format for log and event data used in SIEM systems.",
    "ckpt": "Apache Flink is a stream processing framework.",
    "copy": "PostgreSQL COPY format is a tab-delimited text format used by PostgreSQL for bulk data import/export.",
    "csvw": "CSVW (CSV on the Web) is a W3C standard for describing CSV files with metadata.",
    "db": "SQLite is a self-contained, serverless, zero-configuration, transactional SQL database engine.",
    "dbf": "DBF (dBase/FoxPro) is a database file format used by dBase, FoxPro, and other database systems.",
    "ddb": "DuckDB is an in-process analytical database management system designed for analytical workloads.",
    "der": "ASN.1 (Abstract Syntax Notation One) is a standard interface description language for defining data structures.",
    "dta": "Stata binary dataset format for statistical analysis (.dta).",
    "dxf": "AutoCAD Drawing Exchange Format for CAD vector graphics and entities.",
    "edn": "EDN (Extensible Data Notation) is a data format used in Clojure.",
    "eml": "EML (Email) format represents a single email message in RFC 822 format.",
    "fbs": "FlatBuffers is a cross-platform serialization library developed by Google.",
    "flexbuf": "FlexBuffers is a schemaless binary serialization format developed by Google as part of FlatBuffers.",
    "fwf": "Fixed Width Format (FWF) is a text format where each field has a fixed width in characters.",
    "gelf": "GELF (Graylog Extended Log Format) is a JSON-based log format used by Graylog and other log management systems.",
    "geojson": "GeoJSON is a format for encoding geographic data structures using JSON.",
    "tar": (
        "TAR is an archive container; the tar format iterates the data files inside a tarball "
        "(including .tar.gz/.tgz/.tar.bz2/.tar.xz), detecting each member's format."
    ),
    "geojsonseq": (
        "GeoJSON Text Sequences (RFC 8142) store one GeoJSON Feature per line, "
        "optionally prefixed with the record separator, for streaming geospatial data."
    ),
    "gml": "GML (Geography Markup Language) is an XML-based standard for encoding geographic information.",
    "gpkg": "GeoPackage is an open, portable, self-describing format for transferring geospatial information.",
    "gv": "Graphviz DOT graph description language for nodes and edges.",
    "h5": "HDF5 (Hierarchical Data Format version 5) is a data model, library, and file format for storing and managing data.",
    "hocon": "HOCON (Human-Optimized Config Object Notation) is a configuration file format developed by Lightbend.",
    "htm": "HTML (HyperText Markup Language) is the standard markup language for web pages.",
    "hudi": "Apache Hudi is a data lake platform that brings stream processing to data lakes.",
    "ics": "iCal (iCalendar) is a standard format (RFC 5545) for calendar data exchange.",
    "ilp": "ILP (InfluxDB Line Protocol) is a text-based format used by InfluxDB for writing time series data.",
    "ini": "INI (Initialization) format is a simple configuration file format used for storing application settings.",
    "ion": "Ion is a richly-typed, self-describing, hierarchical data serialization format.",
    "jsonld": "JSON-LD (JSON for Linking Data) is a method of encoding Linked Data using JSON.",
    "kafka": "Apache Kafka is a distributed streaming platform.",
    "kml": "KML (Keyhole Markup Language) is an XML-based format for representing geographic data.",
    "kmz": "Compressed KML archive (ZIP) for geographic placemarks, paths, and overlays.",
    "lance": "Lance is a modern columnar data format designed to optimize machine learning and data science workflows.",
    "ldif": "LDIF (LDAP Data Interchange Format) is a text format for representing LDAP directory entries.",
    "libsvm": "LIBSVM sparse feature vector format for machine learning training data.",
    "log": "Apache Log format is used by Apache HTTP Server for logging HTTP requests.",
    "ltsv": "LTSV (Labeled Tab-Separated Values) is a line-based format with tab-separated key-value pairs.",
    "mbox": "MBOX is a format for storing collections of email messages.",
    "mht": "MHTML web archive bundling HTML and embedded resources in a single file.",
    "mp": "MessagePack is an efficient binary serialization format that's like JSON but faster and more compact.",
    "mvt": "Mapbox Vector Tiles binary format for compact geographic feature layers.",
    "n3": "Notation3 RDF syntax extending Turtle with formulae and additional constructs.",
    "nc": "NetCDF self-describing array format for scientific and climate data.",
    "npy": "NumPy array binary format (.npy/.npz) for numerical tensor storage.",
    "nq": "N-Quads line-based RDF format with graph context per statement.",
    "nt": "N-Triples line-based RDF format with subject-predicate-object triples.",
    "ods": "ODS (OpenDocument Spreadsheet) is an open standard spreadsheet format used by LibreOffice and OpenOffice.",
    "pcap": "Packet capture format for network traffic analysis (.pcap/.pcapng).",
    "pickle": "Pickle is Python's native serialization format.",
    "psv": "PSV (Pipe-Separated Values) is a variant of CSV where fields are separated by pipe characters (`|`).",
    "pulsar": "Apache Pulsar is a distributed messaging and streaming platform.",
    "px": "PC-Axis (PX) is a statistical data format developed by Statistics Sweden and used by statistical offices.",
    "rda": "R workspace binary format storing multiple named R objects.",
    "rdf": "RDF/XML is an XML-based serialization format for RDF (Resource Description Framework) data.",
    "rds": "RDS (`.rds`) is R's native binary format for saving a single R object.",
    "rio": "RecordIO is a binary file format developed by Google for storing sequences of records.",
    "rss": "RSS/Atom syndication feed XML for published content items.",
    "sam": "SAM (Sequence Alignment/Map) text format for genomic read alignments.",
    "sas": "SAS (Statistical Analysis System) files are binary data files used by SAS software for statistical analysis.",
    "sav": "SPSS binary dataset format for survey and statistical data.",
    "seq": "SequenceFile is a flat file format used by Apache Hadoop for storing key-value pairs.",
    "shp": "Shapefile is a popular geospatial vector data format developed by ESRI.",
    "smile": "SMILE is a binary data format similar to JSON but more compact.",
    "sql": "MySQL Dump format is the output format of the `mysqldump` utility.",
    "ssv": "SSV (Semicolon-Separated Values) is a variant of CSV where fields are separated by semicolons (`;`).",
    "tfrecord": "TFRecord is a binary file format used by TensorFlow for storing training data.",
    "thrift": "Apache Thrift is a cross-language serialization framework.",
    "toml": "TOML (Tom's Obvious, Minimal Language) is a configuration file format designed to be easy to read and write.",
    "topojson": "TopoJSON encodes geographic topology with shared arcs for compact maps.",
    "trig": "TriG RDF format encoding named graphs with subject-predicate-object quads.",
    "trix": "TriX XML serialization of RDF triples for graph exchange.",
    "ttl": "Turtle is a text-based format for representing RDF (Resource Description Framework) data.",
    "txt": "TXT format handles plain text files line by line.",
    "ubj": "UBJSON (Universal Binary JSON) is a binary JSON format that's a drop-in replacement for JSON.",
    "vcf": "VCF (vCard) is a standard format (RFC 6350) for electronic business cards.",
    "genomic_vcf": "Genomic Variant Call Format (VCF/BCF) describing sequence variants; read via pysam.",
    "vtx": "Vortex columnar file format optimized for analytics workloads.",
    "xls": "XLS is the binary file format used by Microsoft Excel versions 97-2003.",
    "xlsb": "Excel Binary Workbook (.xlsb) for large spreadsheet data.",
    "yml": "YAML (YAML Ain't Markup Language) is a human-readable data serialization format.",
}


def doc_url_for(format_id: str) -> str | None:
    """Return documentation path for a format when a doc page exists."""
    name = DOC_FILENAMES.get(format_id, f"{format_id}.md")
    return f"{DOCS_BASE}/{name}"


def description_for(format_id: str) -> str | None:
    """Return the curated description for a format id."""
    return FORMAT_DESCRIPTIONS.get(format_id)
