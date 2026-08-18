## Elasticsearch Examples

This directory contains examples demonstrating how to use IterableData with Elasticsearch indices.

## Prerequisites

1. **Install IterableData with Elasticsearch support**:
   
   **Option A: Development mode (recommended for testing examples)**:
   ```bash
   cd /path/to/iterabledata
   pip install -e ".[db]"
   ```
   
   **Option B: Install from PyPI**:
   ```bash
   pip install iterabledata[db]
   ```
   
   Or install elasticsearch separately:
   ```bash
   pip install iterabledata elasticsearch
   ```
   
   **Note**: If you're running examples from the project directory, make sure to run them from the project root or ensure the local code is in your Python path.

2. **Elasticsearch Instance**: Ensure you have a local Elasticsearch instance running on `http://localhost:9200`

3. **Test Data**: The examples use:
   - Index: `logs-2024-01`

   Make sure this index exists with some data before running the examples.

## Running Examples

**Important**: Run examples from the project root directory to ensure the local Elasticsearch driver is used:

```bash
cd /path/to/iterabledata
python examples/elasticsearch/iterate.py
```

Or set PYTHONPATH:
```bash
cd examples/elasticsearch
PYTHONPATH=../.. python iterate.py
```

## Examples

### 1. `iterate.py` - Basic Iteration

Demonstrates how to iterate over Elasticsearch documents using `open_iterable()`.

**Usage**:
```bash
cd /path/to/iterabledata
python examples/elasticsearch/iterate.py
```

This script:
- Connects to Elasticsearch at `http://localhost:9200`
- Opens the `logs-2024-01` index
- Iterates over all documents and prints them
- Uses `source_only=True` to return only document `_source` fields (excludes Elasticsearch metadata)

### 2. `convert_to_parquet.py` - Convert to Parquet

Converts an Elasticsearch index to a Parquet file using the `convert()` function.

**Usage**:
```bash
cd /path/to/iterabledata
python examples/elasticsearch/convert_to_parquet.py
```

**Note**: Parquet requires a fixed schema. The example uses several techniques to handle varying document structures:
- `adapt_schema=True` to adapt the schema from data
- `is_flatten=True` to flatten nested structures (converts nested fields to dot notation like `user.name`)
- `scan_limit=10000` to scan more documents for better schema inference

**Important**: The schema is determined from the first batch of data. If documents have fields that only appear later in the index:
- Those fields will be automatically dropped (not included in the output)
- Missing fields in later documents will be filled with `None`
- This prevents schema mismatch errors but may result in data loss for fields that appear after the initial schema is set

If you need to preserve all fields regardless of when they appear:
- Convert to JSONL instead (more flexible with varying schemas)
- Increase `scan_limit` to scan more documents before setting the schema
- Pre-process data to ensure all documents have consistent structure

This script:
- Reads from Elasticsearch index `logs-2024-01`
- Converts all documents to Parquet format
- Saves to `logs.parquet`
- Shows progress during conversion

### 3. `convert_to_jsonl.py` - Convert to JSONL

Converts an Elasticsearch index to a JSONL file using the `convert()` function.

**Usage**:
```bash
cd /path/to/iterabledata
python examples/elasticsearch/convert_to_jsonl.py
```

**Note**: JSONL format is more flexible than Parquet for documents with varying schemas, so this conversion is less likely to encounter schema issues.

This script:
- Reads from Elasticsearch index `logs-2024-01`
- Converts all documents to JSONL format
- Saves to `logs.jsonl`
- Shows progress during conversion

### 4. `convert_to_jsonl_zst.py` - Convert to JSONL.ZST with Maximum Compression

Converts an Elasticsearch index to a ZStandard-compressed JSONL file with maximum compression level and a progress bar.

**Usage**:
```bash
cd /path/to/iterabledata
python examples/elasticsearch/convert_to_jsonl_zst.py
```

**Features**:
- Uses ZStandard compression with level 22 (maximum compression)
- Shows progress bar with document count
- Uses `open_iterable()` directly for fine-grained control over compression settings
- Produces highly compressed output files (smaller file size)

**Note**: Maximum compression (level 22) is slower but produces the smallest file size. For faster compression with good ratios, use level 3-6.

