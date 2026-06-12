"""
MongoDB database ingestor.
"""

from __future__ import annotations

import collections.abc
import time
from collections.abc import Callable
from typing import Any

try:
    from pymongo import MongoClient
except ImportError:
    MongoClient = None

from ..types import Row
from .core import IngestionResult


def ingest(
    iterable: collections.abc.Iterable[Row],
    db_url: str,
    table: str,
    mode: str = "insert",
    upsert_key: str | list[str] | None = None,
    batch: int = 5000,
    create_table: bool = False,
    progress: Callable[[dict[str, Any]], None] | None = None,
) -> IngestionResult:
    """
    Ingest data into MongoDB collection.

    Args:
        iterable: An iterable of row dictionaries
        db_url: MongoDB connection URL
        table: Collection name
        mode: Ingestion mode - "insert" or "upsert"
        upsert_key: Field name(s) for upsert matching (default: "_id")
        batch: Batch size for bulk inserts
        create_table: Ignored for MongoDB (collections created automatically)
        progress: Optional progress callback

    Returns:
        IngestionResult with statistics
    """
    if MongoClient is None:
        raise ImportError("pymongo is required for MongoDB ingestion. Install with: pip install pymongo")

    start_time = time.time()
    rows_processed = 0
    rows_inserted = 0
    rows_updated = 0
    errors: list[str] = []

    try:
        client = MongoClient(db_url)
        # Extract database name from URL or use default
        db_name = db_url.split("/")[-1].split("?")[0] if "/" in db_url else "test"
        db = client[db_name]
        collection = db[table]

        # Prepare batch
        batch_rows: list[Row] = []
        rows_processed = 0

        for row in iterable:
            batch_rows.append(row)
            rows_processed += 1

            if len(batch_rows) >= batch:
                if mode == "upsert" and upsert_key:
                    _upsert_batch(collection, batch_rows, upsert_key)
                    rows_updated += len(batch_rows)
                else:
                    collection.insert_many(batch_rows)
                    rows_inserted += len(batch_rows)

                batch_rows = []

                if progress:
                    progress({"rows_processed": rows_processed, "rows_inserted": rows_inserted})

        # Insert remaining batch
        if batch_rows:
            if mode == "upsert" and upsert_key:
                _upsert_batch(collection, batch_rows, upsert_key)
                rows_updated += len(batch_rows)
            else:
                collection.insert_many(batch_rows)
                rows_inserted += len(batch_rows)

        client.close()

    except Exception as e:
        errors.append(str(e))

    return IngestionResult(
        rows_processed=rows_processed,
        rows_inserted=rows_inserted,
        rows_updated=rows_updated,
        errors=errors,
        elapsed_seconds=time.time() - start_time,
    )


def _upsert_batch(collection: Any, rows: list[Row], upsert_key: str | list[str]):
    """Upsert a batch of rows into MongoDB."""
    if isinstance(upsert_key, str):
        upsert_key = [upsert_key]

    for row in rows:
        # Build filter for upsert
        filter_dict = {key: row.get(key) for key in upsert_key if row.get(key) is not None}
        collection.replace_one(filter_dict, row, upsert=True)
