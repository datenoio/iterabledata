# Iterable Data

Iterable Data is a Python library for reading and writing data files row by row in a consistent, iterator-based interface. It provides a unified API for working with various data formats (CSV, JSON, Parquet, XML, etc.) similar to `csv.DictReader` but supporting many more formats.

This library simplifies data processing and conversion between formats while preserving complex nested data structures (unlike pandas DataFrames which require flattening).

## Features

- **Unified API**: Single interface for reading/writing multiple data formats
- **Automatic Format Detection**: Detects file type and compression from filename or content (magic numbers and heuristics)
- **Format Capability Reporting**: Programmatically query format capabilities (read/write/bulk/totals/streaming/tables)
- **Support for Compression**: Works seamlessly with compressed files
- **Preserves Nested Data**: Handles complex nested structures as Python dictionaries
- **DuckDB Integration**: Optional DuckDB engine for high-performance queries with pushdown optimizations
- **Pipeline Processing**: Built-in pipeline support for data transformation
- **Encoding Detection**: Automatic encoding and delimiter detection for text files
- **Bulk Operations**: Efficient batch reading and writing
- **Table Listing**: Discover available tables, sheets, and datasets in multi-table formats
- **Context Manager Support**: Use `with` statements for automatic resource cleanup
- **DataFrame Bridges**: Convert iterable data to Pandas, Polars, and Dask DataFrames with one-liner methods
- **Cloud Storage Support**: Direct access to S3, GCS, and Azure Blob Storage via URI schemes
- **Database Engine Support**: Read-only access to SQL and NoSQL databases (PostgreSQL, ClickHouse, MySQL, MongoDB, Elasticsearch, etc.) as iterable data sources
- **Atomic Writes**: Production-safe file writing with temporary files and atomic renames
- **Bulk File Conversion**: Convert multiple files at once using glob patterns or directories
- **Progress Tracking and Metrics**: Built-in progress bars, callbacks, and structured metrics objects
- **Error Handling Controls**: Configurable error policies and structured error logging
- **Type Hints and Type Safety**: Complete type annotations with typed helper functions for dataclasses and Pydantic models

## Supported File Types

### Core Formats

- **JSON** - Standard JSON files
- **JSONL/NDJSON** - JSON Lines format (one JSON object per line)
- **JSON-LD** - JSON for Linking Data (RDF format)
- **CSV/TSV** - Comma and tab-separated values
- **Annotated CSV** - CSV with type annotations and metadata
- **CSVW** - CSV on the Web (with metadata)
- **PSV/SSV** - Pipe and semicolon-separated values
- **LTSV** - Labeled Tab-Separated Values
- **FWF** - Fixed Width Format
- **XML** - XML files with configurable tag parsing
- **ZIP XML** - XML files within ZIP archives
- **HTML** - HTML files with table extraction

### Binary Formats

- **BSON** - Binary JSON format
- **MessagePack** - Efficient binary serialization
- **CBOR** - Concise Binary Object Representation
- **UBJSON** - Universal Binary JSON
- **SMILE** - Binary JSON variant
- **Bencode** - BitTorrent encoding format
- **Avro** - Apache Avro binary format (read & write)
- **Pickle** - Python pickle format

### Columnar & Analytics Formats

- **Parquet** - Apache Parquet columnar format
- **ORC** - Optimized Row Columnar format
- **Arrow/Feather** - Apache Arrow columnar format
- **Lance** - Modern columnar format optimized for ML and vector search
- **Vortex** - Modern columnar format with fast random access
- **Delta Lake** - Delta Lake format
- **Iceberg** - Apache Iceberg format
- **Hudi** - Apache Hudi format

### Database Formats

- **SQLite** - SQLite database files
- **DBF** - dBase/FoxPro database files
- **MySQL Dump** - MySQL dump files
- **PostgreSQL Copy** - PostgreSQL COPY format
- **DuckDB** - DuckDB database files

### Statistical Formats

- **SAS** - SAS data files
- **Stata** - Stata data files
- **SPSS** - SPSS data files
- **R Data** - R RDS and RData files
- **PX** - PC-Axis format
- **ARFF** - Attribute-Relation File Format (Weka format)

### Scientific Formats

- **NetCDF** - Network Common Data Form for scientific data
- **CDF** - NASA Common Data Format (space science)
- **HDF5** - Hierarchical Data Format

### Geospatial Formats

- **GeoJSON** - Geographic JSON format
- **GeoPackage** - OGC GeoPackage format
- **GML** - Geography Markup Language
- **KML** - Keyhole Markup Language
- **KMZ** - KML Zipped (ZIP archive containing KML)
- **GPX** - GPS Exchange Format (waypoints, routes, tracks)
- **Shapefile** - ESRI Shapefile format
- **MVT/PBF** - Mapbox Vector Tiles
- **TopoJSON** - Topology-preserving GeoJSON extension

### RDF & Semantic Formats

- **JSON-LD** - JSON for Linking Data
- **RDF/XML** - RDF in XML format
- **Turtle** - Terse RDF Triple Language
- **N-Triples** - Line-based RDF format
- **N-Quads** - N-Triples with context
- **TriG** - RDF Triple Graph format
- **N3** - Notation3 RDF format
- **TriX** - XML Triple RDF format

### Feed Formats

- **Atom** - Atom Syndication Format
- **RSS** - Rich Site Summary feed format

### Network Formats

- **PCAP** - Packet Capture format
- **PCAPNG** - PCAP Next Generation format

