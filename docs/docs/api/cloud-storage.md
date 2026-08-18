---
sidebar_position: 10
title: Cloud Storage Support
description: Read and write data files directly from cloud object storage (S3, GCS, Azure)
---

# Cloud Storage Support

IterableData supports reading from and writing to cloud object storage services (Amazon S3, Google Cloud Storage, Azure Blob Storage) via URI schemes. This enables direct access to cloud-hosted datasets without downloading files locally.

## Supported Cloud Storage Services

- **Amazon S3**: `s3://` and `s3a://` schemes
- **Google Cloud Storage**: `gs://` and `gcs://` schemes
- **Azure Blob Storage**: `az://`, `abfs://`, and `abfss://` schemes

## Installation

Cloud storage support requires optional dependencies. Install them based on your cloud provider:

```bash
# For all cloud providers
pip install iterabledata[cloud]

# Or install specific backends
pip install fsspec s3fs      # For S3
pip install fsspec gcsfs      # For GCS
pip install fsspec adlfs     # For Azure
```

## Basic Usage

### Reading from S3

```python
from iterable import open_iterable

# Read CSV from S3
with open_iterable('s3://my-bucket/data/events.csv') as source:
    for row in source:
        print(row)
```

### Reading Compressed Files

Cloud storage works seamlessly with compression codecs:

```python
# Read gzipped JSONL from S3
with open_iterable('s3://my-bucket/data/events.jsonl.gz') as source:
    for row in source:
        print(row)

# Read ZStandard-compressed CSV from GCS
with open_iterable('gs://my-bucket/data/large.csv.zst') as source:
    for row in source:
        process(row)
```

### Writing to Cloud Storage

```python
# Write data to S3
with open_iterable('s3://my-bucket/output/results.jsonl', mode='w') as dest:
    dest.write({'name': 'Alice', 'age': 30})
    dest.write({'name': 'Bob', 'age': 25})
```

## Authentication

Cloud storage authentication uses standard methods for each provider, typically via environment variables or credentials files.

### Amazon S3

S3 authentication uses AWS credentials:

```bash
# Via environment variables
export AWS_ACCESS_KEY_ID=your-access-key
export AWS_SECRET_ACCESS_KEY=your-secret-key
export AWS_DEFAULT_REGION=us-east-1

# Or via AWS credentials file (~/.aws/credentials)
# Or via IAM roles (when running on EC2)
```

```python
# Or pass credentials programmatically
with open_iterable(
    's3://my-bucket/data.csv',
    iterableargs={
        'storage_options': {
            'key': 'your-access-key',
            'secret': 'your-secret-key',
            'client_kwargs': {'region_name': 'us-east-1'}
        }
    }
) as source:
    for row in source:
        print(row)
```

### Google Cloud Storage

GCS authentication uses Google Cloud credentials:

```bash
# Via environment variable
export GOOGLE_APPLICATION_CREDENTIALS=/path/to/service-account-key.json

# Or use Application Default Credentials (ADC)
gcloud auth application-default login
```

```python
# Or pass credentials programmatically
with open_iterable(
    'gs://my-bucket/data.csv',
    iterableargs={
        'storage_options': {
            'token': '/path/to/service-account-key.json'
        }
    }
) as source:
    for row in source:
        print(row)
```

### Azure Blob Storage

Azure authentication uses connection strings or service principals:

```bash
# Via environment variable
export AZURE_STORAGE_CONNECTION_STRING="DefaultEndpointsProtocol=https;AccountName=..."

# Or via Azure CLI
az login
```

```python
# Or pass connection string programmatically
with open_iterable(
    'az://my-container/data.csv',
    iterableargs={
        'storage_options': {
            'connection_string': 'DefaultEndpointsProtocol=https;AccountName=...'
        }
    }
) as source:
    for row in source:
        print(row)
```

## Format Detection

Format detection works identically for cloud storage URIs as for local files:

```python
# CSV detection from extension
with open_iterable('s3://bucket/data.csv') as source:
    # Automatically detected as CSV
    pass

# JSONL detection
with open_iterable('gs://bucket/data.jsonl') as source:
    # Automatically detected as JSONL
    pass

# Parquet detection
with open_iterable('s3://bucket/data.parquet') as source:
    # Automatically detected as Parquet
    pass
```

