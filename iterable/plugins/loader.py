"""
Plugin loader for discovering and loading plugins via entry points.

Uses Python's importlib.metadata to discover plugins registered via
setuptools entry points.
"""

from __future__ import annotations

import logging
from typing import Any

try:
    from importlib import metadata
except ImportError:
    # Python < 3.8 compatibility
    import importlib_metadata as metadata  # type: ignore[no-redef]

from .registry import get_plugin_registry

logger = logging.getLogger(__name__)

# Track if plugins have been discovered
_discovered = False


def discover_plugins() -> None:
    """Discover and register plugins via entry points.

    This function scans for plugins registered via setuptools entry points
    and registers them in the global plugin registry. Plugins are discovered
    lazily on first call.

    Entry point groups:
    - iterabledata.formats: Format plugins
    - iterabledata.codecs: Codec plugins
    - iterabledata.database_drivers: Database driver plugins
    - iterabledata.validation_rules: Validation rule plugins
    - iterabledata.engines: Engine plugins
    """
    global _discovered
    if _discovered:
        return

    registry = get_plugin_registry()

    # Discover format plugins
    _discover_format_plugins(registry)

    # Discover codec plugins
    _discover_codec_plugins(registry)

    # Discover database driver plugins
    _discover_database_driver_plugins(registry)

    # Discover validation rule plugins
    _discover_validation_rule_plugins(registry)

    # Discover engine plugins
    _discover_engine_plugins(registry)

    _discovered = True
    logger.debug("Plugin discovery complete")


def _discover_format_plugins(registry: Any) -> None:
    """Discover format plugins from entry points."""
    try:
        for entry_point in metadata.entry_points(group="iterabledata.formats"):
            try:
                format_id = entry_point.name
                value = entry_point.value

                # Parse entry point value: "module.path:ClassName"
                if ":" not in value:
                    logger.warning(
                        f"Invalid format plugin entry point '{format_id}': expected 'module.path:ClassName' format"
                    )
                    continue

                module_path, class_name = value.split(":", 1)

                # Extract metadata from entry point if available
                metadata_dict = {}
                if hasattr(entry_point, "dist"):
                    dist = entry_point.dist
                    if dist:
                        metadata_dict = {
                            "version": getattr(dist, "version", None),
                            "name": getattr(dist, "name", None),
                        }

                registry.register_format(format_id, module_path, class_name, metadata_dict)

                dist_name = entry_point.dist.name if hasattr(entry_point, "dist") and entry_point.dist else "unknown"
                logger.debug(f"Discovered format plugin: {format_id} from {dist_name}")

            except Exception as e:
                logger.warning(f"Error loading format plugin '{entry_point.name}': {e}", exc_info=False)

    except Exception as e:
        logger.debug(f"No format plugins found or error discovering: {e}")


def _discover_codec_plugins(registry: Any) -> None:
    """Discover codec plugins from entry points."""
    try:
        for entry_point in metadata.entry_points(group="iterabledata.codecs"):
            try:
                codec_id = entry_point.name
                value = entry_point.value

                if ":" not in value:
                    logger.warning(
                        f"Invalid codec plugin entry point '{codec_id}': expected 'module.path:ClassName' format"
                    )
                    continue

                module_path, class_name = value.split(":", 1)

                metadata_dict = {}
                if hasattr(entry_point, "dist"):
                    dist = entry_point.dist
                    if dist:
                        metadata_dict = {
                            "version": getattr(dist, "version", None),
                            "name": getattr(dist, "name", None),
                        }

                registry.register_codec(codec_id, module_path, class_name, metadata_dict)

                logger.debug(f"Discovered codec plugin: {codec_id}")

            except Exception as e:
                logger.warning(f"Error loading codec plugin '{entry_point.name}': {e}", exc_info=False)

    except Exception as e:
        logger.debug(f"No codec plugins found or error discovering: {e}")


def _discover_database_driver_plugins(registry: Any) -> None:
    """Discover database driver plugins from entry points."""
    try:
        for entry_point in metadata.entry_points(group="iterabledata.database_drivers"):
            try:
                engine_name = entry_point.name
                value = entry_point.value

                if ":" not in value:
                    logger.warning(
                        f"Invalid database driver plugin entry point '{engine_name}': "
                        "expected 'module.path:ClassName' format"
                    )
                    continue

                module_path, class_name = value.split(":", 1)

                metadata_dict = {}
                if hasattr(entry_point, "dist"):
                    dist = entry_point.dist
                    if dist:
                        metadata_dict = {
                            "version": getattr(dist, "version", None),
                            "name": getattr(dist, "name", None),
                        }

                registry.register_database_driver(engine_name, module_path, class_name, metadata_dict)

                logger.debug(f"Discovered database driver plugin: {engine_name}")

            except Exception as e:
                logger.warning(f"Error loading database driver plugin '{entry_point.name}': {e}", exc_info=False)

    except Exception as e:
        logger.debug(f"No database driver plugins found or error discovering: {e}")


def _discover_validation_rule_plugins(registry: Any) -> None:
    """Discover validation rule plugins from entry points."""
    try:
        for entry_point in metadata.entry_points(group="iterabledata.validation_rules"):
            try:
                rule_name = entry_point.name

                # Validation rules are functions, not classes
                # Entry point value is just the function path: "module.path:function_name"
                value = entry_point.value

                if ":" not in value:
                    logger.warning(
                        f"Invalid validation rule plugin entry point '{rule_name}': "
                        "expected 'module.path:function_name' format"
                    )
                    continue

                module_path, function_name = value.split(":", 1)

                # Load the validator function
                from ..helpers.detect import _load_symbol

                validator = _load_symbol(module_path, function_name)

                metadata_dict = {}
                if hasattr(entry_point, "dist"):
                    dist = entry_point.dist
                    if dist:
                        metadata_dict = {
                            "version": getattr(dist, "version", None),
                            "name": getattr(dist, "name", None),
                        }

                registry.register_validation_rule(rule_name, validator, metadata_dict)

                logger.debug(f"Discovered validation rule plugin: {rule_name}")

            except Exception as e:
                logger.warning(f"Error loading validation rule plugin '{entry_point.name}': {e}", exc_info=False)

    except Exception as e:
        logger.debug(f"No validation rule plugins found or error discovering: {e}")


def _discover_engine_plugins(registry: Any) -> None:
    """Discover engine plugins from entry points."""
    try:
        for entry_point in metadata.entry_points(group="iterabledata.engines"):
            try:
                engine_name = entry_point.name
                value = entry_point.value

                if ":" not in value:
                    logger.warning(
                        f"Invalid engine plugin entry point '{engine_name}': expected 'module.path:ClassName' format"
                    )
                    continue

                module_path, class_name = value.split(":", 1)

                metadata_dict = {}
                if hasattr(entry_point, "dist"):
                    dist = entry_point.dist
                    if dist:
                        metadata_dict = {
                            "version": getattr(dist, "version", None),
                            "name": getattr(dist, "name", None),
                        }

                registry.register_engine(engine_name, module_path, class_name, metadata_dict)

                logger.debug(f"Discovered engine plugin: {engine_name}")

            except Exception as e:
                logger.warning(f"Error loading engine plugin '{entry_point.name}': {e}", exc_info=False)

    except Exception as e:
        logger.debug(f"No engine plugins found or error discovering: {e}")


def reset_discovery() -> None:
    """Reset plugin discovery state (useful for testing).

    This function resets the discovery flag, allowing plugins to be
    rediscovered. Note that this does not clear the registry - use
    get_plugin_registry() to access and clear the registry if needed.
    """
    global _discovered
    _discovered = False