### Log & Event Formats

- **Apache Log** - Apache access/error logs
- **CEF** - Common Event Format
- **GELF** - Graylog Extended Log Format
- **WARC** - Web ARChive format
- **CDX** - Web archive index format
- **ILP** - InfluxDB Line Protocol
- **HTML** - HTML files with table extraction

### Email Formats

- **EML** - Email message format
- **MBOX** - Mailbox format
- **MHTML** - MIME HTML format

### Configuration Formats

- **INI** - INI configuration files
- **TOML** - Tom's Obvious Minimal Language
- **YAML** - YAML Ain't Markup Language
- **HOCON** - Human-Optimized Config Object Notation
- **EDN** - Extensible Data Notation

### Office Formats

- **XLS/XLSX** - Microsoft Excel files
- **XLSB** - Excel Binary format
- **ODS** - OpenDocument Spreadsheet

### CAD Formats

- **DXF** - AutoCAD Drawing Exchange Format

### Graph Formats

- **GraphML** - Graph Markup Language
- **GEXF** - Graph Exchange XML Format
- **DOT** - GraphViz DOT format

### Sequence & Alignment Formats

- **FASTA** - Sequence format (protein/nucleotide)
- **FASTQ** - Sequence with quality format
- **SAM** - Sequence Alignment/Map (text)
- **BAM** - Binary SAM format

### Streaming & Big Data Formats

- **Kafka** - Apache Kafka format
- **Pulsar** - Apache Pulsar format
- **Flink** - Apache Flink format
- **Beam** - Apache Beam format
- **RecordIO** - RecordIO format
- **SequenceFile** - Hadoop SequenceFile
- **TFRecord** - TensorFlow Record format

### Protocol & Serialization Formats

- **Protocol Buffers** - Google Protocol Buffers
- **Cap'n Proto** - Cap'n Proto serialization
- **FlatBuffers** - FlatBuffers serialization
- **FlexBuffers** - FlexBuffers format
- **Thrift** - Apache Thrift format
- **ASN.1** - ASN.1 encoding format
- **Ion** - Amazon Ion format

### Other Formats

- **VCF** - Variant Call Format (genomics)
- **iCal** - iCalendar format
- **LDIF** - LDAP Data Interchange Format
- **TXT** - Plain text files

## Supported Compression Codecs

- **GZip** (.gz)
- **BZip2** (.bz2)
- **LZMA** (.xz, .lzma)
- **LZ4** (.lz4)
- **ZIP** (.zip)
- **Brotli** (.br)
- **ZStandard** (.zst, .zstd)
- **Snappy** (.snappy, .sz)
- **LZO** (.lzo, .lzop)
- **SZIP** (.sz)
- **7z** (.7z)

## Requirements

Python 3.10+

## Installation

```bash
pip install iterabledata
```

Or install from source:

```bash
git clone https://github.com/datenoio/iterabledata.git
cd iterabledata
pip install .
```

### Optional Dependencies

IterableData supports optional extras for additional features:

```bash
# AI-powered documentation generation
pip install iterabledata[ai]

# Database ingestion (PostgreSQL, ClickHouse, MongoDB, MySQL, Elasticsearch, etc.)
pip install iterabledata[db]

# RDF formats (TriG, N3, TriX)
pip install iterabledata[rdf]

# Excel Binary (XLSB)
pip install iterabledata[xlsb]

# Graph formats (GraphML, GEXF, DOT)
pip install iterabledata[graph]

# Alignment formats (BAM, SAM)
pip install iterabledata[alignment]

# All optional dependencies
pip install iterabledata[all]
```

**AI Features** (`[ai]`): Enables AI-powered documentation generation using OpenAI, OpenRouter, Ollama, LMStudio, or Perplexity.

**Database Engines** (`[db]`): Enables read-only database access as iterable data sources. Supports PostgreSQL, ClickHouse, MySQL/MariaDB, Microsoft SQL Server, SQLite, MongoDB, and Elasticsearch/OpenSearch. Includes convenience groups:

- `[db-sql]`: SQL databases only (PostgreSQL, ClickHouse, MySQL, MSSQL)
- `[db-nosql]`: NoSQL databases only (MongoDB, Elasticsearch)

