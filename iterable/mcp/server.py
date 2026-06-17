"""Model Context Protocol server for IterableData agent tools."""

from __future__ import annotations

import json
from typing import Any

from ..tools import schemas


def _register_tools(mcp: Any) -> None:
    """Register IterableData tools on a FastMCP instance."""

    @mcp.tool()
    def detect_format(path: str) -> str:
        """Detect data format and compression for a file."""
        return json.dumps(schemas.call_tool("detect_format", {"path": path}))

    @mcp.tool()
    def describe_capabilities(format_id: str) -> str:
        """Describe format metadata and capabilities."""
        return json.dumps(schemas.call_tool("describe_capabilities", {"format_id": format_id}))

    @mcp.tool()
    def read_sample(path: str, n: int = 10, redact: bool = False) -> str:
        """Read a bounded sample of rows from a data file."""
        return json.dumps(schemas.call_tool("read_sample", {"path": path, "n": n, "redact": redact}))

    @mcp.tool()
    def infer_schema(path: str) -> str:
        """Infer schema for a data file."""
        return json.dumps(schemas.call_tool("infer_schema", {"path": path}))

    @mcp.tool()
    def analyze_dataset(path: str, autodoc: bool = False) -> str:
        """Analyze dataset structure; optional AI documentation."""
        return json.dumps(schemas.call_tool("analyze_dataset", {"path": path, "autodoc": autodoc}))

    @mcp.tool()
    def generate_documentation(path: str, provider: str = "openai", doc_format: str = "json") -> str:
        """Generate AI-powered dataset documentation."""
        return json.dumps(
            schemas.call_tool(
                "generate_documentation",
                {"path": path, "provider": provider, "doc_format": doc_format},
            )
        )

    @mcp.tool()
    def convert_file(
        input_path: str,
        output_path: str,
        confirm: bool = False,
        dry_run: bool = False,
    ) -> str:
        """Convert between formats. Writes require confirm=True."""
        return json.dumps(
            schemas.call_tool(
                "convert_file",
                {
                    "input_path": input_path,
                    "output_path": output_path,
                    "confirm": confirm,
                    "dry_run": dry_run,
                },
            )
        )

    @mcp.tool()
    def plan_conversion(source: str, target: str, use_llm: bool = False) -> str:
        """Produce a declarative conversion plan without writing files."""
        payload = {"source": source, "target": target, "use_llm": use_llm}
        return json.dumps(schemas.call_tool("plan_conversion", payload))

    @mcp.tool()
    def suggest_transform(path: str, goal: str) -> str:
        """Suggest a declarative transform spec (requires iterabledata[ai])."""
        return json.dumps(schemas.call_tool("suggest_transform", {"path": path, "goal": goal}))

    @mcp.tool()
    def translate_filter(expression: str) -> str:
        """Translate a filter expression into a validated AST (DSL parsing; no LLM by default)."""
        return json.dumps(schemas.call_tool("translate_filter", {"expression": expression}))


def create_mcp_server(name: str = "iterabledata") -> Any:
    """Create a FastMCP server with IterableData tools registered."""
    try:
        from mcp.server.fastmcp import FastMCP
    except ImportError as err:
        raise ImportError("mcp package is required. Install with: pip install iterabledata[mcp]") from err

    mcp = FastMCP(name)
    _register_tools(mcp)
    return mcp


def main() -> None:
    """Entry point for ``iterable-mcp`` console script (stdio transport)."""
    create_mcp_server().run()


if __name__ == "__main__":
    main()
