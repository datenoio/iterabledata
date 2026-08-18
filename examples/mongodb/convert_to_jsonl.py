"""
Example: Convert MongoDB collection to JSONL file.

This example demonstrates how to convert a MongoDB collection to a JSONL file
using IterableData's convert() function.
"""

from iterable.convert import convert


def main():
    """Convert MongoDB collection to JSONL file."""
    # MongoDB connection string
    connection_string = "mongodb://localhost:27017/"

    # Output file
    output_file = "inddata.jsonl"

    print("Converting MongoDB collection 'unicef.inddata' to JSONL...")
    print(f"Output file: {output_file}")
    print("-" * 60)

    # Convert MongoDB collection to JSONL
    result = convert(
        fromfile=connection_string,
        tofile=output_file,
        iterableargs={
            "engine": "mongo",
            "database": "mdk",
            "collection": "data",
        },
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
