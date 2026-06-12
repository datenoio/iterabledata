# Change: Enhance AI Documentation Generation

## Why

The current AI documentation generation in IterableData (`iterable.ai.doc.generate()`) provides basic functionality but lacks the comprehensive metadata extraction and robust features found in undatum's `doc` command. After reviewing both implementations, IterableData's AI documentation can be significantly improved to provide:

1. **Structured metadata extraction** - Title, keywords, geographic/temporal coverage, languages, data themes
2. **Semantic type detection** - Integration with tools like Metacrafter for field-level semantic annotations
3. **PII detection** - Privacy-aware documentation with PII field identification and masking
4. **Enhanced statistics integration** - Better use of DuckDB-based statistics for comprehensive documentation
5. **Field-level documentation** - Individual field descriptions beyond dataset-level overview
6. **More robust prompt engineering** - Better structured prompts that leverage all available context
7. **Additional output formats** - Support for YAML and plain text formats
8. **Better error handling** - Retry logic, graceful degradation, and comprehensive error reporting

This enhancement will make IterableData's AI documentation generation more comprehensive, production-ready, and competitive with best-in-class tools.

## What Changes

- **ADDED**: Structured metadata extraction (title, keywords, geographic coverage, temporal coverage, languages, data themes)
- **ADDED**: Field-level documentation generation via `get_fields_info()` method
- **ADDED**: Semantic type detection integration (Metacrafter or similar)
- **ADDED**: PII detection and masking capabilities
- **ADDED**: Enhanced statistics integration using DuckDB-based analysis
- **ADDED**: YAML and plain text output formats
- **MODIFIED**: Enhanced prompt engineering with structured metadata context
- **MODIFIED**: Improved error handling with retry logic and graceful degradation
- **MODIFIED**: Better integration with `ops.stats` and `ops.schema` operations

## Impact

- **Affected specs**: `specs/ai/spec.md` - AI documentation generation requirements
- **Affected code**: 
  - `iterable/ai/doc.py` - Main documentation generation logic
  - `iterable/ai/providers.py` - Provider abstraction (may need enhancements)
  - `iterable/ops/stats.py` - Statistics integration
  - `iterable/ops/schema.py` - Schema integration
- **New dependencies**: 
  - Optional: `metacrafter` CLI tool for semantic types (external dependency)
  - Optional: `langdetect` for language detection
  - Optional: `pandas` for temporal coverage analysis (already optional)
- **Breaking changes**: None - all additions are backward compatible

## Comparison with Undatum

### Undatum Strengths (to adopt):
- Comprehensive metadata extraction (geographic, temporal, languages, themes)
- Metacrafter integration for semantic types and PII
- Field-level AI descriptions via `get_fields_info()`
- Structured metadata via `get_structured_metadata()` method
- Better statistics integration
- Multiple output formats (markdown, text, JSON, YAML)
- Robust error handling

### IterableData Strengths (to preserve):
- Clean API design with `doc.generate()`
- Good provider abstraction layer
- HTML output format support
- Clean separation of concerns

### Key Improvements Needed:
1. Add structured metadata extraction similar to undatum's approach
2. Implement field-level documentation generation
3. Add semantic type and PII detection capabilities
4. Enhance prompt engineering with better context
5. Improve statistics integration
6. Add YAML and text output formats
7. Better error handling and retry logic
