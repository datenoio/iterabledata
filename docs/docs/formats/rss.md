---
title: RSS / Atom Feed Format
description: RSS and Atom syndication entries in IterableData
---

# RSS / Atom Feed Format

Read RSS/Atom feeds as one dict per entry (via feedparser). Feeds are **read-only**.

## Overview

| Property | Value |
|----------|-------|
| Format id | `rss` (aliases `feed`, `atom`) |
| Class | `FeedIterable` |
| Extensions | `.rss`, `.feed`, `.atom` |
| Read | Yes |
| Write | No |
| Extra | `feed` (`feedparser`) |
| Maturity | stable |

## File Extensions

- `.rss` — RSS feeds
- `.atom` — Atom feeds
- `.feed` — generic feed alias

## Implementation Details

### Reading

- Loads the full feed document, then parses with `feedparser`
- One dict per entry; `totals()` is the entry count
- The first entry also includes `feed_title`, `feed_link`, and `feed_description`

### Writing

Writing is not supported. `write()` / `write_bulk()` raise `WriteNotSupportedError`.

### Key Features

- **RSS and Atom** via the same reader
- **Feed metadata** on the first entry
- **Tags and content** normalized into lists

## Usage

```python
from iterable import open_iterable

with open_iterable("blog.rss") as source:
    for entry in source:
        print(entry["title"], entry["link"])
```

Record shape:

```python
{
    "title": "...",
    "link": "https://...",
    "published": "...",
    "updated": "...",
    "author": "...",
    "summary": "...",
    "content": ["..."],
    "id": "...",
    "tags": ["news"],
}
```

## Parameters

| Parameter | Type | Default | Required | Description |
|-----------|------|---------|----------|-------------|
| `encoding` | str | `'utf8'` | No | Text encoding when reading the feed document |

## Error Handling

- **ImportError**: Missing `feedparser` — install with `pip install iterabledata[feed]`
- **WriteNotSupportedError**: Feed formats are read-only
- **FileNotFoundError**: Path is wrong or the file is missing
- Malformed feeds may yield empty `entries` or partial fields rather than a hard parse failure (`feedparser` is permissive)

See [Troubleshooting](/getting-started/troubleshooting) for more help.

## Installation

```bash
pip install 'iterabledata[feed]'
```

## Limitations

1. **Read-only**
2. **Full document load** — not incremental XML streaming
3. **Requires feedparser**

## Related Formats

- [Supported formats](/formats/)
