# Change: Decompose high-complexity core entry points

## Why

Radon rates the core entry points as the highest-risk functions in the codebase: `open_iterable` (F, cyclomatic 91, 255 lines), `convert` (F, 65/333 lines), `bulk_convert` (D, 27/306 lines), and `Pipeline.run` (F, 54). These are the most-exercised code paths and the hardest to test in isolation, and they concentrate broad `except Exception` handling. Decomposing them into named stages reduces regression risk and makes the error-policy work (`update-datatype-error-policy`) tractable.

## What Changes

- Split `open_iterable()` into explicit stages: detect → resolve format/codec → validate source → instantiate → configure engine, each independently testable, preserving the current public signature and behavior.
- Split `convert()` and `bulk_convert()` into read-plan, schema-scan, and write-loop helpers.
- Extract `Pipeline.run()` stage execution into a helper per stage.
- Preserve all observable behavior; this is an internal refactor covered by existing tests plus new unit tests for the extracted stages.
- Reduce each function below cyclomatic complexity C (radon), verified in CI or a dev check.

## Impact

- Affected specs: `open-iterable-structure` (new capability documenting the staged contract), `convert`
- Affected code: `iterable/helpers/open_iterable.py`, `iterable/convert/core.py`, `iterable/pipeline/core.py`, associated tests
- No public API change; behavior preserved and asserted by the existing suite.
