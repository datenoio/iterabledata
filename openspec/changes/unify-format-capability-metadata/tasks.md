## 1. Descriptor schema

- [x] 1.1 Extend `FormatDescriptor` with maturity, memory, native-bulk, selection, codec, and source-constraint fields.
- [x] 1.2 Define enum/tri-state types and a versioned catalog schema.
- [x] 1.3 Add a completeness/audit generator for all canonical descriptors.

## 2. Populate and derive

- [ ] 2.1 Populate install extras and magic signatures for every applicable format.
- [ ] 2.2 Classify API/native bulk, totals, tables, read/write memory, codec composition, selection, maturity, and path/stream/cloud constraints for all built-ins.
- [ ] 2.3 Derive legacy registry, read-only, text, flat, dependency-hint, magic-detection, and docs/catalog structures.
- [ ] 2.4 Remove redundant private metadata tables after equivalence checks pass.

## 3. Capability and catalog APIs

- [ ] 3.1 Replace source-inspection/allowlist capability inference with descriptor values.
- [x] 3.2 Preserve legacy capability keys and add the versioned extended fields.
- [x] 3.3 Add full catalog regeneration/check mode and compatibility documentation.

## 4. Conformance and docs

- [ ] 4.1 Add descriptor uniqueness, alias, import, method ownership, and declared-behavior conformance tests.
- [ ] 4.2 Compare the complete generated catalog and docs matrices with committed outputs.
- [x] 4.3 Document every capability field, enum, and unknown-value policy.
- [ ] 4.4 Run the full suite and OpenSpec strict validation.
