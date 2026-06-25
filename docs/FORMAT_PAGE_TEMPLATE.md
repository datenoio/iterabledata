# Format page template (not published)

Copy this file to `docs/docs/formats/<format-id>.md` when authoring a new format page.
Do **not** place this template under `docs/docs/` — Docusaurus parses all markdown there and
invalid placeholder frontmatter breaks the site build.

---

# [Format Name] Format

## Description

[What the format is, what it's used for, and why it's useful. Include 2-3 sentences about the format's purpose and common use cases.]

## File Extensions

- `.ext1` - [Description of extension 1]
- `.ext2` - [Alternative extension or alias]

## Implementation Details

### Reading

The [Format Name] implementation:
- [Key implementation detail 1]
- [Key implementation detail 2]
- [Key implementation detail 3]
- [Any special handling or features]

### Writing

Writing support:
- [Key writing feature 1]
- [Key writing feature 2]
- [Any special considerations]

### Key Features

- **Feature 1**: [Description]
- **Feature 2**: [Description]
- **Feature 3**: [Description]
- **Feature 4**: [Description]

## Usage

```python
from iterable.helpers.detect import open_iterable

# Recommended: Using context manager (automatic cleanup)
# Basic reading
with open_iterable("data.[ext]") as source:
    for row in source:
        print(row)

# Writing (if supported)
with open_iterable("output.[ext]", mode="w", iterableargs={"param1": "value1"}) as dest:
    dest.write({"key": "value"})
```

## Parameters

| Parameter | Type | Default | Required | Description |
|-----------|------|---------|----------|-------------|
| `param1` | str | `default` | No | [Description of parameter] |

## Installation

```bash
pip install 'iterabledata[<extra>]'
```

## Related Formats

- [Link to related format](related-format.md) - [Why it's related]
