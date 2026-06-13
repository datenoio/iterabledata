"""
Elasticsearch database driver.

Provides read-only access to Elasticsearch indices as iterable data sources.
"""

from __future__ import annotations

from collections.abc import Iterator
from typing import Any

from ..types import Row
from .base import DBDriver

# Imported at module level (guarded) so the optional dependency stays optional
# while remaining patchable as ``iterable.db.elasticsearch.Elasticsearch`` in tests.
try:
    from elasticsearch import Elasticsearch
except ImportError:  # pragma: no cover - exercised when dependency is absent
    Elasticsearch = None


class ElasticsearchDriver(DBDriver):
    """Elasticsearch database driver.

    Supports streaming queries using scroll API for memory efficiency.
    Uses elasticsearch (official Elasticsearch Python client).
    """

    def __init__(self, source: str | Any, **kwargs: Any) -> None:
        """Initialize Elasticsearch driver.

        Args:
            source: Elasticsearch connection URL (http://... or https://...) or existing Elasticsearch client
            **kwargs: Additional parameters:
                - index: Index name (required)
                - body: Elasticsearch query body (dict with query DSL)
                - scroll: Scroll timeout (e.g., "5m") for large result sets
                - size: Number of documents per scroll batch (default: 10000)
                - source_only: Return only _source fields, exclude metadata (default: True)
                - request_timeout: Client-side timeout in seconds (float, e.g., 30.0)
                - timeout: Server-side timeout (string, e.g., "30s", "1m")
                - connect_args: Additional arguments for Elasticsearch() client
                    (e.g., request_timeout for client-level default timeout)
        """
        super().__init__(source, **kwargs)
        self._scroll_id: str | None = None
        self._scroll_timeout: str | None = None

    def connect(self) -> None:
        """Establish Elasticsearch connection.

        Raises:
            ImportError: If elasticsearch is not installed
            ConnectionError: If connection fails
            ValueError: If index is not specified
        """
        # If source is already an Elasticsearch client object, use it (no driver import needed)
        if hasattr(self.source, "search") and hasattr(self.source, "close"):
            self.conn = self.source
            self._connected = True
            self._validate_index()
            return

        if Elasticsearch is None:
            raise ImportError(
                "elasticsearch is required for Elasticsearch support. Install it with: pip install elasticsearch>=8.0"
            )

        # Parse connection string
        if not isinstance(self.source, str):
            raise ValueError(
                f"Elasticsearch source must be a connection URL or Elasticsearch client object, got {type(self.source)}"
            )

        # Extract connection arguments
        connect_args = self.kwargs.get("connect_args", {})

        try:
            # Create Elasticsearch client
            # The connection URL can be a single string or list of strings
            self.conn = Elasticsearch([self.source], **connect_args)
            self._connected = True

            # Validate index is specified
            self._validate_index()

        except Exception as e:
            self._connected = False
            raise ConnectionError(f"Failed to connect to Elasticsearch: {e}") from e

    def _validate_index(self) -> None:
        """Validate that index is specified.

        Raises:
            ValueError: If index is not specified
        """
        index = self.kwargs.get("index")
        if not index:
            raise ValueError("'index' parameter is required for Elasticsearch driver")

    def iterate(self) -> Iterator[Row]:
        """Return iterator of dict documents from Elasticsearch index.

        Yields:
            dict: Elasticsearch document as dictionary

        Raises:
            RuntimeError: If not connected
        """
        if not self._connected or self.conn is None:
            raise RuntimeError("Not connected to database. Call connect() first.")

        # Get parameters
        index = self.kwargs.get("index")
        body = self.kwargs.get("body", {"query": {"match_all": {}}})
        scroll = self.kwargs.get("scroll")
        size = self.kwargs.get("size", 10000)
        source_only = self.kwargs.get("source_only", True)
        request_timeout = self.kwargs.get("request_timeout")  # Client-side timeout in seconds
        timeout = self.kwargs.get("timeout")  # Server-side timeout (e.g., "30s", "1m")

        # Start metrics
        self._start_metrics()

        try:
            if scroll:
                # Use scroll API for large result sets
                self._scroll_timeout = scroll
                # Initial search with scroll
                search_params: dict[str, Any] = {
                    "index": index,
                    "body": body,
                    "scroll": scroll,
                    "size": size,
                }
                if request_timeout is not None:
                    search_params["request_timeout"] = request_timeout
                if timeout is not None:
                    search_params["timeout"] = timeout

                response = self.conn.search(**search_params)
                self._scroll_id = response.get("_scroll_id")

                # Yield results from initial search
                for hit in response.get("hits", {}).get("hits", []):
                    doc = hit["_source"] if source_only else hit
                    yield doc
                    self._update_metrics(rows_read=1)

                # Continue scrolling
                while self._scroll_id:
                    scroll_params: dict[str, Any] = {
                        "scroll_id": self._scroll_id,
                        "scroll": scroll,
                    }
                    if request_timeout is not None:
                        scroll_params["request_timeout"] = request_timeout

                    response = self.conn.scroll(**scroll_params)
                    hits = response.get("hits", {}).get("hits", [])
                    if not hits:
                        # No more results
                        break

                    for hit in hits:
                        doc = hit["_source"] if source_only else hit
                        yield doc
                        self._update_metrics(rows_read=1)

                    # Update scroll_id for next iteration
                    self._scroll_id = response.get("_scroll_id")

            else:
                # Use regular search (limited to default max result window)
                search_params: dict[str, Any] = {
                    "index": index,
                    "body": body,
                    "size": size,
                }
                if request_timeout is not None:
                    search_params["request_timeout"] = request_timeout
                if timeout is not None:
                    search_params["timeout"] = timeout

                response = self.conn.search(**search_params)

                # Yield results
                for hit in response.get("hits", {}).get("hits", []):
                    doc = hit["_source"] if source_only else hit
                    yield doc
                    self._update_metrics(rows_read=1)

        except Exception as e:
            self._handle_error(e, "iterating documents")
            if self._on_error == "raise":
                raise
            # If error handling is 'skip' or 'warn', return empty iterator
            return

        finally:
            # Clean up scroll context if it exists
            if self._scroll_id and self.conn is not None:
                try:
                    self.conn.clear_scroll(scroll_id=self._scroll_id)
                except Exception:
                    pass
                self._scroll_id = None

    def close(self) -> None:
        """Close Elasticsearch connection and clean up resources."""
        # Clean up scroll context if it exists
        if self._scroll_id and self.conn is not None:
            try:
                self.conn.clear_scroll(scroll_id=self._scroll_id)
            except Exception:
                pass
            self._scroll_id = None

        # Close connection
        super().close()

    @staticmethod
    def list_indices(
        connection_string: str,
        **connect_args: Any,
    ) -> list[dict[str, Any]]:
        """List indices in Elasticsearch cluster.

        Args:
            connection_string: Elasticsearch connection URL (http://... or https://...)
            **connect_args: Additional connection arguments for Elasticsearch client

        Returns:
            List of dicts with keys: index, doc_count (document count estimate)

        Raises:
            ImportError: If elasticsearch is not installed
            ConnectionError: If connection fails
        """
        if Elasticsearch is None:
            raise ImportError(
                "elasticsearch is required for Elasticsearch support. Install it with: pip install elasticsearch>=8.0"
            )

        try:
            # Create Elasticsearch client
            client = Elasticsearch([connection_string], **connect_args)

            # Get all indices using cat API (more efficient than stats API)
            # cat.indices returns index names and document counts
            indices_info = client.cat.indices(format="json", h="index,docs.count")

            results = []
            for info in indices_info:
                # Skip system indices (starting with .)
                index_name = info.get("index", "")
                if index_name.startswith("."):
                    continue

                doc_count = info.get("docs.count", "0")
                try:
                    doc_count_int = int(doc_count) if doc_count else 0
                except (ValueError, TypeError):
                    doc_count_int = None

                results.append(
                    {
                        "index": index_name,
                        "doc_count": doc_count_int,
                    }
                )

            # Sort by index name
            results.sort(key=lambda x: x["index"])

            return results

        except Exception as e:
            raise ConnectionError(f"Failed to list indices from Elasticsearch: {e}") from e
