"""
Prompt: "what is in this file" / "infer schema" / "inspect this dataset"

Run: python examples/cookbook/inspect_file.py [path]
"""

from __future__ import annotations

import sys

from iterable.ops import inspect as inspect_ops
from iterable.ops import schema as schema_ops


def main(path: str = "data.csv") -> dict:
    analysis = inspect_ops.analyze(path)
    inferred = schema_ops.infer(path)
    field_names = list((inferred.get("fields") or {}).keys())
    print(f"rows sampled: {analysis.get('row_count')}")
    print("schema fields:", field_names[:20])
    return {"analysis": analysis, "schema": inferred}


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "data.csv")
