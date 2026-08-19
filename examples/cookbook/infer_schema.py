"""
Prompt: "infer schema for this file" / "what columns does this file have"

Run: python examples/cookbook/infer_schema.py [path]
"""

from __future__ import annotations

import sys

from iterable.tools import infer_schema


def main(path: str = "data.csv") -> dict:
    result = infer_schema(path)
    print(result)
    return result


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "data.csv")
