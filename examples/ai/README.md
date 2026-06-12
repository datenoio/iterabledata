## AI Documentation Generation Examples

This directory contains examples demonstrating how to use IterableData's AI-powered documentation generation feature to automatically create comprehensive documentation for datasets using various LLM providers.

## Overview

The AI documentation feature (`iterable.ai.doc.generate()`) uses Large Language Models (LLMs) to automatically analyze datasets and generate human-readable documentation including:

- Dataset overview and purpose
- Field descriptions with types and constraints
- Structured metadata (keywords, geographic/temporal coverage, languages, data themes)
- Field-level AI-generated descriptions
- Semantic type annotations (with Metacrafter)
- PII detection and masking (with Metacrafter)
- Statistics and data quality metrics
- Data quality notes
- Usage examples

## Prerequisites

### 1. Install IterableData with AI Support

**Option A: Development mode (recommended for testing examples)**:
```bash
cd /path/to/iterabledata
pip install -e ".[ai]"
```

**Option B: Install from PyPI**:
```bash
pip install iterabledata[ai]
```

**Option C: Install specific provider dependencies**:
```bash
# For OpenAI, OpenRouter, Perplexity, LMStudio
pip install iterabledata openai

# For Ollama (local)
pip install iterabledata requests
```

### 2. Set Up API Keys (for cloud providers)

Set environment variables for your chosen provider:

```bash
# OpenAI
export OPENAI_API_KEY="sk-..."

# OpenRouter
export OPENROUTER_API_KEY="sk-..."

# Perplexity
export PERPLEXITY_API_KEY="pplx-..."
```

### 3. Set Up Local Providers (Recommended for Free Usage)

