"""
Plugin registry for managing all plugin types.

Provides central registry for formats, codecs, database drivers, validation
rules, and engines registered via plugins or programmatically.
"""

from __future__ import annotations

import logging
from collections.abc import Callable
from typing import Any

logger = logging.getLogger(__name__)

# Global plugin registry instance
_registry: PluginRegistry | None = None


class PluginRegistry:
    """Central registry for all plugin types.

    Manages registration of formats, codecs, database drivers, validation
    rules, and engines. Supports both built-in and third-party plugins.
    """

    def __init__(self) -> None:
        """Initialize plugin registry."""
        # Format registry: format_id -> (module_path, class_name)
        self._formats: dict[str, tuple[str, str]] = {}

        # Codec registry: codec_id -> (module_path, class_name)
        self._codecs: dict[str, tuple[str, str]] = {}

        # Database driver registry: engine_name -> (module_path, class_name)
        self._database_drivers: dict[str, tuple[str, str]] = {}

        # Validation rule registry: rule_name -> validator function
        self._validation_rules: dict[str, Callable[[Any], tuple[bool, str | None]]] = {}

        # Engine registry: engine_name -> (module_path, class_name)
        self._engines: dict[str, tuple[str, str]] = {}

        # Plugin metadata: plugin_id -> metadata dict
        self._metadata: dict[str, dict[str, Any]] = {}

    def register_format(
        self,
        format_id: str,
        module_path: str,
        class_name: str,
        metadata: dict[str, Any] | None = None,
        override: bool = False,
    ) -> None:
        """Register a format plugin.

        Args:
            format_id: Format identifier (e.g., 'csv', 'json')
            module_path: Module path where format class is defined
            class_name: Name of the format class
            metadata: Optional metadata dictionary
            override: If True, allow overriding existing registration

        Raises:
            ValueError: If format_id is already registered and override=False
        """
        if format_id in self._formats and not override:
            raise ValueError(
                f"Format '{format_id}' is already registered. Use override=True to replace existing registration."
            )

        self._formats[format_id] = (module_path, class_name)
        if metadata:
            self._metadata[f"format:{format_id}"] = metadata

        logger.debug(f"Registered format plugin: {format_id} -> {module_path}.{class_name}")

    def register_codec(
        self,
        codec_id: str,
        module_path: str,
        class_name: str,
        metadata: dict[str, Any] | None = None,
        override: bool = False,
    ) -> None:
        """Register a codec plugin.

        Args:
            codec_id: Codec identifier (e.g., 'gz', 'bz2')
            module_path: Module path where codec class is defined
            class_name: Name of the codec class
            metadata: Optional metadata dictionary
            override: If True, allow overriding existing registration

        Raises:
            ValueError: If codec_id is already registered and override=False
        """
        if codec_id in self._codecs and not override:
            raise ValueError(
                f"Codec '{codec_id}' is already registered. Use override=True to replace existing registration."
            )

        self._codecs[codec_id] = (module_path, class_name)
        if metadata:
            self._metadata[f"codec:{codec_id}"] = metadata

        logger.debug(f"Registered codec plugin: {codec_id} -> {module_path}.{class_name}")

    def register_database_driver(
        self,
        engine_name: str,
        module_path: str,
        class_name: str,
        metadata: dict[str, Any] | None = None,
        override: bool = False,
    ) -> None:
        """Register a database driver plugin.

        Args:
            engine_name: Engine identifier (e.g., 'postgres', 'mysql')
            module_path: Module path where driver class is defined
            class_name: Name of the driver class
            metadata: Optional metadata dictionary
            override: If True, allow overriding existing registration

        Raises:
            ValueError: If engine_name is already registered and override=False
        """
        if engine_name in self._database_drivers and not override:
            raise ValueError(
                f"Database driver '{engine_name}' is already registered. "
                "Use override=True to replace existing registration."
            )

        self._database_drivers[engine_name] = (module_path, class_name)
        if metadata:
            self._metadata[f"database_driver:{engine_name}"] = metadata

        logger.debug(f"Registered database driver plugin: {engine_name} -> {module_path}.{class_name}")

    def register_validation_rule(
        self,
        rule_name: str,
        validator: Callable[[Any], tuple[bool, str | None]],
        metadata: dict[str, Any] | None = None,
        override: bool = False,
    ) -> None:
        """Register a validation rule plugin.

        Args:
            rule_name: Rule identifier (e.g., 'common.email', 'custom.rule')
            validator: Validator function that takes a value and returns (is_valid, error_message)
            metadata: Optional metadata dictionary
            override: If True, allow overriding existing registration

        Raises:
            ValueError: If rule_name is already registered and override=False
        """
        if rule_name in self._validation_rules and not override:
            raise ValueError(
                f"Validation rule '{rule_name}' is already registered. "
                "Use override=True to replace existing registration."
            )

        self._validation_rules[rule_name] = validator
        if metadata:
            self._metadata[f"validation_rule:{rule_name}"] = metadata

        logger.debug(f"Registered validation rule plugin: {rule_name}")

    def register_engine(
        self,
        engine_name: str,
        module_path: str,
        class_name: str,
        metadata: dict[str, Any] | None = None,
        override: bool = False,
    ) -> None:
        """Register an engine plugin.

        Args:
            engine_name: Engine identifier (e.g., 'duckdb', 'spark')
            module_path: Module path where engine class is defined
            class_name: Name of the engine class
            metadata: Optional metadata dictionary
            override: If True, allow overriding existing registration

        Raises:
            ValueError: If engine_name is already registered and override=False
        """
        if engine_name in self._engines and not override:
            raise ValueError(
                f"Engine '{engine_name}' is already registered. Use override=True to replace existing registration."
            )

        self._engines[engine_name] = (module_path, class_name)
        if metadata:
            self._metadata[f"engine:{engine_name}"] = metadata

        logger.debug(f"Registered engine plugin: {engine_name} -> {module_path}.{class_name}")

    def get_format(self, format_id: str) -> tuple[str, str] | None:
        """Get format registration.

        Args:
            format_id: Format identifier

        Returns:
            Tuple of (module_path, class_name) or None if not found
        """
        return self._formats.get(format_id)

    def get_codec(self, codec_id: str) -> tuple[str, str] | None:
        """Get codec registration.

        Args:
            codec_id: Codec identifier

        Returns:
            Tuple of (module_path, class_name) or None if not found
        """
        return self._codecs.get(codec_id)

    def get_database_driver(self, engine_name: str) -> tuple[str, str] | None:
        """Get database driver registration.

        Args:
            engine_name: Engine identifier

        Returns:
            Tuple of (module_path, class_name) or None if not found
        """
        return self._database_drivers.get(engine_name)

    def get_validation_rule(self, rule_name: str) -> Callable[[Any], tuple[bool, str | None]] | None:
        """Get validation rule registration.

        Args:
            rule_name: Rule identifier

        Returns:
            Validator function or None if not found
        """
        return self._validation_rules.get(rule_name)

    def get_engine(self, engine_name: str) -> tuple[str, str] | None:
        """Get engine registration.

        Args:
            engine_name: Engine identifier

        Returns:
            Tuple of (module_path, class_name) or None if not found
        """
        return self._engines.get(engine_name)

    def get_metadata(self, plugin_id: str) -> dict[str, Any] | None:
        """Get plugin metadata.

        Args:
            plugin_id: Plugin identifier (e.g., 'format:csv', 'codec:gz')

        Returns:
            Metadata dictionary or None if not found
        """
        return self._metadata.get(plugin_id)

    def list_formats(self) -> list[str]:
        """List all registered format IDs.

        Returns:
            List of format identifiers
        """
        return list(self._formats.keys())

    def list_codecs(self) -> list[str]:
        """List all registered codec IDs.

        Returns:
            List of codec identifiers
        """
        return list(self._codecs.keys())

    def list_database_drivers(self) -> list[str]:
        """List all registered database driver engine names.

        Returns:
            List of engine identifiers
        """
        return list(self._database_drivers.keys())

    def list_validation_rules(self) -> list[str]:
        """List all registered validation rule names.

        Returns:
            List of rule identifiers
        """
        return list(self._validation_rules.keys())

    def list_engines(self) -> list[str]:
        """List all registered engine names.

        Returns:
            List of engine identifiers
        """
        return list(self._engines.keys())


