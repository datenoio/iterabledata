# Framework integration guides

Use these guides when wiring IterableData into AI frameworks or provider SDKs. Longer provider notes stay in the repository so `llms.txt` and GitHub remain the single source of truth; this page summarizes what each guide covers and links to the in-docs agent APIs.

## In-docs guides (start here)

| Guide | When to use |
|-------|-------------|
| [Building agents](BUILDING_AGENTS.md) | Designing an agent that detects formats, samples rows, and converts data |
| [MCP server](MCP.md) | Exposing IterableData tools over Model Context Protocol (`iterabledata[mcp]`) |
| [Agent tools API](/api/tools) | Calling `detect_format`, `read_sample`, `plan_conversion`, and related tools from Python |
| [Catalog API](/api/catalog) | Machine-readable format/capability metadata for planners |
| [AI API](/api/ai) | Native providers (`openai`, `anthropic`, `gemini`, `azure`) and `doc.generate` |

## Provider and framework notes (GitHub)

| Guide | Summary |
|-------|---------|
| [AI frameworks](https://github.com/datenoio/iterabledata/blob/main/docs/integrations/AI_FRAMEWORKS.md) | LangChain, CrewAI, and AutoGen patterns for tools and memory |
| [OpenAI](https://github.com/datenoio/iterabledata/blob/main/docs/integrations/OPENAI.md) | OpenAI SDK usage with `iterable.ai` and redaction |
| [Anthropic Claude](https://github.com/datenoio/iterabledata/blob/main/docs/integrations/CLAUDE.md) | Claude / Messages API wiring |
| [Google Gemini](https://github.com/datenoio/iterabledata/blob/main/docs/integrations/GEMINI.md) | Gemini provider setup |

Install AI extras with `pip install 'iterabledata[ai]'` (add `[mcp]` for the MCP server). Never commit API keys; use `redact_for_llm()` before cloud calls.

## Extending formats outside core

For a niche format that should not land in the main package, ship a small plugin package with the `iterabledata.formats` entry point. See [Plugin system](/api/plugins#creating-a-format-plugin) and the [reference plugin walkthrough](/api/plugins#reference-plugin-package) for a complete layout.