**LM Studio (Recommended - Free, Local, No API Key)**:
1. Install LM Studio from https://lmstudio.ai
2. Open LM Studio and go to the "Search" tab
3. Download a model (e.g., Llama 3, Mistral, Phi-3)
4. Go to the "Local Server" tab
5. Click "Start Server" (usually runs on http://localhost:1234)
6. The server will automatically use the loaded model

**Ollama** (Alternative local option):
1. Install Ollama from https://ollama.ai
2. Start Ollama: `ollama serve`
3. Pull a model: `ollama pull llama2`

## Running Examples

**Important**: Run examples from the project root directory:

```bash
cd /path/to/iterabledata
python examples/ai/generate_documentation.py <data_file> [example_number]
```

Or set PYTHONPATH:
```bash
cd examples/ai
PYTHONPATH=../.. python generate_documentation.py <data_file> [example_number]
```

## Examples

### Example 1: Basic Markdown Documentation (Default)

Generate markdown documentation for a dataset:

```bash
python examples/ai/generate_documentation.py data.csv 1
```

Or simply:
```bash
python examples/ai/generate_documentation.py data.csv
```

**What it does**:
- Generates markdown documentation using OpenAI with latest GPT-4o model
- Saves to `<filename>_documentation.md`
- Includes schema information and sample data

**Code**:
```python
from iterable.ai import doc

documentation = doc.generate(
    "data.csv",
    provider="openai",
    model="gpt-4o",  # Latest GPT-4o model
    format="markdown"
)
```

### Example 2: JSON Format Documentation

Generate documentation in JSON format with structured metadata:

```bash
python examples/ai/generate_documentation.py data.csv 2
```

**What it does**:
- Generates JSON documentation with separate fields for:
  - `documentation`: Generated markdown text
  - `schema`: Schema information
  - `samples`: Sample data rows
  - `usage`: Token usage statistics
- Saves to `<filename>_documentation.json`

**Code**:
```python
from iterable.ai import doc

result = doc.generate(
    "data.csv",
    provider="openai",
    model="gpt-4o",  # Latest GPT-4o model
    format="json"
)

print(result["documentation"])  # Generated markdown
print(result["schema"])          # Schema information
print(result["samples"])         # Sample data
print(result["usage"])           # Token usage
```

### Example 3: HTML Format Documentation

Generate documentation as a standalone HTML file:

```bash
python examples/ai/generate_documentation.py data.csv 3
```

**What it does**:
- Generates a complete HTML document with embedded styles
- Can be opened directly in a web browser
- Saves to `<filename>_documentation.html`

**Code**:
```python
from iterable.ai import doc

html_docs = doc.generate(
    "data.csv",
    provider="openai",
    model="gpt-4o",  # Latest GPT-4o model
    format="html"
)

with open("docs.html", "w") as f:
    f.write(html_docs)
```

### Example 4: Customized Documentation

Generate documentation with custom settings:

```bash
python examples/ai/generate_documentation.py data.csv 4
```

**What it does**:
- Uses more sample rows (10 instead of default 5)
- Lower temperature (0.3 for more deterministic output)
- Skips schema inference (faster, less accurate)
- Saves to `<filename>_documentation_custom.md`

**Code**:
```python
from iterable.ai import doc

documentation = doc.generate(
    "data.csv",
    provider="openai",
    model="gpt-4o",  # Latest GPT-4o model
    sample_size=10,
    temperature=0.3,
    include_schema=False
)
```

### Example 5: Different LLM Providers

Demonstrate using different LLM providers. This example tries LM Studio first (local, free), then falls back to OpenAI:

```bash
python examples/ai/generate_documentation.py data.csv 5
```

**What it does**:
- Tries LM Studio first (local, free, no API key needed)
- Falls back to OpenAI with GPT-4o if LM Studio is not available
- Shows how to use different providers

**Supported Providers**:

1. **LM Studio** (Recommended - local, free, no API key)
   ```python
   doc.generate(
       "data.csv",
       provider="lmstudio",
       base_url="http://localhost:1234/v1",
       model="local-model"  # Use model loaded in LM Studio
   )
   ```

2. **OpenAI** (Latest GPT-4o model)
   ```python
   doc.generate(
       "data.csv",
       provider="openai",
       model="gpt-4o",  # Latest GPT-4o model
       api_key="sk-..."
   )
   ```

3. **OpenRouter**
   ```python
   doc.generate("data.csv", provider="openrouter", api_key="sk-...")
   ```

4. **Ollama** (local, free)
   ```python
   doc.generate(
       "data.csv",
       provider="ollama",
       base_url="http://localhost:11434",
       model="llama2"
   )
   ```

5. **Perplexity**
   ```python
   doc.generate("data.csv", provider="perplexity", api_key="pplx-...")
   ```

### Example 6: LM Studio (Local, Free)

Dedicated example for using LM Studio - completely free and runs locally:

```bash
python examples/ai/generate_documentation.py data.csv 6
```

**What it does**:
- Checks if LM Studio is running
- Lists available models
- Generates documentation using the loaded model
- No API key required - completely free!

**Prerequisites**:
1. Install LM Studio from https://lmstudio.ai
2. Download and load a model in LM Studio
3. Start the local server (usually port 1234)

**Code**:
```python
from iterable.ai import doc

# LM Studio automatically uses the model you have loaded
documentation = doc.generate(
    "data.csv",
    provider="lmstudio",
    base_url="http://localhost:1234/v1",
    model="local-model"  # Or specific model name loaded in LM Studio
)
```

**Benefits of LM Studio**:
- ✅ Completely free - no API costs
- ✅ Runs locally - your data stays on your machine
- ✅ Works offline
- ✅ Supports many open-source models (Llama, Mistral, Phi, etc.)
- ✅ Easy to use GUI for model management

### Example 7: Perplexity Provider

Use Perplexity's online model with web search capabilities:

```bash
python examples/ai/generate_documentation.py data.csv 7
```

**What it does**:
- Uses Perplexity's online model (sonar-pro by default)
- Can leverage web search for additional context
- Good for datasets that may benefit from external knowledge
- Saves to `<filename>_documentation_perplexity.md`

**Prerequisites**:
1. Sign up at https://www.perplexity.ai/
2. Get API key from https://www.perplexity.ai/settings/api
3. Set environment variable: `export PERPLEXITY_API_KEY='pplx-...'`

**Code**:
```python
from iterable.ai import doc
import os

documentation = doc.generate(
    "data.csv",
    provider="perplexity",
    model="sonar-pro",  # Default Perplexity model (best for web-grounded conversations)
    api_key=os.getenv("PERPLEXITY_API_KEY")
)
```

**Available Perplexity Models** (Chat Completions API):
- `sonar-pro` (default, best for web-grounded conversations)
- `sonar` (lightweight, faster)
- `sonar-reasoning` (real-time reasoning with search)
- `sonar-reasoning-pro` (powered by DeepSeek-R1 with visible reasoning)
- `sonar-deep-research` (long-form research)

**Benefits of Perplexity**:
- ✅ Online model with web search capabilities
- ✅ Can provide additional context from the web
- ✅ Good for datasets that reference external concepts
- ✅ Multiple model sizes available

### Example 8: Integration with Schema Inference

Combine documentation generation with other IterableData operations:

```bash
python examples/ai/generate_documentation.py data.csv 8
```

**What it does**:
- Infers schema using `schema.infer()`
- Computes basic statistics using `stats.compute()`
- Generates documentation with schema information using GPT-4o
- Saves to `<filename>_documentation_integrated.md`

**Code**:
```python
from iterable.ai import doc
from iterable.ops import schema, stats

# Analyze dataset first
schema_info = schema.infer("data.csv", detect_constraints=True)
stats_info = stats.compute("data.csv")

# Generate documentation (uses schema internally)
documentation = doc.generate(
    "data.csv",
    provider="openai",
    model="gpt-4o",  # Latest GPT-4o model
    include_schema=True,
    sample_size=5
)
```

**Note**: You can also use Perplexity or LM Studio for this example by changing the `provider` parameter.

### Example 9: Structured Metadata Extraction

Extract structured metadata including keywords, geographic coverage, temporal coverage, languages, and data themes:

```bash
python examples/ai/generate_documentation.py data.csv 9
```

**What it does**:
- Extracts keywords from field names and sample data
- Detects geographic coverage (countries, regions, coordinates)
- Detects temporal coverage (date ranges, granularity)
- Detects languages in text fields
- Classifies data theme (EU data themes)
- Saves to `<filename>_documentation_with_metadata.json`

**Code**:
```python
from iterable.ai import doc

result = doc.generate(
    "data.csv",
    provider="openai",
    format="json",
    include_metadata=True,  # Enable metadata extraction
    sample_size=10
)

metadata = result.get("metadata", {})
keywords = metadata.get("keywords", [])
geographic_coverage = metadata.get("geographic_coverage", {})
temporal_coverage = metadata.get("temporal_coverage")
languages = metadata.get("languages", [])
data_theme = metadata.get("data_theme")
```

### Example 10: Field-Level Descriptions

Generate individual AI descriptions for each field:

```bash
python examples/ai/generate_documentation.py data.csv 10
```

**What it does**:
- Generates individual descriptions for each field using AI
- Provides detailed field-level documentation
- Saves to `<filename>_documentation_with_fields.json`

**Code**:
```python
from iterable.ai import doc

result = doc.generate(
    "data.csv",
    provider="openai",
    format="json",
    include_field_descriptions=True,  # Enable field descriptions
    language="English"
)

field_descriptions = result.get("field_descriptions", {})
for field, description in field_descriptions.items():
    print(f"{field}: {description}")
```

### Example 11: Semantic Types and PII Detection

Detect semantic types and personally identifiable information using Metacrafter:

```bash
python examples/ai/generate_documentation.py data.csv 11
```

**What it does**:
- Detects semantic types for each field (requires Metacrafter)
- Identifies PII fields (email, phone, SSN, etc.)
- Masks PII values in sample data
- Saves to `<filename>_documentation_with_semantic.json`

**Prerequisites**:
- Install Metacrafter CLI tool from https://github.com/metacrafter/metacrafter
- Ensure `metacrafter` is available in PATH

**Code**:
```python
from iterable.ai import doc

result = doc.generate(
    "data.csv",
    provider="openai",
    format="json",
    semantic_types=True,  # Enable semantic type detection
    pii_detect=True,  # Enable PII detection
    pii_mask_samples=True  # Mask PII in samples
)

semantic_types = result.get("semantic_types", {})
pii_fields = result.get("pii_fields", [])
```

**Note**: If Metacrafter is not available, these features will be skipped gracefully.

### Example 12: YAML and Text Output Formats

Generate documentation in YAML and plain text formats:

```bash
python examples/ai/generate_documentation.py data.csv 12
```

**What it does**:
- Generates YAML format documentation (structured, parseable)
- Generates plain text format (markdown formatting removed)
- Saves to `<filename>_documentation.yaml` and `<filename>_documentation.txt`

**Code**:
```python
from iterable.ai import doc

# YAML format
yaml_docs = doc.generate(
    "data.csv",
    provider="openai",
    format="yaml",
    include_metadata=True
)

# Text format
text_docs = doc.generate(
    "data.csv",
    provider="openai",
    format="text"
)
```

### Example 13: Statistics Integration

Include comprehensive statistics in documentation:

```bash
python examples/ai/generate_documentation.py data.csv 13
```

**What it does**:
- Computes statistics using DuckDB (when available)
- Includes uniqueness counts, total counts, min/max values
- Enhances documentation with data quality metrics
- Saves to `<filename>_documentation_with_stats.json`

**Code**:
```python
from iterable.ai import doc

result = doc.generate(
    "data.csv",
    provider="openai",
    format="json",
    include_statistics=True,  # Enable statistics
    sample_size=10
)

statistics = result.get("statistics", {})
for field, stats in statistics.items():
    print(f"{field}: unique={stats.get('unique_count')}, total={stats.get('count')}")
```

### Example 14: Multilingual Documentation

Generate documentation in multiple languages:

```bash
python examples/ai/generate_documentation.py data.csv 14
```

**What it does**:
- Generates documentation in English, Spanish, French, and German
- Includes metadata and field descriptions in each language
- Saves separate files for each language

**Code**:
```python
from iterable.ai import doc

languages = ["English", "Spanish", "French", "German"]

for lang in languages:
    documentation = doc.generate(
        "data.csv",
        provider="openai",
        language=lang,
        include_metadata=True,
        include_field_descriptions=True
    )
    # Save to language-specific file
```

### Example 15: Comprehensive Documentation (All Features)

Generate comprehensive documentation with all features enabled:

```bash
python examples/ai/generate_documentation.py data.csv 15
```

**What it does**:
- Enables all features: schema, samples, metadata, field descriptions, statistics
- Includes semantic types and PII detection (if Metacrafter available)
- Generates both JSON and Markdown outputs
- Provides complete dataset documentation

**Code**:
```python
from iterable.ai import doc

# Comprehensive documentation
result = doc.generate(
    "data.csv",
    provider="openai",
    format="json",
    include_schema=True,
    include_samples=True,
    sample_size=10,
    include_metadata=True,
    include_field_descriptions=True,
    include_statistics=True,
    semantic_types=True,  # Optional: requires Metacrafter
    pii_detect=True,  # Optional: requires Metacrafter
    pii_mask_samples=True,
    language="English"
)

# Also generate markdown version
markdown_docs = doc.generate(
    "data.csv",
    provider="openai",
    format="markdown",
    include_schema=True,
    include_samples=True,
    include_metadata=True,
    include_field_descriptions=True,
    include_statistics=True
)
```

## Supported Data Formats

The documentation generator works with all formats supported by IterableData:

- **CSV** (`.csv`)
- **JSON Lines** (`.jsonl`, `.jsonl.gz`, `.jsonl.zst`)
- **JSON** (`.json`)
- **Parquet** (`.parquet`)
- **Excel** (`.xlsx`, `.xls`)
- **And many more...**

## Configuration Options

### Provider Options

- `provider`: LLM provider name ("openai", "openrouter", "ollama", "lmstudio", "perplexity")
- `model`: Model name (provider-specific, uses default if None)
- `api_key`: API key (uses environment variable if None)
- `base_url`: Base URL for local providers (Ollama, LMStudio)

### Generation Options

- `format`: Output format ("markdown", "json", "html", "yaml", "text")
- `include_schema`: Whether to include schema information (default: True)
- `include_samples`: Whether to include sample data (default: True)
- `sample_size`: Number of sample rows to include (default: 5)
- `temperature`: Sampling temperature (default: 0.7)
- `max_tokens`: Maximum tokens to generate
- `include_field_descriptions`: Whether to generate field-level descriptions (default: False)
- `include_statistics`: Whether to include statistics (default: True)
- `include_metadata`: Whether to extract structured metadata (default: True)
- `semantic_types`: Whether to detect semantic types using Metacrafter (default: False)
- `pii_detect`: Whether to detect PII fields using Metacrafter (default: False)
- `pii_mask_samples`: Whether to mask PII in sample data (default: False)
- `language`: Language for AI-generated content (default: "English")

## Cost Optimization Tips

1. **Use LM Studio (Recommended)** - Completely free, runs locally, no API costs
2. **Use smaller OpenAI models** for cost savings (e.g., `gpt-4o-mini` instead of `gpt-4o`)
3. **Disable schema/samples** if not needed (`include_schema=False`, `include_samples=False`)
4. **Use local providers** (LM Studio, Ollama) for free generation
5. **Limit sample size** to reduce prompt size
6. **Cache results** for repeated documentation generation

## Error Handling

The examples include error handling for common issues:

- Missing dependencies (ImportError)
- Invalid providers (ValueError)
- API errors (network issues, invalid keys)
- File not found errors

## Best Practices

1. **Review generated docs** - AI may make mistakes, always verify
2. **Use schema inference** for accurate field descriptions
3. **Enable metadata extraction** for comprehensive documentation (enabled by default)
4. **Use field descriptions** for detailed field-level documentation (when needed)
5. **Enable statistics** for data quality insights (enabled by default)
6. **Use semantic types** when Metacrafter is available for richer annotations
7. **Detect and mask PII** for privacy-aware documentation
8. **Include samples** for better context (but limit size for cost)
9. **Choose appropriate models** based on quality vs. cost needs
10. **Use local providers** for sensitive data or cost-free generation
11. **Cache results** for repeated documentation generation
12. **Use appropriate output format** - JSON for programmatic use, Markdown for reading, YAML for structured data

## Troubleshooting

### Import Errors

If you get `ImportError` for provider dependencies:
```bash
# Install OpenAI dependencies
pip install openai

# Or install all AI dependencies
pip install iterabledata[ai]
```

### API Key Errors

If you get authentication errors:
- Verify your API key is set correctly: `echo $OPENAI_API_KEY`
- Check that the API key has sufficient credits/permissions
- For local providers, ensure they're running and accessible

### Connection Errors (Local Providers)

For LM Studio (Recommended):
- Ensure LM Studio is running and server is started
- Check the base URL (usually `http://localhost:1234/v1`)
- Verify a model is loaded in LM Studio (go to "Local Server" tab)
- Test connection: `curl http://localhost:1234/v1/models`
- If using a different port, update `base_url` accordingly

For Ollama:
- Ensure Ollama is running: `ollama serve`
- Check that models are installed: `ollama list`
- Verify the base URL: `curl http://localhost:11434/api/tags`

### File Format Errors

If you get errors about unsupported formats:
- Check that IterableData supports your file format
- Verify the file is not corrupted
- Try opening the file with `open_iterable()` first to test

## Additional Resources

- **API Documentation**: See `docs/docs/api/ai.md` for complete API reference
- **Integration Guides**: See `docs/integrations/` for provider-specific guides
- **Main Documentation**: See `README.md` for general IterableData usage

## Example Output

The generated documentation typically includes:

```markdown
# Dataset Documentation

## Overview
This dataset contains user information with demographic and contact details...

## Fields

### id
- Type: integer
- Description: Unique user identifier
- Constraints: Required, non-null, unique

### name
- Type: string
- Description: User's full name
- Constraints: Required, non-null

### email
- Type: string
- Description: User's email address
- Constraints: Required, non-null, unique, valid email format

## Data Quality Notes
- All records have valid email addresses
- No missing values in required fields
- Date fields are consistently formatted

## Usage Examples
...
```
