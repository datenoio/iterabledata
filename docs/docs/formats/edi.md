---
title: EDI Format
description: X12 / EDIFACT segment streams in IterableData
---

# EDI Format

## Description

EDI (Electronic Data Interchange) covers common X12 and EDIFACT text dialects used in business messaging. IterableData provides a pragmatic, **read-only** segment parser: it detects separators, then yields one dict per segment (`segment_id`, `elements`). This is for streaming inspection — not a full HIPAA/mapping validation suite. Marked **experimental**. No optional dependency.

## File Extensions

- `.edi` — EDI interchange documents
- Other text EDI filenames may work when format is forced

## Implementation Details

### Reading

- Reads the full document text, then splits into segments
- Auto-detects segment terminator and element separator from the prefix (ISA / UNA / heuristics)
- Optional overrides: `segment_terminator`, `element_separator`
- Record shape: `{"segment_id": "ISA", "elements": ["00", ...]}`
- Not streaming at the I/O layer (`is_streaming()` is `False`)

### Writing

Writing is not supported (`WriteNotSupportedError`).

### Key Features

- **X12 + EDIFACT heuristics**: ISA and UNA recognition
- **Pure Python**: no extra packages
- **Separator overrides** via `iterableargs`

## Usage

```python
from iterable import open_iterable

with open_iterable("invoice.edi") as source:
    for seg in source:
        print(seg["segment_id"], seg["elements"][:3])

with open_iterable(
    "invoice.edi",
    iterableargs={"segment_terminator": "~", "element_separator": "*"},
) as source:
    for seg in source:
        print(seg)
```

## Parameters

| Parameter | Type | Default | Required | Description |
|-----------|------|---------|----------|-------------|
| `segment_terminator` | str | auto | No | Segment delimiter (e.g. `~` or newline) |
| `element_separator` | str | auto | No | Element delimiter (e.g. `*` or `+`) |
| `encoding` | str | `utf8` | No | Text encoding |

## Installation

```bash
pip install iterabledata
```

No format-specific extra.

## Limitations

1. **Read-only**
2. **Experimental** / pragmatic subset — not a full EDI mapper
3. **Whole-document load** before yielding segments
4. Nested composite elements are not further split beyond the element separator
5. Binary EDI variants are out of scope

## Error Handling

- **WriteNotSupportedError**: write mode or write APIs
- **FormatParseError**: empty document when detecting separators
- **I/O errors**: missing or unreadable files
- No third-party **ImportError** for this format

## Related Formats

- [CSV](csv.md) — delimited tabular text
- [XML](xml.md) — structured markup (when partners use XML instead of EDI)
- [JSON](json.md) — modern interchange payloads
