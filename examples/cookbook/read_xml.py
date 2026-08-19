"""
Prompt: "read this XML file as records" / "parse XML without lxml boilerplate"

Run: python examples/cookbook/read_xml.py [path] [tagname]
"""

from __future__ import annotations

import sys

from iterable import open_iterable


def main(path: str = "data.xml", tagname: str = "item", limit: int = 5) -> list[dict]:
    rows: list[dict] = []
    with open_iterable(path, iterableargs={"tagname": tagname}) as source:
        for i, row in enumerate(source):
            if i >= limit:
                break
            rows.append(row)
            print(row)
    return rows


if __name__ == "__main__":
    path = sys.argv[1] if len(sys.argv) > 1 else "data.xml"
    tag = sys.argv[2] if len(sys.argv) > 2 else "item"
    main(path, tagname=tag)
