#!/usr/bin/env python3
"""
Script to create compression test fixtures for Snappy and LZO codecs.
Run this after installing python-snappy and python-lzo.
"""

import os

fixtures_dir = os.path.join(os.path.dirname(__file__), "fixtures")
source_file = os.path.join(fixtures_dir, "2cols6rows.csv")

# Read the source CSV file
with open(source_file, "rb") as f:
    csv_data = f.read()

print("Creating Snappy fixture...")
try:
    import snappy
    # noqa: F401

    compressed = snappy.compress(csv_data)
    snappy_file = os.path.join(fixtures_dir, "2cols6rows.csv.snappy")
    with open(snappy_file, "wb") as f:
        f.write(compressed)
    print(f"Created: {snappy_file}")
except ImportError:
    print("python-snappy not installed, skipping Snappy fixture")
except Exception as e:
    print(f"Error creating Snappy fixture: {e}")

print("Creating LZO fixture...")
try:
    import lzo
    # noqa: F401

    compressed = lzo.compress(csv_data, 1)  # compression level 1
    lzo_file = os.path.join(fixtures_dir, "2cols6rows.csv.lzo")
    with open(lzo_file, "wb") as f:
        f.write(compressed)
    print(f"Created: {lzo_file}")
except ImportError:
    print("python-lzo not installed, skipping LZO fixture")
except Exception as e:
    print(f"Error creating LZO fixture: {e}")

print("Done!")
