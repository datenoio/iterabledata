"""
Example: Convert WARC file to JSONL file.

This example demonstrates how to convert a WARC (Web ARChive) file to a JSONL file
using IterableData's convert() function.

WARC files contain web archive records including HTTP requests/responses,
metadata, and resource records. This example extracts all records and converts
them to JSONL format for easier processing and analysis.
"""

import os
import sys
from pathlib import Path

from iterable.convert import convert


def main():
    """Convert WARC file to JSONL file."""
    # Get the project root directory (assuming script is in examples/warc/)
    project_root = Path(__file__).parent.parent.parent
    
    # Use test WARC file if no argument provided
    if len(sys.argv) > 1:
        input_file = sys.argv[1]
    else:
        # Default to test WARC file from fixtures (gzipped)
        input_file = str(project_root / "tests" / "fixtures" / "sample.warc.gz")
        if not os.path.exists(input_file):
            # Fallback to testdata file
            input_file = str(project_root / "testdata" / "test_simple.warc")
            if not os.path.exists(input_file):
                print(f"Error: WARC file not found.")
                print("Usage: python convert_to_jsonl.py [path_to_warc_file]")
                sys.exit(1)
    
    # Output file (in same directory as input, with .jsonl extension)
    input_path = Path(input_file)
    output_file = str(input_path.parent / f"{input_path.stem}.jsonl")
    
    print("Converting WARC file to JSONL...")
    print(f"Input file: {input_file}")
    print(f"Output file: {output_file}")
    print("-" * 60)
    
    # Convert WARC to JSONL
    # WARC records contain nested structures (headers, HTTP headers, content)
    # JSONL format preserves all nested data structures
    result = convert(
        fromfile=input_file,
        tofile=output_file,
        silent=True,  # Set to False to show progress (may have issues with some WARC files)
    )
    
    print("-" * 60)
    print("Conversion completed!")
    print(f"WARC records read: {result.rows_in}")
    print(f"JSONL records written: {result.rows_out}")
    print(f"Time elapsed: {result.elapsed_seconds:.2f} seconds")
    if result.errors:
        print(f"Errors: {result.errors}")


if __name__ == "__main__":
    main()
