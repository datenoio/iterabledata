---
sidebar_position: 12
title: Validation
description: Data validation framework with built-in and custom rules
---

# Validation

The `iterable.validate` module provides a framework for validating data against rules and schemas.

## Overview

Validation operations help ensure data quality:
- **Built-in validation rules** (email, URL, Russian identifiers)
- **Custom validator registration** for domain-specific validation
- **Multiple validation modes** (stats, invalid, valid)
- **Streaming validation** for large datasets
- **Detailed error reporting** with context

## Functions

### `iterable()`

Validate rows in an iterable dataset against validation rules.

```python
from iterable import validate

# Basic validation
rules = {"email": ["common.email"], "url": ["common.url"]}
for record, errors in validate.iterable("data.csv", rules):
    if errors:
        print(f"Errors: {errors}")

# Validation with stats
stats = validate.iterable("data.csv", rules, mode="stats")
print(f"Valid: {stats['valid_rows']}, Invalid: {stats['invalid_rows']}")
```

**Parameters:**
- `iterable`: An iterable of row dictionaries, or a file path/stream
- `rules`: Dictionary mapping field names to lists of rule names
  - Example: `{"email": ["common.email", "required"]}`
- `mode`: Validation mode (default: "default")
  - `"default"`: Returns (record, errors) tuples for all rows
  - `"stats"`: Returns validation statistics dictionary
  - `"invalid"`: Returns only rows that failed validation
  - `"valid"`: Returns only rows that passed validation
- `max_errors`: Maximum number of errors to collect before stopping (None for no limit)

**Returns:**
- If `mode="stats"`: Dictionary with validation statistics
- Otherwise: Iterator of (record, errors) tuples where errors is a list of error messages

## Validation Hooks

Validation hooks allow you to automatically validate data during read and write operations, providing fail-fast validation and data quality assurance.

### Basic Usage

```python
from iterable import open_iterable
from iterable.helpers.validation import rules_validator

# Create validation hook
rules = {"email": ["common.email"], "url": ["common.url"]}
hook = rules_validator(rules)

# Use validation hook during iteration
with open_iterable(
    "data.csv",
    iterableargs={"validation_hook": hook, "on_validation_error": "skip"}
) as source:
    for row in source:  # Invalid rows automatically skipped
        process(row)
```

### Error Handling Policies

Validation hooks support four error handling policies:

- `'raise'` (default): Raise exception on validation failure
- `'skip'`: Skip invalid rows, continue processing
- `'log'`: Log errors, continue processing
- `'warn'`: Issue warning, continue processing

```python
# Fail fast on invalid data
with open_iterable("data.csv", iterableargs={"validation_hook": hook, "on_validation_error": "raise"}) as source:
    for row in source:  # Raises on first invalid row
        process(row)

# Skip invalid rows
with open_iterable("data.csv", iterableargs={"validation_hook": hook, "on_validation_error": "skip"}) as source:
    for row in source:  # Invalid rows skipped
        process(row)
```

### Schema Validation Hooks

```python
from iterable.ops import schema
from iterable.helpers.validation import schema_validator

# Infer schema
sch = schema.infer("data.csv")

# Create schema validation hook
hook = schema_validator(sch)

# Use during iteration
with open_iterable("data.csv", iterableargs={"validation_hook": hook}) as source:
    for row in source:  # Automatically validated against schema
        process(row)
```

### Rules Validation Hooks

```python
from iterable.helpers.validation import rules_validator

# Create rules validation hook
rules = {"email": ["common.email"], "age": ["required"]}
hook = rules_validator(rules)

# Use during iteration
with open_iterable("data.csv", iterableargs={"validation_hook": hook}) as source:
    for row in source:  # Automatically validated against rules
        process(row)
```

### Multiple Validation Hooks

You can chain multiple validation hooks:

```python
def validate_schema(row):
    return schema_validator(sch)(row)

def validate_business_rules(row):
    if row["status"] not in ["active", "inactive"]:
        raise ValueError("Invalid status")
    return row

# Chain hooks
with open_iterable(
    "data.csv",
    iterableargs={"validation_hook": [validate_schema, validate_business_rules]}
) as source:
    for row in source:  # Both hooks applied in sequence
        process(row)
```

### Validation During Write

Validation hooks also work during write operations:

```python
def validate_before_write(row):
    if "id" not in row:
        raise ValueError("Row missing required 'id' field")
    return row

with open_iterable(
    "output.jsonl",
    mode="w",
    iterableargs={"validation_hook": validate_before_write, "on_validation_error": "skip"}
) as dest:
    dest.write({"id": 1, "name": "test"})  # Validated before write
    dest.write({"name": "no_id"})  # Skipped (missing id)
```

## Built-in Validation Rules

### Email Validation

```python
from iterable import validate

rules = {"email": ["common.email"]}
for record, errors in validate.iterable("users.csv", rules):
    if errors:
        print(f"Invalid email: {record['email']}")
```

Validates email address format using standard email regex pattern.

### URL Validation

```python
from iterable import validate

rules = {"url": ["common.url"]}
for record, errors in validate.iterable("links.csv", rules):
    if errors:
        print(f"Invalid URL: {record['url']}")
```

