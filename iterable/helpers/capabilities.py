"""Format capability reporting module.

This module provides functions to query format capabilities programmatically,
allowing users to discover what operations and features are supported by each data format.
"""

from __future__ import annotations

import inspect
from typing import TYPE_CHECKING

from ..exceptions import FormatDetectionError
from .detect import _get_format_registry, _load_symbol
from .format_registry import build_read_only_formats, get_descriptor

if TYPE_CHECKING:
    from ..base import BaseIterable

# Capability cache: format_id -> capabilities dict
_CAPABILITY_CACHE: dict[str, dict[str, bool | None]] = {}


def _is_read_only(format_id: str) -> bool:
    """Return True when the format is known not to support writing."""
    fid = format_id.lower()
    desc = get_descriptor(fid)
    if desc is not None:
        return not desc.writable
    # Orphan ids (e.g. ``zipped``) not backed by a descriptor entry.
    return fid in build_read_only_formats()


def _detect_capabilities(format_class: type[BaseIterable]) -> dict[str, bool | None]:
    """Detect capabilities for a format class by introspection.

    Args:
        format_class: The format class to introspect

    Returns:
        Dictionary with capability flags (True/False/None)
    """
    caps: dict[str, bool | None] = {
        "readable": None,
        "writable": None,
        "bulk_read": None,
        "bulk_write": None,
        "totals": None,
        "streaming": None,
        "flat_only": None,
        "tables": None,
        "compression": None,
        "nested": None,
    }

    # Check for read/write methods
    caps["readable"] = hasattr(format_class, "read") and callable(getattr(format_class, "read", None))

    # Check for write support - first check READ_ONLY_FORMATS registry for quick lookup
    format_id = None
    try:
        if hasattr(format_class, "id") and callable(getattr(format_class, "id", None)):
            format_id = format_class.id()
    except (AttributeError, TypeError):
        pass

    # Quick check via format descriptor (falls back to legacy read-only set for orphans).
    if format_id and _is_read_only(format_id):
        caps["writable"] = False
    else:
        # Need to distinguish between actual implementation and base class default
        has_write_method = hasattr(format_class, "write") and callable(getattr(format_class, "write", None))
        if has_write_method:
            # Check if write() is actually implemented (not just base class default)
            # Base class raises WriteNotSupportedError, so we need to check if the method
            # is overridden with actual implementation
            try:
                # Get the write method
                write_method = format_class.write
                # Check if it's the base class method (BaseIterable.write)
                from ..base import BaseIterable

                if write_method is BaseIterable.write:
                    # It's the base class default - not supported
                    caps["writable"] = False
                else:
                    # Method is overridden - check if it actually implements writing
                    # or just raises WriteNotSupportedError
                    try:
                        source = inspect.getsource(write_method)
                        # If source contains WriteNotSupportedError and is very short,
                        # it's likely just raising the error
                        if "WriteNotSupportedError" in source:
                            # Count non-comment, non-docstring lines
                            lines = [
                                line.strip()
                                for line in source.split("\n")
                                if line.strip()
                                and not line.strip().startswith("#")
                                and not line.strip().startswith('"""')
                                and not line.strip().startswith("'''")
                            ]
                            # If only 1-3 lines (def + docstring + raise), it's not supported
                            if len(lines) <= 3:
                                caps["writable"] = False
                            else:
                                # Has more implementation - likely supported
                                caps["writable"] = True
                        else:
                            # No WriteNotSupportedError - likely supported
                            caps["writable"] = True
                    except (OSError, TypeError):
                        # Can't inspect source (e.g., C extension) - assume supported if overridden
                        caps["writable"] = True
            except Exception:
                # Fallback: if method exists and is overridden, assume supported
                caps["writable"] = has_write_method
        else:
            caps["writable"] = False

    caps["bulk_read"] = hasattr(format_class, "read_bulk") and callable(getattr(format_class, "read_bulk", None))
    caps["bulk_write"] = hasattr(format_class, "write_bulk") and callable(getattr(format_class, "write_bulk", None))

    # Check static methods for format characteristics
    try:
        if hasattr(format_class, "has_totals") and callable(getattr(format_class, "has_totals", None)):
            caps["totals"] = format_class.has_totals()
        else:
            caps["totals"] = False
    except (ImportError, AttributeError, TypeError):
        caps["totals"] = None

    try:
        if hasattr(format_class, "has_tables") and callable(getattr(format_class, "has_tables", None)):
            caps["tables"] = format_class.has_tables()
        else:
            caps["tables"] = False
    except (ImportError, AttributeError, TypeError):
        caps["tables"] = None

    try:
        if hasattr(format_class, "is_flatonly") and callable(getattr(format_class, "is_flatonly", None)):
            caps["flat_only"] = format_class.is_flatonly()
            caps["nested"] = not caps["flat_only"]
        else:
            # Default: assume nested data is supported unless proven otherwise
            caps["flat_only"] = False
            caps["nested"] = True
    except (ImportError, AttributeError, TypeError):
        caps["flat_only"] = None
        caps["nested"] = None

    # Check for streaming support
    try:
        # is_streaming() is an instance method, so we need to check it on an instance
        # However, creating an instance might fail if dependencies are missing or if
        # the format requires a filename. We'll try a best-effort approach.

        # Known non-streaming formats (from memory audit)
        # These formats load entire files into memory
        KNOWN_NON_STREAMING_FORMATS = {
            "feed",
            "rss",
            "atom",  # Feed formats
            "arff",  # ARFF format
            "html",
            "htm",  # HTML format
            "toml",  # TOML format
            "hocon",  # HOCON format
            "edn",  # EDN format
            "bencode",  # Bencode format
            "asn1",  # ASN.1 format
            "ical",
            "ics",  # iCal format
            "turtle",
            "ttl",  # Turtle RDF format
            "vcf",  # VCF format
            "mhtml",  # MHTML format
            "flexbuffers",  # FlexBuffers format
            "px",  # PC-Axis format
            "mvt",  # MVT (Mapbox Vector Tile) - single tile per file
        }

        # Check if format ID is in known non-streaming list
        # Try to get format ID from static method
        format_id = None
        try:
            if hasattr(format_class, "id") and callable(getattr(format_class, "id", None)):
                format_id = format_class.id()
        except (AttributeError, TypeError):
            pass

        if format_id and format_id.lower() in KNOWN_NON_STREAMING_FORMATS:
            caps["streaming"] = False
        else:
            # Try to determine streaming capability by checking if is_streaming() exists
            # and if the format has a _should_use_streaming method (indicates conditional streaming)
            has_streaming_method = hasattr(format_class, "is_streaming") and callable(
                getattr(format_class, "is_streaming", None)
            )
            has_conditional_streaming = hasattr(format_class, "_should_use_streaming") and callable(
                getattr(format_class, "_should_use_streaming", None)
            )

            # Formats with conditional streaming (like JSON, GeoJSON, TopoJSON) support streaming
            # for large files but may load small files entirely
            if has_conditional_streaming:
                caps["streaming"] = True  # Supports streaming for large files
            elif has_streaming_method:
                # Has is_streaming() method - likely supports streaming
                # Default to True, but this may vary by instance
                caps["streaming"] = True
            else:
                # Default: assume streaming for most formats (library emphasizes streaming)
                # Most formats in IterableData are designed for streaming (row-by-row processing)
                caps["streaming"] = caps["readable"]
    except (ImportError, AttributeError, TypeError):
        caps["streaming"] = None

    # Compression support: most text formats support compression
    # Binary formats may or may not. We'll be conservative and set to None
    # unless we can determine otherwise. In practice, most formats work with codecs.
    try:
        # Check if format is in TEXT_DATA_TYPES from detect.py (indirect check)
        # For now, assume compression is supported if format is readable
        # This is a reasonable default as most formats work with codecs
        caps["compression"] = caps["readable"]
    except (ImportError, AttributeError, TypeError):
        caps["compression"] = None

    return caps


