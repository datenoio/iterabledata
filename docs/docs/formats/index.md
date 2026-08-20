---
sidebar_position: 1
title: Supported File Formats
description: Overview of all file formats supported by Iterable Data library
---

# Supported File Formats

This document provides an overview of all file formats supported by Iterable Data library. Each format has detailed documentation in the [formats directory](/formats/).

## Overview

Iterable Data supports a wide variety of data formats, from common formats like CSV and JSON to specialized formats like Parquet, Avro, and various statistical data formats. The library provides a unified interface for reading and writing these formats, with automatic format detection and support for compression codecs.

## Format Categories

- **Tabular Formats**: CSV, TSV, PSV, SSV, FWF, Excel (XLS/XLSX/XLSB), ODS, DBF
- **JSON Formats**: JSON, JSONL/NDJSON, GeoJSON, GeoJSONSeq, UBJSON, SMILE
- **Binary Formats**: Parquet, GeoParquet, Avro, ORC, Arrow/Feather, Lance, Vortex, Paimon Row, Paimon Mosaic, BSON, MessagePack, CBOR, Pickle
- **Statistical Formats**: SAS, Stata, SPSS, HDF5, RData, RDS, fst, PC-Axis (PX), ARFF, LIBSVM, NumPy
- **Columnar Storage**: Parquet, ORC, Arrow, Lance, Vortex, Paimon Mosaic, Delta Lake, Iceberg, Hudi, DuckLake, Zarr
- **Serialization Formats**: Protocol Buffers, Cap'n Proto, Thrift, FlatBuffers, FlexBuffers
- **XML/RDF Formats**: XML, RDF/XML, Turtle, N-Triples, N-Quads, N3, TriG, TriX, HDT
- **Geospatial Formats**: GeoJSON, GeoJSONSeq, GeoParquet, FlatGeobuf, KML, KMZ, GML, Shapefile, GeoPackage, FileGDB, MapInfo MIF, ASCII Grid, E00, LAS, BAG, CZML, GPX, MVT, TopoJSON, DXF, CSVW
- **Scientific Formats**: XYZ, CIF, PDB, MATLAB MAT, SEG-Y, GRIB2, miniSEED, NetCDF, CDF, FASTA, FASTQ, SAM, BAM, CRAM, BED, GFF3, GTF, genomic VCF, HDF5, Zarr
- **Business & ML Formats**: EDI, Access MDB, Lotus 1-2-3, WebDataset, fst, IATI
- **Graph Formats**: GraphML, GEXF, Graphviz DOT
- **Log Formats**: Apache Log, GELF, CEF, ILP, OTLP
- **Web Formats**: HTML, WARC, CDX, MHTML
- **Email Formats**: EML, MBOX
- **Configuration Formats**: YAML, TOML, INI, HOCON, EDN
- **Database Formats**: SQLite, DuckDB, MySQL Dump, PostgreSQL Copy
- **Other Formats**: iCal, VCF, LDIF, ASN.1, Bencode, TFRecord, SequenceFile, PCAP, RSS/Atom, TAR, ZIPXML
## Supported Formats Table

