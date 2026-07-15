## MODIFIED Requirements

### Requirement: Filter Expression Safety
The system SHALL ensure that filter expressions cannot execute arbitrary code or access unsafe operations. Expression evaluation SHALL be restricted to a whitelist of abstract-syntax-tree node types (field access, literals, comparisons, and boolean/arithmetic operators); attribute access to Python objects, function/method calls, imports, and attribute dunder access SHALL be rejected before any row is processed.

#### Scenario: Safe expression evaluation
- **WHEN** `filter.filter_expr()` is called with any expression
- **THEN** expression evaluation is restricted to safe operations
- **AND** arbitrary code execution is prevented
- **AND** only field access, comparisons, and basic operators are allowed

#### Scenario: Malformed expression handling
- **WHEN** `filter.filter_expr()` is called with an invalid expression
- **THEN** the function raises a clear error message
- **AND** the error indicates the problem with the expression
- **AND** no partial filtering occurs

#### Scenario: Injection attempt is rejected
- **WHEN** `filter.filter_expr()` is called with an expression containing a disallowed node (e.g. a function call, import, or attribute access such as `__class__`)
- **THEN** the evaluator SHALL raise a validation error before processing any row
- **AND** SHALL NOT execute the disallowed operation
