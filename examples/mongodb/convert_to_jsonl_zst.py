"""
Example: Convert MongoDB collection to JSONL.ZST file with maximum compression.

This example demonstrates how to convert a MongoDB collection to a ZStandard-compressed
JSONL file using maximum compression level and a progress bar.
"""

from iterable import open_iterable
from tqdm import tqdm


def main():
    """Convert MongoDB collection to JSONL.ZST file with maximum compression."""
    # MongoDB connection string
    connection_string = "mongodb://localhost:27017/"

    # Output file with .zst extension (auto-detects ZST compression)
    output_file = "inddata.jsonl.zst"

    print("Converting MongoDB collection 'unicef.inddata' to JSONL.ZST...")
    print(f"Output file: {output_file}")
    print("Using maximum compression level (22)")
    print("-" * 60)

    # Open MongoDB collection as source
    # Using database 'unicef' and collection 'inddata' as specified
    with open_iterable(
        connection_string,
        engine="mongo",
        iterableargs={
            "database": "unicef",
            "collection": "inddata",
        },
    ) as source:
        # Open JSONL.ZST file with maximum compression
        # compression_level=22 is the maximum for ZStandard (ultra mode)
        # Note: Higher compression levels are slower but produce smaller files
        # Note: Streaming compression (writing line-by-line) may produce slightly larger
        # files than one-shot compression (e.g., zstd -22 file.jsonl) due to reduced
        # cross-chunk compression opportunities. This is expected behavior for streaming.
        with open_iterable(
            output_file,
            mode="w",
            codecargs={"compression_level": 22},  # Maximum compression (0-22, default is 0)
        ) as destination:
            # Verify compression level is set correctly
            if hasattr(destination, "codec") and hasattr(destination.codec, "compression_level"):
                actual_level = destination.codec.compression_level
                if actual_level != 22:
                    print(f"Warning: Expected compression level 22, but got {actual_level}")
                else:
                    print(f"Compression level verified: {actual_level} (maximum)")
            # Get total count if available for progress bar
            total = None
            try:
                if source.has_totals():
                    total = source.totals()
            except Exception:
                pass

            # Convert with progress bar
            count = 0
            if total:
                # Use total for accurate progress
                with tqdm(total=total, desc="Converting", unit="doc") as pbar:
                    for doc in source:
                        destination.write(doc)
                        count += 1
                        pbar.update(1)
            else:
                # No total available, show count only
                with tqdm(desc="Converting", unit="doc") as pbar:
                    for doc in source:
                        destination.write(doc)
                        count += 1
                        pbar.update(1)

    print("-" * 60)
    print("Conversion completed!")
    print(f"Documents converted: {count}")
    print(f"Output file: {output_file} (ZStandard compressed with level 22)")


if __name__ == "__main__":
    main()
