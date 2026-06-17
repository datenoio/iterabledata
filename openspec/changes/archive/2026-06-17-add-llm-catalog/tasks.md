## 1. Extend FormatDescriptor for LLM metadata

- [x] 1.1 Add optional fields to `FormatDescriptor`: `description`, `example_args`, `limitations`, `doc_url`
- [x] 1.2 Update `_fmt()` helper and derivation (no behavior change for legacy structures)
- [x] 1.3 Seed LLM metadata for high-traffic formats (csv, json, jsonl, parquet, xml, xlsx, avro, orc, delta, iceberg)
- [x] 1.4 Seed `example_args` for formats requiring `iterableargs` (xml, protobuf, etc.)
- [x] 1.5 Add tests asserting new fields are accessible via `get_descriptor()`

## 2. iterable.catalog module

- [x] 2.1 Create `iterable/catalog/__init__.py` with public API
- [x] 2.2 Implement `list_formats()` returning sorted format ids and aliases
- [x] 2.3 Implement `describe_format(format_id)` merging descriptor + capabilities
- [x] 2.4 Implement `export_catalog(format="json"|"dict", include_capabilities=True)`
- [x] 2.5 Export from top-level `iterable` package optionally (`from iterable.catalog import describe_format`)
- [x] 2.6 Add `tests/test_catalog.py` with golden snapshot for a subset of formats

## 3. LLM context utilities

- [x] 3.1 Create `iterable/ai/context.py` with `sample_for_llm()`
- [x] 3.2 Implement stratified sampling strategy for large iterables
- [x] 3.3 Implement `redact_for_llm()` with column heuristics (email, phone, ssn, etc.)
- [x] 3.4 Integrate optional Metacrafter PII field list when available
- [x] 3.5 Add `tests/test_ai_context.py`

## 4. CI artifact and doc generation

- [x] 4.1 Add `dev/scripts/export_formats_json.py`
- [x] 4.2 Commit initial `dev/formats.json`
- [x] 4.3 Add CI check: regenerate and diff `dev/formats.json` on registry changes
- [x] 4.4 Add `dev/scripts/generate_format_doc_stubs.py` for undocumented formats
- [x] 4.5 Generate stubs for priority undocumented formats (bam, fasta, fastq, gexf, graphml, gpx, etc.)

## 5. Cursor skill and documentation

- [x] 5.1 Create `.cursor/skills/ai-integration/SKILL.md`
- [x] 5.2 Update `.cursor/skills/README.md` to list ai-integration skill
- [x] 5.3 Add `docs/docs/api/catalog.md` API reference page
- [x] 5.4 Link catalog from `llms.txt` and README

## 6. OpenSpec format-registry delta

- [x] 6.1 Apply MODIFIED descriptor requirement delta on merge/archive of `add-format-metadata-registry`
- [x] 6.2 Ensure `openspec validate add-llm-catalog --strict` passes

## 7. Verification

- [x] 7.1 `pytest tests/test_catalog.py tests/test_ai_context.py tests/test_format_registry.py -v`
- [x] 7.2 `ruff check iterable tests && ruff format --check iterable tests`
- [x] 7.3 `openspec validate add-llm-catalog --strict`
