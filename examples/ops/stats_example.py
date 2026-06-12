"""
Example: Compute field statistics and frequency.

Uses iterable.ops.stats: compute(), frequency().
Run: python examples/ops/stats_example.py [path/to/data.csv]
"""

import json
import sys

from iterable.ops import stats as stats_ops


def main():
    path = sys.argv[1] if len(sys.argv) > 1 else "data.csv"
    try:
        summary = stats_ops.compute(path, detect_dates=True)
    except FileNotFoundError:
        print(f"File not found: {path}. Skipping stats example.")
        return
    print("Compute (field statistics):")
    for field, info in list(summary.items())[:5]:
        print(f"  {field}: {info}")

    print("\nFrequency (top values per field, limit 5):")
    freqs = stats_ops.frequency(path, fields=None, limit=5)
    if freqs:
        print(json.dumps(dict(list(freqs.items())[:1]), indent=2))


if __name__ == "__main__":
    main()