This script:
- Reads from Elasticsearch index `logs-2024-01`
- Converts all documents to JSONL format
- Compresses with ZStandard at maximum level (22)
- Saves to `logs.jsonl.zst`
- Shows progress bar during conversion

## Connection Details

All examples use:
- **Connection URL**: `http://localhost:9200`
- **Index**: `logs-2024-01`

To use different connection settings, modify the connection URL and `iterableargs` in each script.

## Advanced Usage

### Filtering Documents

You can filter documents using the `body` parameter with Elasticsearch query DSL:

```python
from iterable import open_iterable

with open_iterable(
    'http://localhost:9200',
    engine='elasticsearch',
    iterableargs={
        'index': 'logs-2024-01',
        'body': {
            'query': {
                'bool': {
                    'must': [
                        {'match': {'status': 'error'}},
                        {'range': {'timestamp': {'gte': '2024-01-01'}}}
                    ]
                }
            }
        },
        'source_only': True
    }
) as source:
    for doc in source:
        print(doc)
```

### Source Filtering (Field Selection)

Select specific fields using `_source` in the query body:

```python
iterableargs={
    'index': 'logs-2024-01',
    'body': {
        'query': {'match_all': {}},
        '_source': ['timestamp', 'message', 'level']  # Include only these fields
    },
    'source_only': True
}
```

### Sorting

Sort results using the `sort` parameter:

```python
iterableargs={
    'index': 'logs-2024-01',
    'body': {'query': {'match_all': {}}},
    'sort': [{'timestamp': {'order': 'desc'}}],  # Sort by timestamp descending
    'source_only': True
}
```

### Scroll API for Large Indices

For large indices, use the scroll API for efficient pagination:

```python
iterableargs={
    'index': 'logs-2024-01',
    'body': {'query': {'match_all': {}}},
    'scroll': '5m',  # Keep scroll context alive for 5 minutes
    'size': 10000,   # Number of documents per scroll batch
    'source_only': True
}
```

### Limiting Results

Limit the number of documents returned:

```python
iterableargs={
    'index': 'logs-2024-01',
    'body': {
        'query': {'match_all': {}},
        'size': 100  # Limit to 100 documents
    },
    'source_only': True
}
```

### Timeout Configuration

Configure timeouts to handle slow queries or network issues:

```python
from iterable import open_iterable

with open_iterable(
    'http://localhost:9200',
    engine='elasticsearch',
    iterableargs={
        'index': 'logs-2024-01',
        'body': {'query': {'match_all': {}}},
        'source_only': True,
        'request_timeout': 30.0,  # Client-side timeout in seconds (float)
        # How long the client waits for a response before raising an error
        'timeout': '30s',  # Server-side timeout (string like "30s", "1m", "5m")
        # Passed to Elasticsearch server - internal timeout for the query
    }
) as source:
    for doc in source:
        print(doc)
```

**Timeout Types:**

- **`request_timeout`**: Client-side timeout (float in seconds). Controls how long the Python client waits for a response from Elasticsearch. If exceeded, the client raises a timeout error. Example: `30.0` (30 seconds)

- **`timeout`**: Server-side timeout (string). Passed to Elasticsearch server to control how long the server processes the query. Format: `"30s"`, `"1m"`, `"5m"`, etc. This is an internal timeout and doesn't guarantee the client will receive a response in that time.

**Setting Client-Level Default Timeout:**

You can also set a default `request_timeout` for all requests via `connect_args`:

```python
iterableargs={
    'index': 'logs-2024-01',
    'body': {'query': {'match_all': {}}},
    'connect_args': {
        'request_timeout': 60.0,  # Default timeout for all requests
        'api_key': 'your_api_key'
    }
}
```

## Troubleshooting

### Connection Errors

If you get connection errors:
- Ensure Elasticsearch is running: `curl http://localhost:9200`
- Check the connection URL format
- Verify network connectivity to Elasticsearch host
- For HTTPS/authentication, use: `https://user:password@localhost:9200`

### Missing Index

If you get errors about missing index:
- Verify the index exists: `curl http://localhost:9200/_cat/indices`
- Check spelling of index name
- Ensure you have read permissions

### Import Errors

If you get `ImportError` for elasticsearch:
- Install elasticsearch: `pip install elasticsearch`
- Or install with db extra: `pip install iterabledata[db]`
- Ensure elasticsearch version is >= 8.0: `pip install 'elasticsearch>=8.0'`

