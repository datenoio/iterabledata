# Apache Iceberg Format

## Description

Apache Iceberg is an open table format for huge analytic tables. It provides schema evolution, hidden partitioning, and time travel capabilities. Iceberg tables are managed through catalogs and store metadata separately from data.

## File Extensions

- No specific extension (Iceberg tables are managed through catalogs)

## Implementation Details

### Reading

The Iceberg implementation:
- Uses `pyiceberg` library for reading
- Requires `catalog_name` and `table_name` parameters
- Loads table from catalog
- Scans table and converts to dictionaries
- Supports catalog properties file

### Writing

Writes use PyIceberg `append` against a SQL (or other) catalog. Pass catalog properties and set `create_table=True` when the table may not exist yet:

```python
catalog = {
    "type": "sql",
    "uri": "sqlite:///catalog.db",
    "warehouse": "file:///path/to/warehouse",
}
with open_iterable("/path/to/warehouse", mode="w", iterableargs={
    "format": "iceberg",
    "catalog_name": "default",
    "table_name": "demo.people",
    "catalog": catalog,
    "create_table": True,
}) as dest:
    dest.write_bulk([{"id": 1, "name": "Alice"}])
```

Requires `pyiceberg` with SQL catalog extras (e.g. `sqlalchemy` / `pyiceberg[sql-sqlite]`).

### Key Features

- **Catalog-based**: Tables managed through catalogs
- **Schema evolution**: Handles schema changes
- **Hidden partitioning**: Automatic partitioning
- **Time travel**: Access historical snapshots
- **Totals support**: Can count total rows

## Usage

```python
from iterable import open_iterable

# Reading Iceberg table
with open_iterable('catalog.properties', iterableargs={
    'catalog_name': 'my_catalog',
    'table_name': 'my_table'
}) as source:
    for row in source:
        print(row)

# Discover available tables in catalog
from iterable.datatypes.iceberg import IcebergIterable

# Before opening - discover tables
iterable = IcebergIterable(
    filename='catalog.properties',
    catalog_name='my_catalog',
    table_name='dummy_table'  # Required but may not be used for listing
)
tables = iterable.list_tables('catalog.properties')
print(f"Available tables: {tables}")

# After opening - list all tables (reuses catalog connection)
source = open_iterable('catalog.properties', iterableargs={
    'catalog_name': 'my_catalog',
    'table_name': 'my_table'
})
all_tables = source.list_tables()  # Reuses catalog connection
print(f"All tables: {all_tables}")

# Process different tables
for table_name in all_tables:
    with open_iterable('catalog.properties', iterableargs={
        'catalog_name': 'my_catalog',
        'table_name': table_name
    }) as source:
        print(f"Processing table: {table_name}")
        for row in source:
            process(row)
```

### Discovering Available Tables

Iceberg catalogs can contain multiple tables. Use `list_tables()` to discover available tables:

```python
from iterable.datatypes.iceberg import IcebergIterable

# Before opening - discover tables
iterable = IcebergIterable(
    filename='catalog.properties',
    catalog_name='my_catalog',
    table_name='dummy_table'  # Required parameter
)
tables = iterable.list_tables('catalog.properties')
print(f"Available tables: {tables}")
# Output: ['customers', 'orders', 'products']

# After opening - list all tables (reuses catalog connection)
source = open_iterable('catalog.properties', iterableargs={
    'catalog_name': 'my_catalog',
    'table_name': 'customers'
})
all_tables = source.list_tables()  # Reuses catalog connection
print(f"All tables: {all_tables}")
```

## Parameters

- `catalog_name` (str): **Required** - Name of the Iceberg catalog
- `table_name` (str): **Required** - Name of the table in the catalog
- `filename` (str): Optional path to catalog properties file

## Limitations

1. **pyiceberg dependency**: Requires `pyiceberg` (SQL catalog extras for local catalogs, e.g. `pyiceberg[sql-sqlite]`)
2. **Catalog required**: Must have catalog and table names
3. **Flat data only**: Only supports tabular data
4. **Configuration**: Requires proper catalog configuration
5. **Write**: Appends via PyIceberg; set `create_table=True` when the table may not exist yet

## Compression Support

Iceberg uses underlying file formats (typically Parquet) which have built-in compression. Iceberg tables themselves are managed through catalogs.

## Use Cases

- **Data lakes**: Managing large analytic tables
- **Schema evolution**: When schemas change frequently
- **Partitioning**: Automatic data partitioning
- **Time travel**: Accessing historical data versions

## Related Formats

- [Parquet](parquet.md) - Common underlying format
- [Delta Lake](delta.md) - Similar table format
- [Hudi](hudi.md) - Another data lake format
