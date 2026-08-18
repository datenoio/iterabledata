"""
Prompt: "sample rows from this file" / "what format is this"

Run: python examples/cookbook/sample_file.py [path]
"""

from __future__ import annotations

import sys

from iterable.tools import detect_format, read_sample


def main(path: str = "data.csv", n: int = 5) -> dict:
    detected = detect_format(path)
    sample = read_sample(path, n=n, redact=True)
    print(detected)
    print(sample)
    return {"detect": detected, "sample": sample}


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "data.csv")
