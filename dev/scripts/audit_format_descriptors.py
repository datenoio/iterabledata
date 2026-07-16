"""Audit the declarative format catalog for missing identity metadata."""

from __future__ import annotations

import argparse
import csv
import sys


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="fail when required descriptor fields are empty")
    args = parser.parse_args()

    from iterable.helpers.format_registry import iter_descriptors

    rows = list(iter_descriptors())
    writer = csv.writer(sys.stdout)
    writer.writerow(
        [
            "id",
            "module",
            "class",
            "extra",
            "maturity",
            "read_memory",
            "write_memory",
            "native_bulk_read",
            "native_bulk_write",
            "selection",
            "source_constraints",
        ]
    )
    missing: list[str] = []
    for descriptor in rows:
        writer.writerow(
            [
                descriptor.id,
                descriptor.module,
                descriptor.cls,
                descriptor.extra or "",
                descriptor.maturity,
                descriptor.read_memory,
                descriptor.write_memory,
                descriptor.native_bulk_read,
                descriptor.native_bulk_write,
                ",".join(descriptor.selection),
                ",".join(descriptor.source_constraints),
            ]
        )
        if not descriptor.module or not descriptor.cls or not descriptor.description:
            missing.append(descriptor.id)

    if args.check and missing:
        raise SystemExit(f"Descriptors missing required fields: {', '.join(missing)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
