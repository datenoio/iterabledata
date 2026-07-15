# Change: Harden untrusted-input handling (XXE, eval, pickle)

## Why

The 2026-07-14 review and a Bandit scan (0 high, 34 medium) surfaced input-security patterns that are risky when processing untrusted data: lxml parsing without XXE protection (`xml.py:66`, `kml.py`, `gml.py`, `kmz.py:105` use `lxml.etree.parse/iterparse` with no entity/network restrictions and no `defusedxml`), `eval()` for type resolution in `iterable/helpers/validation.py:138`, `eval()` for filter expressions in `iterable/ops/filter.py:117`, and `pickle.load` in `iterable/datatypes/picklef.py` without a documented trust warning.

## What Changes

- XML: disable external entity resolution and network access on all lxml parsers (`resolve_entities=False`, `no_network=True`, or a hardened `XMLParser`), or route parsing through `defusedxml`. Applies to `xml.py`, `kml.py`, `gml.py`, `kmz.py`, and any other lxml call sites.
- Validation: replace `eval(python_type)` in `validation.py:138` with an explicit type-name lookup table (no `eval`).
- Filter: keep `filter_expr` behavior but tighten the evaluator so only whitelisted AST node types are permitted, and add a test asserting injection attempts are rejected (strengthens the existing `ops-filter` safety requirement).
- Pickle: add an explicit untrusted-input warning to the `picklef` class docstring and format documentation; optionally gate loading behind an explicit `trust=True` argument.
- Add security regression tests: an XXE payload does not read external entities; a malicious filter expression is rejected; validation type resolution no longer uses `eval`.

## Impact

- Affected specs: `input-security` (new capability), `ops-filter` (modified safety requirement)
- Affected code: `iterable/datatypes/xml.py`, `kml.py`, `gml.py`, `kmz.py`, `iterable/helpers/validation.py`, `iterable/ops/filter.py`, `iterable/datatypes/picklef.py`, tests
- Behavior change: XML with external entities will no longer resolve them (secure default); documented as a security fix.
