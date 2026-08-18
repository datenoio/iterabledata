# Google Gemini AI Integration Guide

This document provides guidance on integrating IterableData with Google Gemini AI for data processing, analysis, and transformation tasks.

## Overview

Google Gemini AI can leverage IterableData's unified interface to process various data formats, enabling intelligent data analysis, transformation, schema inference, and format conversion. This guide covers integration patterns, use cases, and best practices for using Gemini with IterableData.

---

## Setup

### Installation

```bash
pip install google-generativeai iterabledata
```

### API Key Configuration

```python
import google.generativeai as genai

# Set your API key
genai.configure(api_key="YOUR_API_KEY")

# Or use environment variable
# export GOOGLE_API_KEY="your-api-key"
```

---

## Basic Integration

### Reading Data with Gemini

Use IterableData to read data and send to Gemini for analysis:

```python
import google.generativeai as genai
from iterable import open_iterable
import json

# Configure Gemini
genai.configure(api_key="YOUR_API_KEY")
model = genai.GenerativeModel('gemini-pro')

def analyze_data_with_gemini(filename: str, question: str) -> str:
    """Read data and analyze with Gemini."""
    # Read sample data
    with open_iterable(filename) as source:
        sample_records = [row for i, row in enumerate(source) if i < 10]
        data_str = json.dumps(sample_records, indent=2, default=str)
    
    # Send to Gemini
    prompt = f"""
    Analyze the following data and answer: {question}
    
    Data:
    {data_str}
    """
    
    response = model.generate_content(prompt)
    return response.text

# Use it
result = analyze_data_with_gemini('sales.csv', 'What are the key trends?')
print(result)
```

### Converting Data Formats

Use Gemini to intelligently convert between formats:

```python
import google.generativeai as genai
from iterable import open_iterable
from iterable.convert import convert
import json

genai.configure(api_key="YOUR_API_KEY")
model = genai.GenerativeModel('gemini-pro')

def smart_convert(input_file: str, output_file: str, instructions: str = None):
    """Convert data format with Gemini-guided transformation."""
    # Analyze input data
    with open_iterable(input_file) as source:
        sample = [row for i, row in enumerate(source) if i < 5]
        sample_str = json.dumps(sample, indent=2, default=str)
    
    # Get conversion guidance from Gemini
    if instructions:
        prompt = f"""
        Given this data sample:
        {sample_str}
        
        Instructions: {instructions}
        
        Provide JSON schema and transformation rules for converting to target format.
        """
        response = model.generate_content(prompt)
        print(f"Conversion guidance: {response.text}")
    
    # Perform conversion
    convert(input_file, output_file)
    return f"Converted {input_file} to {output_file}"

# Use it
smart_convert('input.csv', 'output.jsonl', 
              instructions='Normalize dates and convert amounts to float')
```

---

## Advanced Patterns

### Schema Inference with Gemini

Use Gemini to infer and document data schemas:

```python
import google.generativeai as genai
from iterable import open_iterable
from iterable.helpers.schema import infer_schema
import json

genai.configure(api_key="YOUR_API_KEY")
model = genai.GenerativeModel('gemini-pro')

def gemini_schema_inference(filename: str) -> dict:
    """Infer schema using both IterableData and Gemini."""
    with open_iterable(filename) as source:
        # Get technical schema
        technical_schema = infer_schema(source, sample_size=100)
        
        # Get sample data for Gemini
        source.seek(0)  # Reset if needed
        sample = [row for i, row in enumerate(source) if i < 10]
        sample_str = json.dumps(sample, indent=2, default=str)
    
    # Get semantic schema from Gemini
    prompt = f"""
    Analyze this data sample and provide:
    1. Semantic field descriptions
    2. Business context
    3. Data quality observations
    4. Recommended transformations
    
    Data:
    {sample_str}
    
    Technical Schema:
    {json.dumps(technical_schema, indent=2)}
    """
    
    response = model.generate_content(prompt)
    
    return {
        "technical_schema": technical_schema,
        "semantic_analysis": response.text
    }

result = gemini_schema_inference('customer_data.parquet')
print(result["semantic_analysis"])
```

### Data Transformation with Gemini

Use Gemini for planning, then apply explicit transforms via `pipeline()` (do not `exec()` generated code):