| Format | Extensions | Type | Flat Only | Read | Write | Dependencies | Documentation |
|--------|------------|------|-----------|------|-------|-------------|---------------|
| [Apache Avro](/formats/avro) | `.avro` | Binary | Yes | ✅ | ❌ | `avro-python3` | [Details](/formats/avro) |
| [Apache Arrow/Feather](/formats/arrow) | `.arrow`, `.feather` | Binary | Yes | ✅ | ✅ | `pyarrow` | [Details](/formats/arrow) |
| [Apache Log](/formats/apachelog) | `.log`, `.access.log` | Text | Yes | ✅ | ❌ | - | [Details](/formats/apachelog) |
| [Annotated CSV](/formats/annotatedcsv) | `.annotatedcsv` | Text | Yes | ✅ | ❌ | - | [Details](/formats/annotatedcsv) |
| [ASN.1](/formats/asn1) | `.asn1`, `.der` | Binary | No | ✅ | ✅ | `pyasn1` | [Details](/formats/asn1) |
| [Apache Beam](/formats/beam) | - | Binary | No | ✅ | ❌ | - | [Details](/formats/beam) |
| [Bencode](/formats/bencode) | `.torrent` | Binary | No | ✅ | ✅ | `bencode` or `bencodepy` | [Details](/formats/bencode) |
| [BSON](/formats/bson) | `.bson` | Binary | No | ✅ | ✅ | `bson` | [Details](/formats/bson) |
| [Cap'n Proto](/formats/capnp) | `.capnp` | Binary | No | ✅ | ✅ | `pycapnp` | [Details](/formats/capnp) |
| [CBOR](/formats/cbor) | `.cbor` | Binary | No | ✅ | ✅ | `cbor2` or `cbor` | [Details](/formats/cbor) |
| [CDX](/formats/cdx) | `.cdx` | Text | Yes | ✅ | ❌ | - | [Details](/formats/cdx) |
| [CEF](/formats/cef) | `.cef` | Text | Yes | ✅ | ❌ | - | [Details](/formats/cef) |
| [CSV](/formats/csv) | `.csv`, `.tsv` | Text | Yes | ✅ | ✅ | - | [Details](/formats/csv) |
| [CSVW](/formats/csvw) | `.csvw` | Text | Yes | ✅ | ✅ | - | [Details](/formats/csvw) |
| [DBF](/formats/dbf) | `.dbf` | Binary | Yes | ✅ | ❌ | `dbfread` | [Details](/formats/dbf) |
| [Delta Lake](/formats/delta) | - | Binary | Yes | ✅ | ✅ | `deltalake` | [Details](/formats/delta) |
| [DuckLake](/formats/ducklake) | - | Binary | Yes | ✅ | ✅ | `pyducklake` | [Details](/formats/ducklake) |
| [EDN](/formats/edn) | `.edn` | Text | No | ✅ | ✅ | `edn_format` or `pyedn` | [Details](/formats/edn) |
| [EML](/formats/eml) | `.eml` | Text | No | ✅ | ❌ | - | [Details](/formats/eml) |
| [FlatBuffers](/formats/flatbuffers) | `.fbs` | Binary | No | ✅ | ❌ | `flatbuffers` | [Details](/formats/flatbuffers) |
| [FlexBuffers](/formats/flexbuffers) | `.flexbuf` | Binary | No | ✅ | ✅ | `flexbuffers` | [Details](/formats/flexbuffers) |
| [Apache Flink](/formats/flink) | `.ckpt` | Binary | No | ✅ | ❌ | - | [Details](/formats/flink) |
| [Fixed Width](/formats/fwf) | `.fwf`, `.fixed` | Text | Yes | ✅ | ✅ | - | [Details](/formats/fwf) |
| [GELF](/formats/gelf) | `.gelf` | Text | Yes | ✅ | ✅ | - | [Details](/formats/gelf) |
| [GeoJSON](/formats/geojson) | `.geojson` | Text | No | ✅ | ✅ | `geojson` | [Details](/formats/geojson) |
| [GeoPackage](/formats/geopackage) | `.gpkg`, `.geopackage` | Binary | No | ✅ | ✅ | `fiona` | [Details](/formats/geopackage) |
| [GML](/formats/gml) | `.gml` | Text | No | ✅ | ✅ | `lxml` | [Details](/formats/gml) |
| [HDF5](/formats/hdf5) | `.hdf5`, `.h5` | Binary | Yes | ✅ | ✅ | `h5py` | [Details](/formats/hdf5) |
| [HOCON](/formats/hocon) | `.hocon` | Text | No | ✅ | ❌ | `pyhocon` | [Details](/formats/hocon) |
| [Apache Hudi](/formats/hudi) | - | Binary | Yes | ✅ | ❌ | `pyhudi` or `hudi` | [Details](/formats/hudi) |
| [iCal](/formats/ical) | `.ical`, `.ics` | Text | No | ✅ | ✅ | `icalendar` or `ics` | [Details](/formats/ical) |
| [Apache Iceberg](/formats/iceberg) | - | Binary | Yes | ✅ | ✅ | `pyiceberg` | [Details](/formats/iceberg) |
| [ILP](/formats/ilp) | `.ilp` | Text | Yes | ✅ | ✅ | - | [Details](/formats/ilp) |
| [INI](/formats/ini) | `.ini`, `.properties`, `.conf` | Text | No | ✅ | ✅ | - | [Details](/formats/ini) |
| [Ion](/formats/ion) | `.ion` | Binary | No | ✅ | ✅ | `ion-python` | [Details](/formats/ion) |
| [JSON](/formats/json) | `.json` | Text | No | ✅ | ✅ | - | [Details](/formats/json) |
| [JSON Lines](/formats/jsonl) | `.jsonl`, `.ndjson` | Text | No | ✅ | ✅ | - | [Details](/formats/jsonl) |
| [Apache Kafka](/formats/kafka) | - | Binary | No | ✅ | ✅ | `kafka-python` | [Details](/formats/kafka) |
| [KML](/formats/kml) | `.kml` | Text | No | ✅ | ✅ | `lxml` | [Details](/formats/kml) |
| [Lance](/formats/lance) | `.lance` | Binary | Yes | ✅ | ✅ | `lance` | [Details](/formats/lance) |
| [LDIF](/formats/ldif) | `.ldif` | Text | No | ✅ | ❌ | `ldif3` or `ldif` | [Details](/formats/ldif) |
| [MBOX](/formats/mbox) | `.mbox` | Text | No | ✅ | ❌ | - | [Details](/formats/mbox) |
| [MessagePack](/formats/msgpack) | `.msgpack`, `.mp` | Binary | No | ✅ | ✅ | `msgpack` | [Details](/formats/msgpack) |
| [MHTML](/formats/mhtml) | `.mhtml`, `.mht` | Text | No | ✅ | ❌ | - | [Details](/formats/mhtml) |
| [MySQL Dump](/formats/mysqldump) | `.sql`, `.mysqldump` | Text | Yes | ✅ | ❌ | - | [Details](/formats/mysqldump) |
| [N-Quads](/formats/nquads) | `.nq`, `.nquads` | Text | Yes | ✅ | ❌ | - | [Details](/formats/nquads) |
| [N-Triples](/formats/ntriples) | `.nt`, `.ntriples` | Text | Yes | ✅ | ❌ | - | [Details](/formats/ntriples) |
| [ODS](/formats/ods) | `.ods` | Binary | Yes | ✅ | ❌ | `odfpy` or `pyexcel-ods3` | [Details](/formats/ods) |
| [ORC](/formats/orc) | `.orc` | Binary | Yes | ✅ | ✅ | `pyorc` | [Details](/formats/orc) |
| [Parquet](/formats/parquet) | `.parquet` | Binary | Yes | ✅ | ✅ | `pyarrow` | [Details](/formats/parquet) |
| [Pickle](/formats/pickle) | `.pickle` | Binary | No | ✅ | ✅ | - | [Details](/formats/pickle) |
| [PostgreSQL Copy](/formats/pgcopy) | `.copy`, `.pgcopy` | Text | Yes | ✅ | ✅ | - | [Details](/formats/pgcopy) |
| [Protocol Buffers](/formats/protobuf) | `.pb`, `.protobuf` | Binary | No | ✅ | ✅ | `protobuf` | [Details](/formats/protobuf) |
| [PC-Axis (PX)](/formats/px) | `.px` | Text | Yes | ✅ | ❌ | - | [Details](/formats/px) |
| [Apache Pulsar](/formats/pulsar) | - | Binary | No | ✅ | ✅ | `pulsar-client` | [Details](/formats/pulsar) |
| [PSV](/formats/psv) | `.psv` | Text | Yes | ✅ | ✅ | - | [Details](/formats/psv) |
| [RDF/XML](/formats/rdfxml) | `.rdf`, `.rdf.xml` | Text | No | ✅ | ❌ | - | [Details](/formats/rdfxml) |
| [RData](/formats/rdata) | `.rdata`, `.RData`, `.rda` | Binary | Yes | ✅ | ❌ | `pyreadr` | [Details](/formats/rdata) |
| [RDS](/formats/rds) | `.rds` | Binary | Yes | ✅ | ❌ | `pyreadr` | [Details](/formats/rds) |
| [RecordIO](/formats/recordio) | `.rio`, `.recordio` | Binary | No | ✅ | ❌ | - | [Details](/formats/recordio) |
| [SAS](/formats/sas) | `.sas`, `.sas7bdat` | Binary | Yes | ✅ | ❌ | `pyreadstat` or `sas7bdat` | [Details](/formats/sas) |
| [SequenceFile](/formats/sequencefile) | `.seq`, `.sequencefile` | Binary | No | ✅ | ❌ | - | [Details](/formats/sequencefile) |
| [Shapefile](/formats/shapefile) | `.shp`, `.shapefile` | Binary | No | ✅ | ✅ | `pyshp` | [Details](/formats/shapefile) |
| [SMILE](/formats/smile) | `.smile` | Binary | No | ✅ | ✅ | `smile-json` | [Details](/formats/smile) |
| [SPSS](/formats/spss) | `.sav`, `.spss` | Binary | Yes | ✅ | ❌ | `pyreadstat` | [Details](/formats/spss) |
| [SQLite](/formats/sqlite) | `.db`, `.sqlite` | Binary | Yes | ✅ | ✅ | - | [Details](/formats/sqlite) |
| [DuckDB](/formats/duckdb) | `.duckdb`, `.ddb` | Binary | Yes | ✅ | ✅ | `duckdb` | [Details](/formats/duckdb) |
| [SSV](/formats/ssv) | `.ssv` | Text | Yes | ✅ | ✅ | - | [Details](/formats/ssv) |
| [Stata](/formats/stata) | `.dta`, `.stata` | Binary | Yes | ✅ | ❌ | `pyreadstat` | [Details](/formats/stata) |
| [TFRecord](/formats/tfrecord) | `.tfrecord`, `.tfrecords` | Binary | No | ✅ | ❌ | - | [Details](/formats/tfrecord) |
| [Apache Thrift](/formats/thrift) | `.thrift` | Binary | No | ✅ | ✅ | `thrift` | [Details](/formats/thrift) |
| [TOML](/formats/toml) | `.toml` | Text | No | ✅ | ✅ | `tomli`/`tomli-w` or `toml` | [Details](/formats/toml) |
| [Turtle](/formats/turtle) | `.ttl`, `.turtle` | Text | No | ✅ | ❌ | `rdflib` | [Details](/formats/turtle) |
| [TXT](/formats/txt) | `.txt`, `.text` | Text | Yes | ✅ | ✅ | - | [Details](/formats/txt) |
| [UBJSON](/formats/ubjson) | `.ubj`, `.ubjson` | Binary | No | ✅ | ✅ | `py-ubjson` | [Details](/formats/ubjson) |
| [VCF](/formats/vcf) | `.vcf`, `.vcard` | Text | No | ✅ | ❌ | `vobject` or `vcard` | [Details](/formats/vcf) |
| [Vortex](/formats/vortex) | `.vortex`, `.vtx` | Binary | Yes | ✅ | ✅ | `vortex-data` | [Details](/formats/vortex) |
| [Paimon tables](/formats/paimon) | - | Binary | Yes | ✅ | ✅ | `pypaimon` | [Details](/formats/paimon) |
| [Paimon Row](/formats/paimon-row) | `.row` | Binary | Yes | ✅ | ✅ | `zstandard` (`paimon-row`) | [Details](/formats/paimon-row) |
| [Paimon Mosaic](/formats/paimon-mosaic) | `.mosaic` | Binary | Yes | ✅ | ✅ | `paimon-mosaic` | [Details](/formats/paimon-mosaic) |
| [WARC](/formats/warc) | `.warc`, `.arc` | Binary | No | ✅ | ❌ | `warcio` | [Details](/formats/warc) |
| [XLS](/formats/xls) | `.xls` | Binary | Yes | ✅ | ❌ | `xlrd` | [Details](/formats/xls) |
| [XLSX](/formats/xlsx) | `.xlsx` | Binary | Yes | ✅ | ❌ | `openpyxl` | [Details](/formats/xlsx) |
| [XML](/formats/xml) | `.xml` | Text | No | ✅ | ❌ | `lxml` | [Details](/formats/xml) |
| [YAML](/formats/yaml) | `.yaml`, `.yml` | Text | No | ✅ | ✅ | `pyyaml` | [Details](/formats/yaml) |
| [ARFF](/formats/arff) | `.arff` | Text | Yes | ✅ | ❌ | `arff` | [Details](/formats/arff) |
| [ASCII Grid](/formats/asc) | `.asc` | Text | Yes | ✅ | ✅ | - | [Details](/formats/asc) |
| [BAG](/formats/bag) | `.bag` | Binary | No | ✅ | ❌ | `hdf5` (`h5py`) | [Details](/formats/bag) |
| [BAM](/formats/bam) | `.bam` | Binary | Yes | ✅ | ❌ | `alignment` | [Details](/formats/bam) |
| [CDF](/formats/cdf) | `.cdf` | Binary | No | ✅ | ❌ | `cdf` | [Details](/formats/cdf) |
| [CIF](/formats/cif) | `.cif` | Text | Yes | ✅ | ❌ | - | [Details](/formats/cif) |
| [CZML](/formats/czml) | `.czml` | Text | No | ✅ | ✅ | - | [Details](/formats/czml) |
| [DXF](/formats/dxf) | `.dxf` | Binary | No | ✅ | ❌ | `dxf` | [Details](/formats/dxf) |
| [E00](/formats/e00) | `.e00` | Text | No | ✅ | ❌ | - | [Details](/formats/e00) |
| [EDI](/formats/edi) | `.edi` | Text | No | ✅ | ❌ | - | [Details](/formats/edi) |
| [FA](/formats/fa) | `.fa`, `.fasta`, `.fna`, `.faa` | Text | Yes | ✅ | ❌ | - | [Details](/formats/fa) |
| [File Geodatabase](/formats/fgdb) | `.gdb`, `.fgdb` | Binary | No | ✅ | ❌ | `geospatial` | [Details](/formats/fgdb) |
| [FQ](/formats/fq) | `.fq`, `.fastq` | Text | Yes | ✅ | ❌ | - | [Details](/formats/fq) |
| [fst](/formats/fst) | `.fst` | Binary | Yes | ✅ | ❌ | `fst` | [Details](/formats/fst) |
| [GEXF](/formats/gexf) | `.gexf` | Text | No | ✅ | ❌ | `graph` | [Details](/formats/gexf) |
| [GPX](/formats/gpx) | `.gpx` | Text | No | ✅ | ❌ | `xml` | [Details](/formats/gpx) |
| [GRIB2](/formats/grib2) | `.grib2`, `.grb2`, `.grib` | Binary | No | ✅ | ❌ | `geophysical` | [Details](/formats/grib2) |
| [Graphml](/formats/graphml) | `.graphml` | Text | No | ✅ | ❌ | `graph` | [Details](/formats/graphml) |
| [GV](/formats/gv) | `.gv`, `.dot` | Text | No | ✅ | ❌ | `graph` | [Details](/formats/gv) |
| [HDT](/formats/hdt) | `.hdt` | Binary | No | ✅ | ❌ | `rdf` | [Details](/formats/hdt) |
| [IATI](/formats/iati) | `.iati`, `.iati.xml` | Text | No | ✅ | ❌ | `xml` | [Details](/formats/iati) |
| [Jsonld](/formats/jsonld) | `.jsonld` | Text | No | ✅ | ✅ | - | [Details](/formats/jsonld) |
| [KMZ](/formats/kmz) | `.kmz` | Binary | No | ✅ | ❌ | `geospatial` | [Details](/formats/kmz) |
| [LAS](/formats/las) | `.las` | Binary | No | ✅ | ❌ | `lidar` | [Details](/formats/las) |
| [LIBSVM](/formats/libsvm) | `.libsvm` | Text | Yes | ✅ | ✅ | - | [Details](/formats/libsvm) |
| [Lotus 1-2-3](/formats/lotus123) (`123`) | `.123`, `.wk1`, `.wks` | Binary | Yes | ✅ | ❌ | - | [Details](/formats/lotus123) |
| [LTSV](/formats/ltsv) | `.ltsv` | Text | No | ✅ | ✅ | - | [Details](/formats/ltsv) |
| [MATLAB MAT](/formats/mat) | `.mat` | Binary | Yes | ✅ | ❌ | `mat` | [Details](/formats/mat) |
| [Microsoft Access](/formats/mdb) | `.mdb`, `.accdb` | Binary | Yes | ✅ | ❌ | `access` | [Details](/formats/mdb) |
| [MapInfo MIF](/formats/mif) | `.mif` | Text | No | ✅ | ❌ | `geospatial` | [Details](/formats/mif) |
| [miniSEED](/formats/mseed) | `.mseed` | Binary | No | ✅ | ❌ | `geophysical` | [Details](/formats/mseed) |
| [MVT](/formats/mvt) | `.mvt`, `.pbf` | Binary | No | ✅ | ❌ | `mvt` | [Details](/formats/mvt) |
| [N3](/formats/n3) | `.n3` | Text | No | ✅ | ❌ | `rdf` | [Details](/formats/n3) |
| [NC](/formats/nc) | `.nc`, `.netcdf` | Binary | No | ✅ | ❌ | `netcdf` | [Details](/formats/nc) |
| [NPY](/formats/npy) | `.npy`, `.npz` | Binary | Yes | ✅ | ✅ | `npy` | [Details](/formats/npy) |
| [PCAP](/formats/pcap) | `.pcap`, `.pcapng` | Binary | No | ✅ | ❌ | `pcap` | [Details](/formats/pcap) |
| [PDB](/formats/pdb) | `.pdb` | Text | Yes | ✅ | ✅ | - | [Details](/formats/pdb) |
| [RSS](/formats/rss) | `.rss`, `.feed`, `.atom` | Text | No | ✅ | ❌ | `feed` | [Details](/formats/rss) |
| [SAM](/formats/sam) | `.sam` | Text | Yes | ✅ | ❌ | `alignment` | [Details](/formats/sam) |
| [SEG-Y](/formats/segy) | `.segy`, `.sgy` | Binary | No | ✅ | ❌ | `geophysical` | [Details](/formats/segy) |
| [TopoJSON](/formats/topojson) | `.topojson` | Text | No | ✅ | ✅ | `topojson` | [Details](/formats/topojson) |
| [TRIG](/formats/trig) | `.trig` | Text | No | ✅ | ❌ | `rdf` | [Details](/formats/trig) |
| [TRIX](/formats/trix) | `.trix` | Text | No | ✅ | ❌ | `rdf` | [Details](/formats/trix) |
| [WebDataset](/formats/webdataset) | `.tar` / `.wds` (`format=webdataset`) | Binary | No | ✅ | ❌ | - | [Details](/formats/webdataset) |
| [XLSB](/formats/xlsb) | `.xlsb` | Binary | Yes | ✅ | ❌ | `xlsb` | [Details](/formats/xlsb) |
| [XYZ](/formats/xyz) | `.xyz` | Text | Yes | ✅ | ✅ | - | [Details](/formats/xyz) |
| [Zipxml](/formats/zipxml) | `.zipxml` | Binary | No | ✅ | ❌ | - | [Details](/formats/zipxml) |
| [Zarr](/formats/zarr) | directory store | Binary | Yes | ✅ | ✅ | `zarr` | [Details](/formats/zarr) |
| [GeoParquet](/formats/geoparquet) | `.parquet` | Binary | Yes | ✅ | ✅ | `pyarrow` | [Details](/formats/geoparquet) |
| [GeoJSONSeq](/formats/geojsonseq) | `.geojsonl`, `.geojsons` | Text | No | ✅ | ✅ | - | [Details](/formats/geojsonseq) |
| [FlatGeobuf](/formats/flatgeobuf) | `.fgb` | Binary | No | ✅ | ❌ | `geospatial` | [Details](/formats/flatgeobuf) |
| [HTML](/formats/html) | `.html`, `.htm` | Text | Yes | ✅ | ❌ | `html` | [Details](/formats/html) |
| [TAR](/formats/tar) | `.tar`, `.tar.gz`, `.tgz` | Binary | No | ✅ | ❌ | - | [Details](/formats/tar) |
| [OTLP](/formats/otlp) | `.json` / protobuf | Binary | No | ✅ | ✅ | `otlp` | [Details](/formats/otlp) |
| [Genomic VCF/BCF](/formats/genomic_vcf) | `.vcf`, `.bcf` | Text/Binary | Yes | ✅ | ❌ | `bio` | [Details](/formats/genomic_vcf) |
| [CRAM](/formats/genomic-intervals) | `.cram` | Binary | Yes | ✅ | ❌ | `alignment` | [Details](/formats/genomic-intervals) |
| [BED](/formats/genomic-intervals) | `.bed` | Text | Yes | ✅ | ✅ | - | [Details](/formats/genomic-intervals) |
| [GFF3](/formats/genomic-intervals) | `.gff`, `.gff3` | Text | Yes | ✅ | ✅ | - | [Details](/formats/genomic-intervals) |
| [GTF](/formats/genomic-intervals) | `.gtf` | Text | Yes | ✅ | ✅ | - | [Details](/formats/genomic-intervals) |

## Compression Support

All formats can be used with compression codecs:
- **GZip** (`.gz`)
- **BZip2** (`.bz2`)
- **LZMA** (`.xz`, `.lzma`)
- **LZ4** (`.lz4`)
- **ZIP** (`.zip`)
- **Brotli** (`.br`)
- **ZStandard** (`.zst`, `.zstd`)
- **Snappy** (`.snappy`, `.sz`)
- **LZO** (`.lzo`, `.lzop`)
- **7-Zip** (`.7z`)

## Format Characteristics

### Flat vs Nested Data

- **Flat Only**: Formats that only support tabular/flat data structures (CSV, Parquet, Excel, etc.)
- **Nested Support**: Formats that support complex nested data structures (JSON, XML, BSON, etc.)

### Read/Write Support

- **✅ Read**: Format supports reading data
- **✅ Write**: Format supports writing data
- **❌**: Feature not supported (read-only format)

**Note**: Some formats are read-only and do not support write operations. Attempting to write to these formats will raise a `WriteNotSupportedError`. See the [Capability Matrix](/api/capabilities#read-only-formats) documentation for a complete list of read-only formats and how to check write support programmatically.

### Dependencies

Some formats require additional Python packages. Install them as needed:
- Most formats work out of the box
- Binary formats often require specific libraries (e.g., `pyarrow` for Parquet, `pyorc` for ORC)
- Specialized formats may need domain-specific libraries

## Usage

All formats can be opened using the unified `open_iterable()` function:

```python
from iterable import open_iterable

# Automatically detects format from file extension
with open_iterable('data.csv.gz') as source:
    for row in source:
        print(row)
```

For format-specific options, see individual format documentation pages.
