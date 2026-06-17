# Anthropic Claude AI Integration Guide

This document provides guidance on integrating IterableData with Anthropic Claude AI for data processing, analysis, and transformation tasks.

## Overview

Anthropic Claude AI can leverage IterableData's unified interface to process various data formats, enabling intelligent data analysis, transformation, schema inference, and format conversion. This guide covers integration patterns, use cases, and best practices for using Claude with IterableData.

---

## Setup

### Installation

```bash
pip install anthropic iterabledata
```

### API Key Configuration

```python
import anthropic

# Initialize client
client = anthropic.Anthropic(api_key="YOUR_API_KEY")

# Or use environment variable
# export ANTHROPIC_API_KEY="your-api-key"
client = anthropic.Anthropic()  # Automatically uses ANTHROPIC_API_KEY
```

---

## Basic Integration

### Reading Data with Claude

Use IterableData to read data and send to Claude for analysis:

```python
import anthropic
from iterable.helpers.detect import open_iterable
import json

# Initialize Claude client
client = anthropic.Anthropic(api_key="YOUR_API_KEY")

def analyze_data_with_claude(filename: str, question: str) -> str:
    """Read data and analyze with Claude."""
    # Read sample data
    with open_iterable(filename) as source:
        sample_records = [row for i, row in enumerate(source) if i < 10]
        data_str = json.dumps(sample_records, indent=2, default=str)
    
    # Send to Claude
    message = client.messages.create(
        model="claude-3-5-sonnet-20241022",
        max_tokens=1024,
        messages=[
            {
                "role": "user",
                "content": f"Analyze the following data and answer: {question}\n\nData:\n{data_str}"
            }
        ]
    )
    
    return message.content[0].text

# Use it
result = analyze_data_with_claude('sales.csv', 'What are the key trends?')
print(result)
```

### Converting Data Formats

Use Claude to intelligently convert between formats:

```python
import anthropic
from iterable.helpers.detect import open_iterable
from iterable.convert import convert
import json

client = anthropic.Anthropic(api_key="YOUR_API_KEY")

def smart_convert(input_file: str, output_file: str, instructions: str = None):
    """Convert data format with Claude-guided transformation."""
    # Analyze input data
    with open_iterable(input_file) as source:
        sample = [row for i, row in enumerate(source) if i < 5]
        sample_str = json.dumps(sample, indent=2, default=str)
    
    # Get conversion guidance from Claude
    if instructions:
        message = client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=1024,
            messages=[
                {
                    "role": "user",
                    "content": f"""Given this data sample:
{sample_str}

Instructions: {instructions}

Provide JSON schema and transformation rules for converting to target format."""
                }
            ]
        )
        print(f"Conversion guidance: {message.content[0].text}")
    
    # Perform conversion
    convert(input_file, output_file)
    return f"Converted {input_file} to {output_file}"

# Use it
smart_convert('input.csv', 'output.jsonl', 
              instructions='Normalize dates and convert amounts to float')
```

---

## Advanced Patterns

### Schema Inference with Claude

Use Claude to infer and document data schemas:

```python
import anthropic
from iterable.helpers.detect import open_iterable
from iterable.helpers.schema import infer_schema
import json

client = anthropic.Anthropic(api_key="YOUR_API_KEY")

def claude_schema_inference(filename: str) -> dict:
    """Infer schema using both IterableData and Claude."""
    with open_iterable(filename) as source:
        # Get technical schema
        technical_schema = infer_schema(source, sample_size=100)
        
        # Get sample data for Claude
        source.reset()  # Reset iterator
        sample = [row for i, row in enumerate(source) if i < 10]
        sample_str = json.dumps(sample, indent=2, default=str)
    
    # Get semantic schema from Claude
    message = client.messages.create(
        model="claude-3-5-sonnet-20241022",
        max_tokens=2048,
        messages=[
            {
                "role": "user",
                "content": f"""Analyze this data sample and provide:
1. Semantic field descriptions
2. Business context
3. Data quality observations
4. Recommended transformations

Data:
{sample_str}

Technical Schema:
{json.dumps(technical_schema, indent=2)}"""
            }
        ]
    )
    
    return {
        "technical_schema": technical_schema,
        "semantic_analysis": message.content[0].text
    }

result = claude_schema_inference('customer_data.parquet')
print(result["semantic_analysis"])
```

