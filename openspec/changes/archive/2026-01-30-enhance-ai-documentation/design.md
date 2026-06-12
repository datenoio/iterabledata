# Design: Enhance AI Documentation Generation

## Context

### Background

IterableData currently provides basic AI-powered documentation generation via `iterable.ai.doc.generate()`, which uses LLM providers to generate markdown documentation from schema and sample data. However, after reviewing undatum's more comprehensive `doc` command implementation, we identified significant opportunities to enhance IterableData's documentation generation with:

- Structured metadata extraction (keywords, geographic/temporal coverage, languages, data themes)
- Field-level AI descriptions
- Semantic type detection and PII identification
- Enhanced statistics integration
- Additional output formats
- Better error handling and reliability

### Constraints

- **Backward compatibility**: All changes must be backward compatible - existing API calls must continue to work
- **Optional dependencies**: New features should gracefully degrade when optional dependencies are missing
- **Performance**: Documentation generation should remain efficient, with caching where appropriate
- **Token costs**: Prompt engineering must optimize token usage to minimize API costs
- **Memory efficiency**: Must maintain IterableData's streaming-first approach

### Stakeholders

- **End users**: Data analysts, data engineers who need comprehensive dataset documentation
- **Developers**: Contributors maintaining and extending the codebase
- **Integrators**: Users building tools on top of IterableData

## Goals / Non-Goals

### Goals

1. **Comprehensive metadata extraction** - Extract structured metadata (keywords, geographic/temporal coverage, languages, data themes) from datasets
2. **Field-level documentation** - Generate individual field descriptions using AI
3. **Semantic awareness** - Integrate semantic type detection and PII identification
4. **Enhanced statistics** - Better integration with DuckDB-based statistics
5. **Multiple output formats** - Support YAML and plain text in addition to existing formats
6. **Robust error handling** - Retry logic, graceful degradation, comprehensive error reporting
7. **Better prompts** - Optimized prompt engineering with structured context
8. **Seamless integration** - Better integration with `ops.stats` and `ops.schema`

### Non-Goals

1. **Breaking changes** - No breaking changes to existing API
2. **Mandatory dependencies** - No new mandatory dependencies (all new dependencies optional)
3. **CLI tool** - Not creating a CLI command (focusing on library API)
4. **Real-time updates** - Not implementing incremental documentation updates
5. **Multi-dataset** - Not implementing batch documentation for multiple datasets (can be done via loops)

## Decisions

### Decision 1: Metadata Extraction Architecture

**Decision**: Implement metadata extraction as separate utility functions that can be called independently or integrated into documentation generation.

**Rationale**: 
- Allows reuse across different contexts
- Enables testing in isolation
- Supports graceful degradation (can skip if dependencies missing)
- Follows single responsibility principle

**Alternatives considered**:
- Embedding extraction directly in `generate()` - rejected because it reduces flexibility and testability
- External service/API - rejected because it adds complexity and dependencies

**Implementation**: Create `iterable/ai/metadata.py` with extraction functions:
- `extract_keywords(field_names, samples, max_keywords=15) -> list[str]`
- `extract_geographic_coverage(samples, field_names) -> dict[str, Any]`
- `extract_temporal_coverage(samples, field_names) -> dict[str, Any] | None`
- `detect_languages(samples, field_names) -> list[dict[str, Any]]`
- `classify_data_theme(field_names, keywords) -> dict[str, str] | None`

### Decision 2: Field-Level Documentation API

**Decision**: Add `get_fields_info()` method to provider abstraction layer, and add `include_field_descriptions` parameter to `doc.generate()`.

**Rationale**:
- Consistent with undatum's approach
- Allows field descriptions to be generated independently
- Provider abstraction handles implementation differences
- Optional feature (defaults to False for backward compatibility)

**Alternatives considered**:
- Separate function `doc.generate_field_descriptions()` - rejected because it duplicates provider logic
- Always generate field descriptions - rejected because it increases API costs and time

**Implementation**:
- Add `get_fields_info(fields: list[str], language: str = 'English') -> dict[str, str]` to `LLMProvider` base class
- Implement in all provider classes
- Add `include_field_descriptions: bool = False` parameter to `doc.generate()`

### Decision 3: Semantic Types and PII Detection

**Decision**: Integrate with Metacrafter CLI tool (external dependency) with graceful fallback when unavailable.

**Rationale**:
- Metacrafter is a proven tool for semantic type detection
- External CLI tool keeps dependencies optional
- Graceful fallback ensures core functionality works without it
- Can be extended to support other tools in the future

