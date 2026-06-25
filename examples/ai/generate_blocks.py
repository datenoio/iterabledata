"""
Example: Block-based AI dataset documentation.

Demonstrates ``iterable.ai.doc.generate_blocks`` which produces independent,
machine-readable documentation blocks (each with markdown + structured data),
user-provided context, in-process progress hooks, and an assembled document.

Uses OpenRouter by default (same provider settings as ``generate_documentation.py``).

Usage:
    export OPENROUTER_API_KEY="sk-or-..."
    python generate_blocks.py <data_file>

Configuration via environment variables:
    OPENROUTER_API_KEY   API key for OpenRouter (required for the default provider)
    OPENROUTER_MODEL     Optional model override (defaults to the provider default)

You can also target any other provider by editing the call below, or rely on the
provider-agnostic LLM_* variables (LLM_PROVIDER/LLM_BASE_URL/LLM_API_KEY/LLM_DEFAULT_MODEL).
"""

from __future__ import annotations

import os
import sys
import time

from iterable.ai import doc
from iterable.ai.progress import ProgressEvent

# Default provider settings, mirroring examples/ai/generate_documentation.py.
PROVIDER = "openrouter"
API_KEY_ENV = "OPENROUTER_API_KEY"

BLOCKS = ["general", "schema", "quality", "examples", "statistics", "codebook"]


class ProgressPrinter:
    """Print each progress stage with elapsed timing.

    Reports the time spent since the previous event (``+step``) and the cumulative
    time since the first event (``total``), then a per-stage breakdown on summary.
    """

    def __init__(self) -> None:
        self.start: float | None = None
        self.last: float | None = None
        self.timings: list[tuple[str, float]] = []

    def __call__(self, event: ProgressEvent) -> None:
        now = time.perf_counter()
        if self.start is None:
            self.start = now
            self.last = now
        step = now - (self.last or now)
        total = now - self.start
        label = event.stage.value
        detail = f"  {event.detail}" if event.detail else ""
        print(f"  [{event.progress:3d}%] {label:<11} +{step:6.2f}s  ({total:6.2f}s total){detail}")
        self.timings.append((event.detail or label, step))
        self.last = now

    @property
    def total_seconds(self) -> float:
        if self.start is None or self.last is None:
            return 0.0
        return self.last - self.start

    def slowest(self, limit: int = 5) -> list[tuple[str, float]]:
        return sorted((t for t in self.timings if t[1] > 0), key=lambda t: t[1], reverse=True)[:limit]


def _hr(title: str = "") -> None:
    if title:
        print(f"\n{'=' * 70}\n{title}\n{'=' * 70}")
    else:
        print("=" * 70)


def _format_bytes(num: int | None) -> str:
    if not num:
        return "-"
    size = float(num)
    for unit in ("B", "KB", "MB", "GB"):
        if size < 1024 or unit == "GB":
            return f"{size:.0f} {unit}" if unit == "B" else f"{size:.1f} {unit}"
        size /= 1024
    return f"{num} B"


def _block_summary(name: str, block: dict) -> str:
    data = block.get("data", {}) or {}
    status = data.get("status")
    if status == "not_implemented":
        return "deferred (not implemented in this version)"
    if name == "schema" or name.startswith("schema:"):
        return f"{len(data.get('fields', []))} fields"
    if name == "statistics":
        return f"{len(data.get('fields', {}))} fields profiled"
    if name == "quality":
        overall = data.get("overall")
        obs = len(data.get("observations", []))
        return f"overall={overall or '-'}, {obs} observations"
    if name == "examples":
        return f"{len(data.get('examples', []))} examples"
    if name == "codebook":
        return f"{len(data.get('entries', []))} entries"
    chars = len(block.get("markdown") or "")
    return f"{chars} chars of markdown"


def main() -> None:
    if len(sys.argv) < 2:
        print("Usage: python generate_blocks.py <data_file>")
        return
    data_file = sys.argv[1]
    if not os.path.exists(data_file):
        print(f"Error: file not found: {data_file}")
        return

    api_key = os.getenv(API_KEY_ENV)
    if not api_key:
        print(f"\n⚠ {API_KEY_ENV} environment variable not set.")
        print("  1. Sign up at https://openrouter.ai/ and create an API key")
        print(f"  2. Set environment variable: export {API_KEY_ENV}='sk-or-...'")
        return

    # Optional model override; OpenRouter provider default is used when unset.
    model = os.getenv("OPENROUTER_MODEL")

    _hr("Block-based dataset documentation")
    print(f"  File     : {data_file}")
    print(f"  Provider : {PROVIDER}")
    print(f"  Model    : {model or '(provider default)'}")
    print(f"  Blocks   : {', '.join(BLOCKS)}")

    _hr("Progress")
    progress = ProgressPrinter()
    wall_start = time.perf_counter()
    result = doc.generate_blocks(
        data_file,
        blocks=BLOCKS,
        provider=PROVIDER,
        model=model,
        api_key=api_key,
        context={},
        language="Russian",
        progress=progress,
    )
    wall_elapsed = time.perf_counter() - wall_start

    _hr("Source")
    source = result["source"]
    print(f"  Name        : {source.get('name')}")
    print(f"  Format      : {source.get('format')}")
    print(f"  Size        : {_format_bytes(source.get('size_bytes'))}")
    print(f"  Records     : {source.get('record_count')}")
    print(f"  SHA-256     : {source.get('sha256')}")
    if source.get("tables"):
        print(f"  Tables      : {', '.join(source['tables'])}")

    _hr("Blocks")
    for name, block in result["blocks"].items():
        print(f"  - {name:<14} {_block_summary(name, block)}")

    _hr("Timing")
    print(f"  Total wall time : {wall_elapsed:6.2f}s")
    slowest = progress.slowest()
    if slowest:
        print("  Slowest stages  :")
        for label, seconds in slowest:
            print(f"      {seconds:6.2f}s  {label}")

    _hr("Full document (markdown)")
    print()
    print(result["full_document_markdown"])

    print()
    print(f"job_id={result['job_id']}  created_at={result['created_at']}")


if __name__ == "__main__":
    main()