### Data Transformation with Claude

Use Claude to plan transformations, then apply them with an explicit, reviewable function via `pipeline()`:

```python
import anthropic
from iterable.helpers.detect import open_iterable
from iterable.pipeline import pipeline
import json

client = anthropic.Anthropic(api_key="YOUR_API_KEY")


def normalize_record(record: dict) -> dict:
    """Explicit transform — review and test before production use."""
    out = dict(record)
    if "email" in out and isinstance(out["email"], str):
        out["email"] = out["email"].strip().lower()
    return out


def claude_guided_transform(input_file: str, output_file: str, transformation_goal: str):
    """Use Claude for planning; apply a hand-written transform (do not exec LLM code)."""
    with open_iterable(input_file) as source:
        sample = [row for i, row in enumerate(source) if i < 5]
        sample_str = json.dumps(sample, indent=2, default=str)

    message = client.messages.create(
        model="claude-3-5-sonnet-20241022",
        max_tokens=2048,
        messages=[
            {
                "role": "user",
                "content": f"""Given this data sample:
{sample_str}

Goal: {transformation_goal}

List transformation steps as a numbered checklist (field renames, normalizations, filters).
Do not output executable Python.""",
            }
        ],
    )
    plan = message.content[0].text
    print(f"Transformation plan:\n{plan}\n")

    with open_iterable(input_file) as source, open_iterable(output_file, mode="w") as dest:
        pipeline(source=source, destination=dest, process_func=normalize_record)

    return f"Transformed {input_file} -> {output_file}"


claude_guided_transform(
    "raw_data.jsonl",
    "cleaned_data.jsonl",
    "Normalize email addresses, convert dates to ISO format, remove nulls",
)
```

## Data Privacy

When sending samples to cloud LLM APIs:

- Limit samples (e.g. first 5–10 rows); never upload full files by default.
- Prefer local providers (Ollama, LM Studio) for sensitive data.
- Use `iterable.ai.doc.generate()` with `pii_detect=True` and `pii_mask_samples=True` when documenting datasets with personal data.
- Review generated outputs before publishing documentation.

### Data Quality Analysis

Use Claude to analyze data quality:

```python
import anthropic
from iterable.helpers.detect import open_iterable
import json

client = anthropic.Anthropic(api_key="YOUR_API_KEY")

def claude_data_quality_analysis(filename: str) -> dict:
    """Analyze data quality with Claude."""
    with open_iterable(filename) as source:
        # Collect statistics
        records = list(source)
        total = len(records)
        
        # Calculate basic stats
        null_counts = {}
        for record in records:
            for key, value in record.items():
                if value is None or value == '':
                    null_counts[key] = null_counts.get(key, 0) + 1
        
        sample = records[:10]
        sample_str = json.dumps(sample, indent=2, default=str)
        stats_str = json.dumps({
            "total_records": total,
            "null_counts": null_counts
        }, indent=2)
    
    # Get Claude analysis
    message = client.messages.create(
        model="claude-3-5-sonnet-20241022",
        max_tokens=2048,
        messages=[
            {
                "role": "user",
                "content": f"""Analyze data quality:

Statistics:
{stats_str}

Sample Data:
{sample_str}

Provide:
1. Data quality assessment
2. Issues found
3. Recommendations for improvement"""
            }
        ]
    )
    
    return {
        "statistics": {
            "total_records": total,
            "null_counts": null_counts
        },
        "claude_analysis": message.content[0].text
    }

result = claude_data_quality_analysis('dataset.csv')
print(result["claude_analysis"])
```