**Alternatives considered**:
- Built-in semantic type detection - rejected because it's complex and would require ML models
- Required dependency - rejected because it adds mandatory external tool requirement
- Different tool - considered but Metacrafter is well-established

**Implementation**:
- Add `semantic_types: bool = False` and `pii_detect: bool = False` parameters
- Create `iterable/ai/semantic.py` with Metacrafter integration
- Implement graceful fallback when Metacrafter unavailable
- Add `pii_mask_samples: bool = False` for masking PII in sample data

### Decision 4: Statistics Integration

**Decision**: Integrate with `ops.stats.compute()` when DuckDB is available, use results to enhance documentation and field descriptions.

**Rationale**:
- Leverages existing statistics functionality
- DuckDB provides fast, accurate statistics
- Statistics enhance AI-generated descriptions
- Optional - falls back gracefully when DuckDB unavailable

**Alternatives considered**:
- Reimplement statistics in doc module - rejected because it duplicates existing functionality
- Always require DuckDB - rejected because it adds mandatory dependency

**Implementation**:
- Add `include_statistics: bool = True` parameter (default True for better docs)
- Call `ops.stats.compute()` when available
- Include statistics in prompt context
- Add statistics section to documentation output

### Decision 5: Output Format Implementation

**Decision**: Add YAML and plain text formats using existing patterns, extend `_format_as_*` functions.

**Rationale**:
- Consistent with existing format implementation pattern
- YAML useful for structured metadata
- Plain text useful for simple terminal output
- Minimal code changes required

**Alternatives considered**:
- Separate formatting module - rejected because current approach is simple and works
- Template-based formatting - rejected because it adds unnecessary complexity

**Implementation**:
- Add `_format_as_yaml()` function
- Add `_format_as_text()` function
- Extend format parameter validation
- Update documentation

### Decision 6: Error Handling Strategy

**Decision**: Implement retry logic with exponential backoff for API calls, graceful degradation for optional features.

**Rationale**:
- API calls can fail due to rate limits, network issues, timeouts
- Retry logic improves reliability
- Graceful degradation ensures core functionality works even if optional features fail
- Follows best practices for external API integration

**Alternatives considered**:
- No retry logic - rejected because it reduces reliability
- User-provided retry logic - rejected because it adds complexity for users
- Fail-fast approach - rejected because it reduces usability

**Implementation**:
- Create `iterable/ai/utils.py` with `retry_with_backoff()` function
- Implement retry logic in provider `generate()` methods
- Add try/except blocks around optional features with logging
- Return partial results when possible

### Decision 7: Prompt Engineering

**Decision**: Enhance prompts with structured metadata, statistics, and better organization while optimizing token usage.

**Rationale**:
- Better context leads to better documentation
- Structured metadata improves accuracy
- Token optimization reduces costs
- Follows prompt engineering best practices

**Alternatives considered**:
- Simple prompts - rejected because they produce lower quality documentation
- Very detailed prompts - rejected because they increase token costs significantly

**Implementation**:
- Enhance `_build_documentation_prompt()` with structured sections
- Include metadata, statistics, schema, samples in organized format
- Add prompt templates for different use cases
- Truncate large samples/data to stay within token limits

## Architecture

### Component Structure

```
iterable/ai/
├── __init__.py           # Public API exports
├── doc.py                # Main documentation generation (MODIFIED)
├── providers.py          # Provider abstraction (MODIFIED - add get_fields_info)
├── metadata.py           # Metadata extraction utilities (NEW)
├── semantic.py           # Semantic types and PII detection (NEW)
└── utils.py              # Retry logic and utilities (NEW)
```

### Data Flow

```
User calls doc.generate()
    │
    ├─> Open iterable (if file path)
    │
    ├─> Extract samples (if include_samples=True)
    │
    ├─> Infer schema (if include_schema=True)
    │
    ├─> Compute statistics (if include_statistics=True, DuckDB available)
    │
    ├─> Extract metadata (keywords, geographic, temporal, languages, themes)
    │
    ├─> Detect semantic types (if semantic_types=True, Metacrafter available)
    │
    ├─> Detect PII (if pii_detect=True, Metacrafter available)
    │
    ├─> Mask PII in samples (if pii_mask_samples=True)
    │
    ├─> Generate field descriptions (if include_field_descriptions=True)
    │
    ├─> Build enhanced prompt with all context
    │
    ├─> Call LLM provider (with retry logic)
    │
    ├─> Format output (markdown/json/html/yaml/text)
    │
    └─> Return documentation
```

### Integration Points

1. **ops.schema**: Used for schema inference (`schema.infer()`)
2. **ops.stats**: Used for statistics computation (`stats.compute()`)
3. **helpers.detect**: Used for file type detection and opening iterables
4. **ai.providers**: Extended with `get_fields_info()` method

