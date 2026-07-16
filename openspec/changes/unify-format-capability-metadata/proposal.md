# Change: Unify Format Capability Metadata

## Why

Format metadata is nominally declarative but remains fragmented across descriptors, allowlists, source inspection, magic-signature tables, install-extra maps, and documentation metadata. Most descriptors omit dependency and magic data, compression is inferred optimistically, and API bulk support is not distinguished from native batching or memory behavior.

## What Changes

- Make the format descriptor the authoritative source for installation, detection, capability, maturity, memory, and source-constraint metadata.
- Populate every built-in descriptor explicitly and derive legacy registries/lists/catalogs/docs from it.
- Replace optimistic source-inspection heuristics with declared values plus conformance tests.
- Add native-bulk, read/write memory, projection/selection, path/stream/cloud, maturity, and codec-composition capability fields.
- Version the exported catalog schema and use `unknown`/`None` when a capability is not established.

## Dependencies

- Archive `update-format-dependency-metadata` and `update-streaming-capability-truth` before implementation.
- Coordinate memory/native-bulk values with `optimize-format-io-hot-paths` and `add-native-batch-conversion`.

## Impact

- Affected specs: `format-registry`, `format-capabilities`
- Affected code: descriptor definitions, detection registries, capability helpers, catalog export, docs generation, install hints
- Compatibility: legacy registry/list names remain available; catalog consumers receive a schema version and additional fields
