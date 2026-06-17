# AI Frameworks Integration Guide

> **See also:** [Building AI Agents](../docs/integrations/BUILDING_AGENTS.md) — canonical hub for `iterable.tools`, MCP, and schemas.

This document provides guidance on integrating IterableData with AI agent frameworks (LangChain, CrewAI, AutoGen) for automated data processing, transformation, and analysis tasks.

## Overview

AI agent frameworks can leverage IterableData's unified interface to process various data formats, enabling intelligent data transformation, validation, schema inference, and format conversion workflows. This guide covers integration patterns, use cases, and best practices.

---

## Supported Agent Frameworks

### LangChain Agents

LangChain agents can use IterableData as tools for reading, writing, and converting data formats.

#### Basic Integration

```python
from langchain.agents import AgentExecutor, create_openai_functions_agent
from langchain_openai import ChatOpenAI
from langchain.tools import Tool
from iterable.helpers.detect import open_iterable
from iterable.convert import convert

def read_iterable_data(filename: str, limit: int = 10) -> str:
    """Read data from a file and return as JSON string."""
    with open_iterable(filename) as source:
        records = [row for i, row in enumerate(source) if i < limit]
        return str(records)

def convert_data_format(input_file: str, output_file: str, format_hint: str = None) -> str:
    """Convert data from one format to another."""
    convert(input_file, output_file)
    return f"Converted {input_file} to {output_file}"

# Create LangChain tools
iterable_tools = [
    Tool(
        name="read_data",
        func=read_iterable_data,
        description="Read data from files (CSV, JSON, Parquet, XML, etc.). Returns first N records as JSON."
    ),
    Tool(
        name="convert_format",
        func=convert_data_format,
        description="Convert data files between formats (e.g., CSV to JSON, Parquet to CSV)."
    )
]

# Create agent
llm = ChatOpenAI(model="gpt-4")
agent = create_openai_functions_agent(llm, iterable_tools, "")
agent_executor = AgentExecutor(agent=agent, tools=iterable_tools, verbose=True)

# Use agent
result = agent_executor.invoke({
    "input": "Read the first 5 records from data.csv and convert it to JSON format"
})
```

#### Advanced Pattern: Schema Inference Agent

```python
from langchain.agents import AgentExecutor, create_openai_functions_agent
from langchain_openai import ChatOpenAI
from langchain.tools import Tool
from iterable.helpers.detect import open_iterable
from iterable.helpers.schema import infer_schema
import json

def infer_data_schema(filename: str, sample_size: int = 100) -> str:
    """Infer schema from a data file."""
    with open_iterable(filename) as source:
        schema = infer_schema(source, sample_size=sample_size)
        return json.dumps(schema, indent=2)

def analyze_data_quality(filename: str) -> str:
    """Analyze data quality: missing values, duplicates, outliers."""
    with open_iterable(filename) as source:
        stats = {
            "total_records": 0,
            "null_counts": {},
            "unique_values": {}
        }
        for record in source:
            stats["total_records"] += 1
            for key, value in record.items():
                if value is None:
                    stats["null_counts"][key] = stats["null_counts"].get(key, 0) + 1
        return json.dumps(stats, indent=2)

schema_tools = [
    Tool(
        name="infer_schema",
        func=infer_data_schema,
        description="Infer data schema from a file. Returns field types and structure."
    ),
    Tool(
        name="analyze_quality",
        func=analyze_data_quality,
        description="Analyze data quality metrics including null counts and statistics."
    )
]

llm = ChatOpenAI(model="gpt-4")
agent = create_openai_functions_agent(llm, schema_tools, "")
executor = AgentExecutor(agent=agent, tools=schema_tools, verbose=True)

result = executor.invoke({
    "input": "Analyze the schema and data quality of sales_data.parquet"
})
```

### CrewAI Agents

CrewAI agents can collaborate on data processing tasks using IterableData.

```python
from crewai import Agent, Task, Crew
from iterable.helpers.detect import open_iterable
from iterable.convert import convert

def data_reader_tool(filename: str) -> str:
    """Read and summarize data file."""
    with open_iterable(filename) as source:
        count = sum(1 for _ in source)
        return f"File contains {count} records"

def data_converter_tool(input_file: str, output_file: str) -> str:
    """Convert data format."""
    convert(input_file, output_file)
    return f"Converted to {output_file}"

# Define agents
data_analyst = Agent(
    role='Data Analyst',
    goal='Analyze data files and provide insights',
    backstory='Expert in data analysis and format conversion',
    tools=[data_reader_tool, data_converter_tool],
    verbose=True
)

data_engineer = Agent(
    role='Data Engineer',
    goal='Convert and transform data between formats',
    backstory='Specialist in data pipeline and ETL operations',
    tools=[data_reader_tool, data_converter_tool],
    verbose=True
)

# Define tasks
task1 = Task(
    description='Read customer_data.csv and convert it to JSON format',
    agent=data_analyst
)

task2 = Task(
    description='Validate the converted JSON file structure',
    agent=data_engineer
)

# Create crew
crew = Crew(
    agents=[data_analyst, data_engineer],
    tasks=[task1, task2],
    verbose=True
)

result = crew.kickoff()
```

