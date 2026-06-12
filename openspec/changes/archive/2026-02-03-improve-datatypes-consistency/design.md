# Design: Data Types Consistency

## Architectural Changes

### validation-consistency
The base class `BaseIterable` already provides `_apply_validation_hooks`. The design change is largely operational: enforcing its usage across subclasses.
Alternative considered: Template Method Pattern.
-   We could wrap `write` in the base class and call `_write_impl`. However, this would require a breaking change to the inheritance structure of all plugins.
-   **Decision**: Manually update existing subclasses to call `_apply_validation_hooks`. This is less intrusive for now.

### sqlite-optimization
Leverage the standard DBAPI 2.0 `fetchmany` method for `read_bulk`. This avoids the overhead of multiple Python function calls and `fetchone` round-trips (if applicable in the driver).

### topojson-fix
TopoJSON writing currently produces invalid files (concatenated JSON objects instead of a single Topology object).
-   True streaming write for TopoJSON is complex because the `arcs` array is usually separate from `objects`, and efficient encoding requires global knowledge for topology.
-   **Decision**: For `write_bulk`, we will construct a valid minimal Topology object wrapping the geometries. For invalid streaming usage, we should document limitations or warn.

## Implementation Strategy
1.  **Audit**: `grep` for `def write` and check for validation hooks.
2.  **Refactor**: Apply the validation logic standard pattern:
    ```python
    if self._validation_hooks:
        validated = self._apply_validation_hooks(record)
        if validated is None: return
        record = validated
    ```
