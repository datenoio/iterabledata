"""
Example: Infer schema and export to JSON Schema.

Uses iterable.ops.schema: infer(), to_json_schema().
Run: python examples/ops/schema_example.py [path/to/data.csv]
"""

import json
import sys

from iterable.ops import schema as schema_ops


def main():
    path = sys.argv[1] if len(sys.argv) > 1 else "data.csv"
    try:
        inferred = schema_ops.infer(path, detect_dates=True, sample_size=5000)
    except FileNotFoundError:
        print(f"File not found: {path}. Skipping schema example.")
        return
    print("Inferred schema (fields):")
    print(json.dumps(inferred.get("fields", {}), indent=2)[:500], "...")

    json_schema = schema_ops.to_json_schema(inferred)
    print("\nJSON Schema (excerpt):")
    print(json.dumps(json_schema, indent=2)[:400], "...")


if __name__ == "__main__":
    main()