---

## Function Calling with Claude (Tools)

Use Claude's tools (function calling) feature for structured operations:

```python
import anthropic
from iterable.helpers.detect import open_iterable
from iterable.convert import convert
import json

client = anthropic.Anthropic(api_key="YOUR_API_KEY")

# Define tools (functions)
def read_data_file(filename: str, limit: int = 10) -> dict:
    """Read data from file."""
    with open_iterable(filename) as source:
        records = [row for i, row in enumerate(source) if i < limit]
        return {"data": records, "count": len(records)}

def convert_data_file(input_file: str, output_file: str) -> dict:
    """Convert data format."""
    convert(input_file, output_file)
    return {"status": "success", "input_file": input_file, "output_file": output_file}

def get_file_info(filename: str) -> dict:
    """Get file information."""
    with open_iterable(filename) as source:
        count = sum(1 for _ in source)
        return {"filename": filename, "record_count": count}

# Define tools schema
tools = [
    {
        "name": "read_data_file",
        "description": "Read data from files (CSV, JSON, Parquet, etc.)",
        "input_schema": {
            "type": "object",
            "properties": {
                "filename": {"type": "string", "description": "Path to the data file"},
                "limit": {"type": "integer", "description": "Maximum number of records to read", "default": 10}
            },
            "required": ["filename"]
        }
    },
    {
        "name": "convert_data_file",
        "description": "Convert data between formats",
        "input_schema": {
            "type": "object",
            "properties": {
                "input_file": {"type": "string", "description": "Source file path"},
                "output_file": {"type": "string", "description": "Destination file path"}
            },
            "required": ["input_file", "output_file"]
        }
    },
    {
        "name": "get_file_info",
        "description": "Get file information including record count",
        "input_schema": {
            "type": "object",
            "properties": {
                "filename": {"type": "string", "description": "Path to the file"}
            },
            "required": ["filename"]
        }
    }
]

# Use tools with Claude
message = client.messages.create(
    model="claude-3-5-sonnet-20241022",
    max_tokens=1024,
    tools=tools,
    messages=[
        {
            "role": "user",
            "content": "Read data.csv and convert it to JSONL format"
        }
    ]
)

# Handle tool use
tool_map = {
    "read_data_file": read_data_file,
    "convert_data_file": convert_data_file,
    "get_file_info": get_file_info
}

# Process tool calls
for content_block in message.content:
    if content_block.type == "tool_use":
        tool_name = content_block.name
        tool_input = content_block.input
        
        if tool_name in tool_map:
            result = tool_map[tool_name](**tool_input)
            
            # Continue conversation with result
            follow_up = client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=1024,
                tools=tools,
                messages=[
                    {
                        "role": "user",
                        "content": "Read data.csv and convert it to JSONL format"
                    },
                    message.content,
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "tool_result",
                                "tool_use_id": content_block.id,
                                "content": json.dumps(result)
                            }
                        ]
                    }
                ]
            )
            print(follow_up.content[0].text)
```

---

## Use Cases

### 1. Intelligent Data Analysis

Use Claude to provide natural language insights from data:

```python
def analyze_data_natural_language(filename: str, question: str) -> str:
    """Get natural language analysis of data."""
    client = anthropic.Anthropic(api_key="YOUR_API_KEY")
    
    with open_iterable(filename) as source:
        sample = [row for i, row in enumerate(source) if i < 20]
        data_str = json.dumps(sample, indent=2, default=str)
    
    message = client.messages.create(
        model="claude-3-5-sonnet-20241022",
        max_tokens=2048,
        messages=[
            {
                "role": "user",
                "content": f"Analyze this data and answer: {question}\n\nData:\n{data_str}\n\nProvide a clear, insightful answer."
            }
        ]
    )
    
    return message.content[0].text
```

### 2. Data Cleaning Recommendations

