#!/usr/bin/env python3
"""Example: Anthropic tool schemas with IterableData tools."""

from __future__ import annotations

import json

from iterable.tools import schemas


def main() -> None:
    tools = schemas.to_anthropic_tools()
    print(f"Registered {len(tools)} IterableData tools for Anthropic:")
    for tool in tools:
        print(f"  - {tool['name']}")

    result = schemas.call_tool("infer_schema", {"path": "fixtures/2cols6rows.csv"})
    print("\nInfer schema tool result:")
    print(json.dumps(result, indent=2)[:500], "...")


if __name__ == "__main__":
    main()