```python
import google.generativeai as genai
from iterable import open_iterable
from iterable.pipeline import pipeline
import json

genai.configure(api_key="YOUR_API_KEY")
model = genai.GenerativeModel("gemini-pro")


def normalize_record(record: dict) -> dict:
    out = dict(record)
    if "email" in out and isinstance(out["email"], str):
        out["email"] = out["email"].strip().lower()
    return out


def gemini_guided_transform(input_file: str, output_file: str, transformation_goal: str):
    with open_iterable(input_file) as source:
        sample = [row for i, row in enumerate(source) if i < 5]
        sample_str = json.dumps(sample, indent=2, default=str)

    prompt = f"""Given this data sample:
{sample_str}

Goal: {transformation_goal}

List transformation steps as a numbered checklist. Do not output executable Python."""
    print(model.generate_content(prompt).text)

    with open_iterable(input_file) as source, open_iterable(output_file, mode="w") as dest:
        pipeline(source=source, destination=dest, process_func=normalize_record)

    return f"Transformed {input_file} -> {output_file}"
```

## Data Privacy

- Limit samples sent to Google's API; use on-prem or local tooling for regulated data.
- Prefer `iterable.ai` with local providers when data cannot leave your environment.
- Mask PII in samples before any cloud LLM call.

### Data Quality Analysis

Use Gemini to analyze data quality:

```python
import google.generativeai as genai
from iterable import open_iterable
import json

genai.configure(api_key="YOUR_API_KEY")
model = genai.GenerativeModel('gemini-pro')

def gemini_data_quality_analysis(filename: str) -> dict:
    """Analyze data quality with Gemini."""
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
    
    # Get Gemini analysis
    prompt = f"""
    Analyze data quality:
    
    Statistics:
    {stats_str}
    
    Sample Data:
    {sample_str}
    
    Provide:
    1. Data quality assessment
    2. Issues found
    3. Recommendations for improvement
    """
    
    response = model.generate_content(prompt)
    
    return {
        "statistics": {
            "total_records": total,
            "null_counts": null_counts
        },
        "gemini_analysis": response.text
    }

result = gemini_data_quality_analysis('dataset.csv')
print(result["gemini_analysis"])
```

---

## Function Calling with Gemini

Use Gemini's function calling feature for structured operations:

```python
import google.generativeai as genai
from iterable import open_iterable
from iterable.convert import convert
import json

genai.configure(api_key="YOUR_API_KEY")

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

# Create tools
tools = [
    {
        "function_declarations": [
            {
                "name": "read_data_file",
                "description": "Read data from files (CSV, JSON, Parquet, etc.)",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "filename": {"type": "string"},
                        "limit": {"type": "integer", "default": 10}
                    },
                    "required": ["filename"]
                }
            },
            {
                "name": "convert_data_file",
                "description": "Convert data between formats",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "input_file": {"type": "string"},
                        "output_file": {"type": "string"}
                    },
                    "required": ["input_file", "output_file"]
                }
            }
        ]
    }
]

# Create model with tools
model = genai.GenerativeModel(
    model_name='gemini-pro',
    tools=tools
)

# Use function calling
response = model.generate_content(
    "Read data.csv and convert it to JSONL format"
)

# Handle function calls
if response.candidates[0].content.parts[0].function_call:
    function_call = response.candidates[0].content.parts[0].function_call
    function_name = function_call.name
    
    if function_name == "read_data_file":
        args = dict(function_call.args)
        result = read_data_file(**args)
        # Continue conversation with result
        response = model.generate_content([
            response.candidates[0].content,
            {"function_response": {"name": function_name, "response": result}}
        ])
```

---

## Use Cases

### 1. Intelligent Data Analysis

Use Gemini to provide natural language insights from data:

```python
def analyze_data_natural_language(filename: str, question: str) -> str:
    """Get natural language analysis of data."""
    with open_iterable(filename) as source:
        sample = [row for i, row in enumerate(source) if i < 20]
        data_str = json.dumps(sample, indent=2, default=str)
    
    prompt = f"""
    Analyze this data and answer: {question}
    
    Data:
    {data_str}
    
    Provide a clear, insightful answer.
    """
    
    model = genai.GenerativeModel('gemini-pro')
    response = model.generate_content(prompt)
    return response.text
```

### 2. Data Cleaning Recommendations