def get_plugin_registry() -> PluginRegistry:
    """Get the global plugin registry instance.

    Returns:
        PluginRegistry instance
    """
    global _registry
    if _registry is None:
        _registry = PluginRegistry()
    return _registry


# Convenience functions for programmatic registration
def register_format(
    format_id: str,
    module_path: str,
    class_name: str,
    metadata: dict[str, Any] | None = None,
    override: bool = False,
) -> None:
    """Register a format plugin (convenience function).

    Args:
        format_id: Format identifier
        module_path: Module path where format class is defined
        class_name: Name of the format class
        metadata: Optional metadata dictionary
        override: If True, allow overriding existing registration
    """
    get_plugin_registry().register_format(format_id, module_path, class_name, metadata, override)


def register_codec(
    codec_id: str,
    module_path: str,
    class_name: str,
    metadata: dict[str, Any] | None = None,
    override: bool = False,
) -> None:
    """Register a codec plugin (convenience function).

    Args:
        codec_id: Codec identifier
        module_path: Module path where codec class is defined
        class_name: Name of the codec class
        metadata: Optional metadata dictionary
        override: If True, allow overriding existing registration
    """
    get_plugin_registry().register_codec(codec_id, module_path, class_name, metadata, override)


def register_database_driver(
    engine_name: str,
    module_path: str,
    class_name: str,
    metadata: dict[str, Any] | None = None,
    override: bool = False,
) -> None:
    """Register a database driver plugin (convenience function).

    Args:
        engine_name: Engine identifier
        module_path: Module path where driver class is defined
        class_name: Name of the driver class
        metadata: Optional metadata dictionary
        override: If True, allow overriding existing registration
    """
    get_plugin_registry().register_database_driver(engine_name, module_path, class_name, metadata, override)


def register_validation_rule(
    rule_name: str,
    validator: Callable[[Any], tuple[bool, str | None]],
    metadata: dict[str, Any] | None = None,
    override: bool = False,
) -> None:
    """Register a validation rule plugin (convenience function).

    Args:
        rule_name: Rule identifier
        validator: Validator function
        metadata: Optional metadata dictionary
        override: If True, allow overriding existing registration
    """
    get_plugin_registry().register_validation_rule(rule_name, validator, metadata, override)


def register_engine(
    engine_name: str,
    module_path: str,
    class_name: str,
    metadata: dict[str, Any] | None = None,
    override: bool = False,
) -> None:
    """Register an engine plugin (convenience function).

    Args:
        engine_name: Engine identifier
        module_path: Module path where engine class is defined
        class_name: Name of the engine class
        metadata: Optional metadata dictionary
        override: If True, allow overriding existing registration
    """
    get_plugin_registry().register_engine(engine_name, module_path, class_name, metadata, override)