Validates URL format (http:// or https://).

### Required Field Validation

```python
from iterable import validate

rules = {"name": ["required"]}
for record, errors in validate.iterable("data.csv", rules):
    if errors:
        print(f"Missing required field: {errors}")
```

Validates that a field is not None or empty string.

### Russian INN Validation

```python
from iterable import validate

rules = {"inn": ["ru.org.inn"]}
for record, errors in validate.iterable("companies.csv", rules):
    if errors:
        print(f"Invalid INN: {record['inn']}")
```

Validates Russian tax identification number (INN) format (10 or 12 digits).

### Russian OGRN Validation

```python
from iterable import validate

rules = {"ogrn": ["ru.org.ogrn"]}
for record, errors in validate.iterable("companies.csv", rules):
    if errors:
        print(f"Invalid OGRN: {record['ogrn']}")
```

Validates Russian state registration number (OGRN) format (13 or 15 digits).

## Custom Validators

### Registering Custom Validators

```python
from iterable.validate import register
from iterable import validate

# Define custom validator
def validate_positive(value):
    """Validate that value is positive."""
    return isinstance(value, (int, float)) and value > 0

# Register the validator
register("positive", validate_positive)

# Use in validation rules
rules = {"price": ["positive"]}
for record, errors in validate.iterable("products.csv", rules):
    if errors:
        print(f"Invalid price: {record['price']}")
```

### Validator with Parameters

```python
from iterable.validate import register

def validate_range(min_val, max_val):
    """Create a validator for a value range."""
    def validator(value):
        return isinstance(value, (int, float)) and min_val <= value <= max_val
    return validator

# Register with specific parameters
register("age_range", validate_range(18, 120))

rules = {"age": ["age_range"]}
```

## Examples

### Basic Validation

```python
from iterable import validate

# Validate email addresses
rules = {"email": ["common.email"]}
for record, errors in validate.iterable("users.csv", rules):
    if errors:
        print(f"User {record.get('id')}: {errors}")
```

### Multiple Rules per Field

```python
from iterable import validate

# Validate email is both required and valid format
rules = {"email": ["required", "common.email"]}
for record, errors in validate.iterable("users.csv", rules):
    if errors:
        print(f"Validation failed: {errors}")
```

### Validation Statistics

```python
from iterable import validate

rules = {"email": ["common.email"], "url": ["common.url"]}
stats = validate.iterable("data.csv", rules, mode="stats")

print(f"Total rows: {stats['total_rows']}")
print(f"Valid rows: {stats['valid_rows']}")
print(f"Invalid rows: {stats['invalid_rows']}")
print(f"Error counts: {stats['error_counts']}")
```

### Filter Invalid Rows

```python
from iterable import validate

rules = {"email": ["common.email"]}
invalid_rows = list(validate.iterable("users.csv", rules, mode="invalid"))

print(f"Found {len(invalid_rows)} invalid rows")
for record, errors in invalid_rows:
    print(f"  {record.get('id')}: {errors}")
```

### Filter Valid Rows

```python
from iterable import validate

rules = {"email": ["common.email"]}
valid_rows = list(validate.iterable("users.csv", rules, mode="valid"))

print(f"Found {len(valid_rows)} valid rows")
# Process only valid rows
for record, errors in valid_rows:
    process(record)
```

### Early Termination

```python
from iterable import validate

# Stop after finding 100 errors
rules = {"email": ["common.email"]}
results = list(validate.iterable("large_file.csv", rules, max_errors=100))

print(f"Checked {len(results)} rows before hitting error limit")
```

### Custom Validation Rules

```python
from iterable.validate import register
from iterable import validate

# Register custom validators
def validate_phone(value):
    """Validate US phone number format."""
    import re
    pattern = r"^\d{3}-\d{3}-\d{4}$"
    return isinstance(value, str) and bool(re.match(pattern, value))

register("us.phone", validate_phone)

# Use custom validator
rules = {"phone": ["us.phone"]}
for record, errors in validate.iterable("contacts.csv", rules):
    if errors:
        print(f"Invalid phone: {record['phone']}")
```

### Combining with Other Operations

```python
from iterable import validate, filter as f, transform

# Filter, validate, then process
filtered = f.filter_expr("data.csv", "`status` == 'active'")
validated = validate.iterable(filtered, {"email": ["common.email"]}, mode="valid")
deduped = transform.deduplicate(validated, keys=["email"])

for record, errors in deduped:
    process(record)
```

## Validation Modes

### Default Mode

Returns all rows with their validation errors:

```python
for record, errors in validate.iterable("data.csv", rules):
    if errors:
        print(f"Row has errors: {errors}")
    else:
        print("Row is valid")
```

### Stats Mode

Returns only statistics, no individual row results:

```python
stats = validate.iterable("data.csv", rules, mode="stats")
print(f"Validation complete: {stats['valid_rows']}/{stats['total_rows']} valid")
```

### Invalid Mode

Returns only rows that failed validation:

```python
invalid = list(validate.iterable("data.csv", rules, mode="invalid"))
for record, errors in invalid:
    print(f"Invalid: {errors}")
```

### Valid Mode

Returns only rows that passed validation:

```python
valid = list(validate.iterable("data.csv", rules, mode="valid"))
for record, errors in valid:
    process(record)  # All records here are valid
```

## Error Reporting

Error messages include:
- **Field name**: Which field failed validation
- **Rule name**: Which rule failed
- **Error message**: Human-readable description

Example error messages:
```
"email: Value failed validation rule 'common.email'"
"name: Value failed validation rule 'required'"
```

## Performance Notes

- **Streaming validation**: Memory usage remains constant regardless of dataset size
- **Early termination**: Use `max_errors` to stop validation early when many errors are found
- **Rule order**: Rules are evaluated in order; first failure stops evaluation for that field (unless all rules need checking)

## Best Practices

1. **Validate early**: Validate data as soon as possible in your pipeline
2. **Use specific rules**: Use the most specific validation rules for your data
3. **Combine rules**: Use multiple rules per field for comprehensive validation
4. **Monitor statistics**: Use stats mode to understand data quality at scale
5. **Custom validators**: Register domain-specific validators for reusable validation logic
