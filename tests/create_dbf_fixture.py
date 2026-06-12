#!/usr/bin/env python3
"""
Script to create a DBF test fixture file matching the 2cols6rows pattern.

Usage:
    cd tests
    python create_dbf_fixture.py

Or from project root:
    python tests/create_dbf_fixture.py

Requires: pip install dbf
"""

import os
import sys

# Only import dbf when script is run directly, not when imported
if __name__ == "__main__":
    try:
        import dbf  # noqa: F401
    except ImportError:
        print("Error: 'dbf' package is required to create DBF files.")
        print("Install it with: pip install dbf")
        sys.exit(1)


def create_dbf_fixture():
    """Create a DBF file with the same data as other fixtures"""
    # Import here to avoid import errors when script is imported
    import dbf

    # noqa: F401
    from fixdata import FIXTURES
    # noqa: F401

    # Get the directory where this script is located
    script_dir = os.path.dirname(os.path.abspath(__file__))
    fixture_path = os.path.join(script_dir, "fixtures", "2cols6rows.dbf")

    # Ensure fixtures directory exists
    fixtures_dir = os.path.join(script_dir, "fixtures")
    os.makedirs(fixtures_dir, exist_ok=True)

    # Remove existing file if it exists
    if os.path.exists(fixture_path):
        os.remove(fixture_path)

    # Define the table structure: id (Numeric, 3 digits) and name (Character, 20 chars)
    table = dbf.Table(filename=fixture_path, field_specs="id N(3,0); name C(20)", on_disk=True)

    # Open the table in read-write mode
    table.open(dbf.READ_WRITE)

    # Add records from FIXTURES
    for record in FIXTURES:
        # Convert id from string to int
        id_value = int(record["id"])
        name_value = record["name"]
        table.append((id_value, name_value))

    # Close the table
    table.close()

    print(f"Created DBF fixture: {fixture_path}")
    print(f"Added {len(FIXTURES)} records")


if __name__ == "__main__":
    create_dbf_fixture()
