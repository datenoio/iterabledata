"""
Example: Transform – head, tail, sample, select, slice.

Uses iterable.ops.transform: head(), tail(), sample_rows(), select(), slice_rows().
Run: python examples/ops/transform_example.py [path/to/data.csv]
"""

import sys

from iterable.ops import transform as transform_ops


def main():
    path = sys.argv[1] if len(sys.argv) > 1 else "data.csv"
    try:
        print("Head (first 3):")
        for row in transform_ops.head(path, n=3):
            print(row)
        print("\nTail (last 2):")
        for row in transform_ops.tail(path, n=2):
            print(row)
        print("\nSample (up to 2 rows, seed=42):")
        for row in transform_ops.sample_rows(path, n=2, seed=42):
            print(row)
        print("\nSelect fields (e.g. first two column names – adjust to your file):")
        for i, row in enumerate(transform_ops.select(path, fields=["id", "name"])):
            print(row)
            if i >= 2:
                break
        print("\nSlice rows (start=0, end=2):")
        for row in transform_ops.slice_rows(path, start=0, end=2):
            print(row)
    except FileNotFoundError:
        print(f"File not found: {path}. Skipping transform example.")


if __name__ == "__main__":
    main()