## API Design

### Enhanced `doc.generate()` Signature

```python
def generate(
    iterable: collections.abc.Iterable[Row] | str,
    provider: str = "openai",
    model: str | None = None,
    format: str = "markdown",  # Extended: "markdown", "json", "html", "yaml", "text"
    api_key: str | None = None,
    base_url: str | None = None,
    include_schema: bool = True,
    include_samples: bool = True,
    sample_size: int = 5,
    temperature: float = 0.7,
    max_tokens: int | None = None,
    # New parameters:
    include_field_descriptions: bool = False,
    include_statistics: bool = True,
    include_metadata: bool = True,  # Enable metadata extraction
    semantic_types: bool = False,  # Enable semantic type detection
    pii_detect: bool = False,  # Enable PII detection
    pii_mask_samples: bool = False,  # Mask PII in sample data
    language: str = "English",  # Language for AI-generated content
    **kwargs: Any,
) -> str | dict[str, Any]:
```

### New `metadata` Module Functions

```python
def extract_keywords(
    field_names: list[str],
    samples: list[Row] | None = None,
    max_keywords: int = 15
) -> list[str]:
    """Extract keywords from field names and sample data."""

def extract_geographic_coverage(
    samples: list[Row],
    field_names: list[str]
) -> dict[str, Any]:
    """Extract geographic coverage information."""

def extract_temporal_coverage(
    samples: list[Row],
    field_names: list[str]
) -> dict[str, Any] | None:
    """Extract temporal coverage information."""

def detect_languages(
    samples: list[Row],
    field_names: list[str]
) -> list[dict[str, Any]]:
    """Detect languages in text fields."""

def classify_data_theme(
    field_names: list[str],
    keywords: list[str]
) -> dict[str, str] | None:
    """Classify data theme based on field names and keywords."""
```

### Enhanced Provider Interface

```python
class LLMProvider(ABC):
    @abstractmethod
    def generate(...) -> str:
        """Existing method."""
    
    @abstractmethod
    def get_usage_info(...) -> dict[str, Any] | None:
        """Existing method."""
    
    @abstractmethod
    def get_fields_info(
        self,
        fields: list[str],
        language: str = "English"
    ) -> dict[str, str]:
        """NEW: Get field descriptions."""
```

## Performance Considerations

### Caching Strategy

1. **Schema caching**: Cache inferred schemas per file (hash-based key)
2. **Statistics caching**: Cache computed statistics per file
3. **Metadata caching**: Cache extracted metadata per file
4. **Field descriptions caching**: Cache field descriptions per (fields, language) combination

**Implementation**: Use `functools.lru_cache` with appropriate cache sizes, or file-based caching for expensive operations.

### Token Optimization

1. **Truncate samples**: Limit sample size and truncate long text values
2. **Selective inclusion**: Only include relevant metadata in prompts
3. **Prompt templates**: Use efficient prompt structures
4. **Batch field descriptions**: Generate multiple field descriptions in single API call when possible

### Memory Efficiency

1. **Streaming samples**: Use iterator pattern for sample collection
2. **Lazy evaluation**: Only extract metadata when requested
3. **Clear large objects**: Explicitly clear large data structures after use

## Error Handling

### Retry Logic

```python
def retry_with_backoff(
    func: Callable,
    max_retries: int = 3,
    initial_delay: float = 1.0,
    backoff_factor: float = 2.0,
    retry_statuses: tuple = (429, 500, 502, 503, 504)
) -> Any:
    """Retry function with exponential backoff."""
```

**Behavior**:
- Retry on rate limit (429) and server errors (5xx)
- Exponential backoff with jitter
- Respect `Retry-After` header when present
- Raise `AIAPIError` after max retries

### Graceful Degradation

1. **Missing dependencies**: Log warning, continue without feature
2. **Metacrafter unavailable**: Skip semantic types/PII detection, continue
3. **DuckDB unavailable**: Skip statistics, continue
4. **API failures**: Retry with backoff, raise error only after retries exhausted
5. **Partial failures**: Return partial results when possible

### Error Types

```python
class AIAPIError(Exception):
    """Base exception for AI API errors."""
    status_code: int | None
    response: str | None

class AIConfigurationError(AIAPIError):
    """Configuration errors."""

class AIRetryExhaustedError(AIAPIError):
    """All retries exhausted."""
```

## Dependencies

### New Optional Dependencies

1. **langdetect** - Language detection (`pip install langdetect`)
   - Used for: Language detection in text fields
   - Fallback: Skip language detection if unavailable

