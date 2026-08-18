"""
Prompt: "convert this CSV to JSONL" / "convert between formats"

Run: python examples/cookbook/convert_formats.py [input] [output]
"""

from __future__ import annotations

import sys

from iterable.convert import convert


def main(src: str = "data.csv", dest: str = "data.jsonl") -> None:
    result = convert(src, dest)
    print(f"Wrote {dest} ({result.rows_out} rows)")


if __name__ == "__main__":
    main(
        sys.argv[1] if len(sys.argv) > 1 else "data.csv",
        sys.argv[2] if len(sys.argv) > 2 else "data.jsonl",
    )
