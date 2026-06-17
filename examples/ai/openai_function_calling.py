#!/usr/bin/env python3
"""Example: OpenAI function calling with IterableData tools."""

from __future__ import annotations

import json

from iterable.tools import schemas


def main() -> None:
    functions = schemas.to_openai_functions()
    print(f"Registered {len(functions)} IterableData tools for OpenAI:")
    for fn in functions:
        print(f"  - {fn['function']['name']}")

    # Simulate a tool call result without calling OpenAI
    result = schemas.call_tool(
        "read_sample",
        {"path": "fixtures/2cols6rows.csv", "n": 3, "redact": False},
    )
    print("\nSample tool result:")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