def _get_format_class(format_id: str) -> type[BaseIterable]:
    """Get format class for a format ID.

    Args:
        format_id: Format identifier (file extension or format name)

    Returns:
        Format class

    Raises:
        ValueError: If format_id is not in registry
        ImportError: If format class cannot be loaded (optional dependency missing)
    """
    format_id_lower = format_id.lower()
    registry = _get_format_registry()
    if format_id_lower not in registry:
        raise FormatDetectionError(
            filename=None,
            reason=f"Unknown format: '{format_id}'. Available formats: {sorted(set(registry.keys()))}",
        )

    module_path, symbol = registry[format_id_lower]
    try:
        return _load_symbol(module_path, symbol)
    except ImportError as e:
        # Re-raise with more context
        raise ImportError(
            f"Failed to load format class for '{format_id}'. "
            f"This format likely requires an optional dependency. "
            f"Original error: {e}"
        ) from e


def get_format_capabilities(format_id: str) -> dict[str, bool | None]:
    """Get all capabilities for a specific format.

    Args:
        format_id: Format identifier (file extension or format name, e.g., "csv", "json", "parquet")

    Returns:
        Dictionary with capability flags:
        - readable: Format supports reading data
        - writable: Format supports writing data (False for read-only formats)
        - bulk_read: Format supports bulk reading
        - bulk_write: Format supports bulk writing
        - totals: Format supports row count totals
        - streaming: Format supports streaming (doesn't load entire file)
        - flat_only: Format only supports flat (non-nested) data
        - tables: Format supports multiple tables/sheets/datasets
        - compression: Format supports compression codecs
        - nested: Format can preserve nested data structures

        Values are True/False/None (None indicates unknown/unsupported)

    Raises:
        ValueError: If format_id is not recognized
        ImportError: If format class cannot be loaded (optional dependency missing)

    Example:
        >>> caps = get_format_capabilities("csv")
        >>> print(caps["readable"])
        True
        >>> print(caps["writable"])
        True
        >>> caps = get_format_capabilities("pcap")
        >>> print(caps["writable"])
        False
    """
    format_id_lower = format_id.lower()

    # Check cache first
    if format_id_lower in _CAPABILITY_CACHE:
        return _CAPABILITY_CACHE[format_id_lower].copy()

    # Quick check via format descriptor before loading the format class.
    if _is_read_only(format_id_lower):
        # Still need to load class for other capabilities, but we know writable=False
        try:
            format_class = _get_format_class(format_id_lower)
            capabilities = _detect_capabilities(format_class)
            # Ensure writable is False (should already be set by _detect_capabilities, but be explicit)
            capabilities["writable"] = False
        except ImportError:
            # If import fails, return dict with writable=False (we know it's read-only)
            capabilities = {
                "readable": None,
                "writable": False,  # Known to be read-only from registry
                "bulk_read": None,
                "bulk_write": None,
                "totals": None,
                "streaming": None,
                "flat_only": None,
                "tables": None,
                "compression": None,
                "nested": None,
            }
    else:
        # Get format class and detect capabilities
        try:
            format_class = _get_format_class(format_id_lower)
            capabilities = _detect_capabilities(format_class)
        except ImportError:
            # If import fails, return dict with None values
            # This allows graceful handling of missing optional dependencies
            capabilities = {
                "readable": None,
                "writable": None,
                "bulk_read": None,
                "bulk_write": None,
                "totals": None,
                "streaming": None,
                "flat_only": None,
                "tables": None,
                "compression": None,
                "nested": None,
            }

    # Cache the result
    _CAPABILITY_CACHE[format_id_lower] = capabilities.copy()

    return capabilities


