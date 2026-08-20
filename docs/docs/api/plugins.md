---
sidebar_position: 20
title: Plugin System
description: Extend IterableData with custom formats, codecs, database drivers, and more
---

# Plugin System

IterableData provides a comprehensive plugin system that enables third-party developers to extend the library with custom formats, codecs, database drivers, validation rules, and engines without modifying the core library.

## Overview

The plugin system uses Python's entry point mechanism (via `setuptools`/`pip`) for automatic plugin discovery. Plugins are discovered lazily when needed and integrated seamlessly with existing IterableData functionality.

### Key Features

- **Automatic Discovery**: Plugins are discovered via entry points - no manual registration needed
- **Backward Compatible**: Built-in formats/codecs take precedence over plugins
- **Error Isolation**: Plugin errors don't crash the core library
- **Metadata Support**: Plugins can provide version, author, and custom metadata
- **Programmatic Registration**: Alternative to entry points for dynamic registration

## Plugin Types

The plugin system supports five types of plugins:

1. **Format Plugins** - Custom data formats
2. **Codec Plugins** - Custom compression codecs
3. **Database Driver Plugins** - Custom database drivers
4. **Validation Rule Plugins** - Custom validation rules
5. **Engine Plugins** - Custom processing engines

## Creating a Format Plugin

### Step 1: Create Your Format Class

```python
# myplugin/format.py
from iterable.base import BaseFileIterable
from iterable.types import Row

class CustomFormatIterable(BaseFileIterable):
    """Custom format implementation."""
    
    @staticmethod
    def id() -> str:
        return "customformat"
    
    @staticmethod
    def fileexts() -> list[str]:
        return [".custom", ".cf"]
    
    def read(self, skip_empty: bool = True) -> Row:
        """Read a row from the custom format."""
        # Your implementation here
        ...
    
    def read_bulk(self, num: int = 1000) -> list[Row]:
        """Read multiple rows."""
        # Your implementation here
        ...
```

### Step 2: Register via Entry Point

In your `pyproject.toml`:

```toml
[project.entry-points."iterabledata.formats"]
customformat = "myplugin.format:CustomFormatIterable"
```

Or in `setup.py`:

```python
setup(
    name="iterabledata-plugin-customformat",
    entry_points={
        "iterabledata.formats": [
            "customformat = myplugin.format:CustomFormatIterable",
        ],
    },
)
```

### Step 3: Install and Use

```bash
pip install -e .
```

Now your format can be used just like built-in formats:

```python
from iterable import open_iterable

with open_iterable("data.custom") as source:
    for row in source:
        print(row)
```

## Creating a Codec Plugin

```python
# myplugin/codec.py
from iterable.codecs.base import BaseCodec

class CustomCodec(BaseCodec):
    """Custom compression codec."""
    
    @staticmethod
    def fileexts() -> list[str]:
        return [".custom", ".cc"]
    
    def open(self) -> None:
        """Open the codec."""
        # Your implementation here
        ...
    
    def read(self, size: int = -1) -> bytes:
        """Read compressed data."""
        # Your implementation here
        ...
```

Register in `pyproject.toml`:

```toml
[project.entry-points."iterabledata.codecs"]
customcodec = "myplugin.codec:CustomCodec"
```

## Creating a Database Driver Plugin

```python
# myplugin/db.py
from iterable.db.base import DBDriver
from collections.abc import Iterator
from iterable.types import Row

class CustomDBDriver(DBDriver):
    """Custom database driver."""
    
    def connect(self) -> None:
        """Establish database connection."""
        # Your implementation here
        ...
    
    def iterate(self) -> Iterator[Row]:
        """Return iterator of rows."""
        # Your implementation here
        ...
```

Register in `pyproject.toml`:

```toml
[project.entry-points."iterabledata.database_drivers"]
customdb = "myplugin.db:CustomDBDriver"
```

Use with `open_iterable()`:

```python
with open_iterable(
    "customdb://connection_string",
    engine="customdb",
    iterableargs={"query": "SELECT * FROM table"}
) as source:
    for row in source:
        print(row)
```

## Creating a Validation Rule Plugin

```python
# myplugin/validation.py
def validate_custom_field(value: Any) -> tuple[bool, str | None]:
    """Validate a custom field."""
    if not value:
        return False, "Field is required"
    if len(str(value)) < 5:
        return False, "Field must be at least 5 characters"
    return True, None
```

Register in `pyproject.toml`:

```toml
[project.entry-points."iterabledata.validation_rules"]
custom.field = "myplugin.validation:validate_custom_field"
```

Use with validation hooks:

```python
from iterable.helpers.validation import rules_validator

rules = {"field_name": ["custom.field"]}
hook = rules_validator(rules)

with open_iterable("data.csv", iterableargs={"validation_hook": hook}) as source:
    for row in source:
        process(row)
```

## Programmatic Registration

Instead of entry points, you can register plugins programmatically:

```python
from iterable.plugins import register_format

register_format(
    "customformat",
    "myplugin.format",
    "CustomFormatIterable",
    metadata={"version": "1.0.0", "author": "Your Name"}
)
```

