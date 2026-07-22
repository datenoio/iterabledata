---
title: RSS / Atom Feed Format
description: RSS and Atom syndication entries in IterableData
---

# RSS / Atom Feed Format

Read RSS/Atom feeds as one dict per entry (via feedparser).

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

## Record shape

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

The first entry also includes `feed_title`, `feed_link`, and `feed_description`. `totals()` is the entry count.

## Usage

```python
from iterable.helpers.detect import open_iterable

with open_iterable("blog.rss") as source:
    for entry in source:
        print(entry["title"], entry["link"])
```

Install with `pip install iterabledata[feed]`.

## See also

- [Supported formats](/formats/)