def list_all_capabilities() -> dict[str, dict[str, bool | None]]:
    """List capabilities for all registered formats.

    Returns:
        Dictionary mapping format IDs to their capability dictionaries.
        Each capability dictionary has the same structure as returned by
        `get_format_capabilities()`.

    Example:
        >>> all_caps = list_all_capabilities()
        >>> print(all_caps["csv"]["readable"])
        True
        >>> print(all_caps["json"]["nested"])
        True
    """
    # Get unique format classes (multiple extensions may map to same class)
    registry = _get_format_registry()
    format_classes_seen: set[tuple[str, str]] = set()
    result: dict[str, dict[str, bool | None]] = {}

    for format_id in sorted(registry.keys()):
        module_path, symbol = registry[format_id]
        class_key = (module_path, symbol)

        # Only process each unique class once, but include all format IDs
        if class_key not in format_classes_seen:
            format_classes_seen.add(class_key)
            try:
                result[format_id] = get_format_capabilities(format_id)
            except (ValueError, ImportError):
                # Skip formats that can't be loaded
                # Return empty capabilities dict
                result[format_id] = {
                    "readable": None,
                    "writable": None,
                    "bulk_read": None,
                    "bulk_write": None,
                    "totals": None,
                    "streaming": None,
                    "flat_only": None,
                    "tables": None,
                    "compression": None,
                    "nested": None,
                }
        else:
            # Reuse capabilities from the first format ID that uses this class
            # Find the first format_id that uses this class
            for first_id in sorted(registry.keys()):
                first_module, first_symbol = registry[first_id]
                if (first_module, first_symbol) == class_key:
                    result[format_id] = result[first_id].copy()
                    break

    return result


def get_capability(format_id: str, capability: str) -> bool | None:
    """Get a specific capability for a format.

    Args:
        format_id: Format identifier (file extension or format name)
        capability: Capability name (one of: readable, writable, bulk_read, bulk_write,
                   totals, streaming, flat_only, tables, compression, nested)

    Returns:
        Capability value (True/False/None), or None if capability name is invalid

    Raises:
        ValueError: If format_id is not recognized

    Example:
        >>> is_writable = get_capability("csv", "writable")
        >>> print(is_writable)
        True
        >>> has_totals = get_capability("json", "totals")
        >>> print(has_totals)
        True
    """
    capabilities = get_format_capabilities(format_id)
    return capabilities.get(capability)


def supports_write(format_id: str) -> bool:
    """Check if a format supports write operations.

    This is a convenience function that checks if a format has write support.
    It returns True only if the format explicitly implements write methods
    (not just the base class default that raises WriteNotSupportedError).

    Args:
        format_id: Format identifier (file extension or format name)

    Returns:
        True if format supports writing, False otherwise

    Raises:
        ValueError: If format_id is not recognized
        ImportError: If format class cannot be loaded (optional dependency missing)

    Example:
        >>> if supports_write("csv"):
        ...     print("CSV format supports writing")
        ... else:
        ...     print("CSV format is read-only")
        CSV format supports writing

        >>> if supports_write("pcap"):
        ...     print("PCAP format supports writing")
        ... else:
        ...     print("PCAP format is read-only")
        PCAP format is read-only
    """
    capabilities = get_format_capabilities(format_id)
    writable = capabilities.get("writable")

    # Return False if None (format couldn't be loaded) or explicitly False
    return bool(writable)
