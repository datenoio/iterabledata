---
sidebar_position: 3
title: Wikipedia Processing
description: Process Wikipedia XML dumps with Iterable Data
---

# Wikipedia Processing

This example demonstrates how to process Wikipedia XML dumps using Iterable Data. The example converts Wikipedia XML dumps to compressed JSONL format for efficient querying with DuckDB.

## Overview

Wikipedia provides XML dumps of all articles. These dumps are large (often several GB compressed) and need efficient processing. Iterable Data makes it easy to:

1. Read compressed XML dumps
2. Parse XML pages
3. Convert to JSONL format
4. Compress for storage

## Example: Converting Wikipedia XML to JSONL

Here's a complete example from the `examples/simplewiki` directory:

```python
import os
from iterable.datatypes.xml import XMLIterable
from iterable.datatypes.jsonl import JSONLinesIterable
from iterable.codecs.bz2codec import BZIP2Codec
from iterable.codecs.zstdcodec import ZSTDCodec
from tqdm import tqdm

RAW_FILE = 'data/raw/simplewiki-latest-pages-articles-multistream.xml.bz2'
RESULT_ZSTD_JSONL_FILE = 'data/raw/simplewiki.jsonl.zst'

def convert_wikipedia_dump():
    # Open compressed XML file
    codecobj = BZIP2Codec(RAW_FILE, mode='r')
    iterable = XMLIterable(codec=codecobj, tagname='page')
    
    # Open output JSONL file with ZStandard compression
    wrcodecobj = ZSTDCodec(RESULT_ZSTD_JSONL_FILE, mode='w')
    witerable = JSONLinesIterable(codec=wrcodecobj, mode='w')
    
    # Process with progress bar
    for row in tqdm(iterable, desc='Converting data'):
        witerable.write(row)
    
    iterable.close()
    witerable.close()

if __name__ == "__main__":
    convert_wikipedia_dump()
```

## Using the High-Level API

You can also use the simpler `open_iterable()` function:

```python
from iterable import open_iterable
from tqdm import tqdm

RAW_FILE = 'data/raw/simplewiki-latest-pages-articles-multistream.xml.bz2'
RESULT_FILE = 'data/raw/simplewiki.jsonl.zst'

# Open XML file with BZIP2 compression
source = open_iterable(RAW_FILE, iterableargs={'tagname': 'page'})

# Open output JSONL file with ZStandard compression
with open_iterable(RESULT_FILE, mode='w') as destination:

    # Process with progress tracking
    for row in tqdm(source, desc='Converting Wikipedia dump'):
        destination.write(row)

    source.close()
```

## Enriching Wikipedia Data

After converting to JSONL, you can enrich the data with additional processing:

```python
from iterable import open_iterable
from iterable.pipeline import pipeline

def enrich_wikipedia_page(page, state):
    """Add categories to Wikipedia pages"""
    # Extract categories from page content
    categories = extract_categories(page)
    page['categories'] = categories
    return page

# Read converted JSONL file
source = open_iterable('simplewiki.jsonl.zst')
with open_iterable('simplewiki_enriched.jsonl.zst', mode='w') as destination:

    pipeline(
        source=source,
        destination=destination,
        process_func=enrich_wikipedia_page
    )

    source.close()
```

## Querying with DuckDB

Once converted to JSONL, you can query the data efficiently with DuckDB:

```python
from iterable import open_iterable

# Use DuckDB engine for fast queries
with open_iterable('simplewiki.jsonl.zst', engine='duckdb') as source:

    # Get total count
    total = source.totals()
    print(f"Total pages: {total}")

    # Query specific pages
    for page in source:
        if 'Argentina' in page.get('categories', []):
            print(page['title'])

```

Or use DuckDB directly:

```python
import duckdb

# Query JSONL file directly
conn = duckdb.connect()
result = conn.execute("""
    SELECT title, categories 
    FROM 'simplewiki.jsonl.zst' 
    WHERE list_contains(categories, 'Argentina')
""").fetchall()

for row in result:
    print(row)
```

## Processing Steps

1. **Download Wikipedia dump**: Get the latest dump from [dumps.wikimedia.org](https://dumps.wikimedia.org)
2. **Extract index file**: Extract the index file to get page count
3. **Convert to JSONL**: Use Iterable Data to convert XML to JSONL
4. **Enrich data**: Add categories, links, or other metadata
5. **Query data**: Use DuckDB for fast queries

## Performance Tips

1. **Use compression**: ZStandard (`.zst`) provides excellent compression and speed
2. **Batch processing**: Process in batches for better memory usage
3. **Use DuckDB**: DuckDB engine provides fast queries on JSONL files
4. **Progress tracking**: Use `tqdm` or pipeline callbacks to monitor progress

## Complete Example

See the full example in the `examples/simplewiki/` directory:

- `convert.py` - Converts XML dump to JSONL
- `enrich.py` - Enriches pages with categories
- `convert_parquet.py` - Converts to Parquet format

## Related Topics

- [DuckDB Integration](/use-cases/duckdb-integration) - Learn about DuckDB engine
- [Data Pipelines](/use-cases/data-pipelines) - Build processing pipelines
- [Format Conversion](/use-cases/format-conversion) - Convert between formats