Get Claude recommendations for data cleaning:

```python
def get_cleaning_recommendations(filename: str) -> str:
    """Get data cleaning recommendations from Claude."""
    client = anthropic.Anthropic(api_key="YOUR_API_KEY")
    
    with open_iterable(filename) as source:
        sample = [row for i, row in enumerate(source) if i < 15]
        data_str = json.dumps(sample, indent=2, default=str)
    
    message = client.messages.create(
        model="claude-3-5-sonnet-20241022",
        max_tokens=2048,
        messages=[
            {
                "role": "user",
                "content": f"""Analyze this data and provide cleaning recommendations:

{data_str}

Provide:
1. Issues found
2. Recommended cleaning steps
3. Example transformations"""
            }
        ]
    )
    
    return message.content[0].text
```

### 3. Format Recommendations

Get format recommendations based on use case:

```python
def recommend_format(filename: str, use_case: str) -> str:
    """Get format recommendation from Claude."""
    client = anthropic.Anthropic(api_key="YOUR_API_KEY")
    
    with open_iterable(filename) as source:
        sample = [row for i, row in enumerate(source) if i < 5]
        data_str = json.dumps(sample, indent=2, default=str)
        
        # Get file stats
        source.reset()
        count = sum(1 for _ in source)
    
    message = client.messages.create(
        model="claude-3-5-sonnet-20241022",
        max_tokens=1024,
        messages=[
            {
                "role": "user",
                "content": f"""Given this data (sample and record count: {count}):
{data_str}

Use case: {use_case}

Recommend the best data format (Parquet, JSONL, CSV, etc.) and explain why."""
            }
        ]
    )
    
    return message.content[0].text
```

### 4. Schema Documentation

Generate documentation from data schema:

```python
def generate_schema_documentation(filename: str) -> str:
    """Generate schema documentation using Claude."""
    client = anthropic.Anthropic(api_key="YOUR_API_KEY")
    
    with open_iterable(filename) as source:
        from iterable.helpers.schema import infer_schema
        schema = infer_schema(source, sample_size=100)
        
        source.reset()
        sample = [row for i, row in enumerate(source) if i < 5]
    
    message = client.messages.create(
        model="claude-3-5-sonnet-20241022",
        max_tokens=4096,
        messages=[
            {
                "role": "user",
                "content": f"""Generate comprehensive documentation for this data schema:

Schema: {json.dumps(schema, indent=2)}
Sample: {json.dumps(sample, indent=2)}

Include:
1. Field descriptions
2. Data types and constraints
3. Example values
4. Usage notes"""
            }
        ]
    )
    
    return message.content[0].text
```

---

## Best Practices

### 1. Sampling for Large Files

Don't send entire large files to Claude. Sample instead:

```python
def smart_sample(filename: str, sample_size: int = 20) -> list:
    """Intelligently sample data for Claude analysis."""
    with open_iterable(filename) as source:
        total = source.totals() if hasattr(source, 'totals') else None
        
        if total and total > sample_size * 10:
            # Stratified sampling for large files
            step = total // sample_size
            sample = [row for i, row in enumerate(source) if i % step == 0]
        else:
            sample = [row for i, row in enumerate(source) if i < sample_size]
        
        return sample
```

### 2. Streaming Processing

For large files, process in chunks:

```python
def claude_stream_processing(filename: str, output_file: str, 
                            process_func_prompt: str):
    """Process large files in chunks with Claude."""
    client = anthropic.Anthropic(api_key="YOUR_API_KEY")
    
    # Get transformation function from Claude (once)
    message = client.messages.create(
        model="claude-3-5-sonnet-20241022",
        max_tokens=2048,
        messages=[
            {
                "role": "user",
                "content": f"Create a transform function: {process_func_prompt}"
            }
        ]
    )
    # ... extract and prepare transform function ...
    
    # Process in batches
    with open_iterable(filename) as source, \
         open_iterable(output_file, mode='w') as dest:
        batch = []
        for record in source:
            batch.append(record)
            if len(batch) >= 100:
                # Process batch
                for transformed in [transform(r) for r in batch]:
                    dest.write(transformed)
                batch = []
```

