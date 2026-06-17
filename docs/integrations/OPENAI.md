# OpenAI Integration Guide

This document provides guidance on integrating IterableData with OpenAI's API for data processing, analysis, and transformation tasks.

## Overview

OpenAI's models (GPT-4, GPT-3.5, etc.) can leverage IterableData's unified interface to process various data formats, enabling intelligent data analysis, transformation, schema inference, and format conversion. This guide covers integration patterns, use cases, and best practices for using OpenAI with IterableData.

---

## Setup

### Installation

```bash
pip install openai iterabledata
```

### API Key Configuration

```python
from openai import OpenAI

# Initialize client
client = OpenAI(api_key="YOUR_API_KEY")

# Or use environment variable
# export OPENAI_API_KEY="your-api-key"
client = OpenAI()  # Automatically uses OPENAI_API_KEY
```

---

## Basic Integration

### Reading Data with OpenAI

Use IterableData to read data and send to OpenAI for analysis:

```python
from openai import OpenAI
from iterable.helpers.detect import open_iterable
import json

# Initialize OpenAI client
client = OpenAI(api_key="YOUR_API_KEY")

def analyze_data_with_openai(filename: str, question: str) -> str:
    """Read data and analyze with OpenAI."""
    # Read sample data
    with open_iterable(filename) as source:
        sample_records = [row for i, row in enumerate(source) if i < 10]
        data_str = json.dumps(sample_records, indent=2, default=str)
    
    # Send to OpenAI
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {
                "role": "user",
                "content": f"Analyze the following data and answer: {question}\n\nData:\n{data_str}"
            }
        ],
        temperature=0.7,
        max_tokens=1024
    )
    
    return response.choices[0].message.content

# Use it
result = analyze_data_with_openai('sales.csv', 'What are the key trends?')
print(result)
```

### Converting Data Formats

Use OpenAI to intelligently convert between formats:

```python
from openai import OpenAI
from iterable.helpers.detect import open_iterable
from iterable.convert import convert
import json

client = OpenAI(api_key="YOUR_API_KEY")

def smart_convert(input_file: str, output_file: str, instructions: str = None):
    """Convert data format with OpenAI-guided transformation."""
    # Analyze input data
    with open_iterable(input_file) as source:
        sample = [row for i, row in enumerate(source) if i < 5]
        sample_str = json.dumps(sample, indent=2, default=str)
    
    # Get conversion guidance from OpenAI
    if instructions:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {
                    "role": "user",
                    "content": f"""Given this data sample:
{sample_str}

Instructions: {instructions}

Provide JSON schema and transformation rules for converting to target format."""
                }
            ],
            max_tokens=1024
        )
        print(f"Conversion guidance: {response.choices[0].message.content}")
    
    # Perform conversion
    convert(input_file, output_file)
    return f"Converted {input_file} to {output_file}"

# Use it
smart_convert('input.csv', 'output.jsonl', 
              instructions='Normalize dates and convert amounts to float')
```

---

## Advanced Patterns

### Schema Inference with OpenAI

Use OpenAI to infer and document data schemas:

```python
from openai import OpenAI
from iterable.helpers.detect import open_iterable
from iterable.helpers.schema import infer_schema
import json

client = OpenAI(api_key="YOUR_API_KEY")

def openai_schema_inference(filename: str) -> dict:
    """Infer schema using both IterableData and OpenAI."""
    with open_iterable(filename) as source:
        # Get technical schema
        technical_schema = infer_schema(source, sample_size=100)
        
        # Get sample data for OpenAI
        source.reset()  # Reset iterator
        sample = [row for i, row in enumerate(source) if i < 10]
        sample_str = json.dumps(sample, indent=2, default=str)
    
    # Get semantic schema from OpenAI
    response = client.chat.completions.create(
        model="gpt-4o",
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
        ],
        max_tokens=2048
    )
    
    return {
        "technical_schema": technical_schema,
        "semantic_analysis": response.choices[0].message.content
    }

result = openai_schema_inference('customer_data.parquet')
print(result["semantic_analysis"])
```

