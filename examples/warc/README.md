## WARC Examples

This directory contains examples demonstrating how to use IterableData with WARC (Web ARChive) files.

## Prerequisites

1. **Install IterableData with WARC support**:
   
   **Option A: Development mode (recommended for testing examples)**:
   ```bash
   cd /path/to/iterabledata
   pip install -e ".[dev]"
   ```
   
   **Option B: Install from PyPI**:
   ```bash
   pip install iterabledata
   ```
   
   The WARC format support requires the `warcio` package, which should be installed automatically.
   If you get an ImportError, install it separately:
   ```bash
   pip install warcio
   ```

2. **WARC Files**: The examples use test WARC files:
   - `tests/fixtures/sample.warc.gz` - Sample WARC file (gzipped, used by default)
   - `testdata/test_simple.warc` - Simple WARC file with basic records (fallback)
   - `testdata/test_debug.warc` - WARC file with debug records

   You can also use your own WARC files by passing the file path as a command-line argument.
   WARC files can be compressed (`.warc.gz`, `.warc.zst`, etc.) - IterableData handles compression automatically.

## Running Examples

**Important**: Run examples from the project root directory to ensure the local code is used:

```bash
cd /path/to/iterabledata
python examples/warc/convert_to_jsonl.py
```

Or set PYTHONPATH:
```bash
cd examples/warc
PYTHONPATH=../.. python convert_to_jsonl.py
```

## Examples

### 1. `convert_to_jsonl.py` - Convert to JSONL

Converts a WARC file to a JSONL file using the `convert()` function.

**Usage**:
```bash
cd /path/to/iterabledata
python examples/warc/convert_to_jsonl.py [path_to_warc_file]
```

If no file path is provided, the script uses `tests/fixtures/sample.warc.gz` by default (or falls back to `testdata/test_simple.warc` if the fixtures file is not found).

**Note**: JSONL format is flexible and preserves all nested structures in WARC records, including:
- Record headers (WARC headers)
- HTTP headers (for request/response records)
- Content payloads
- Metadata fields

This script:
- Reads WARC records from the input file
- Converts all records to JSONL format
- Saves to `{input_filename}.jsonl` in the same directory
- Shows progress during conversion

**Example output**:
```
Converting WARC file to JSONL...
Input file: tests/fixtures/sample.warc.gz
Output file: tests/fixtures/sample.warc.jsonl
------------------------------------------------------------
------------------------------------------------------------
Conversion completed!
WARC records read: 18
JSONL records written: 18
Time elapsed: 0.23 seconds
```

### 2. `convert_to_parquet.py` - Convert to Parquet

Converts a WARC file to a Parquet file using the `convert()` function.

**Usage**:
```bash
cd /path/to/iterabledata
python examples/warc/convert_to_parquet.py [path_to_warc_file]
```

If no file path is provided, the script uses `tests/fixtures/sample.warc.gz` by default (or falls back to `testdata/test_simple.warc` if the fixtures file is not found).

**Note**: Parquet requires a fixed schema. The example uses several techniques to handle varying record structures:
- `adapt_schema=True` to adapt the schema from data
- `is_flatten=True` to flatten nested structures (converts nested fields to dot notation like `rec_headers.WARC-Target-URI`)
- `scan_limit=1000` to scan more records for better schema inference

**Important**: The schema is determined from the first batch of records. If WARC records have fields that only appear later:
- Those fields will be automatically dropped (not included in the output)
- Missing fields in later records will be filled with `None`
- This prevents schema mismatch errors but may result in data loss for fields that appear after the initial schema is set

If you need to preserve all fields regardless of when they appear:
- Convert to JSONL instead (more flexible with varying schemas)
- Increase `scan_limit` to scan more records before setting the schema
- Pre-process data to ensure all records have consistent structure

This script:
- Reads WARC records from the input file
- Converts all records to Parquet format
- Saves to `{input_filename}.parquet` in the same directory
- Shows progress during conversion

**Example output**:
```
Converting WARC file to Parquet...
Input file: tests/fixtures/sample.warc.gz
Output file: tests/fixtures/sample.warc.parquet
------------------------------------------------------------
------------------------------------------------------------
Conversion completed!
WARC records read: 18
Parquet records written: 18
Time elapsed: 0.33 seconds

Note: Parquet schema is determined from the first batch of records.
If WARC records have fields that only appear later, those fields
may be automatically dropped to prevent schema mismatch errors.
```

## WARC Record Structure

WARC records contain the following fields:

- **rec_type**: Record type (e.g., "response", "request", "resource", "metadata")
- **rec_headers**: Dictionary of WARC headers (e.g., WARC-Target-URI, WARC-Date, WARC-Record-ID)
- **target_uri**: Target URI (extracted from WARC-Target-URI header)
- **date**: Record date (extracted from WARC-Date header)
- **record_id**: Record ID (extracted from WARC-Record-ID header)
- **warc_type**: WARC type (extracted from WARC-Type header)
- **content_type**: Content type of the record
- **length**: Length of the record
- **http_headers**: Dictionary of HTTP headers (for request/response records)
- **http_status_code**: HTTP status code (for response records)
- **http_status_line**: HTTP status line (for response records)
- **http_request_line**: HTTP request line (for request records)
- **http_method**: HTTP method (for request records)
- **http_path**: HTTP path (for request records)
- **http_protocol**: HTTP protocol (for request records)
- **content**: Record content (payload)
- **content_length**: Length of the content

## Advanced Usage

### Custom Output Location

You can modify the scripts to specify custom output locations:

```python
output_file = "/path/to/output/records.jsonl"
```

### Filtering Records

You can filter WARC records by type using the `open_iterable()` function directly:

```python
from iterable import open_iterable

with open_iterable("archive.warc") as source:
    for record in source:
        # Filter for response records only
        if record.get("rec_type") == "response":
            print(record.get("target_uri"))
```

### Processing Large WARC Files

For large WARC files, use batch processing:

```python
from iterable import open_iterable

with open_iterable("large_archive.warc") as source:
    batch = []
    for record in source:
        batch.append(record)
        if len(batch) >= 1000:
            # Process batch
            process_batch(batch)
            batch = []
    # Process remaining records
    if batch:
        process_batch(batch)
```

### Extracting Specific Fields

You can extract and transform specific fields during conversion:

```python
from iterable import open_iterable
from iterable.datatypes.jsonl import JSONLIterable

with open_iterable("archive.warc") as source:
    with JSONLIterable("output.jsonl", mode="w") as dest:
        for record in source:
            # Extract only specific fields
            extracted = {
                "url": record.get("target_uri"),
                "date": record.get("date"),
                "status": record.get("http_status_code"),
                "content_length": record.get("content_length"),
            }
            dest.write(extracted)
```

## Troubleshooting

### Import Errors

If you get `ImportError` for warcio:
- Install warcio: `pip install warcio`
- Or install with dev extra: `pip install iterabledata[dev]`

### File Not Found Errors

If you get file not found errors:
- Verify the WARC file path is correct
- Check that the file exists and is readable
- Ensure you're running from the project root or have set PYTHONPATH correctly

### Schema Errors (Parquet)

If you get schema errors when converting to Parquet:
- Use `is_flatten=True` to flatten nested structures
- Increase `scan_limit` to scan more records before setting the schema
- Consider converting to JSONL instead for more flexible schema handling
- Pre-process WARC records to ensure consistent structure

### Memory Issues

If you encounter memory issues with large WARC files:
- Use batch processing instead of loading all records at once
- Process records one at a time instead of using `read_bulk()`
- Consider streaming conversion instead of loading entire file
