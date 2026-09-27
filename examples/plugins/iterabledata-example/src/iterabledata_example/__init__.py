"""Reference IterableData plugin package.

Provides the ``journal`` format via the ``iterabledata.formats`` entry point.
"""

from .journal import JournalIterable

__all__ = ["JournalIterable"]