### Data Transformation with OpenAI

Use OpenAI to plan transformations, then apply an explicit, reviewable function via `pipeline()`:

```python
from openai import OpenAI
from iterable.helpers.detect import open_iterable
from iterable.pipeline import pipeline
import json

client = OpenAI(api_key="YOUR_API_KEY")


def normalize_record(record: dict) -> dict:
    out = dict(record)
    if "email" in out and isinstance(out["email"], str):
        out["email"] = out["email"].strip().lower()
    return out


def openai_guided_transform(input_file: str, output_file: str, transformation_goal: str):
    with open_iterable(input_file) as source:
        sample = [row for i, row in enumerate(source) if i < 5]
        sample_str = json.dumps(sample, indent=2, default=str)

    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {
                "role": "user",
                "content": f"""Given this data sample:
{sample_str}

Goal: {transformation_goal}

List transformation steps as a numbered checklist. Do not output executable Python.""",
            }
        ],
        max_tokens=2048,
    )
    print(response.choices[0].message.content)

    with open_iterable(input_file) as source, open_iterable(output_file, mode="w") as dest:
        pipeline(source=source, destination=dest, process_func=normalize_record)

    return f"Transformed {input_file} -> {output_file}"
```

## Data Privacy

- Sample only a few rows for cloud API calls; avoid uploading full datasets.
- Prefer local models (Ollama, LM Studio) for sensitive data.
- Use `iterable.ai.doc.generate()` with `pii_mask_samples=True` when documenting PII-bearing data.
- Never `exec()` LLM-generated code in production pipelines.

### Data Quality Analysis

Use OpenAI to analyze data quality:

```python
from openai import OpenAI
from iterable.helpers.detect import open_iterable
import json

client = OpenAI(api_key="YOUR_API_KEY")

def openai_data_quality_analysis(filename: str) -> dict:
    """Analyze data quality with OpenAI."""
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
    
    # Get OpenAI analysis
    response = client.chat.completions.create(
        model="gpt-4o",
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
        ],
        max_tokens=2048
    )
    
    return {
        "statistics": {
            "total_records": total,
            "null_counts": null_counts
        },
        "openai_analysis": response.choices[0].message.content
    }

result = openai_data_quality_analysis('dataset.csv')
print(result["openai_analysis"])
```

---

## Function Calling with OpenAI

Use OpenAI's function calling feature for structured operations:

```python
from openai import OpenAI
from iterable.helpers.detect import open_iterable
from iterable.convert import convert
import json

client = OpenAI(api_key="YOUR_API_KEY")

# Define functions
def read_data_file(filename: str, limit: int = 10) -> str:
    """Read data from file."""
    with open_iterable(filename) as source:
        records = [row for i, row in enumerate(source) if i < limit]
        return json.dumps(records, indent=2, default=str)

def convert_data_file(input_file: str, output_file: str) -> str:
    """Convert data format."""
    convert(input_file, output_file)
    return f"Converted {input_file} to {output_file}"

def get_file_info(filename: str) -> dict:
    """Get file information."""
    with open_iterable(filename) as source:
        count = sum(1 for _ in source)
        return {"filename": filename, "record_count": count}

# Define function schemas
functions = [
    {
        "type": "function",
        "function": {
            "name": "read_data_file",
            "description": "Read data from files (CSV, JSON, Parquet, etc.)",
            "parameters": {
                "type": "object",
                "properties": {
                    "filename": {
                        "type": "string",
                        "description": "Path to the data file"
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Maximum number of records to read",
                        "default": 10
                    }
                },
                "required": ["filename"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "convert_data_file",
            "description": "Convert data between formats",
            "parameters": {
                "type": "object",
                "properties": {
                    "input_file": {
                        "type": "string",
                        "description": "Source file path"
                    },
                    "output_file": {
                        "type": "string",
                        "description": "Destination file path"
                    }
                },
                "required": ["input_file", "output_file"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_file_info",
            "description": "Get file information including record count",
            "parameters": {
                "type": "object",
                "properties": {
                    "filename": {
                        "type": "string",
                        "description": "Path to the file"
                    }
                },
                "required": ["filename"]
            }
        }
    }
]

# Use function calling
function_map = {
    "read_data_file": read_data_file,
    "convert_data_file": convert_data_file,
    "get_file_info": get_file_info
}

messages = [
    {
        "role": "user",
        "content": "Read data.csv and convert it to JSONL format"
    }
]

response = client.chat.completions.create(
    model="gpt-4o",
    messages=messages,
    tools=[{"type": "function", "function": f["function"]} for f in functions],
    tool_choice="auto"
)

# Handle function calls
message = response.choices[0].message
if message.tool_calls:
    messages.append(message)  # Add assistant's message with tool calls
    
    for tool_call in message.tool_calls:
        function_name = tool_call.function.name
        function_args = json.loads(tool_call.function.arguments)
        
        if function_name in function_map:
            function_result = function_map[function_name](**function_args)
            
            messages.append({
                "tool_call_id": tool_call.id,
                "role": "tool",
                "name": function_name,
                "content": str(function_result)
            })
    
    # Get final response
    final_response = client.chat.completions.create(
        model="gpt-4o",
        messages=messages
    )
    print(final_response.choices[0].message.content)
```

