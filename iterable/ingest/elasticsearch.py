"""
Elasticsearch ingestor.
"""

from __future__ import annotations

import collections.abc
import time
from collections.abc import Callable
from typing import Any

try:
    from elasticsearch import Elasticsearch
except ImportError:
    Elasticsearch = None

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
    Ingest data into Elasticsearch index.

    Args:
        iterable: An iterable of row dictionaries
        db_url: Elasticsearch connection URL
        table: Index name
        mode: Ingestion mode - "insert" or "upsert"
        upsert_key: Field name to use as document ID (default: "_id" or first field)
        batch: Batch size for bulk operations
        create_table: Whether to create index if it doesn't exist
        progress: Optional progress callback

    Returns:
        IngestionResult with statistics
    """
    if Elasticsearch is None:
        raise ImportError(
            "elasticsearch is required for Elasticsearch ingestion. Install with: pip install elasticsearch>=8.0"
        )

    start_time = time.time()
    rows_processed = 0
    rows_inserted = 0
    rows_updated = 0
    errors: list[str] = []

    try:
        es = Elasticsearch([db_url])

        # Create index if needed
        if create_table:
            if not es.indices.exists(index=table):
                es.indices.create(index=table)

        # Prepare batch
        batch_actions: list[dict[str, Any]] = []
        rows_processed = 0
        doc_id_field = upsert_key if isinstance(upsert_key, str) else (upsert_key[0] if upsert_key else None)

        for row in iterable:
            action: dict[str, Any] = {"_index": table, "_source": row}

            if mode == "upsert" and doc_id_field and doc_id_field in row:
                action["_id"] = str(row[doc_id_field])
                action["_op_type"] = "index"  # Index with ID = upsert
            else:
                action["_op_type"] = "index"

            batch_actions.append(action)
            rows_processed += 1

            if len(batch_actions) >= batch:
                from elasticsearch.helpers import bulk

                bulk(es, batch_actions)
                rows_inserted += len(batch_actions)
                batch_actions = []

                if progress:
                    progress({"rows_processed": rows_processed, "rows_inserted": rows_inserted})

        # Insert remaining batch
        if batch_actions:
            from elasticsearch.helpers import bulk

            bulk(es, batch_actions)
            rows_inserted += len(batch_actions)

    except Exception as e:
        errors.append(str(e))

    return IngestionResult(
        rows_processed=rows_processed,
        rows_inserted=rows_inserted,
        rows_updated=rows_updated,
        errors=errors,
        elapsed_seconds=time.time() - start_time,
    )