## Compression Support

All compression codecs work with cloud storage:

- **GZIP**: `.gz` files
- **BZIP2**: `.bz2` files
- **ZStandard**: `.zst`, `.zstd` files
- **LZ4**: `.lz4` files
- And other supported codecs

```python
# Compressed files work transparently
with open_iterable('s3://bucket/large.jsonl.gz') as source:
    # Automatically decompresses and parses
    for row in source:
        print(row)
```

## Streaming and Memory Efficiency

Cloud storage files are streamed, maintaining memory efficiency:

```python
# Large files are processed row-by-row without loading into memory
with open_iterable('s3://bucket/huge-dataset.csv') as source:
    for row in source:
        process(row)  # Memory-efficient streaming
```

## Engine Support

**Note**: The DuckDB engine does not support cloud storage URIs. Use `engine='internal'` (the default) for cloud storage files.

```python
# This works (internal engine, default)
with open_iterable('s3://bucket/data.csv') as source:
    pass

# This raises an error
with open_iterable('s3://bucket/data.csv', engine='duckdb') as source:
    pass  # ValueError: DuckDB engine does not support cloud storage URIs
```

## Error Handling

### Missing Dependencies

If cloud storage dependencies are not installed, you'll get a helpful error:

```python
# Without fsspec installed
open_iterable('s3://bucket/file.csv')
# ImportError: Cloud storage support requires 'fsspec'. Install it with: pip install fsspec

# Without s3fs installed (for S3)
open_iterable('s3://bucket/file.csv')
# ImportError: Cloud storage URI 's3://bucket/file.csv' requires 's3fs'. Install it with: pip install s3fs
```

### File Not Found

```python
try:
    with open_iterable('s3://bucket/nonexistent.csv') as source:
        pass
except FileNotFoundError as e:
    print(f"File not found: {e}")
```

### Authentication Errors

```python
try:
    with open_iterable('s3://bucket/data.csv') as source:
        pass
except RuntimeError as e:
    if "Authentication failed" in str(e):
        print("Check your AWS credentials")
```

## Examples

### Processing S3 Data Pipeline

```python
from iterable import open_iterable

# Read from S3, process, write to another S3 location
with open_iterable('s3://input-bucket/raw-data.jsonl') as source:
    with open_iterable('s3://output-bucket/processed-data.jsonl', mode='w') as dest:
        for row in source:
            # Process row
            processed = transform(row)
            dest.write(processed)
```

### Reading Multiple Cloud Files

```python
# Process files from different cloud providers
files = [
    's3://bucket1/data.csv',
    'gs://bucket2/data.csv',
    'az://container/data.csv'
]

for file_uri in files:
    with open_iterable(file_uri) as source:
        for row in source:
            process(row)
```

### Working with Compressed Cloud Data

```python
# Read compressed data from cloud storage
with open_iterable('s3://bucket/archive.jsonl.zst') as source:
    # Automatically handles ZStandard decompression
    for row in source:
        print(row)
```

## Troubleshooting

### Common Issues

1. **ImportError for fsspec/s3fs/gcsfs/adlfs**
   - Solution: Install the required dependencies: `pip install iterabledata[cloud]`

2. **Authentication errors**
   - Solution: Configure credentials via environment variables or `storage_options`

3. **File not found errors**
   - Solution: Verify the URI path and bucket/container name are correct
   - Check that you have read/write permissions

4. **DuckDB engine errors**
   - Solution: Use `engine='internal'` (default) for cloud storage files

### Performance Tips

- Cloud storage operations are network-bound; consider using compression to reduce transfer sizes
- For large files, streaming (row-by-row processing) is more memory-efficient than loading entire files
- Consider using cloud storage regions close to your compute resources for better performance

## Technical Details

Cloud storage support is implemented using [fsspec](https://filesystem-spec.readthedocs.io/), which provides a unified interface for various filesystems. The implementation:

- Detects cloud storage URIs automatically
- Opens files via fsspec to get file-like objects
- Passes these objects to existing format detection and codec logic
- Maintains full compatibility with local file processing

This means all existing format detection, codec support, and processing logic works identically for cloud storage as for local files.