---

## OpenAI Assistants API

Use OpenAI's Assistants API for persistent, stateful data processing workflows:

```python
from openai import OpenAI
from iterable.helpers.detect import open_iterable
import json

client = OpenAI(api_key="YOUR_API_KEY")

def create_data_processing_assistant() -> str:
    """Create an assistant for data processing."""
    assistant = client.beta.assistants.create(
        name="Data Processing Assistant",
        instructions="""You are a data processing assistant. You help users analyze, 
        transform, and convert data files using IterableData. You can read data files, 
        analyze their structure, suggest transformations, and help with format conversions.""",
        model="gpt-4o",
        tools=[
            {
                "type": "function",
                "function": {
                    "name": "read_data_file",
                    "description": "Read data from files",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "filename": {"type": "string"},
                            "limit": {"type": "integer", "default": 10}
                        },
                        "required": ["filename"]
                    }
                }
            }
        ]
    )
    return assistant.id

def analyze_with_assistant(filename: str, question: str) -> str:
    """Use assistant to analyze data."""
    assistant_id = create_data_processing_assistant()
    
    # Create thread
    thread = client.beta.threads.create()
    
    # Add message
    with open_iterable(filename) as source:
        sample = [row for i, row in enumerate(source) if i < 10]
        data_str = json.dumps(sample, indent=2, default=str)
    
    client.beta.threads.messages.create(
        thread_id=thread.id,
        role="user",
        content=f"{question}\n\nData sample:\n{data_str}"
    )
    
    # Run assistant
    run = client.beta.threads.runs.create(
        thread_id=thread.id,
        assistant_id=assistant_id
    )
    
    # Wait for completion (simplified - in production, poll properly)
    import time
    while run.status in ['queued', 'in_progress']:
        time.sleep(1)
        run = client.beta.threads.runs.retrieve(
            thread_id=thread.id,
            run_id=run.id
        )
    
    # Get messages
    messages = client.beta.threads.messages.list(thread_id=thread.id)
    return messages.data[0].content[0].text.value
```

---

## Structured Outputs

Use OpenAI's structured outputs feature for consistent data analysis results:

