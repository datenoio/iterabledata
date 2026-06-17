from __future__ import annotations

import typing

try:
    import feedparser

    HAS_FEEDPARSER = True
except ImportError:
    HAS_FEEDPARSER = False

from typing import Any

from ..base import BaseCodec, BaseFileIterable
from ..exceptions import WriteNotSupportedError
from ..types import Row


class FeedIterable(BaseFileIterable):
    def __init__(
        self,
        filename: str | None = None,
        stream: typing.IO[Any] | None = None,
        codec: BaseCodec | None = None,
        mode: str = "r",
        encoding: str = "utf8",
        options: dict[str, Any] | None = None,
    ):
        if options is None:
            options = {}
        if not HAS_FEEDPARSER:
            raise ImportError("Feed support requires 'feedparser' package")

        super().__init__(filename, stream, codec=codec, binary=False, mode=mode, encoding=encoding, options=options)
        self.reset()

    def reset(self):
        """Reset iterable"""
        super().reset()
        self.pos = 0
        if self.mode == "r":
            # Read feed content
            self.fobj.seek(0)
            feed_content = self.fobj.read()

            # Parse feed
            self.feed = feedparser.parse(feed_content)

            # Extract entries
            self.entries = self.feed.get("entries", [])

            # Convert entries to dicts
            self.features = []
            for entry in self.entries:
                # Convert entry to a plain dict
                entry_dict = {
                    "title": entry.get("title"),
                    "link": entry.get("link"),
                    "published": entry.get("published"),
                    "updated": entry.get("updated"),
                    "author": entry.get("author"),
                    "summary": entry.get("summary"),
                    "content": [c.get("value", "") for c in entry.get("content", [])] if "content" in entry else None,
                    "id": entry.get("id"),
                    "tags": [tag.get("term", "") for tag in entry.get("tags", [])],
                }
                # Add feed metadata to first entry
                if not self.features:
                    entry_dict["feed_title"] = self.feed.feed.get("title")
                    entry_dict["feed_link"] = self.feed.feed.get("link")
                    entry_dict["feed_description"] = self.feed.feed.get("description")

                self.features.append(entry_dict)

            self.iterator = iter(self.features)

    @staticmethod
    def id() -> str:
        return "feed"

    @staticmethod
    def is_flatonly() -> bool:
        return False

    @staticmethod
    def has_totals() -> bool:
        return True

    def totals(self):
        if hasattr(self, "features"):
            return len(self.features)
        return 0

    def read(self, skip_empty: bool = True) -> dict:
        entry = next(self.iterator)
        self.pos += 1
        return entry

    def write(self, record: Row) -> None:
        """Write not supported for feeds"""
        raise WriteNotSupportedError("feed", "feed formats are read-only")

    def write_bulk(self, records: list[Row]) -> None:
        """Write not supported for feeds"""
        raise WriteNotSupportedError("feed", "feed formats are read-only")
