---
sidebar_position: 6
title: Exception Hierarchy
description: Comprehensive exception hierarchy for error handling
---

# Exception Hierarchy

IterableData provides a comprehensive exception hierarchy that allows you to catch and handle specific error types programmatically. All exceptions inherit from `IterableDataError`, allowing you to catch all library errors with a single exception handler.

## Base Exception

### `IterableDataError`

Base exception for all iterable data errors. All exceptions raised by the IterableData library inherit from this class.

**Attributes:**
- `message` (str): Human-readable error message
- `error_code` (str, optional): Error code for programmatic handling

**Example:**
```python
from iterable.exceptions import IterableDataError

try:
    # Some iterable operation
    pass
except IterableDataError as e:
    print(f"Error: {e.message}")
    if e.error_code:
        print(f"Error code: {e.error_code}")
```

## Format Exceptions

### `FormatError`

Base exception for format-specific errors. Raised when an error occurs related to data format handling.

**Attributes:**
- `message` (str): Human-readable error message
- `format_id` (str, optional): Format identifier (e.g., "csv", "json")
- `error_code` (str, optional): Error code for programmatic handling

### `FormatNotSupportedError`

Format is not supported or not available. Raised when a requested format is not supported by the library, or when required dependencies are missing.

**Error Code:** `FORMAT_NOT_SUPPORTED`

**Attributes:**
- `format_id` (str): Format identifier that is not supported
- `reason` (str, optional): Reason why format is not supported

**Example:**
```python
from iterable.exceptions import FormatNotSupportedError

try:
    with open_iterable('data.parquet') as source:
        pass
except FormatNotSupportedError as e:
    print(f"Format '{e.format_id}' not supported: {e.reason}")
    # Install missing dependencies: pip install pyarrow
```

### `FormatDetectionError`

Could not detect file format. Raised when the system cannot determine the format of a file, either from filename extension or content analysis.

**Error Code:** `FORMAT_DETECTION_FAILED`

**Attributes:**
- `filename` (str, optional): Filename that could not be detected
- `reason` (str, optional): Reason why detection failed

**Example:**
```python
from iterable.exceptions import FormatDetectionError

try:
    with open_iterable('data.unknown') as source:
        pass
except FormatDetectionError as e:
    print(f"Could not detect format for '{e.filename}': {e.reason}")
    # Try specifying format explicitly or check file content
```

### `FormatParseError`

Format parsing failed. Raised when a file cannot be parsed as the expected format, typically due to malformed data.

**Error Code:** `FORMAT_PARSE_FAILED`

**Attributes:**
- `format_id` (str): Format identifier
- `position` (int, optional): Position in file where error occurred

**Example:**
```python
from iterable.exceptions import FormatParseError

try:
    with open_iterable('malformed.json') as source:
        for row in source:
            pass
except FormatParseError as e:
    print(f"Failed to parse {e.format_id} format")
    if e.position:
        print(f"Error at position: {e.position}")
```

## Codec Exceptions

### `CodecError`

Base exception for compression codec errors. Raised when an error occurs related to compression/decompression.

**Attributes:**
- `message` (str): Human-readable error message
- `codec_name` (str, optional): Codec name (e.g., "gzip", "bzip2")
- `error_code` (str, optional): Error code for programmatic handling

### `CodecNotSupportedError`

Compression codec is not supported. Raised when a requested codec is not available, typically due to missing dependencies.

**Error Code:** `CODEC_NOT_SUPPORTED`

**Attributes:**
- `codec_name` (str): Codec name that is not supported
- `reason` (str, optional): Reason why codec is not supported

**Example:**
```python
from iterable.exceptions import CodecNotSupportedError

try:
    with open_iterable('data.csv.lz4') as source:
        pass
except CodecNotSupportedError as e:
    print(f"Codec '{e.codec_name}' not supported: {e.reason}")
    # Install missing dependencies: pip install lz4
```

### `CodecDecompressionError`

Decompression failed. Raised when decompressing data fails.

**Error Code:** `CODEC_DECOMPRESSION_FAILED`

**Attributes:**
- `codec_name` (str): Codec name
- `message` (str, optional): Additional error message

**Example:**
```python
from iterable.exceptions import CodecDecompressionError

try:
    with open_iterable('corrupted.csv.gz') as source:
        pass
except CodecDecompressionError as e:
    print(f"Failed to decompress using {e.codec_name}: {e.message}")
    # File may be corrupted or incomplete
```

### `CodecCompressionError`

Compression failed. Raised when compressing data fails.

**Error Code:** `CODEC_COMPRESSION_FAILED`

**Attributes:**
- `codec_name` (str): Codec name
- `message` (str, optional): Additional error message

## Read/Write Exceptions

### `ReadError`

Base exception for reading errors. Raised when an error occurs during data reading operations.

**Attributes:**
- `message` (str): Human-readable error message
- `filename` (str, optional): Filename being read
- `error_code` (str, optional): Error code for programmatic handling

### `WriteError`

Base exception for writing errors. Raised when an error occurs during data writing operations.

**Attributes:**
- `message` (str): Human-readable error message
- `filename` (str, optional): Filename being written
- `error_code` (str, optional): Error code for programmatic handling

### `WriteNotSupportedError`

The format does not implement writing (or the current dataset layout cannot be written). Also available as `from iterable import WriteNotSupportedError`.

**Error Code:** `WRITE_NOT_SUPPORTED`

**Attributes:**
- `format_id` (str): Format identifier
- `reason` (str, optional): Why writing is not supported

