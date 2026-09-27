# Tasks

## 1. Inventory and rollout

- [x] 1.1 Enumerate writable formats lacking `_apply_validation_hooks` from the registry (currently ~64 of ~88).
- [x] 1.2 Wire hooks into each write/write_bulk path, batched by format family.

## 2. Conformance guard

- [x] 2.1 Add a registry-driven conformance test that fails when a writable format bypasses validation hooks.

## 3. Verification

- [x] 3.1 Full serial suite green; hook behavior verified with an error-injection test per family.
- [x] 3.2 CHANGELOG updated; `validation-consistency` spec extended.