### AutoGen Agents

AutoGen agents can use IterableData for multi-agent data processing workflows.

```python
from autogen import ConversableAgent, GroupChat, GroupChatManager
from iterable.helpers.detect import open_iterable
import json

def read_data_function(filename: str) -> str:
    """Read data file and return summary."""
    with open_iterable(filename) as source:
        records = list(source)
        return json.dumps({
            "count": len(records),
            "sample": records[:3] if records else []
        })

# Define agents
data_agent = ConversableAgent(
    name="data_processor",
    system_message="You are a data processing agent. Use the read_data function to analyze files.",
    llm_config={"model": "gpt-4"},
    function_map={"read_data": read_data_function}
)

analyst_agent = ConversableAgent(
    name="analyst",
    system_message="You analyze data and provide insights.",
    llm_config={"model": "gpt-4"}
)

# Create group chat
groupchat = GroupChat(
    agents=[data_agent, analyst_agent],
    messages=[],
    max_round=10
)

manager = GroupChatManager(groupchat=groupchat, llm_config={"model": "gpt-4"})

# Start conversation
result = manager.initiate_chat(
    data_agent,
    message="Read data.csv and provide analysis"
)
```

---

## Use Cases

### 1. Intelligent Data Conversion

Agents can automatically detect input formats and convert to target formats with appropriate transformations.

```python
def smart_converter(input_file: str, target_format: str, schema_hint: str = None):
    """Agent-powered format converter with intelligent schema handling."""
    with open_iterable(input_file) as source:
        # Agent analyzes format and schema
        # Performs necessary transformations
        # Outputs in target format
        pass
```

### 2. Data Validation and Cleaning

Agents can validate data quality, identify issues, and suggest or perform cleaning operations.

### 3. Schema Mapping and Transformation

Agents can map schemas between formats, handle nested structures, and transform data accordingly.

### 4. Format Detection and Recommendation

Agents can analyze data characteristics and recommend optimal formats for storage or processing.

---

## Best Practices

### 1. Efficient Data Streaming

When working with large files, use IterableData's iterator interface to stream data to agents rather than loading everything into memory.

### 2. Format-Specific Optimization

Different formats have different characteristics. Agents should leverage format-specific features:

- **Parquet/ORC**: Use columnar reading for analytics
- **JSONL**: Stream line-by-line for large files
- **CSV**: Use DuckDB engine for fast queries
- **XML**: Handle nested structures carefully

### 3. Error Handling

Implement robust error handling for agent operations.

### 4. Context Management

Always use context managers (`with` statements) to ensure proper resource cleanup.

### 5. Declarative Transforms (Safe Pattern)

Do not `exec()` LLM-generated Python. Use the LLM for planning, then apply explicit functions:

```python
from iterable.helpers.detect import open_iterable
from iterable.pipeline import pipeline


def normalize_row(record: dict) -> dict:
    out = dict(record)
    if "email" in out and isinstance(out["email"], str):
        out["email"] = out["email"].strip().lower()
    return out


with open_iterable("input.csv") as source, open_iterable("output.jsonl", mode="w") as dest:
    pipeline(source=source, destination=dest, process_func=normalize_row)
```

For AI-generated documentation, use `iterable.ai.doc.generate()` or `inspect.analyze(autodoc=True)`.

### 6. Data Privacy

- Sample small subsets for agent/LLM prompts.
- Prefer local providers (Ollama, LM Studio) for sensitive datasets.
- Enable PII masking when using `iterable.ai` on production data.

---

## Integration Patterns

### Pattern 1: Agent as Data Processor

Agent processes data row-by-row with IterableData.

### Pattern 2: Agent as Format Converter

Agent orchestrates format conversion with intelligent handling.

### Pattern 3: Agent as Schema Mapper

Agent maps schemas between different formats.

---

## Performance Considerations

### Batch Processing

Process data in batches for better agent efficiency.

### Streaming for Large Files

Use IterableData's streaming capabilities to avoid memory issues.

### Caching Agent Results

Cache agent analysis results to avoid reprocessing.

---

## Limitations and Considerations

1. **Token Limits**: Large files may exceed LLM context windows. Use sampling or chunking strategies.
2. **Cost**: Agent operations can be expensive. Consider caching and batch processing.
3. **Latency**: Agent operations add latency. Use for complex tasks, not simple conversions.
4. **Error Handling**: Agents may make mistakes. Always validate agent outputs.
5. **Format Support**: Not all IterableData formats may be suitable for agent processing. Test compatibility.

---

## Resources

- [LangChain Documentation](https://python.langchain.com/)
- [CrewAI Documentation](https://docs.crewai.com/)
- [AutoGen Documentation](https://microsoft.github.io/autogen/)
- [IterableData API Reference](../docs/api/)
- [Format Documentation](../docs/formats/)