2. **pandas** - Already optional, used for temporal coverage analysis
   - Used for: Date parsing and temporal coverage extraction
   - Fallback: Skip temporal coverage if unavailable

3. **metacrafter** - External CLI tool (not Python package)
   - Used for: Semantic type detection and PII identification
   - Fallback: Skip semantic types/PII if unavailable
   - Installation: External tool, checked via `shutil.which()`

### Dependency Management

- All new dependencies are optional
- Graceful degradation when dependencies missing
- Clear error messages with installation instructions
- Document in `pyproject.toml` optional dependencies section

## Migration Plan

### Backward Compatibility

1. **API compatibility**: All existing `doc.generate()` calls continue to work
2. **Default behavior**: New features default to False/disabled
3. **Return format**: Existing return formats unchanged
4. **Error handling**: Existing error types preserved, new types extend base

### Migration Steps

1. **Phase 1**: Add new optional parameters (defaults preserve existing behavior)
2. **Phase 2**: Implement metadata extraction utilities
3. **Phase 3**: Add field-level documentation support
4. **Phase 4**: Add semantic types and PII detection
5. **Phase 5**: Enhance output formats
6. **Phase 6**: Add retry logic and error handling improvements
7. **Phase 7**: Update documentation and examples

### Testing Strategy

1. **Unit tests**: Test each metadata extraction function independently
2. **Integration tests**: Test full documentation generation with various configurations
3. **Backward compatibility tests**: Ensure existing API calls still work
4. **Error handling tests**: Test retry logic, graceful degradation
5. **Performance tests**: Measure token usage, execution time

## Risks / Trade-offs

### Risk 1: Increased API Costs

**Risk**: More comprehensive prompts and field descriptions increase token usage and costs.

**Mitigation**:
- Make field descriptions optional (default False)
- Optimize prompts for token efficiency
- Cache expensive operations
- Provide cost estimation in usage info

**Trade-off**: Better documentation vs. higher costs - users can control via parameters

### Risk 2: External Tool Dependency (Metacrafter)

**Risk**: Metacrafter may not be installed or available, reducing functionality.

**Mitigation**:
- Make semantic types/PII optional (default False)
- Graceful fallback when unavailable
- Clear documentation on installation
- Consider alternative tools in future

**Trade-off**: Rich semantic information vs. external dependency - optional feature

### Risk 3: Performance Impact

**Risk**: Additional metadata extraction and API calls slow down documentation generation.

**Mitigation**:
- Make expensive operations optional
- Implement caching
- Use efficient algorithms
- Parallelize independent operations where possible

**Trade-off**: Comprehensive documentation vs. speed - users can disable features

### Risk 4: Prompt Engineering Complexity

**Risk**: Complex prompts may produce inconsistent or lower-quality results.

**Mitigation**:
- Test prompts with various datasets
- Provide prompt templates
- Allow customization via parameters
- Iterate based on user feedback

**Trade-off**: Rich context vs. prompt complexity - balance through testing

## Open Questions

1. **Caching strategy**: Should we implement file-based caching or in-memory only? (Decision: Start with in-memory, add file-based if needed)

2. **Field description batching**: Should we batch multiple field descriptions in single API call? (Decision: Yes, implement batching for efficiency)

3. **Metadata extraction order**: Should metadata extraction happen before or after AI generation? (Decision: Before - use metadata to enhance prompts)

4. **Statistics integration**: Should statistics be computed even when DuckDB unavailable? (Decision: Yes, use Python fallback from `ops.stats`)

5. **PII masking format**: What format should masked PII use? (Decision: Use "***" for consistency with undatum)

6. **YAML library**: Which YAML library to use? (Decision: Use `pyyaml` if available, fallback to JSON representation)

7. **Language detection sample size**: How many text samples needed for reliable detection? (Decision: Use 50 samples minimum, as in undatum)

8. **Data theme taxonomy**: Should we use EU data themes or create custom taxonomy? (Decision: Start with EU data themes, allow customization later)

## Implementation Notes

### Code Organization

- Keep metadata extraction pure functions (no side effects)
- Use type hints throughout
- Follow existing code style (ruff formatting)
- Add comprehensive docstrings

### Testing Approach

- Test each metadata extraction function with various inputs
- Test error handling and retry logic
- Test graceful degradation scenarios
- Test backward compatibility
- Mock external dependencies in tests

### Documentation Updates

- Update `docs/docs/api/ai.md` with new parameters and features
- Add examples for new capabilities
- Document optional dependencies
- Add migration guide if needed

### Performance Monitoring

- Track token usage in usage info
- Log execution time for expensive operations
- Monitor cache hit rates
- Profile prompt construction time
