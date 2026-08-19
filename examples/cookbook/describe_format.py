"""
Prompt: "what is parquet support in IterableData" / "describe the csv format"

Run: python examples/cookbook/describe_format.py [format_id]
"""

from __future__ import annotations

import sys

from iterable.catalog import describe_format


def main(format_id: str = "csv") -> dict:
    info = describe_format(format_id)
    print(f"{info['id']}: {info.get('description')}")
    return info


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "csv")