## Plugin Discovery

Plugins are discovered automatically when IterableData is first used. Discovery happens lazily and is cached for performance.

### Manual Discovery

You can manually trigger plugin discovery:

```python
from iterable.plugins import discover_plugins

discover_plugins()
```

### Checking Registered Plugins

```python
from iterable.plugins import get_plugin_registry

registry = get_plugin_registry()

# List all registered formats (including plugins)
formats = registry.list_formats()
print(f"Registered formats: {formats}")

# Get plugin metadata
metadata = registry.get_metadata("format:customformat")
print(f"Plugin metadata: {metadata}")
```

## Priority System

Built-in formats and codecs always take precedence over plugins. If a plugin registers a format with the same ID as a built-in format, the built-in format will be used.

```python
# This will NOT override the built-in CSV format
register_format("csv", "myplugin.format", "MyCSVFormat")

# Built-in CSV is still used
from iterable.helpers.detect import _get_format_registry
registry = _get_format_registry()
assert registry["csv"] == ("iterable.datatypes.csv", "CSVIterable")
```

## Error Handling

Plugin errors are isolated and don't crash the core library:

- **Import Errors**: If a plugin's dependencies are missing, the plugin is skipped
- **Registration Errors**: Invalid entry points are logged but don't stop discovery
- **Runtime Errors**: Plugin errors during use are handled according to error policies

## Plugin Metadata

Plugins can provide metadata for version tracking and documentation:

```python
register_format(
    "customformat",
    "myplugin.format",
    "CustomFormatIterable",
    metadata={
        "version": "1.0.0",
        "author": "Your Name",
        "description": "Custom format plugin",
        "homepage": "https://example.com/plugin"
    }
)
```

Metadata is accessible via:

```python
registry = get_plugin_registry()
metadata = registry.get_metadata("format:customformat")
```

## Testing Plugins

When testing plugins, you may want to reset the discovery state:

```python
from iterable.plugins import reset_discovery, discover_plugins

# Reset discovery state
reset_discovery()

# Re-discover plugins
discover_plugins()
```

## Complete Example

Here's a complete example of a format plugin package:

### Project Structure

```
iterabledata-plugin-customformat/
├── pyproject.toml
├── src/
│   └── customformat/
│       ├── __init__.py
│       └── format.py
└── README.md
```

### `pyproject.toml`

```toml
[build-system]
requires = ["setuptools>=61.0", "wheel"]
build-backend = "setuptools.build_meta"

[project]
name = "iterabledata-plugin-customformat"
version = "1.0.0"
description = "Custom format plugin for IterableData"
requires-python = ">=3.10"
dependencies = ["iterabledata"]

[project.entry-points."iterabledata.formats"]
customformat = "customformat.format:CustomFormatIterable"
```

### `src/customformat/format.py`

```python
from iterable.base import BaseFileIterable
from iterable.types import Row

class CustomFormatIterable(BaseFileIterable):
    @staticmethod
    def id() -> str:
        return "customformat"
    
    @staticmethod
    def fileexts() -> list[str]:
        return [".custom", ".cf"]
    
    def read(self, skip_empty: bool = True) -> Row:
        # Implementation
        ...
```

### Installation and Usage

```bash
pip install -e .
```

```python
from iterable import open_iterable

with open_iterable("data.custom") as source:
    for row in source:
        print(row)
```

## Reference plugin package

A minimal third-party package that adds one format end to end:

```text
iterabledata-plugin-acme/
  pyproject.toml
  src/iterabledata_plugin_acme/
    __init__.py
    acme.py          # BaseFileIterable subclass
  tests/test_acme.py
  README.md
```

`pyproject.toml`:

```toml
[project]
name = "iterabledata-plugin-acme"
version = "0.1.0"
dependencies = ["iterabledata>=1.0"]

[project.entry-points."iterabledata.formats"]
acme = "iterabledata_plugin_acme.acme:AcmeIterable"
```

Implement `AcmeIterable` like any in-tree format (`id()`, `fileexts()`, `read()`, raise `WriteNotSupportedError` if read-only). Then:

```bash
pip install -e ./iterabledata-plugin-acme
```

```python
from iterable import open_iterable

with open_iterable("sample.acme") as source:
    for row in source:
        print(row)
```

Built-in format ids always win over plugins with the same id. For an in-tree checklist (registry, detection, docs site), see [Adding formats](/development/adding-formats).

## Best Practices

1. **Follow Naming Conventions**: Use descriptive plugin IDs (e.g., `customformat` not `cf`)
2. **Provide Metadata**: Include version, author, and description in metadata
3. **Handle Errors Gracefully**: Implement proper error handling in your plugin
4. **Test Thoroughly**: Test your plugin with various data sources
5. **Document Usage**: Provide clear documentation and examples
6. **Version Compatibility**: Test with different IterableData versions

## Related Topics

- [Format Detection](/api/open-iterable) - How formats are detected
- [Database Engines](/api/database-engines) - Database driver plugins
- [Validation Hooks](/api/validate) - Validation rule plugins
- [Base Classes](/api/base-iterable) - Base classes for plugin development
