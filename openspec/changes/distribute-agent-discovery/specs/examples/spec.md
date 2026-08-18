## ADDED Requirements

### Requirement: Gzip, JSONL write, and sample cookbook scripts
The cookbook SHALL include short runnable scripts for reading a gzip CSV,
writing JSONL, and sampling rows via `iterable.tools.read_sample`, using only
canonical public imports.

#### Scenario: Gzip read cookbook runs on a committed fixture
- **WHEN** the gzip-read cookbook script is invoked on a committed `.csv.gz` fixture
- **THEN** it yields at least one dict row without loading pandas

#### Scenario: JSONL write cookbook produces a file
- **WHEN** the JSONL-write cookbook script is invoked with a destination path
- **THEN** the destination exists and contains at least one JSON object per line

#### Scenario: Sample cookbook uses tools.read_sample
- **WHEN** the sample cookbook script is invoked on a committed CSV fixture
- **THEN** it returns a successful tool envelope with a list of row dicts