See the [API documentation](https://datenoio.github.io/iterabledata/) for details on these features.

For AI agents and LLM tooling, see **[llms.txt](llms.txt)** (machine-readable index) and [CONTRIBUTING.md](CONTRIBUTING.md).

## AI Quick Start

Generate dataset documentation with a **local** LLM (no API key) via LM Studio or Ollama, or use OpenAI:

```python
from iterable.ai import doc

# Local (LM Studio on http://localhost:1234/v1)
documentation = doc.generate(
    "data.csv",
    provider="lmstudio",
    base_url="http://localhost:1234/v1",
    format="markdown",
)

# Or analyze structure + docs in one call
from iterable.ops import inspect

analysis = inspect.analyze("data.csv", autodoc=True, autodoc_provider="openai")
print(analysis["documentation"])
```

Need structured, machine-readable output? Use `generate_blocks()` to get independent documentation blocks (`general`, `schema`, `quality`, `examples`, `statistics`, `codebook`) plus the assembled markdown:

```python
from iterable.ai import doc

result = doc.generate_blocks(
    "data.csv",
    provider="openai",
    context={"title": "Sales 2025", "description": "Monthly sales export"},
    progress=lambda event: print(event.stage, event.detail),
)
print(result["blocks"]["schema"]["data"])     # structured JSON
print(result["full_document_markdown"])        # assembled markdown
```

Install AI support: `pip install iterabledata[ai]`. See [examples/ai/](examples/ai/) and [docs/docs/api/ai.md](docs/docs/api/ai.md).

### Format catalog (agents)

```python
from iterable.catalog import describe_format

info = describe_format("xml")
print(info["example_args"])  # {'tagname': 'item'}
```

Full export: `dev/formats.json` or `export_catalog(format="json")`. See [docs/docs/api/catalog.md](docs/docs/api/catalog.md).

## Quick Start

### Basic Reading

```python
from iterable.helpers.detect import open_iterable

# Automatically detects format and compression
# Using context manager (recommended)
with open_iterable('data.csv.gz') as source:
    for row in source:
        print(row)
        # Process your data here
# File is automatically closed

# Or manually (still supported)
source = open_iterable('data.csv.gz')
for row in source:
    print(row)
source.close()
```

### Writing Data

```python
from iterable.helpers.detect import open_iterable

# Write compressed JSONL file
# Using context manager (recommended)
with open_iterable('output.jsonl.zst', mode='w') as dest:
    for item in my_data:
        dest.write(item)
# File is automatically closed

# Or manually (still supported)
dest = open_iterable('output.jsonl.zst', mode='w')
for item in my_data:
    dest.write(item)
dest.close()
```

## Usage Examples

### Reading Compressed CSV Files

```python
from iterable.helpers.detect import open_iterable

# Read compressed CSV file (supports .gz, .bz2, .xz, .zst, .lz4, .br, .snappy, .lzo)
source = open_iterable('data.csv.xz')
n = 0
for row in source:
    n += 1
    # Process row data
    if n % 1000 == 0:
        print(f'Processed {n} rows')
source.close()
```

### Reading Different Formats

```python
from iterable.helpers.detect import open_iterable

# Read JSONL file
jsonl_file = open_iterable('data.jsonl')
for row in jsonl_file:
    print(row)
jsonl_file.close()

# Read Parquet file
parquet_file = open_iterable('data.parquet')
for row in parquet_file:
    print(row)
parquet_file.close()

# Read XML file (specify tag name)
xml_file = open_iterable('data.xml', iterableargs={'tagname': 'item'})
for row in xml_file:
    print(row)
xml_file.close()

# Read Excel file
xlsx_file = open_iterable('data.xlsx')
for row in xlsx_file:
    print(row)
xlsx_file.close()
```

### Reading from Databases

```python
from iterable.helpers.detect import open_iterable

# Read from PostgreSQL database
with open_iterable(
    'postgresql://user:password@localhost:5432/mydb',
    engine='postgres',
    iterableargs={'query': 'users'}
) as source:
    for row in source:
        print(row)

# Read specific columns with filtering
with open_iterable(
    'postgresql://localhost/mydb',
    engine='postgres',
    iterableargs={
        'query': 'users',
        'columns': ['id', 'name', 'email'],
        'filter': 'active = TRUE'
    }
) as source:
    for row in source:
        print(row)

# Read from ClickHouse database
with open_iterable(
    'clickhouse://user:password@localhost:9000/analytics',
    engine='clickhouse',
    iterableargs={'query': 'events', 'settings': {'max_threads': 4}}
) as source:
    for row in source:
        print(row)

# Convert database to file
from iterable.convert import convert
convert(
    fromfile='postgresql://localhost/mydb',
    tofile='users.parquet',
    iterableargs={'engine': 'postgres', 'query': 'users'}
)

# Convert ClickHouse to Parquet
convert(
    fromfile='clickhouse://localhost:9000/analytics',
    tofile='events.parquet',
    iterableargs={'engine': 'clickhouse', 'query': 'events'}
)
```

### Format Detection and Encoding

```python
from iterable.helpers.detect import open_iterable, detect_file_type, detect_file_type_from_content
from iterable.helpers.utils import detect_encoding, detect_delimiter

# Detect file type and compression (uses filename extension)
result = detect_file_type('data.csv.gz')
print(f"Type: {result['datatype']}, Codec: {result['codec']}")

# Content-based detection (for files without extensions or streams)
with open('data.unknown', 'rb') as f:
    detection_result = detect_file_type_from_content(f)
    if detection_result:
        format_id, confidence, method = detection_result
        print(f"Detected format: {format_id} (confidence: {confidence:.2f}, method: {method})")

# open_iterable() automatically uses content-based detection as fallback
# Works with files without extensions, streams, or incorrect extensions
with open_iterable('data.unknown') as source:  # Detects from content
    for row in source:
        print(row)

# Detect encoding for CSV files
encoding_info = detect_encoding('data.csv')
print(f"Encoding: {encoding_info['encoding']}, Confidence: {encoding_info['confidence']}")

# Detect delimiter for CSV files
delimiter = detect_delimiter('data.csv', encoding=encoding_info['encoding'])

# Open with detected settings
source = open_iterable('data.csv', iterableargs={
    'encoding': encoding_info['encoding'],
    'delimiter': delimiter
})
```

### Error Handling

IterableData provides a comprehensive exception hierarchy and configurable error handling:

```python
from iterable.helpers.detect import open_iterable
from iterable.exceptions import (
    FormatDetectionError,
    FormatNotSupportedError,
    FormatParseError,
    CodecError
)

# Basic exception handling
try:
    with open_iterable('data.unknown') as source:
        for row in source:
            process(row)
except FormatDetectionError as e:
    print(f"Could not detect format: {e.reason}")
    # Try with explicit format or check file content
except FormatNotSupportedError as e:
    print(f"Format '{e.format_id}' not supported: {e.reason}")
    # Install missing dependencies or use different format
except FormatParseError as e:
    print(f"Failed to parse {e.format_id} format")
    if e.position:
        print(f"Error at position: {e.position}")
except CodecError as e:
    print(f"Compression error with {e.codec_name}: {e.message}")
    # Check file integrity or try different codec
except Exception as e:
    print(f"Unexpected error: {e}")
```

**Configurable Error Policies**: Control how malformed records are handled:

```python
# Skip malformed records and continue processing
with open_iterable(
    'data.csv',
    iterableargs={'on_error': 'skip', 'error_log': 'errors.log'}
) as src:
    for row in src:
        process(row)  # Only processes valid rows

# Warn on errors but continue processing
with open_iterable(
    'data.jsonl',
    iterableargs={'on_error': 'warn', 'error_log': 'errors.log'}
) as src:
    for row in src:
        process(row)  # Warnings logged, processing continues

# Default: raise exceptions immediately (existing behavior)
with open_iterable('data.csv', iterableargs={'on_error': 'raise'}) as src:
    for row in src:
        process(row)
```

**Error Logging**: Structured JSON logs with context (filename, row number, byte offset, error message, original line).

See [Exception Hierarchy documentation](docs/docs/api/exceptions.md) for complete exception reference.

### Querying Format Capabilities

```python
from iterable.helpers.capabilities import (
    get_format_capabilities,
    get_capability,
    list_all_capabilities
)

# Get all capabilities for a format
caps = get_format_capabilities("csv")
print(f"CSV readable: {caps['readable']}")
print(f"CSV writable: {caps['writable']}")
print(f"CSV supports totals: {caps['totals']}")
print(f"CSV supports tables: {caps['tables']}")

# Query a specific capability
is_writable = get_capability("json", "writable")
has_totals = get_capability("parquet", "totals")
supports_tables = get_capability("xlsx", "tables")

# List capabilities for all formats
all_caps = list_all_capabilities()
for format_id, capabilities in all_caps.items():
    if capabilities.get("tables"):
        print(f"{format_id} supports multiple tables")
```

### Format Conversion

```python
from iterable.helpers.detect import open_iterable
from iterable.convert.core import convert

# Simple format conversion
convert('input.jsonl.gz', 'output.parquet')

# Convert with options
convert(
    'input.csv.xz',
    'output.jsonl.zst',
    iterableargs={'delimiter': ';', 'encoding': 'utf-8'},
    batch_size=10000
)

# Convert and flatten nested structures
convert(
    'input.jsonl',
    'output.csv',
    is_flatten=True,
    batch_size=50000
)
```

### Atomic Writes for Production Safety

Use atomic writes to ensure output files are never left in a partially written state:

```python
from iterable.convert.core import convert
from iterable.pipeline.core import pipeline

# Convert with atomic writes (production-safe)
result = convert('input.csv', 'output.parquet', atomic=True)
# Output file only appears when conversion completes successfully

# Atomic writes in pipelines
pipeline(
    source=source,
    destination=destination,
    process_func=transform_func,
    atomic=True  # Ensures destination file is only created on success
)
```

**Benefits**: Prevents data corruption from crashes, interruptions, or mid-process failures. Original files are preserved on failure.

### Bulk File Conversion

Convert multiple files at once using glob patterns, directories, or file lists:

```python
from iterable.convert.core import bulk_convert

# Convert all CSV files matching glob pattern
result = bulk_convert('data/raw/*.csv.gz', 'data/processed/', to_ext='parquet')

# Convert with custom filename pattern
result = bulk_convert('data/*.csv', 'output/', pattern='{name}.parquet')

# Convert entire directory
result = bulk_convert('data/raw/', 'data/processed/', to_ext='parquet')

# Access results
print(f"Converted {result.successful_files}/{result.total_files} files")
print(f"Total rows: {result.total_rows_out}")
print(f"Throughput: {result.throughput:.0f} rows/second")

# Check individual file results
for file_result in result.file_results:
    if file_result.success:
        print(f"✓ {file_result.source_file}: {file_result.result.rows_out} rows")
    else:
        print(f"✗ {file_result.source_file}: {file_result.error}")
```

**Features**: Error resilience (continues if one file fails), aggregated metrics, flexible output naming with placeholders (`{name}`, `{stem}`, `{ext}`).

### Progress Tracking and Metrics

Track conversion and pipeline progress with callbacks, progress bars, and structured metrics:

```python
from iterable.convert.core import convert
from iterable.pipeline.core import pipeline

# Progress callback for conversions
def progress_cb(stats):
    print(f"Progress: {stats['rows_read']} rows read, "
          f"{stats['rows_written']} rows written, "
          f"{stats.get('elapsed', 0):.2f}s elapsed")

# Convert with progress tracking
result = convert(
    'input.csv',
    'output.parquet',
    progress=progress_cb,
    show_progress=True  # Also shows tqdm progress bar
)

# Access conversion metrics
print(f"Converted {result.rows_out} rows in {result.elapsed_seconds:.2f}s")
print(f"Read {result.bytes_read} bytes, wrote {result.bytes_written} bytes")

# Pipeline with progress and metrics
result = pipeline(
    source=source,
    destination=destination,
    process_func=transform_func,
    progress=progress_cb  # Progress callback
)

# Access pipeline metrics (supports both attribute and dict access)
print(f"Processed {result.rows_processed} rows")
print(f"Throughput: {result.throughput:.0f} rows/second")
print(f"Exceptions: {result.exceptions}")
# Backward compatible: result['rec_count'] also works
```

**Features**: Real-time progress callbacks, automatic progress bars with `tqdm`, structured metrics objects (`ConversionResult`, `PipelineResult`).

### Using Pipeline for Data Processing

```python
from iterable.helpers.detect import open_iterable
from iterable.pipeline.core import pipeline

source = open_iterable('input.parquet')
destination = open_iterable('output.jsonl.xz', mode='w')

def transform_record(record, state):
    """Transform each record"""
    # Add processing logic
    out = {}
    for key in ['name', 'email', 'age']:
        if key in record:
            out[key] = record[key]
    return out

def progress_callback(stats, state):
    """Called every trigger_on records"""
    print(f"Processed {stats['rec_count']} records, "
          f"Duration: {stats.get('duration', 0):.2f}s")

def final_callback(stats, state):
    """Called when processing completes"""
    print(f"Total records: {stats['rec_count']}")
    print(f"Total time: {stats['duration']:.2f}s")

result = pipeline(
    source=source,
    destination=destination,
    process_func=transform_record,
    trigger_func=progress_callback,
    trigger_on=1000,
    final_func=final_callback,
    start_state={},
    atomic=True  # Use atomic writes for production safety
)

# Access pipeline metrics
print(f"Throughput: {result.throughput:.0f} rows/second")

source.close()
destination.close()
```

### Manual Format and Codec Usage

```python
from iterable.datatypes.jsonl import JSONLinesIterable
from iterable.datatypes.bsonf import BSONIterable
from iterable.codecs.gzipcodec import GZIPCodec
from iterable.codecs.lzmacodec import LZMACodec

# Read gzipped JSONL
read_codec = GZIPCodec('input.jsonl.gz', mode='r', open_it=True)
reader = JSONLinesIterable(codec=read_codec)

# Write LZMA compressed BSON
write_codec = LZMACodec('output.bson.xz', mode='wb', open_it=False)
writer = BSONIterable(codec=write_codec, mode='w')

for row in reader:
    writer.write(row)

reader.close()
writer.close()
```

### Cloud Storage Support

Read and write data directly from cloud object storage (S3, GCS, Azure):

```python
from iterable.helpers.detect import open_iterable

# Read from S3
with open_iterable('s3://my-bucket/data/events.csv') as source:
    for row in source:
        print(row)

# Read compressed file from GCS
with open_iterable('gs://my-bucket/data/events.jsonl.gz') as source:
    for row in source:
        process(row)

# Write to Azure Blob Storage
with open_iterable(
    'az://my-container/output/results.jsonl',
    mode='w',
    iterableargs={'storage_options': {'connection_string': '...'}}
) as dest:
    dest.write({'name': 'Alice', 'age': 30})
    dest.write({'name': 'Bob', 'age': 25})
```

**Supported Providers**:

- Amazon S3: `s3://` and `s3a://` schemes
- Google Cloud Storage: `gs://` and `gcs://` schemes
- Azure Blob Storage: `az://`, `abfs://`, and `abfss://` schemes

**Installation**: `pip install iterabledata[cloud]`

**Note**: DuckDB engine does not support cloud storage URIs; use `engine='internal'` (default).

### Using DuckDB Engine with Pushdown Optimizations

The DuckDB engine provides high-performance querying with advanced optimizations:

```python
from iterable.helpers.detect import open_iterable

# Basic DuckDB usage
source = open_iterable('data.csv.gz', engine='duckdb')
total = source.totals()  # Fast counting
for row in source:
    print(row)
source.close()

# Column projection pushdown (only read specified columns)
with open_iterable(
    'data.csv',
    engine='duckdb',
    iterableargs={'columns': ['name', 'age']}  # Reduces I/O and memory
) as src:
    for row in src:
        process(row)

# Filter pushdown (filter at database level)
with open_iterable(
    'data.csv',
    engine='duckdb',
    iterableargs={'filter': "age > 18 AND status = 'active'"}
) as src:
    for row in src:
        process(row)

# Combined column projection and filtering
with open_iterable(
    'data.parquet',
    engine='duckdb',
    iterableargs={
        'columns': ['name', 'age', 'email'],
        'filter': 'age > 18'
    }
) as src:
    for row in src:
        process(row)

# Direct SQL query support
with open_iterable(
    'data.parquet',
    engine='duckdb',
    iterableargs={
        'query': 'SELECT name, age FROM read_parquet(\'data.parquet\') WHERE age > 18 ORDER BY age DESC LIMIT 100'
    }
) as src:
    for row in src:
        process(row)
```

**Supported Formats**: CSV, JSONL, NDJSON, JSON, Parquet  
**Supported Codecs**: GZIP, ZStandard (.zst)  
**Benefits**: Reduced I/O, lower memory usage, faster processing through database-level optimizations

### Bulk Operations

```python
from iterable.helpers.detect import open_iterable

source = open_iterable('input.jsonl')
destination = open_iterable('output.parquet', mode='w')

# Read and write in batches for better performance
batch = []
for row in source:
    batch.append(row)
    if len(batch) >= 10000:
        destination.write_bulk(batch)
        batch = []

# Write remaining records
if batch:
    destination.write_bulk(batch)

source.close()
destination.close()
```

### Working with Excel Files

```python
from iterable.helpers.detect import open_iterable

# Read Excel file (specify sheet or page)
xls_file = open_iterable('data.xlsx', iterableargs={'page': 0})

for row in xls_file:
    print(row)
xls_file.close()

# Read specific sheet in XLSX
xlsx_file = open_iterable('data.xlsx', iterableargs={'page': 'Sheet2'})
```

### XML Processing

```python
from iterable.helpers.detect import open_iterable

# Parse XML with specific tag name
xml_file = open_iterable(
    'data.xml',
    iterableargs={
        'tagname': 'book',
        'prefix_strip': True  # Strip XML namespace prefixes
    }
)

for item in xml_file:
    print(item)
xml_file.close()
```

### DataFrame Bridges

Convert iterable data to Pandas, Polars, or Dask DataFrames:

```python
from iterable.helpers.detect import open_iterable

# Convert to Pandas DataFrame
with open_iterable('data.csv.gz') as source:
    df = source.to_pandas()
    print(df.head())

# Chunked processing for large files
with open_iterable('large_data.csv') as source:
    for df_chunk in source.to_pandas(chunksize=100_000):
        # Process each chunk
        result = df_chunk.groupby('category').sum()
        process_chunk(result)

# Convert to Polars DataFrame
with open_iterable('data.csv.gz') as source:
    df = source.to_polars()
    print(df.head())

# Convert to Dask DataFrame (single file)
with open_iterable('data.csv.gz') as source:
    ddf = source.to_dask()
    result = ddf.groupby('category').sum().compute()

# Multi-file Dask DataFrame (automatic format detection)
from iterable.helpers.bridges import to_dask

ddf = to_dask(['file1.csv', 'file2.jsonl', 'file3.parquet'])
result = ddf.groupby('category').sum().compute()
```

**Note**: DataFrame bridges require optional dependencies. Install with:

```bash
pip install iterabledata[dataframes]  # All DataFrame libraries
# Or individually:
pip install pandas
pip install polars
pip install "dask[dataframe]"
```

### Type Hints and Type Safety

IterableData includes complete type annotations and typed helper functions for modern Python development:

```python
from iterable.helpers.detect import open_iterable
from iterable.helpers.typed import as_dataclasses, as_pydantic
from dataclasses import dataclass
from pydantic import BaseModel

# Type aliases for better code readability
from iterable.types import Row, IterableArgs, CodecArgs

# Convert to dataclasses for type safety
@dataclass
class Person:
    name: str
    age: int
    email: str | None = None

with open_iterable('people.csv') as source:
    for person in as_dataclasses(source, Person):
        # Full IDE autocomplete and type checking
        print(person.name, person.age)

# Convert to Pydantic models with validation
class PersonModel(BaseModel):
    name: str
    age: int
    email: str | None = None

with open_iterable('people.jsonl') as source:
    for person in as_pydantic(source, PersonModel, validate=True):
        # Automatic schema validation
        print(person.name, person.age)
        # Access as Pydantic model with all features
```

**Benefits**:

- Complete type annotations across the public API
- `py.typed` marker file enables mypy, pyright, and other type checkers
- Typed helpers provide IDE autocomplete and type safety
- Pydantic validation catches schema issues early

**Installation**: `pip install iterabledata[pydantic]` for Pydantic support

### Advanced: Converting Compressed XML to Parquet

```python
from iterable.datatypes.xml import XMLIterable
from iterable.datatypes.parquet import ParquetIterable
from iterable.codecs.bz2codec import BZIP2Codec

# Read compressed XML
read_codec = BZIP2Codec('data.xml.bz2', mode='r')
reader = XMLIterable(codec=read_codec, tagname='page')

# Write to Parquet with schema adaptation
writer = ParquetIterable(
    'output.parquet',
    mode='w',
    use_pandas=False,
    adapt_schema=True,
    batch_size=10000
)

batch = []
for row in reader:
    batch.append(row)
    if len(batch) >= 10000:
        writer.write_bulk(batch)
        batch = []

if batch:
    writer.write_bulk(batch)

reader.close()
writer.close()
```

## API Reference

### Main Functions

#### `open_iterable(filename, mode='r', engine='internal', codecargs={}, iterableargs={})`

Opens a file and returns an iterable object.

**Parameters:**

- `filename` (str): Path to the file (supports local files and cloud storage URIs: `s3://`, `gs://`, `az://`)
- `mode` (str): File mode ('r' for read, 'w' for write)
- `engine` (str): Processing engine ('internal' or 'duckdb')
- `codecargs` (dict): Arguments for codec initialization
- `iterableargs` (dict): Arguments for iterable initialization
  - `columns` (list[str]): For DuckDB engine, only read specified columns (pushdown optimization)
  - `filter` (str | callable): For DuckDB engine, filter rows at database level (SQL string or Python callable)
  - `query` (str): For DuckDB engine, execute custom SQL query (read-only)
  - `on_error` (str): Error policy ('raise', 'skip', or 'warn')
  - `error_log` (str | file-like): Path or file object for structured error logging
  - `storage_options` (dict): Cloud storage authentication options

**Returns:** Iterable object for the detected file type

#### `detect_file_type(filename)`

Detects file type and compression codec from filename.

**Returns:** Dictionary with `success`, `datatype`, and `codec` keys

#### `convert(fromfile, tofile, iterableargs={}, toiterableargs={}, scan_limit=1000, batch_size=50000, silent=True, is_flatten=False, use_totals=False, progress=None, show_progress=False, atomic=False) -> ConversionResult`

Converts data between formats.

**Parameters:**

- `fromfile` (str): Source file path
- `tofile` (str): Destination file path
- `iterableargs` (dict): Options for reading source file
- `toiterableargs` (dict): Options for writing destination file
- `scan_limit` (int): Number of records to scan for schema detection
- `batch_size` (int): Batch size for bulk operations
- `silent` (bool): Suppress progress output
- `is_flatten` (bool): Flatten nested structures
- `use_totals` (bool): Use total count for progress tracking (if available)
- `progress` (callable): Optional callback function receiving progress stats dictionary
- `show_progress` (bool): Display progress bar using tqdm (if available)
- `atomic` (bool): Write to temporary file and atomically rename on success

**Returns:** `ConversionResult` object with:

- `rows_in` (int): Total rows read
- `rows_out` (int): Total rows written
- `elapsed_seconds` (float): Conversion time
- `bytes_read` (int | None): Bytes read (if available)
- `bytes_written` (int | None): Bytes written (if available)
- `errors` (list[Exception]): List of errors encountered

#### `bulk_convert(source, destination, pattern=None, to_ext=None, **kwargs) -> BulkConversionResult`

Convert multiple files at once using glob patterns, directories, or file lists.

**Parameters:**

- `source` (str): Glob pattern, directory path, or file path
- `destination` (str): Output directory or filename pattern
- `pattern` (str): Filename pattern with placeholders (`{name}`, `{stem}`, `{ext}`)
- `to_ext` (str): Replace file extension (e.g., `'parquet'`)
- `**kwargs`: All parameters from `convert()` function

**Returns:** `BulkConversionResult` object with:

- `total_files` (int): Total files processed
- `successful_files` (int): Files successfully converted
- `failed_files` (int): Files that failed
- `total_rows_in` (int): Total rows read across all files
- `total_rows_out` (int): Total rows written across all files
- `total_elapsed_seconds` (float): Total conversion time
- `file_results` (list[FileConversionResult]): Per-file results
- `errors` (list[Exception]): All errors encountered
- `throughput` (float | None): Rows per second

#### `pipeline(source, destination, process_func, trigger_func=None, trigger_on=1000, final_func=None, reset_iterables=True, skip_nulls=True, start_state=None, debug=False, batch_size=1000, progress=None, atomic=False) -> PipelineResult`

Execute a data processing pipeline.

**Parameters:**

- `source` (BaseIterable): Source iterable to read from
- `destination` (BaseIterable | None): Destination iterable to write to
- `process_func` (callable): Function to process each record
- `trigger_func` (callable | None): Function called periodically during processing
- `trigger_on` (int): Number of records between trigger function calls
- `final_func` (callable | None): Function called after processing completes
- `reset_iterables` (bool): Reset iterables before processing
- `skip_nulls` (bool): Skip None results from process_func
- `start_state` (dict | None): Initial state dictionary
- `debug` (bool): Raise exceptions instead of catching them
- `batch_size` (int): Number of records to batch before writing
- `progress` (callable | None): Optional callback function for progress updates
- `atomic` (bool): Use atomic writes if destination is a file

**Returns:** `PipelineResult` object with:

- `rows_processed` (int): Total rows processed
- `elapsed_seconds` (float): Processing time
- `throughput` (float | None): Rows per second
- `exceptions` (int): Number of exceptions encountered
- `nulls` (int): Number of null results
- Supports both attribute access (`result.rows_processed`) and dictionary access (`result['rec_count']`) for backward compatibility

### Iterable Methods

All iterable objects support:

- `read(skip_empty=True) -> Row` - Read single record
- `read_bulk(num=DEFAULT_BULK_NUMBER) -> list[Row]` - Read multiple records
- `write(record)` - Write single record
- `write_bulk(records)` - Write multiple records
- `reset()` - Reset iterator to beginning
- `close()` - Close file handles
- `to_pandas(chunksize=None)` - Convert to pandas DataFrame (optional chunked processing)
- `to_polars(chunksize=None)` - Convert to Polars DataFrame (optional chunked processing)
- `to_dask(chunksize=1000000)` - Convert to Dask DataFrame
- `list_tables(filename=None) -> list[str] | None` - List available tables/sheets/datasets
- `has_tables() -> bool` - Check if format supports multiple tables

### Helper Functions

#### `as_dataclasses(iterable, dataclass_type, skip_empty=True) -> Iterator[T]`

Convert dict-based rows from an iterable into dataclass instances.

**Parameters:**

- `iterable` (BaseIterable): The iterable to read rows from
- `dataclass_type` (type[T]): The dataclass type to convert rows to
- `skip_empty` (bool): Whether to skip empty rows

**Returns:** Iterator of dataclass instances

#### `as_pydantic(iterable, model_type, skip_empty=True, validate=True) -> Iterator[T]`

Convert dict-based rows from an iterable into Pydantic model instances.

**Parameters:**

- `iterable` (BaseIterable): The iterable to read rows from
- `model_type` (type[T]): The Pydantic model type to convert rows to
- `skip_empty` (bool): Whether to skip empty rows
- `validate` (bool): Whether to validate rows against the model schema

**Returns:** Iterator of Pydantic model instances

**Raises:** `ImportError` if pydantic is not installed

#### `to_dask(files, chunksize=1000000, **iterableargs) -> DaskDataFrame`

Convert multiple files to a unified Dask DataFrame with automatic format detection.

**Parameters:**

- `files` (str | list[str]): Single file path or list of file paths
- `chunksize` (int): Number of rows per partition
- `**iterableargs`: Additional arguments to pass to `open_iterable()` for each file

**Returns:** Dask DataFrame containing data from all files

**Raises:** `ImportError` if dask or pandas is not installed

## Engines

### Internal Engine (Default)

The internal engine uses pure Python implementations for all formats. It supports all file types and compression codecs.

### DuckDB Engine

The DuckDB engine provides high-performance querying capabilities for supported formats:

- **Formats**: CSV, JSONL, NDJSON, JSON
- **Codecs**: GZIP, ZStandard (.zst)
- **Features**: Fast querying, totals counting, SQL-like operations

Use `engine='duckdb'` when opening files:

```python
source = open_iterable('data.csv.gz', engine='duckdb')
```

## Examples Directory

See the [examples](examples/) directory for more complete examples:

- `simplewiki/` - Processing Wikipedia XML dumps

## More Examples and Tests

See the [tests](tests/) directory for comprehensive usage examples and test cases.

## AI Integration Guides

IterableData can be integrated with AI platforms and frameworks for intelligent data processing:

- **[AI Frameworks](docs/integrations/AI_FRAMEWORKS.md)** - Integration with LangChain, CrewAI, and AutoGen
  - Tool creation for data reading and format conversion
  - Schema inference and data quality analysis
  - Multi-agent workflows for data processing
- **[OpenAI](docs/integrations/OPENAI.md)** - Direct OpenAI API integration (GPT-4, GPT-3.5, etc.)
  - Function calling and Assistants API
  - Structured outputs for consistent results
  - Natural language data analysis and transformation
- **[Claude](docs/integrations/CLAUDE.md)** - Anthropic Claude AI integration
  - Claude API integration with tools support
  - Intelligent data analysis and schema inference
  - Format conversion with AI guidance
  - Data quality assessment and documentation
- **[Gemini](docs/integrations/GEMINI.md)** - Google Gemini AI integration
  - Natural language data analysis
  - Intelligent format conversion with AI guidance
  - Schema documentation and data quality assessment
  - Function calling integration

These guides provide patterns, examples, and best practices for combining IterableData's unified data interface with AI capabilities.

## Related Projects

This library is used in:

- [undatum](https://github.com/datacoon/undatum) - Command line data processing tool
- [datacrafter](https://github.com/apicrafter/datacrafter) - Data processing ETL engine

## License

MIT License

## Contributing

Contributions are welcome! Please feel free to submit pull requests or open issues.

## Changelog

See [CHANGELOG.md](CHANGELOG.md) for detailed version history.

### Version 1.0.11 (2026-01-25)

- **Atomic Writes**: Production-safe file writing with temporary files and atomic renames
- **Bulk File Conversion**: Convert multiple files at once using glob patterns, directories, or file lists
- **Observability Features**: Progress tracking, metrics objects, and progress bars for conversions and pipelines
- **Cloud Storage Support**: Direct access to S3, GCS, and Azure Blob Storage via URI schemes
- **DuckDB Engine Pushdown Optimizations**: Column projection, filter pushdown, and direct SQL query support
- **Error Handling Controls**: Configurable error policies (`on_error`) and structured error logging (`error_log`)
- **Type Hints and Typed Helpers**: Complete type annotations with `as_dataclasses()` and `as_pydantic()` helper functions
- **Vortex Format Support**: Added support for reading and writing Vortex columnar data files

### Version 1.0.11 (2026-01-25)

- **Enhanced Format Detection**: Added content-based format detection using magic numbers and heuristics for files without extensions, streams, and files with incorrect extensions
- **Exception Hierarchy**: Added comprehensive exception hierarchy (`IterableDataError`, `FormatError`, `CodecError`, etc.) for better error handling
- **Format Capability Reporting**: Added programmatic API to query format capabilities (`get_format_capabilities()`, `list_all_capabilities()`, `get_capability()`)
- **Table Listing Support**: Added `list_tables()` and `has_tables()` methods for discovering tables, sheets, and datasets in multi-table formats

### Version 1.0.8 (2026-01-05)

- **AI Integration Guides**: Added comprehensive guides for LangChain, CrewAI, AutoGen, and Google Gemini AI
- **Documentation**: Added capability matrix and enhanced API documentation
- **Development Tools**: Added benchmarking and utility scripts
- **Code Improvements**: Enhanced format detection, codecs, and data type handlers
- **Examples**: Added ZIP XML processing example

### Version 1.0.7 (2024-12-15)

- **Major Format Expansion**: Added support for 50+ new data formats across multiple categories
- **Enhanced Compression**: Added LZO, Snappy, and SZIP codec support
- **CI/CD**: Added GitHub Actions workflows for automated testing and deployment
- **Documentation**: Complete documentation site with Docusaurus
- **Testing**: Comprehensive test suite for all formats

### Version 1.0.6

- Comprehensive documentation enhancements
- GitHub Actions release workflow
- Improved examples and use cases

### Version 1.0.5

- DuckDB engine support
- Enhanced format detection
- Pipeline processing framework
- Bulk operations support

