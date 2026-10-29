"""
Database driver registry and utilities.

This module provides a registry for database drivers that enable reading
from SQL and NoSQL databases as iterable data sources.
"""

import importlib

from .base import DBDriver

# Registry mapping engine names to driver classes (user registrations and loaded built-ins)
_DRIVER_REGISTRY: dict[str, type[DBDriver]] = {}

# Built-in drivers by import path. They are imported on first ``get_driver()`` so that
# ``import iterable`` does not load every installed database client (elasticsearch,
# pymongo, ... cost ~0.3 s together).
_BUILTIN_DRIVERS: dict[str, tuple[str, str]] = {
    "postgres": ("iterable.db.postgres", "PostgresDriver"),
    "postgresql": ("iterable.db.postgres", "PostgresDriver"),
    "clickhouse": ("iterable.db.clickhouse", "ClickHouseDriver"),
    "mongo": ("iterable.db.mongo", "MongoDriver"),
    "mongodb": ("iterable.db.mongo", "MongoDriver"),
    "elasticsearch": ("iterable.db.elasticsearch", "ElasticsearchDriver"),
    "opensearch": ("iterable.db.elasticsearch", "ElasticsearchDriver"),  # OpenSearch is compatible
    "mysql": ("iterable.db.mysql", "MySQLDriver"),
    "mariadb": ("iterable.db.mysql", "MySQLDriver"),
    "mssql": ("iterable.db.mssql", "MSSQLDriver"),
    "sqlserver": ("iterable.db.mssql", "MSSQLDriver"),
    "sqlite": ("iterable.db.sqlite", "SQLiteDriver"),
    "sqlite3": ("iterable.db.sqlite", "SQLiteDriver"),
}


def register_driver(engine_name: str, driver_class: type[DBDriver]) -> None:
    """Register a database driver for a given engine name.

    Args:
        engine_name: Name of the database engine (e.g., 'postgres', 'mongo')
        driver_class: Driver class that inherits from DBDriver

    Raises:
        ValueError: If engine_name is invalid or driver_class is not a subclass of DBDriver
    """
    if not engine_name or not isinstance(engine_name, str):
        raise ValueError(f"engine_name must be a non-empty string, got {engine_name!r}")
    if not issubclass(driver_class, DBDriver):
        raise ValueError(f"driver_class must be a subclass of DBDriver, got {driver_class}")
    if engine_name in _DRIVER_REGISTRY or engine_name in _BUILTIN_DRIVERS:
        raise ValueError(f"Driver for engine '{engine_name}' is already registered")

    _DRIVER_REGISTRY[engine_name] = driver_class


def get_driver(engine_name: str) -> type[DBDriver] | None:
    """Get a registered driver class for an engine name.

    Built-in drivers are imported on first use.

    Args:
        engine_name: Name of the database engine

    Returns:
        Driver class if registered and importable, None otherwise
    """
    driver_class = _DRIVER_REGISTRY.get(engine_name)
    if driver_class is not None or engine_name not in _BUILTIN_DRIVERS:
        return driver_class
    module_path, symbol = _BUILTIN_DRIVERS[engine_name]
    try:
        driver_class = getattr(importlib.import_module(module_path), symbol)
    except ImportError:
        return None
    _DRIVER_REGISTRY[engine_name] = driver_class
    return driver_class


def list_drivers() -> list[str]:
    """List all registered database engine names.

    Returns:
        List of registered engine names (built-ins first, then user registrations)
    """
    return list(_BUILTIN_DRIVERS) + [name for name in _DRIVER_REGISTRY if name not in _BUILTIN_DRIVERS]


def is_database_engine(engine_name: str) -> bool:
    """Check if an engine name is a registered database engine.

    Args:
        engine_name: Name of the engine to check

    Returns:
        True if the engine is a registered database engine, False otherwise
    """
    return engine_name in _DRIVER_REGISTRY or engine_name in _BUILTIN_DRIVERS


__all__ = ["DBDriver", "register_driver", "get_driver", "list_drivers", "is_database_engine"]
