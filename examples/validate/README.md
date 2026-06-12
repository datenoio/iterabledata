# Validate examples

Validate rows in an iterable against rules (email, url, required, etc.) using `iterable.validate.iterable`.

## Scripts

- **validate_example.py** – Validate a CSV with rules and print invalid rows or stats.

## Run

```bash
python examples/validate/validate_example.py [path/to/data.csv]
```

## API

```python
from iterable import validate

rules = {
    "email": ["common.email", "required"],
    "url": ["common.url"],
}
for record, errors in validate.iterable("data.csv", rules):
    if errors:
        print(record, errors)
```

Modes: `default` (yield (row, errors)), `stats` (return stats dict), `invalid` (only invalid rows), `valid` (only valid rows).