```python
from iterable import open_iterable, WriteNotSupportedError

try:
    with open_iterable("data.pcap", mode="w") as dest:
        dest.write({"timestamp": 1234567890})
except WriteNotSupportedError as e:
    print(f"{e.format_id}: {e.reason}")
```

### `StreamingNotSupportedError`

Format doesn't support streaming. Raised when a streaming operation is attempted on a format that doesn't support streaming (e.g., formats that load entire file).

**Error Code:** `STREAMING_NOT_SUPPORTED`

**Attributes:**
- `format_id` (str): Format identifier that doesn't support streaming
- `reason` (str, optional): Reason why streaming is not supported

**Example:**
```python
from iterable.exceptions import StreamingNotSupportedError

try:
    # Attempt streaming operation on non-streaming format
    pass
except StreamingNotSupportedError as e:
    print(f"Format '{e.format_id}' does not support streaming: {e.reason}")
```

## Resource Exceptions

### `ResourceError`

Base exception for resource management errors. Raised when an error occurs related to resource management (file handles, streams, connections, etc.).

**Attributes:**
- `message` (str): Human-readable error message
- `error_code` (str, optional): Error code for programmatic handling

### `StreamNotSeekableError`

Stream is not seekable. Raised when an operation requires seeking (e.g., `reset()`) but the stream doesn't support seeking.

**Error Code:** `STREAM_NOT_SEEKABLE`

**Attributes:**
- `operation` (str, optional): Operation that requires seeking

**Example:**
```python
from iterable.exceptions import StreamNotSeekableError

try:
    source = open_iterable('data.csv')
    source.read()
    source.reset()  # Requires seeking
except StreamNotSeekableError as e:
    print(f"Stream is not seekable (required for {e.operation})")
    # Cannot reset non-seekable streams (e.g., network streams)
```

### `ResourceLeakError`

Resource leak detected. Raised when a resource (file, connection, etc.) is not properly closed.

**Error Code:** `RESOURCE_LEAK`

**Attributes:**
- `resource_type` (str, optional): Type of resource that leaked

## Error Handling Best Practices

### Catching Specific Exceptions

```python
from iterable import open_iterable
from iterable.exceptions import (
    FormatDetectionError,
    FormatNotSupportedError,
    FormatParseError,
    CodecError,
    ReadError
)

try:
    with open_iterable('data.unknown') as source:
        for row in source:
            process(row)
except FormatDetectionError as e:
    # Handle format detection failure
    print(f"Could not detect format: {e.reason}")
    # Try with explicit format or check file content
except FormatNotSupportedError as e:
    # Handle unsupported format
    print(f"Format '{e.format_id}' not supported: {e.reason}")
    # Install missing dependencies or use different format
except FormatParseError as e:
    # Handle parsing errors
    print(f"Failed to parse {e.format_id} format")
    if e.position:
        print(f"Error at position: {e.position}")
except CodecError as e:
    # Handle compression errors
    print(f"Compression error with {e.codec_name}: {e.message}")
    # Check file integrity or try different codec
except ReadError as e:
    # Handle read errors
    print(f"Read error: {e.message}")
except Exception as e:
    # Catch-all for unexpected errors
    print(f"Unexpected error: {e}")
```

### Catching All IterableData Errors

```python
from iterable import open_iterable
from iterable.exceptions import IterableDataError

try:
    with open_iterable('data.csv') as source:
        for row in source:
            process(row)
except IterableDataError as e:
    # Catch all IterableData errors
    print(f"IterableData error: {e.message}")
    if e.error_code:
        print(f"Error code: {e.error_code}")
```

### Using Error Codes

```python
from iterable import open_iterable
from iterable.exceptions import IterableDataError

try:
    with open_iterable('data.parquet') as source:
        pass
except IterableDataError as e:
    if e.error_code == "FORMAT_NOT_SUPPORTED":
        # Install missing dependencies
        print("Installing required dependencies...")
    elif e.error_code == "FORMAT_DETECTION_FAILED":
        # Try alternative detection method
        print("Trying alternative format detection...")
    elif e.error_code == "CODEC_DECOMPRESSION_FAILED":
        # Check file integrity
        print("File may be corrupted...")
```

## Error Code Reference

| Error Code | Exception | Description |
|------------|-----------|-------------|
| `FORMAT_NOT_SUPPORTED` | `FormatNotSupportedError` | Format is not supported or dependencies missing |
| `FORMAT_DETECTION_FAILED` | `FormatDetectionError` | Could not detect file format |
| `FORMAT_PARSE_FAILED` | `FormatParseError` | Format parsing failed |
| `CODEC_NOT_SUPPORTED` | `CodecNotSupportedError` | Compression codec is not supported |
| `CODEC_DECOMPRESSION_FAILED` | `CodecDecompressionError` | Decompression failed |
| `CODEC_COMPRESSION_FAILED` | `CodecCompressionError` | Compression failed |
| `STREAMING_NOT_SUPPORTED` | `StreamingNotSupportedError` | Format doesn't support streaming |
| `STREAM_NOT_SEEKABLE` | `StreamNotSeekableError` | Stream doesn't support seeking |
| `RESOURCE_LEAK` | `ResourceLeakError` | Resource leak detected |

## See Also

- [open_iterable()](/api/open-iterable) - Main entry point for opening files
- [BaseIterable Methods](/api/base-iterable) - Methods available on iterable objects
- [Troubleshooting](/getting-started/troubleshooting) - Common issues and solutions
