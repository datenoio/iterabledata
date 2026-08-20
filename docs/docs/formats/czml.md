---
title: CZML Format
description: Cesium CZML JSON packets in IterableData
---

# CZML Format

Read and write Cesium CZML documents as one JSON packet per record.

## Overview

| Property | Value |
|----------|-------|
| Format id | `czml` |
| Class | `CZMLIterable` |
| Extensions | `.czml` |
| Read | Yes |
| Write | Yes |
| Extra | none (`ijson` optional for streaming arrays) |
| Maturity | experimental |

## Record shape

Each packet is a dict (document header, entities, etc.):

```python
{"id": "document", "version": "1.0"}
{"id": "point-1", "position": {"cartographicDegrees": [...]}}
```

A bare JSON object is treated as a single-packet document. Writes emit a JSON array of packets.

## Usage

```python
from iterable import open_iterable

with open_iterable("scene.czml") as source:
    for packet in source:
        print(packet.get("id"))

with open_iterable("out.czml", mode="w", format="czml") as dest:
    dest.write({"id": "document", "version": "1.0"})
    dest.write({"id": "entity-1", "name": "Sample"})
```


## Error Handling

- **Missing dependency**: optional libraries raise `ImportError` with an install hint (`pip install 'iterabledata[<extra>]'` when an extra exists).
- **Write mode**: read-only formats raise `WriteNotSupportedError` or `ValueError` when opened with `mode="w"`.
- **Bad or unsupported input**: may raise `ValueError`, `OSError`, or library-specific errors.
- See [Troubleshooting](/getting-started/troubleshooting) for decoding, detection, and engine issues.

## See also

- [GeoJSON](/formats/geojson) — geospatial features
- [KML](/formats/kml) — Keyhole Markup Language
- [Supported formats](/formats/)

## Parameters

| Parameter | Type | Default | Required | Description |
|-----------|------|---------|----------|-------------|
| `encoding` | str | `'utf-8'` | No | Passed via `iterableargs`. |

