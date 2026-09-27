"""
MongoDB database driver.

Provides read-only access to MongoDB databases as iterable data sources.
"""

from __future__ import annotations

from collections.abc import Iterator
from typing import Any
from urllib.parse import urlparse

from ..types import Row
from .base import DBDriver
from .pooling import pool_enabled, pooled_acquire, pooled_release

# Imported at module level (guarded) so the optional dependency stays optional
# while remaining patchable as ``iterable.db.mongo.MongoClient`` in tests.
try:
    from pymongo import MongoClient
except ImportError:  # pragma: no cover - exercised when dependency is absent
    MongoClient = None


def _validate_connection(conn: Any) -> bool:
    """Validate that a pooled MongoDB client is still usable."""
    try:
        conn.admin.command("ping")
        return True
    except Exception:
        return False


class MongoDriver(DBDriver):
    """MongoDB database driver.

    Supports streaming queries using batch processing for memory efficiency.
    Uses pymongo (official MongoDB driver).
    """

    def __init__(self, source: str | Any, **kwargs: Any) -> None:
        """Initialize MongoDB driver.

        Args:
            source: MongoDB connection string (mongodb://...) or existing pymongo.MongoClient
            **kwargs: Additional parameters:
                - database: Database name (required if not in connection string)
                - collection: Collection name (required)
                - filter: MongoDB query dict for filtering documents
                - projection: Field inclusion/exclusion dict
                - sort: Sort specification (list of tuples, list of dicts, or dict)
                - skip: Number of documents to skip
                - limit: Maximum number of documents to return
                - pipeline: Aggregation pipeline (alternative to filter)
                - batch_size: Number of documents per batch (default: 10000)
                - connect_args: Additional arguments for pymongo.MongoClient()
                - pool: Pool configuration dict (or bool) with keys:
                    - enabled: Enable connection pooling (default: False, opt-in)
                    - min_size: Minimum pool size (default: 1)
                    - max_size: Maximum pool size (default: 10)
                    - timeout: Connection acquisition timeout in seconds (default: 30.0)
                    - max_idle: Maximum idle time in seconds (default: 300.0)
                  Ignored when `source` is an existing MongoClient object. Note that
                  pymongo's MongoClient already maintains an internal connection pool;
                  this option pools whole client objects.
        """
        super().__init__(source, **kwargs)
        self._cursor: Any = None
        self._database: Any = None
        self._collection: Any = None
        self._pool: Any = None
        self._pooled_conn: Any = None
        self._pooled_created_time: float | None = None

    def connect(self) -> None:
        """Establish MongoDB connection.

        Raises:
            ImportError: If pymongo is not installed
            ConnectionError: If connection fails
            ValueError: If database or collection is not specified
        """
        # If source is already a MongoClient object, use it (no driver import needed)
        if hasattr(self.source, "list_database_names") and hasattr(self.source, "close"):
            self.conn = self.source
            self._connected = True
            self._get_database_and_collection()
            return

        if MongoClient is None:
            raise ImportError("pymongo is required for MongoDB support. Install it with: pip install pymongo")

        # Parse connection string
        if not isinstance(self.source, str):
            raise ValueError(
                f"MongoDB source must be a connection string or MongoClient object, got {type(self.source)}"
            )

        # Extract connection arguments
        connect_args = self.kwargs.get("connect_args", {})

        # Extract pool configuration (opt-in: disabled by default)
        pool_config = self.kwargs.get("pool", {})
        use_pool = pool_enabled(pool_config, default=False)

        try:
            # Parse connection string to extract database name if present
            parsed = urlparse(self.source)
            db_name_from_url = parsed.path.lstrip("/").split("/")[0] if parsed.path else None

            # Get database name from kwargs or connection string
            database = self.kwargs.get("database") or db_name_from_url

            # Create MongoDB client (pooled or direct)
            if use_pool:
                pool_key = f"mongo:{self.source}"

                def factory():
                    """Factory function to create new MongoDB client."""
                    return MongoClient(self.source, **connect_args)

                config_dict = pool_config if isinstance(pool_config, dict) else {}
                self._pool, self._pooled_conn, self._pooled_created_time = pooled_acquire(
                    pool_key, factory, config_dict, validate=_validate_connection
                )
                self.conn = self._pooled_conn
            else:
                self.conn = MongoClient(self.source, **connect_args)
            self._connected = True

            # Get database and collection
            self._get_database_and_collection(database)

        except Exception as e:
            self._connected = False
            raise ConnectionError(f"Failed to connect to MongoDB: {e}") from e

    def _get_database_and_collection(self, database: str | None = None) -> None:
        """Get database and collection objects.

        Args:
            database: Database name (if not provided, get from kwargs)

        Raises:
            ValueError: If database or collection is not specified
        """
        if self.conn is None:
            raise RuntimeError("Not connected to database. Call connect() first.")

        # Get database name
        if database is None:
            database = self.kwargs.get("database")

        if not database:
            raise ValueError("'database' parameter is required for MongoDB driver")

        # Get collection name
        collection_name = self.kwargs.get("collection")
        if not collection_name:
            raise ValueError("'collection' parameter is required for MongoDB driver")

        # Get database and collection objects
        self._database = self.conn[database]
        self._collection = self._database[collection_name]

    @staticmethod
    def _prepare_pipeline(pipeline: Any, limit: Any, skip: Any) -> Any:
        """Add $limit/$skip stages to the pipeline unless already present."""
        # Add $limit to pipeline if limit is specified
        if limit is not None:
            # Check if $limit already exists in pipeline
            has_limit = any(stage.get("$limit") is not None for stage in pipeline if isinstance(stage, dict))
            if not has_limit:
                pipeline = list(pipeline) + [{"$limit": limit}]

        # Add $skip to pipeline if skip is specified
        if skip is not None:
            # Check if $skip already exists in pipeline
            has_skip = any(stage.get("$skip") is not None for stage in pipeline if isinstance(stage, dict))
            if not has_skip:
                pipeline = [{"$skip": skip}] + list(pipeline)
        return pipeline

    @staticmethod
    def _normalize_sort(sort: Any) -> list:
        """Normalize sort to list of tuples."""
        if isinstance(sort, dict):
            # Convert dict to list of tuples
            return list(sort.items())
        if isinstance(sort, list):
            # Already a list, but may contain dicts - convert to tuples
            sort_list = []
            for item in sort:
                if isinstance(item, dict):
                    sort_list.extend(item.items())
                elif isinstance(item, (list, tuple)) and len(item) == 2:
                    sort_list.append(tuple(item))
                else:
                    raise ValueError(f"Invalid sort item: {item}")
            return sort_list
        raise ValueError(f"Invalid sort format: {sort}. Expected dict, list of tuples, or list of dicts")

    def _build_find_kwargs(self, filter_dict: Any, projection: Any, sort: Any, skip: Any, limit: Any) -> dict[str, Any]:
        find_kwargs: dict[str, Any] = {}

        if filter_dict is not None:
            find_kwargs["filter"] = filter_dict

        if projection is not None:
            find_kwargs["projection"] = projection

        if sort is not None:
            find_kwargs["sort"] = self._normalize_sort(sort)

        if skip is not None:
            find_kwargs["skip"] = skip

        if limit is not None:
            find_kwargs["limit"] = limit
        return find_kwargs

    def _open_cursor(
        self, batch_size: Any, filter_dict: Any, projection: Any, sort: Any, skip: Any, limit: Any, pipeline: Any
    ) -> None:
        if pipeline:
            # Use aggregation pipeline
            self._cursor = self._collection.aggregate(
                self._prepare_pipeline(pipeline, limit, skip), batchSize=batch_size
            )
        else:
            # Use find() with filter, projection, sort, skip, limit
            find_kwargs = self._build_find_kwargs(filter_dict, projection, sort, skip, limit)

            # Execute find() with batch size
            self._cursor = self._collection.find(**find_kwargs).batch_size(batch_size)

    def _iter_cursor_docs(self) -> Iterator[Row]:
        """Iterate over cursor results, converting BSON types to native Python types."""
        for doc in self._cursor:
            # Convert ObjectId and other BSON types to native Python types
            # This ensures compatibility with JSON serialization and other formats
            if isinstance(doc, dict):
                doc_dict = self._convert_bson_types(doc)
                yield doc_dict
            else:
                yield doc

            self._update_metrics(rows_read=1)

    def _cleanup_cursor(self) -> None:
        """Clean up cursor."""
        if self._cursor is not None:
            try:
                self._cursor.close()
            except Exception:
                pass
            self._cursor = None

    def iterate(self) -> Iterator[Row]:
        """Return iterator of dict documents from MongoDB collection.

        Yields:
            dict: MongoDB document as dictionary

        Raises:
            RuntimeError: If not connected
        """
        if not self._connected or self.conn is None or self._collection is None:
            raise RuntimeError("Not connected to database. Call connect() first.")

        # Get parameters
        batch_size = self.kwargs.get("batch_size", 10000)
        filter_dict = self.kwargs.get("filter")
        projection = self.kwargs.get("projection")
        sort = self.kwargs.get("sort")
        skip = self.kwargs.get("skip")
        limit = self.kwargs.get("limit")
        pipeline = self.kwargs.get("pipeline")

        # Start metrics
        self._start_metrics()

        try:
            self._open_cursor(batch_size, filter_dict, projection, sort, skip, limit, pipeline)

            yield from self._iter_cursor_docs()

        except Exception as e:
            self._handle_error(e, "iterating documents")
            if self._on_error == "raise":
                raise
            # If error handling is 'skip' or 'warn', return empty iterator
            return

        finally:
            self._cleanup_cursor()

    def _convert_bson_types(self, obj: Any) -> Any:
        """Convert BSON types (ObjectId, etc.) to native Python types.

        Args:
            obj: Object that may contain BSON types

        Returns:
            Object with BSON types converted to native Python types
        """
        if isinstance(obj, dict):
            return {key: self._convert_bson_types(value) for key, value in obj.items()}
        elif isinstance(obj, list):
            return [self._convert_bson_types(item) for item in obj]
        else:
            # Check if it's an ObjectId
            # Use type name check to avoid importing bson.ObjectId
            if hasattr(obj, "__str__") and type(obj).__name__ == "ObjectId":
                return str(obj)
            # Check for other BSON types that might need conversion
            # datetime objects are already Python datetime, so they're fine
            # Decimal128, etc. would need similar handling if needed
            return obj

    def close(self) -> None:
        """Close MongoDB connection and clean up resources."""
        # Close cursor first
        if self._cursor is not None:
            try:
                self._cursor.close()
            except Exception:
                pass
            self._cursor = None

        # Return client to pool if pooled, otherwise close directly
        if self._pool is not None and self._pooled_conn is not None and self._pooled_created_time is not None:
            pooled_release(self._pool, self._pooled_conn, self._pooled_created_time)
            self._pool = None
            self._pooled_conn = None
            self._pooled_created_time = None
            self.conn = None
            self._connected = False
            self._closed = True
        else:
            # Direct close (no pooling)
            super().close()

    @staticmethod
    def list_collections(
        connection_string: str,
        database: str | None = None,
        **connect_args: Any,
    ) -> list[dict[str, Any]]:
        """List collections in MongoDB database.

        Args:
            connection_string: MongoDB connection string
            database: Optional database name (required if not in connection string)
            **connect_args: Additional connection arguments

        Returns:
            List of dicts with keys: database, collection, document_count (estimate)

        Raises:
            ImportError: If pymongo is not installed
            ConnectionError: If connection fails
            ValueError: If database is not specified
        """
        if MongoClient is None:
            raise ImportError("pymongo is required for MongoDB support. Install it with: pip install pymongo")

        try:
            # Parse connection string to extract database name if present
            parsed = urlparse(connection_string)
            db_name_from_url = parsed.path.lstrip("/").split("/")[0] if parsed.path else None

            # Get database name from parameter or connection string
            if database is None:
                database = db_name_from_url

            if not database:
                raise ValueError("'database' parameter is required for MongoDB list_collections")

            # Create MongoDB client
            client = MongoClient(connection_string, **connect_args)
            db = client[database]

            # List collections
            collection_names = db.list_collection_names()

            results = []
            for coll_name in collection_names:
                try:
                    # Get document count (may be slow for large collections)
                    doc_count = db[coll_name].estimated_document_count()
                except Exception:
                    # If count fails, set to None
                    doc_count = None

                results.append(
                    {
                        "database": database,
                        "collection": coll_name,
                        "document_count": doc_count,
                    }
                )

            client.close()
            return results

        except Exception as e:
            raise ConnectionError(f"Failed to list collections from MongoDB: {e}") from e
