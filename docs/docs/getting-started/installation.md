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

Some formats require extras. Install them as needed:

```bash
pip install iterabledata[parquet]
pip install iterabledata[excel]
pip install iterabledata[xml]
pip install iterabledata[duckdb]
pip install iterabledata[ai]
```

See `pyproject.toml` optional-dependencies (or the format page) for the full extras map.

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