Get Gemini recommendations for data cleaning:

```python
def get_cleaning_recommendations(filename: str) -> str:
    """Get data cleaning recommendations from Gemini."""
    with open_iterable(filename) as source:
        sample = [row for i, row in enumerate(source) if i < 15]
        data_str = json.dumps(sample, indent=2, default=str)
    
    prompt = f"""
    Analyze this data and provide cleaning recommendations:
    
    {data_str}
    
    Provide:
    1. Issues found
    2. Recommended cleaning steps
    3. Example transformations
    """
    
    model = genai.GenerativeModel('gemini-pro')
    response = model.generate_content(prompt)
    return response.text
```

### 3. Format Recommendations

Get format recommendations based on use case:

```python
def recommend_format(filename: str, use_case: str) -> str:
    """Get format recommendation from Gemini."""
    with open_iterable(filename) as source:
        sample = [row for i, row in enumerate(source) if i < 5]
        data_str = json.dumps(sample, indent=2, default=str)
        
        # Get file stats
        count = sum(1 for _ in source)
    
    prompt = f"""
    Given this data (sample and record count: {count}):
    {data_str}
    
    Use case: {use_case}
    
    Recommend the best data format (Parquet, JSONL, CSV, etc.) and explain why.
    """
    
    model = genai.GenerativeModel('gemini-pro')
    response = model.generate_content(prompt)
    return response.text
```

### 4. Schema Documentation

Generate documentation from data schema:

```python
def generate_schema_documentation(filename: str) -> str:
    """Generate schema documentation using Gemini."""
    with open_iterable(filename) as source:
        from iterable.helpers.schema import infer_schema
        schema = infer_schema(source, sample_size=100)
        
        source.seek(0)
        sample = [row for i, row in enumerate(source) if i < 5]
    
    prompt = f"""
    Generate comprehensive documentation for this data schema:
    
    Schema: {json.dumps(schema, indent=2)}
    Sample: {json.dumps(sample, indent=2)}
    
    Include:
    1. Field descriptions
    2. Data types and constraints
    3. Example values
    4. Usage notes
    """
    
    model = genai.GenerativeModel('gemini-pro')
    response = model.generate_content(prompt)
    return response.text
```

---

## Best Practices

### 1. Sampling for Large Files

Don't send entire large files to Gemini. Sample instead:

```python
def smart_sample(filename: str, sample_size: int = 20) -> list:
    """Intelligently sample data for Gemini analysis."""
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
def gemini_stream_processing(filename: str, output_file: str, 
                            process_func_prompt: str):
    """Process large files in chunks with Gemini."""
    model = genai.GenerativeModel('gemini-pro')
    
    # Get transformation function from Gemini (once)
    sample_prompt = f"Create a transform function: {process_func_prompt}"
    # ... get function code ...
    
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

### 3. Caching Gemini Responses

Cache Gemini analysis to avoid repeated API calls:

```python
from functools import lru_cache
import hashlib

@lru_cache(maxsize=50)
def cached_gemini_analysis(data_hash: str, prompt: str) -> str:
    """Cache Gemini analysis results."""
    model = genai.GenerativeModel('gemini-pro')
    response = model.generate_content(prompt)
    return response.text

def analyze_with_cache(filename: str, question: str) -> str:
    """Analyze data with caching."""
    with open_iterable(filename) as source:
        sample = [row for i, row in enumerate(source) if i < 10]
        data_str = json.dumps(sample, sort_keys=True)
        data_hash = hashlib.md5(data_str.encode()).hexdigest()
    
    prompt = f"Analyze: {question}\n\nData:\n{data_str}"
    return cached_gemini_analysis(data_hash, prompt)
```

### 4. Error Handling

Implement robust error handling:

```python
def safe_gemini_operation(operation_func, *args, **kwargs):
    """Safely execute Gemini operations with error handling."""
    try:
        return operation_func(*args, **kwargs)
    except Exception as e:
        # Handle rate limits, API errors, etc.
        if "quota" in str(e).lower():
            return "API quota exceeded. Please try later."
        elif "safety" in str(e).lower():
            return "Content was blocked by safety filters."
        else:
            return f"Error: {str(e)}"