```python
from openai import OpenAI
from iterable.helpers.detect import open_iterable
import json
from typing import List, Dict, Optional

client = OpenAI(api_key="YOUR_API_KEY")

def structured_data_analysis(filename: str) -> dict:
    """Get structured analysis results."""
    with open_iterable(filename) as source:
        sample = [row for i, row in enumerate(source) if i < 10]
        data_str = json.dumps(sample, indent=2, default=str)
    
    response = client.beta.chat.completions.parse(
        model="gpt-4o-2024-11-20",
        messages=[
            {
                "role": "user",
                "content": f"""Analyze this data and provide structured analysis:

{data_str}

Provide quality assessment, issues found, and recommendations."""
            }
        ],
        response_format={
            "type": "json_schema",
            "json_schema": {
                "name": "data_analysis",
                "strict": True,
                "schema": {
                    "type": "object",
                    "properties": {
                        "quality_score": {
                            "type": "number",
                            "description": "Overall data quality score (0-100)"
                        },
                        "issues": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "field": {"type": "string"},
                                    "issue": {"type": "string"},
                                    "severity": {"type": "string", "enum": ["low", "medium", "high"]}
                                }
                            }
                        },
                        "recommendations": {
                            "type": "array",
                            "items": {"type": "string"}
                        }
                    },
                    "required": ["quality_score", "issues", "recommendations"]
                }
            }
        }
    )
    
    return json.loads(response.choices[0].message.content)
```

---

## Use Cases

### 1. Intelligent Data Analysis

Use OpenAI to provide natural language insights from data:

```python
def analyze_data_natural_language(filename: str, question: str) -> str:
    """Get natural language analysis of data."""
    client = OpenAI(api_key="YOUR_API_KEY")
    
    with open_iterable(filename) as source:
        sample = [row for i, row in enumerate(source) if i < 20]
        data_str = json.dumps(sample, indent=2, default=str)
    
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {
                "role": "user",
                "content": f"Analyze this data and answer: {question}\n\nData:\n{data_str}\n\nProvide a clear, insightful answer."
            }
        ],
        max_tokens=2048
    )
    
    return response.choices[0].message.content
```

### 2. Data Cleaning Recommendations

Get OpenAI recommendations for data cleaning:

```python
def get_cleaning_recommendations(filename: str) -> str:
    """Get data cleaning recommendations from OpenAI."""
    client = OpenAI(api_key="YOUR_API_KEY")
    
    with open_iterable(filename) as source:
        sample = [row for i, row in enumerate(source) if i < 15]
        data_str = json.dumps(sample, indent=2, default=str)
    
    response = client.chat.completions.create(
        model="gpt-4o",
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
        ],
        max_tokens=2048
    )
    
    return response.choices[0].message.content
```

### 3. Format Recommendations

Get format recommendations based on use case:

```python
def recommend_format(filename: str, use_case: str) -> str:
    """Get format recommendation from OpenAI."""
    client = OpenAI(api_key="YOUR_API_KEY")
    
    with open_iterable(filename) as source:
        sample = [row for i, row in enumerate(source) if i < 5]
        data_str = json.dumps(sample, indent=2, default=str)
        
        # Get file stats
        source.reset()
        count = sum(1 for _ in source)
    
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {
                "role": "user",
                "content": f"""Given this data (sample and record count: {count}):
{data_str}

Use case: {use_case}

Recommend the best data format (Parquet, JSONL, CSV, etc.) and explain why."""
            }
        ],
        max_tokens=1024
    )
    
    return response.choices[0].message.content
```

### 4. Schema Documentation

Generate documentation from data schema:

```python
def generate_schema_documentation(filename: str) -> str:
    """Generate schema documentation using OpenAI."""
    client = OpenAI(api_key="YOUR_API_KEY")
    
    with open_iterable(filename) as source:
        from iterable.helpers.schema import infer_schema
        schema = infer_schema(source, sample_size=100)
        
        source.reset()
        sample = [row for i, row in enumerate(source) if i < 5]
    
    response = client.chat.completions.create(
        model="gpt-4o",
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
        ],
        max_tokens=4096
    )
    
    return response.choices[0].message.content
```

---

## Best Practices

### 1. Sampling for Large Files

Don't send entire large files to OpenAI. Sample instead:

