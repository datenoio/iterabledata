"""Debug mode and verbose logging support for IterableData.

This module provides debug mode configuration and logging infrastructure
for detailed operation visibility during troubleshooting and development.
"""

import logging
import os

# Logger hierarchy for different components
logger = logging.getLogger("iterable")
format_detection_logger = logging.getLogger("iterable.detect")
file_io_logger = logging.getLogger("iterable.io")
parsing_logger = logging.getLogger("iterable.parse")
performance_logger = logging.getLogger("iterable.perf")


def enable_debug_mode(level: int = logging.DEBUG, handler: logging.Handler | None = None) -> None:
    """Enable debug mode with verbose logging.

    This function configures the IterableData loggers to output detailed
    debug information. It sets up logging handlers and configures log levels
    for all IterableData components.

    Args:
        level: Logging level (default: logging.DEBUG)
        handler: Optional logging handler (default: StreamHandler to stderr)

    Example:
        >>> from iterable.helpers.debug import enable_debug_mode
        >>> import logging
        >>> enable_debug_mode(level=logging.DEBUG)
        >>> # Now all IterableData operations will log debug information
    """
    if handler is None:
        handler = logging.StreamHandler()
        handler.setFormatter(logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s"))

    # Configure root iterable logger
    logger.setLevel(level)
    if not logger.handlers:
        logger.addHandler(handler)
    logger.propagate = False  # Don't propagate to root logger

    # Configure sub-loggers
    for sub_logger in [
        format_detection_logger,
        file_io_logger,
        parsing_logger,
        performance_logger,
    ]:
        sub_logger.setLevel(level)
        if not sub_logger.handlers:
            sub_logger.addHandler(handler)
        sub_logger.propagate = False


def is_debug_enabled() -> bool:
    """Check if debug mode is enabled.

    Checks both the logger level and the ITERABLEDATA_DEBUG environment variable.

    Returns:
        True if debug mode is enabled, False otherwise
    """
    # Check environment variable
    if os.getenv("ITERABLEDATA_DEBUG", "").lower() in ("1", "true", "yes"):
        return True

    # Check logger level
    return logger.isEnabledFor(logging.DEBUG)


def configure_debug_from_env() -> None:
    """Configure debug mode from environment variable.

    If ITERABLEDATA_DEBUG environment variable is set, enables debug mode.
    """
    if os.getenv("ITERABLEDATA_DEBUG", "").lower() in ("1", "true", "yes"):
        enable_debug_mode()


# Auto-configure from environment on import
configure_debug_from_env()
