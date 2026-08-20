---
sidebar_position: 1
title: Installation
description: How to install Iterable Data library
---

# Installation

Iterable Data is a Python library for reading and writing data files row by row in a consistent, iterator-based interface. It provides a unified API for working with various data formats (CSV, JSON, Parquet, XML, etc.) similar to `csv.DictReader` but supporting many more formats.

## Requirements

- Python 3.10 or higher

## Install from PyPI

The PyPI package is **iterabledata**. The import package is **iterable**:

```bash
pip install iterabledata
```

```python
from iterable import open_iterable
```

## Install from Source

To install the latest development version from source:

```bash
git clone https://github.com/datenoio/iterabledata.git
cd iterabledata
pip install -e ".[dev]"
```

## Optional Dependencies

Some formats and engines need extras. Install only what you use:

```bash
pip install iterabledata[parquet]      # Parquet, Arrow, GeoParquet
pip install iterabledata[excel]        # XLS / XLSX
pip install iterabledata[xml]          # XML, ZIPXML, several geospatial XML formats
pip install iterabledata[duckdb]       # DuckDB engine and .duckdb files
pip install iterabledata[compression]  # zstd, brotli, lz4, snappy, lzo, 7z
pip install iterabledata[geospatial]   # GeoJSON, Shapefile, FlatGeobuf, Fiona/GDAL
pip install iterabledata[cloud]        # s3://, gs://, az:// via fsspec
pip install iterabledata[db]           # SQL/NoSQL engines and ingest
pip install iterabledata[ai]           # LLM documentation generation
pip install iterabledata[mcp]          # iterable-mcp stdio server
```

### Extras by area

| Extra | What it enables |
|-------|-----------------|
| `parquet`, `orc`, `avro`, `vortex`, `npy` | Columnar / binary analytics formats |
| `excel`, `xlsb`, `ods` | Spreadsheets |
| `xml`, `html`, `rdf` | Markup and RDF |
| `geospatial`, `lidar`, `mvt`, `topojson` | Spatial formats |
| `stats`, `rdata`, `mat`, `hdf5`, `zarr`, `netcdf`, `cdf` | Scientific / stats |
| `alignment`, `bio` | SAM/BAM/CRAM, genomic VCF, BED/GFF/GTF extras |
| `geophysical` | SEG-Y, GRIB2, miniSEED |
| `lakehouse`, `ducklake`, `paimon`, `paimon-row`, `paimon-mosaic`, `paimon-table` | Lakehouse tables and Paimon files |
| `otlp`, `protobuf` | OpenTelemetry and generic protobuf |
| `db`, `db-sql`, `db-nosql`, `db-ingest` | Database engines and ingest |
| `dataframes`, `pydantic` | pandas/Polars/Dask bridges and typed models |
| `cloud` | S3, GCS, Azure |
| `ai`, `anthropic`, `google-genai`, `langchain`, `mcp`, `agents` | LLM and agent surfaces |
| `compression` | Optional codecs (see [Codecs](/api/codecs)) |
| `all` | Everything except `dev` |
| `dev` | Tests, ruff, mypy, pre-commit |

The full pin list is in `pyproject.toml` `[project.optional-dependencies]`. Format pages name the extra they need.

## Verify Installation

You can verify the installation by importing the library:

```python
from iterable import open_iterable

# If this runs without errors, installation was successful
print("Iterable Data installed successfully!")
```

## Next Steps

- [Quick Start Guide](/getting-started/quick-start) - Get up and running quickly
- [When to use IterableData](/getting-started/when-to-use) - vs pandas and the standard library
- [Cookbook](/getting-started/cookbook) - prompt-shaped recipes
- [Basic Usage](/getting-started/basic-usage) - Learn common patterns
- [Supported Formats](/formats/) - See all available formats