```python
def smart_sample(filename: str, sample_size: int = 20) -> list:
    """Intelligently sample data for OpenAI analysis."""
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
def openai_stream_processing(filename: str, output_file: str, 
                            process_func_prompt: str):
    """Process large files in chunks with OpenAI."""
    client = OpenAI(api_key="YOUR_API_KEY")
    
    # Get transformation function from OpenAI (once)
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {
                "role": "user",
                "content": f"Create a transform function: {process_func_prompt}"
            }
        ],
        max_tokens=2048
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

### 3. Caching OpenAI Responses

Cache OpenAI analysis to avoid repeated API calls:

```python
from functools import lru_cache
import hashlib

@lru_cache(maxsize=50)
def cached_openai_analysis(data_hash: str, prompt: str) -> str:
    """Cache OpenAI analysis results."""
    client = OpenAI(api_key="YOUR_API_KEY")
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=2048
    )
    return response.choices[0].message.content

def analyze_with_cache(filename: str, question: str) -> str:
    """Analyze data with caching."""
    with open_iterable(filename) as source:
        sample = [row for i, row in enumerate(source) if i < 10]
        data_str = json.dumps(sample, sort_keys=True)
        data_hash = hashlib.md5(data_str.encode()).hexdigest()
    
    prompt = f"Analyze: {question}\n\nData:\n{data_str}"
    return cached_openai_analysis(data_hash, prompt)
```

### 4. Error Handling

Implement robust error handling:

```python
from openai import APIError, RateLimitError, APIConnectionError

def safe_openai_operation(operation_func, *args, **kwargs):
    """Safely execute OpenAI operations with error handling."""
    try:
        return operation_func(*args, **kwargs)
    except RateLimitError as e:
        return f"Rate limit exceeded. Please try again later. Error: {str(e)}"
    except APIConnectionError as e:
        return f"Connection error. Please check your internet connection. Error: {str(e)}"
    except APIError as e:
        return f"API error: {str(e)}"
    except Exception as e:
        return f"Error: {str(e)}"
```

### 5. Streaming Responses

Use streaming for long responses:

```python
def stream_analysis(filename: str, question: str):
    """Stream analysis response from OpenAI."""
    client = OpenAI(api_key="YOUR_API_KEY")
    
    with open_iterable(filename) as source:
        sample = [row for i, row in enumerate(source) if i < 10]
        data_str = json.dumps(sample, indent=2, default=str)
    
    stream = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {
                "role": "user",
                "content": f"{question}\n\nData:\n{data_str}"
            }
        ],
        stream=True,
        max_tokens=2048
    )
    
    for chunk in stream:
        if chunk.choices[0].delta.content:
            print(chunk.choices[0].delta.content, end='', flush=True)
```

### 6. Model Selection

Choose the right model for your use case:

```python
# For cost-effective analysis
def analyze_with_gpt35(filename: str, question: str) -> str:
    """Use GPT-3.5 for simpler tasks."""
    client = OpenAI(api_key="YOUR_API_KEY")
    # ... use gpt-3.5-turbo ...

# For complex reasoning
def analyze_with_gpt4(filename: str, question: str) -> str:
    """Use GPT-4 for complex analysis."""
    client = OpenAI(api_key="YOUR_API_KEY")
    # ... use gpt-4o ...
```

---

## Performance Optimization

### Batch Processing

Process multiple files or operations in batches:

```python
def batch_openai_analysis(filenames: list[str], question: str) -> dict:
    """Analyze multiple files with OpenAI."""
    client = OpenAI(api_key="YOUR_API_KEY")
    results = {}
    
    for filename in filenames:
        with open_iterable(filename) as source:
            sample = [row for i, row in enumerate(source) if i < 10]
            data_str = json.dumps(sample, indent=2, default=str)
        
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {
                    "role": "user",
                    "content": f"File: {filename}\n\n{question}\n\nData:\n{data_str}"
                }
            ],
            max_tokens=2048
        )
        results[filename] = response.choices[0].message.content
    
    return results
