"""
Example: Run a pipeline with a process function.

Uses iterable.pipeline.core.pipeline to read, transform, and write rows.
Run: python examples/pipeline/run_pipeline.py [source.csv] [output.csv]
"""

import os
import sys
import tempfile

from iterable.helpers.detect import open_iterable
from iterable.pipeline.core import pipeline


def process(row, state):
    """Add a computed field and increment state."""
    state["count"] = state.get("count", 0) + 1
    row = dict(row)
    val = row.get("value") or row.get("id") or 0
    try:
        row["doubled"] = int(val) * 2
    except (TypeError, ValueError):
        row["doubled"] = val
    return row


def main():
    src_path = sys.argv[1] if len(sys.argv) > 1 else None
    out_path = sys.argv[2] if len(sys.argv) > 2 else None

    if not src_path or not os.path.isfile(src_path):
        print("No source file; using minimal demo data (3 rows) and temp output.")
        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
            f.write("id,value\n1,10\n2,20\n3,30\n")
            src_path = f.name
        out_path = out_path or tempfile.mktemp(suffix=".csv")

    with open_iterable(src_path) as src:
        keys = list(next(iter(src), {}).keys()) if src_path else ["id", "value"]
    keys = keys or ["id", "value"]
    if "doubled" not in keys:
        keys.append("doubled")

    with open_iterable(src_path) as src, open_iterable(
        out_path, mode="w", iterableargs={"keys": keys}
    ) as dst:
        result = pipeline(src, dst, process_func=process)
        print(f"Pipeline: rows_read={result.rows_read}, rows_written={result.rows_written}")
    if out_path and os.path.isfile(out_path):
        print(f"Output: {out_path}")


if __name__ == "__main__":
    main()
