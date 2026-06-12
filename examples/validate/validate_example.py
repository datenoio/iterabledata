"""
Example: Validate rows with rules (email, required, etc.).

Uses iterable.validate.iterable with a rules dict.
Run: python examples/validate/validate_example.py [path/to/data.csv]
"""

import os
import sys
import tempfile

from iterable import validate


def main():
    path = sys.argv[1] if len(sys.argv) > 1 else None
    if not path or not os.path.isfile(path):
        print("No file provided or file not found. Using minimal demo CSV.")
        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
            f.write("email,name\ninvalid,Alice\nuser@example.com,Bob\n")
            path = f.name

    rules = {"email": ["common.email"]}
    print("Validation (rules: email = common.email):")
    invalid_count = 0
    for record, errors in validate.iterable(path, rules):
        if errors:
            invalid_count += 1
            print(f"  Invalid: {record} -> {errors}")
    print(f"Invalid rows: {invalid_count}")

    print("\nValidation stats:")
    stats = validate.iterable(path, rules, mode="stats")
    print(stats)


if __name__ == "__main__":
    main()