### 3. Caching Claude Responses

Cache Claude analysis to avoid repeated API calls:

```python
from functools import lru_cache
import hashlib

@lru_cache(maxsize=50)
def cached_claude_analysis(data_hash: str, prompt: str) -> str:
    """Cache Claude analysis results."""
    client = anthropic.Anthropic(api_key="YOUR_API_KEY")
    message = client.messages.create(
        model="claude-3-5-sonnet-20241022",
        max_tokens=2048,
        messages=[{"role": "user", "content": prompt}]
    )
    return message.content[0].text

def analyze_with_cache(filename: str, question: str) -> str:
    """Analyze data with caching."""
    with open_iterable(filename) as source:
        sample = [row for i, row in enumerate(source) if i < 10]
        data_str = json.dumps(sample, sort_keys=True)
        data_hash = hashlib.md5(data_str.encode()).hexdigest()
    
    prompt = f"Analyze: {question}\n\nData:\n{data_str}"
    return cached_claude_analysis(data_hash, prompt)
```

### 4. Error Handling

Implement robust error handling:

```python
def safe_claude_operation(operation_func, *args, **kwargs):
    """Safely execute Claude operations with error handling."""
    try:
        return operation_func(*args, **kwargs)
    except anthropic.RateLimitError as e:
        return f"Rate limit exceeded. Please try again later. Error: {str(e)}"
    except anthropic.APIError as e:
        return f"API error: {str(e)}"
    except Exception as e:
        return f"Error: {str(e)}"
```

### 5. System Prompts for Better Results

Use system prompts to guide Claude's behavior:

```python
def analyze_with_system_prompt(filename: str, question: str) -> str:
    """Analyze data with a system prompt for better results."""
    client = anthropic.Anthropic(api_key="YOUR_API_KEY")
    
    with open_iterable(filename) as source:
        sample = [row for i, row in enumerate(source) if i < 10]
        data_str = json.dumps(sample, indent=2, default=str)
    
    message = client.messages.create(
        model="claude-3-5-sonnet-20241022",
        max_tokens=2048,
        system="You are a data analyst expert. Provide clear, concise, and actionable insights.",
        messages=[
            {
                "role": "user",
                "content": f"{question}\n\nData:\n{data_str}"
            }
        ]
    )
    
    return message.content[0].text
```

---

## Performance Optimization

### Batch Processing

Process multiple files or operations in batches:

```python
def batch_claude_analysis(filenames: list[str], question: str) -> dict:
    """Analyze multiple files with Claude."""
    client = anthropic.Anthropic(api_key="YOUR_API_KEY")
    results = {}
    
    for filename in filenames:
        with open_iterable(filename) as source:
            sample = [row for i, row in enumerate(source) if i < 10]
            data_str = json.dumps(sample, indent=2, default=str)
        
        message = client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=2048,
            messages=[
                {
                    "role": "user",
                    "content": f"File: {filename}\n\n{question}\n\nData:\n{data_str}"
                }
            ]
        )
        results[filename] = message.content[0].text
    
    return results
```

### Parallel Processing

Use threading for parallel Claude API calls (be mindful of rate limits):

```python
from concurrent.futures import ThreadPoolExecutor
import anthropic

def parallel_claude_analysis(filenames: list[str], question: str) -> dict:
    """Analyze files in parallel."""
    client = anthropic.Anthropic(api_key="YOUR_API_KEY")
    
    def analyze_file(filename: str) -> tuple:
        with open_iterable(filename) as source:
            sample = [row for i, row in enumerate(source) if i < 10]
            data_str = json.dumps(sample, indent=2, default=str)
        
        message = client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=2048,
            messages=[
                {
                    "role": "user",
                    "content": f"{question}\n\nData:\n{data_str}"
                }
            ]
        )
        return filename, message.content[0].text
    
    with ThreadPoolExecutor(max_workers=5) as executor:
        results = dict(executor.map(analyze_file, filenames))
    
    return results
```