```

### Parallel Processing

Use threading for parallel OpenAI API calls (be mindful of rate limits):

```python
from concurrent.futures import ThreadPoolExecutor
from openai import OpenAI

def parallel_openai_analysis(filenames: list[str], question: str) -> dict:
    """Analyze files in parallel."""
    client = OpenAI(api_key="YOUR_API_KEY")
    
    def analyze_file(filename: str) -> tuple:
        with open_iterable(filename) as source:
            sample = [row for i, row in enumerate(source) if i < 10]
            data_str = json.dumps(sample, indent=2, default=str)
        
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {
                    "role": "user",
                    "content": f"{question}\n\nData:\n{data_str}"
                }
            ],
            max_tokens=2048
        )
        return filename, response.choices[0].message.content
    
    with ThreadPoolExecutor(max_workers=5) as executor:
        results = dict(executor.map(analyze_file, filenames))
    
    return results
```

---

## Complete Example

```python
from openai import OpenAI
from iterable.helpers.detect import open_iterable
from iterable.convert import convert
from iterable.pipeline import pipeline
import json

# Configure
client = OpenAI(api_key="YOUR_API_KEY")

def comprehensive_data_processing(input_file: str, output_file: str, 
                                  goal: str) -> dict:
    """Complete data processing workflow with OpenAI."""
    
    # 1. Analyze input data
    with open_iterable(input_file) as source:
        sample = [row for i, row in enumerate(source) if i < 10]
        sample_str = json.dumps(sample, indent=2, default=str)
    
    # 2. Get processing plan from OpenAI
    plan_response = client.chat.completions.create(
        model="gpt-4o",
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
        ],
        max_tokens=2048
    )
    plan = plan_response.choices[0].message.content
    print(f"Processing Plan:\n{plan}\n")
    
    # 3. Get transformation function
    transform_response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {
                "role": "user",
                "content": f"""Goal: {goal}

Create Python function: def transform(record: dict) -> dict:
Only return function code."""
            }
        ],
        max_tokens=2048
    )
    transform_code = transform_response.choices[0].message.content
    # Extract and execute function...
    
    # 4. Execute transformation
    # ... apply transformations ...
    
    # 5. Convert format
    convert(input_file, output_file)
    
    # 6. Validate output
    with open_iterable(output_file) as source:
        validation_sample = [row for i, row in enumerate(source) if i < 5]
        validation_str = json.dumps(validation_sample, indent=2, default=str)
    
    validation_response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {
                "role": "user",
                "content": f"""Validate this processed data:
{validation_str}

Goal was: {goal}

Provide validation assessment."""
            }
        ],
        max_tokens=1024
    )
    
    return {
        "plan": plan,
        "validation": validation_response.choices[0].message.content,
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

1. **API Rate Limits**: OpenAI API has rate limits based on tier. Implement retry logic and exponential backoff.

2. **Token Limits**: Large data samples may exceed context windows. GPT-4o supports up to 128K tokens. Use sampling strategies.

3. **Cost**: OpenAI API calls incur costs based on model and usage. Cache results and batch operations when possible.

4. **Latency**: API calls add latency. Use for complex analysis, not simple operations.

5. **Data Privacy**: Don't send sensitive data to external APIs without proper safeguards. Consider using OpenAI Enterprise for enhanced privacy controls.

6. **Context Window**: Be mindful of context window limits. For very large datasets, use iterative processing.

7. **Model Availability**: Different models have different capabilities and costs. Choose appropriately for your use case.

---

## Resources

- [OpenAI API Documentation](https://platform.openai.com/docs)
- [OpenAI Python SDK](https://github.com/openai/openai-python)
- [OpenAI Function Calling Guide](https://platform.openai.com/docs/guides/function-calling)
- [OpenAI Assistants API](https://platform.openai.com/docs/assistants/overview)
- [OpenAI Structured Outputs](https://platform.openai.com/docs/guides/structured-outputs)
- [IterableData API Reference](../docs/api/)
- [IterableData Format Documentation](../docs/formats/)
