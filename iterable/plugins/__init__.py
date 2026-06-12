"""
Plugin system for IterableData.

Enables third-party developers to extend IterableData with custom formats,
codecs, database drivers, validation rules, and engines without modifying
the core library.
"""

from .loader import discover_plugins, reset_discovery
from .registry import (
    PluginRegistry,
    get_plugin_registry,
    register_codec,
    register_database_driver,
    register_engine,
    register_format,
    register_validation_rule,
)

__all__ = [
    "PluginRegistry",
    "get_plugin_registry",
    "register_format",
    "register_codec",
    "register_database_driver",
    "register_validation_rule",
    "register_engine",
    "discover_plugins",
    "reset_discovery",
]