```

---

## Performance Optimization

### Batch Processing

Process multiple files or operations in batches:

```python
def batch_gemini_analysis(filenames: list[str], question: str) -> dict:
    """Analyze multiple files with Gemini."""
    model = genai.GenerativeModel('gemini-pro')
    results = {}
    
    for filename in filenames:
        with open_iterable(filename) as source:
            sample = [row for i, row in enumerate(source) if i < 10]
            data_str = json.dumps(sample, indent=2, default=str)
        
        prompt = f"File: {filename}\n\n{question}\n\nData:\n{data_str}"
        response = model.generate_content(prompt)
        results[filename] = response.text
    
    return results
```

### Parallel Processing

Use threading for parallel Gemini API calls:

```python
from concurrent.futures import ThreadPoolExecutor
import google.generativeai as genai

def parallel_gemini_analysis(filenames: list[str], question: str) -> dict:
    """Analyze files in parallel."""
    genai.configure(api_key="YOUR_API_KEY")
    
    def analyze_file(filename: str) -> tuple:
        with open_iterable(filename) as source:
            sample = [row for i, row in enumerate(source) if i < 10]
            data_str = json.dumps(sample, indent=2, default=str)
        
        model = genai.GenerativeModel('gemini-pro')
        prompt = f"{question}\n\nData:\n{data_str}"
        response = model.generate_content(prompt)
        return filename, response.text
    
    with ThreadPoolExecutor(max_workers=5) as executor:
        results = dict(executor.map(analyze_file, filenames))
    
    return results
```

---

## Complete Example

```python
import google.generativeai as genai
from iterable import open_iterable
from iterable.convert import convert
from iterable.pipeline import pipeline
import json

# Configure
genai.configure(api_key="YOUR_API_KEY")
model = genai.GenerativeModel('gemini-pro')

def comprehensive_data_processing(input_file: str, output_file: str, 
                                  goal: str) -> dict:
    """Complete data processing workflow with Gemini."""
    
    # 1. Analyze input data
    with open_iterable(input_file) as source:
        sample = [row for i, row in enumerate(source) if i < 10]
        sample_str = json.dumps(sample, indent=2, default=str)
    
    # 2. Get processing plan from Gemini
    planning_prompt = f"""
    Given this data:
    {sample_str}
    
    Goal: {goal}
    
    Provide a step-by-step processing plan:
    1. Data quality issues to address
    2. Transformations needed
    3. Target format recommendation
    4. Validation steps
    """
    plan_response = model.generate_content(planning_prompt)
    plan = plan_response.text
    print(f"Processing Plan:\n{plan}\n")
    
    # 3. Get transformation function
    transform_prompt = f"""
    Goal: {goal}
    
    Create Python function: def transform(record: dict) -> dict:
    Only return function code.
    """
    transform_response = model.generate_content(transform_prompt)
    transform_code = transform_response.text
    # Extract and execute function...
    
    # 4. Execute transformation
    # ... apply transformations ...
    
    # 5. Convert format
    convert(input_file, output_file)
    
    # 6. Validate output
    with open_iterable(output_file) as source:
        validation_sample = [row for i, row in enumerate(source) if i < 5]
        validation_str = json.dumps(validation_sample, indent=2, default=str)
    
    validation_prompt = f"""
    Validate this processed data:
    {validation_str}
    
    Goal was: {goal}
    
    Provide validation assessment.
    """
    validation_response = model.generate_content(validation_prompt)
    
    return {
        "plan": plan,
        "validation": validation_response.text,
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

1. **API Rate Limits**: Gemini API has rate limits. Implement retry logic and rate limiting.

2. **Token Limits**: Large data samples may exceed context windows. Use sampling strategies.

3. **Cost**: Gemini API calls incur costs. Cache results and batch operations when possible.

4. **Latency**: API calls add latency. Use for complex analysis, not simple operations.

5. **Data Privacy**: Don't send sensitive data to external APIs without proper safeguards.

6. **Content Safety**: Gemini may block certain content. Handle safety filter responses.

---

## Resources

- [Google Gemini API Documentation](https://ai.google.dev/docs)
- [Generative AI Python SDK](https://github.com/google/generative-ai-python)
- [IterableData API Reference](../docs/api/)
- [IterableData Format Documentation](../docs/formats/)
- [Gemini Function Calling Guide](https://ai.google.dev/docs/function_calling)

