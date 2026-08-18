## MongoDB Examples

This directory contains examples demonstrating how to use IterableData with MongoDB databases.

## Prerequisites

1. **Install IterableData with MongoDB support**:
   
   **Option A: Development mode (recommended for testing examples)**:
   ```bash
   cd /path/to/iterabledata
   pip install -e ".[db]"
   ```
   
   **Option B: Install from PyPI**:
   ```bash
   pip install iterabledata[db]
   ```
   
   Or install pymongo separately:
   ```bash
   pip install iterabledata pymongo
   ```
   
   **Note**: If you're running examples from the project directory, make sure to run them from the project root or ensure the local code is in your Python path.

2. **MongoDB Instance**: Ensure you have a local MongoDB instance running on `localhost:27017`

3. **Test Data**: The examples use:
   - Database: `unicef`
   - Collection: `inddata`

   Make sure this database and collection exist with some data before running the examples.

## Running Examples

**Important**: Run examples from the project root directory to ensure the local MongoDB driver is used:

```bash
cd /path/to/iterabledata
python examples/mongodb/iterate.py
```

Or set PYTHONPATH:
```bash
cd examples/mongodb
PYTHONPATH=../.. python iterate.py
```

## Examples

### 1. `iterate.py` - Basic Iteration

Demonstrates how to iterate over MongoDB documents using `open_iterable()`.

**Usage**:
```bash
cd /path/to/iterabledata
python examples/mongodb/iterate.py
```

This script:
- Connects to MongoDB at `mongodb://localhost:27017/`
- Opens the `inddata` collection in the `unicef` database
- Iterates over all documents and prints them

### 2. `convert_to_parquet.py` - Convert to Parquet

Converts a MongoDB collection to a Parquet file using the `convert()` function.

**Usage**:
```bash
cd /path/to/iterabledata
python examples/mongodb/convert_to_parquet.py
```

**Note**: Parquet requires a fixed schema. The example uses several techniques to handle varying document structures:
- `adapt_schema=True` to adapt the schema from data
- `is_flatten=True` to flatten nested structures (converts nested fields to dot notation like `cinfo.parent`)
- `scan_limit=10000` to scan more documents for better schema inference

**Important**: The schema is determined from the first batch of data. If documents have fields that only appear later in the collection:
- Those fields will be automatically dropped (not included in the output)
- Missing fields in later documents will be filled with `None`
- This prevents schema mismatch errors but may result in data loss for fields that appear after the initial schema is set

If you need to preserve all fields regardless of when they appear:
- Convert to JSONL instead (more flexible with varying schemas)
- Increase `scan_limit` to scan more documents before setting the schema
- Pre-process data to ensure all documents have consistent structure

This script:
- Reads from MongoDB collection `unicef.inddata`
- Converts all documents to Parquet format
- Saves to `inddata.parquet`
- Shows progress during conversion

### 3. `convert_to_jsonl.py` - Convert to JSONL

Converts a MongoDB collection to a JSONL file using the `convert()` function.

**Usage**:
```bash
cd /path/to/iterabledata
python examples/mongodb/convert_to_jsonl.py
```

**Note**: JSONL format is more flexible than Parquet for documents with varying schemas, so this conversion is less likely to encounter schema issues.

This script:
- Reads from MongoDB collection `unicef.inddata`
- Converts all documents to JSONL format
- Saves to `inddata.jsonl`
- Shows progress during conversion

### 4. `convert_to_jsonl_zst.py` - Convert to JSONL.ZST with Maximum Compression

Converts a MongoDB collection to a ZStandard-compressed JSONL file with maximum compression level and a progress bar.

**Usage**:
```bash
cd /path/to/iterabledata
python examples/mongodb/convert_to_jsonl_zst.py
```

**Features**:
- Uses ZStandard compression with level 22 (maximum compression)
- Shows progress bar with document count
- Uses `open_iterable()` directly for fine-grained control over compression settings
- Produces highly compressed output files (smaller file size)

**Note**: Maximum compression (level 22) is slower but produces the smallest file size. For faster compression with good ratios, use level 3-6.

This script:
- Reads from MongoDB collection `unicef.inddata`
- Converts all documents to JSONL format
- Compresses with ZStandard at maximum level (22)
- Saves to `inddata.jsonl.zst`
- Shows progress bar during conversion

## Connection Details

All examples use:
- **Connection String**: `mongodb://localhost:27017/`
- **Database**: `unicef`
- **Collection**: `inddata`

To use different connection settings, modify the connection string and `iterableargs` in each script.

## Advanced Usage

### Filtering Documents

You can filter documents using the `filter` parameter:

```python
from iterable import open_iterable

with open_iterable(
    'mongodb://localhost:27017/',
    engine='mongo',
    iterableargs={
        'database': 'unicef',
        'collection': 'inddata',
        'filter': {'status': 'active'}  # MongoDB query dict
    }
) as source:
    for doc in source:
        print(doc)
```

### Projection (Field Selection)

Select specific fields using the `projection` parameter:

```python
iterableargs={
    'database': 'unicef',
    'collection': 'inddata',
    'projection': {'name': 1, 'age': 1, '_id': 0}  # Include name and age, exclude _id
}
```

### Sorting and Limiting

Sort and limit results:

```python
iterableargs={
    'database': 'unicef',
    'collection': 'inddata',
    'sort': [('created_at', -1)],  # Sort by created_at descending
    'limit': 100  # Limit to 100 documents
}
```

### Aggregation Pipeline

Use MongoDB aggregation pipeline for complex queries:

```python
iterableargs={
    'database': 'unicef',
    'collection': 'inddata',
    'pipeline': [
        {'$match': {'status': 'active'}},
        {'$group': {'_id': '$category', 'count': {'$sum': 1}}},
        {'$sort': {'count': -1}}
    ]
}
```

## Troubleshooting

### Connection Errors

If you get connection errors:
- Ensure MongoDB is running: `mongosh --eval "db.adminCommand('ping')"`
- Check the connection string format
- Verify network connectivity to MongoDB host

### Missing Database/Collection

If you get errors about missing database or collection:
- Verify the database and collection exist
- Check spelling of database and collection names
- Ensure you have read permissions

### Import Errors

If you get `ImportError` for pymongo:
- Install pymongo: `pip install pymongo`
- Or install with db extra: `pip install iterabledata[db]`
