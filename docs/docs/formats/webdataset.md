---
title: WebDataset Format
description: WebDataset TAR sample shards in IterableData
---

# WebDataset Format

Read WebDataset TAR shards as grouped sample dictionaries. Unlike the plain [TAR](/formats/tar) container (one member → delegated format), WebDataset groups members that share a key into a single record.

## Overview

| Property | Value |
|----------|-------|
| Format id | `webdataset` (alias `wds`) |
| Class | `WebDatasetIterable` |
| Extensions | prefer `format="webdataset"` on `.tar` / `.tar.gz`; `.wds` alias |
| Read | Yes |
| Write | No |
| Extra | none (stdlib `tarfile`) |

## Record shape

```python
{"__key__": "0001", "jpg": b"...", "json": {"label": "cat"}, "txt": "cat"}
```

- `.json` members decode to dicts when `decode_json=True` (default).
- Common text suffixes (`.txt`, `.cls`, …) decode as strings; other payloads stay as bytes.
- Incomplete trailing groups raise by default (`partial_group="error"`); use `"yield"` to emit them.

## Usage

```python
from iterable import open_iterable

with open_iterable("shard.tar", format="webdataset") as source:
    for sample in source:
        print(sample["__key__"], sample.keys())
```

Plain `open_iterable("shard.tar")` without `format="webdataset"` continues to use member-oriented TAR iteration.

## See also

- [TAR](/formats/tar) — member-oriented archive container
- [Supported formats](/formats/)

## Parameters

| Parameter | Type | Default | Required | Description |
|-----------|------|---------|----------|-------------|
| `encoding` | str | `'utf8'` | No | Passed via `iterableargs`. |

