#!/usr/bin/env python3
"""Example: LangChain StructuredTools from IterableData."""

from __future__ import annotations


def main() -> None:
    try:
        from iterable.tools.langchain import get_tools
    except ImportError:
        print("Install with: pip install iterabledata[langchain]")
        return

    tools = get_tools()
    print(f"Loaded {len(tools)} LangChain tools:")
    for tool in tools:
        print(f"  - {tool.name}: {tool.description[:60]}...")


if __name__ == "__main__":
    main()
