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

# Imported at module level (guarded) so the optional dependency stays optional
# while remaining patchable as ``iterable.db.mongo.MongoClient`` in tests.
try:
    from pymongo import MongoClient
except ImportError:  # pragma: no cover - exercised when dependency is absent
    MongoClient = None


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
        """
        super().__init__(source, **kwargs)
        self._cursor: Any = None
        self._database: Any = None
        self._collection: Any = None

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

        try:
            # Parse connection string to extract database name if present
            parsed = urlparse(self.source)
            db_name_from_url = parsed.path.lstrip("/").split("/")[0] if parsed.path else None

            # Get database name from kwargs or connection string
            database = self.kwargs.get("database") or db_name_from_url

            # Create MongoDB client
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
            if pipeline:
                # Use aggregation pipeline
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

                # Execute aggregation pipeline
                self._cursor = self._collection.aggregate(pipeline, batchSize=batch_size)

            else:
                # Use find() with filter, projection, sort, skip, limit
                find_kwargs: dict[str, Any] = {}

                if filter_dict is not None:
                    find_kwargs["filter"] = filter_dict

                if projection is not None:
                    find_kwargs["projection"] = projection

                if sort is not None:
                    # Normalize sort to list of tuples
                    if isinstance(sort, dict):
                        # Convert dict to list of tuples
                        sort_list = list(sort.items())
                    elif isinstance(sort, list):
                        # Already a list, but may contain dicts - convert to tuples
                        sort_list = []
                        for item in sort:
                            if isinstance(item, dict):
                                sort_list.extend(item.items())
                            elif isinstance(item, (list, tuple)) and len(item) == 2:
                                sort_list.append(tuple(item))
                            else:
                                raise ValueError(f"Invalid sort item: {item}")
                    else:
                        raise ValueError(
                            f"Invalid sort format: {sort}. Expected dict, list of tuples, or list of dicts"
                        )

                    find_kwargs["sort"] = sort_list

                if skip is not None:
                    find_kwargs["skip"] = skip

                if limit is not None:
                    find_kwargs["limit"] = limit

                # Execute find() with batch size
                self._cursor = self._collection.find(**find_kwargs).batch_size(batch_size)

            # Iterate over cursor results
            for doc in self._cursor:
                # Convert ObjectId and other BSON types to native Python types
                # This ensures compatibility with JSON serialization and other formats
                if isinstance(doc, dict):
                    doc_dict = self._convert_bson_types(doc)
                    yield doc_dict
                else:
                    yield doc

                self._update_metrics(rows_read=1)

        except Exception as e:
            self._handle_error(e, "iterating documents")
            if self._on_error == "raise":
                raise
            # If error handling is 'skip' or 'warn', return empty iterator
            return

        finally:
            # Clean up cursor
            if self._cursor is not None:
                try:
                    self._cursor.close()
                except Exception:
                    pass
                self._cursor = None

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

        # Close connection
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
