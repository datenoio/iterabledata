"""
Prompt: "compute stats on this file" / "summarize this dataset"

Run: python examples/cookbook/stats_file.py [path]
"""

from __future__ import annotations

import sys

from iterable import open_iterable
from iterable.ops import stats


def main(path: str = "data.csv") -> dict:
    with open_iterable(path) as source:
        summary = stats.compute(source)
    field_names = list(summary.keys())[:20]
    print(f"fields: {field_names}")
    return summary


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "data.csv")
