---
title: IATI Format
description: IATI aid-transparency activity XML in IterableData
---

# IATI Format

Read IATI (International Aid Transparency Initiative) activity XML as one activity dict per record.

## Overview

| Property | Value |
|----------|-------|
| Format id | `iati` |
| Class | `IATIIterable` |
| Extensions | `.iati`, `.iati.xml` |
| Read | Yes |
| Write | No |
| Extra | `xml` (`lxml`) |
| Maturity | experimental |

## Record shape

Activities are flattened from XML: element text, `@attr` attributes, and nested children. Typical keys include `iati-identifier` and `title`.

## Parameters

| Parameter | Default | Description |
|-----------|---------|-------------|
| `tagname` | `iati-activity` | Element name to iterate |

Streaming via `lxml` iterparse. Filename or stream supported.

## Usage

```python
from iterable.helpers.detect import open_iterable

with open_iterable("activities.iati.xml", format="iati") as source:
    for activity in source:
        print(activity["iati-identifier"], activity.get("title"))
```

Install with `pip install iterabledata[xml]`.

## See also

- [XML](/formats/xml) — generic XML element streaming
- [Supported formats](/formats/)
