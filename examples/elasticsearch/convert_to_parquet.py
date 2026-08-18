"""
Example: Convert Elasticsearch index to Parquet file.

This example demonstrates how to convert an Elasticsearch index to a Parquet file
using IterableData's convert() function.
"""

from iterable.convert import convert


def main():
    """Convert Elasticsearch index to Parquet file."""
    # Elasticsearch connection URL
    connection_url = "http://localhost:9200"
    # For authenticated clusters, use one of these options:
    # Option 1: URL-based auth: connection_url = "https://username:password@localhost:9200"
    # Option 2: API key via connect_args (see iterableargs below)
    # Option 3: Basic auth via connect_args: "connect_args": {"basic_auth": ("user", "pass")}

    # Output file
    output_file = "logs.parquet"

    print("Converting Elasticsearch index 'logs-2024-01' to Parquet...")
    print(f"Output file: {output_file}")
    print("-" * 60)

    # Convert Elasticsearch index to Parquet
    # Note: Parquet requires a fixed schema. The schema is determined from the first batch.
    # Fields that appear only in later documents will be dropped to prevent schema errors.
    # If you need to preserve all fields, consider converting to JSONL instead.
    result = convert(
        fromfile=connection_url,
        tofile=output_file,
        iterableargs={
            "engine": "elasticsearch",
            "index": "logs-2024-01",
            "body": {"query": {"match_all": {}}},
            "source_only": True,  # Return only _source fields
            # Uncomment to use API key authentication:
            # "connect_args": {
            #     "api_key": "your_api_key_string"  # Just the API key, or use ("id", "api_key") tuple
            # }
            # Uncomment to set timeouts:
            # "request_timeout": 30.0,  # Client-side timeout in seconds
            # "timeout": "30s",  # Server-side timeout
        },
        toiterableargs={
            "adapt_schema": True,  # Adapt schema for varying document structures
        },
        is_flatten=True,  # Flatten nested structures to handle schema variations
        scan_limit=10000,  # Scan more documents to infer a more complete schema
        silent=False,  # Show progress
    )

    print("-" * 60)
    print("Conversion completed!")
    print(f"Documents read: {result.rows_in}")
    print(f"Rows written: {result.rows_out}")
    print(f"Time elapsed: {result.elapsed_seconds:.2f} seconds")
    if result.errors:
        print(f"Errors: {result.errors}")


if __name__ == "__main__":
    main()