### Authentication

There are several ways to authenticate with Elasticsearch clusters:

#### 1. URL-based Authentication (Basic Auth)

Include credentials directly in the connection URL:

```python
from iterable import open_iterable

connection_url = "https://username:password@localhost:9200"

with open_iterable(
    connection_url,
    engine="elasticsearch",
    iterableargs={
        "index": "logs-2024-01",
        "body": {"query": {"match_all": {}}},
        "source_only": True,
    }
) as source:
    for doc in source:
        print(doc)
```

#### 2. API Key via `connect_args` (Recommended)

Use `connect_args` to pass API key credentials. This approach is consistent with how MongoDB and PostgreSQL drivers handle authentication.

The `api_key` parameter accepts either:
- **String format**: Just the API key itself
- **Tuple format**: `(id, api_key)` if you have both

```python
from iterable import open_iterable

# Option A: API key as string (most common)
with open_iterable(
    "https://localhost:9200",
    engine="elasticsearch",
    iterableargs={
        "index": "logs-2024-01",
        "body": {"query": {"match_all": {}}},
        "source_only": True,
        "connect_args": {
            "api_key": "your_api_key_string"  # Just the API key
        }
    }
) as source:
    for doc in source:
        print(doc)

# Option B: API key as tuple (id, api_key)
with open_iterable(
    "https://localhost:9200",
    engine="elasticsearch",
    iterableargs={
        "index": "logs-2024-01",
        "body": {"query": {"match_all": {}}},
        "source_only": True,
        "connect_args": {
            "api_key": ("id", "api_key")  # Tuple format
        }
    }
) as source:
    for doc in source:
        print(doc)
```

#### 3. Basic Auth via `connect_args`

Pass username and password using `basic_auth`:

```python
from iterable import open_iterable

with open_iterable(
    "https://localhost:9200",
    engine="elasticsearch",
    iterableargs={
        "index": "logs-2024-01",
        "body": {"query": {"match_all": {}}},
        "source_only": True,
        "connect_args": {
            "basic_auth": ("username", "password")
        }
    }
) as source:
    for doc in source:
        print(doc)
```

#### 4. Pre-configured Elasticsearch Client

Create an Elasticsearch client with authentication and pass it directly:

```python
from elasticsearch import Elasticsearch
from iterable import open_iterable

# Create client with API key (string or tuple format)
es = Elasticsearch(
    ['https://localhost:9200'],
    api_key='your_api_key_string'  # Or api_key=('id', 'api_key')
)

# Or with basic auth
# es = Elasticsearch(
#     ['https://localhost:9200'],
#     basic_auth=('username', 'password')
# )

# Pass the client object to open_iterable
with open_iterable(
    es,
    engine='elasticsearch',
    iterableargs={
        "index": "logs-2024-01",
        "body": {"query": {"match_all": {}}},
        "source_only": True,
    }
) as source:
    for doc in source:
        print(doc)
```

#### Using Environment Variables

For security, you can load credentials from environment variables:

```python
import os
from iterable import open_iterable

# Option A: Just API key (most common)
api_key = os.getenv("ELASTICSEARCH_API_KEY")

with open_iterable(
    "https://localhost:9200",
    engine="elasticsearch",
    iterableargs={
        "index": "logs-2024-01",
        "body": {"query": {"match_all": {}}},
        "source_only": True,
        "connect_args": {
            "api_key": api_key  # Just the API key string
        }
    }
) as source:
    for doc in source:
        print(doc)

# Option B: API key with ID
api_key_id = os.getenv("ELASTICSEARCH_API_KEY_ID")
api_key = os.getenv("ELASTICSEARCH_API_KEY")

with open_iterable(
    "https://localhost:9200",
    engine="elasticsearch",
    iterableargs={
        "index": "logs-2024-01",
        "body": {"query": {"match_all": {}}},
        "source_only": True,
        "connect_args": {
            "api_key": (api_key_id, api_key)  # Tuple format
        }
    }
) as source:
    for doc in source:
        print(doc)
```

**Note**: The `connect_args` approach (options 2 and 3) is recommended as it keeps credentials separate from the connection URL and is consistent with how other database drivers (MongoDB, PostgreSQL) handle authentication.
