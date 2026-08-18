"""
Example: Convert MongoDB collection to Parquet file.

This example demonstrates how to convert a MongoDB collection to a Parquet file
using IterableData's convert() function.
"""

from iterable.convert import convert


def main():
    """Convert MongoDB collection to Parquet file."""
    # MongoDB connection string
    connection_string = "mongodb://localhost:27017/"

    # Output file
    output_file = "data.parquet"

    print("Converting MongoDB collection 'unicef.inddata' to Parquet...")
    print(f"Output file: {output_file}")
    print("-" * 60)

    # Convert MongoDB collection to Parquet
    # Note: Parquet requires a fixed schema. The schema is determined from the first batch.
    # Fields that appear only in later documents will be dropped to prevent schema errors.
    # If you need to preserve all fields, consider converting to JSONL instead.
    result = convert(
        fromfile=connection_string,
        tofile=output_file,
        iterableargs={
            "engine": "mongo",
            "database": "mdk",
            "collection": "data",
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