---

## Complete Example

```python
import anthropic
from iterable.helpers.detect import open_iterable
from iterable.convert import convert
from iterable.pipeline import pipeline
import json

# Configure
client = anthropic.Anthropic(api_key="YOUR_API_KEY")

def comprehensive_data_processing(input_file: str, output_file: str, 
                                  goal: str) -> dict:
    """Complete data processing workflow with Claude."""
    
    # 1. Analyze input data
    with open_iterable(input_file) as source:
        sample = [row for i, row in enumerate(source) if i < 10]
        sample_str = json.dumps(sample, indent=2, default=str)
    
    # 2. Get processing plan from Claude
    plan_message = client.messages.create(
        model="claude-3-5-sonnet-20241022",
        max_tokens=2048,
        messages=[
            {
                "role": "user",
                "content": f"""Given this data:
{sample_str}

Goal: {goal}

Provide a step-by-step processing plan:
1. Data quality issues to address
2. Transformations needed
3. Target format recommendation
4. Validation steps"""
            }
        ]
    )
    plan = plan_message.content[0].text
    print(f"Processing Plan:\n{plan}\n")
    
    # 3. Get transformation function
    transform_message = client.messages.create(
        model="claude-3-5-sonnet-20241022",
        max_tokens=2048,
        messages=[
            {
                "role": "user",
                "content": f"""Goal: {goal}

Create Python function: def transform(record: dict) -> dict:
Only return function code."""
            }
        ]
    )
    transform_code = transform_message.content[0].text
    # Extract and execute function...
    
    # 4. Execute transformation
    # ... apply transformations ...
    
    # 5. Convert format
    convert(input_file, output_file)
    
    # 6. Validate output
    with open_iterable(output_file) as source:
        validation_sample = [row for i, row in enumerate(source) if i < 5]
        validation_str = json.dumps(validation_sample, indent=2, default=str)
    
    validation_message = client.messages.create(
        model="claude-3-5-sonnet-20241022",
        max_tokens=1024,
        messages=[
            {
                "role": "user",
                "content": f"""Validate this processed data:
{validation_str}

Goal was: {goal}

Provide validation assessment."""
            }
        ]
    )
    
    return {
        "plan": plan,
        "validation": validation_message.content[0].text,
        "output_file": output_file
    }

# Execute
result = comprehensive_data_processing(
    'raw_data.csv',
    'processed_data.jsonl',
    'Clean and normalize customer data for analytics'
)
print(result)
```

---

## Limitations and Considerations

1. **API Rate Limits**: Claude API has rate limits. Implement retry logic and rate limiting.

2. **Token Limits**: Large data samples may exceed context windows. Claude 3.5 Sonnet supports up to 200K tokens. Use sampling strategies.

3. **Cost**: Claude API calls incur costs. Cache results and batch operations when possible.

4. **Latency**: API calls add latency. Use for complex analysis, not simple operations.

5. **Data Privacy**: Don't send sensitive data to external APIs without proper safeguards. Consider using Claude Enterprise for enhanced privacy controls.

6. **Context Window**: Be mindful of context window limits. For very large datasets, use iterative processing.

---

## Resources

- [Anthropic Claude API Documentation](https://docs.anthropic.com/)
- [Anthropic Python SDK](https://github.com/anthropics/anthropic-sdk-python)
- [Claude Models Overview](https://docs.anthropic.com/claude/docs/models-overview)
- [Claude Tools Documentation](https://docs.anthropic.com/claude/docs/tool-use)
- [IterableData API Reference](../docs/api/)
- [IterableData Format Documentation](../docs/formats/)
