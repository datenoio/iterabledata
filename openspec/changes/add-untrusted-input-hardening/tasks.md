## 1. XML XXE hardening

- [x] 1.1 Introduce a shared hardened lxml parser factory (`resolve_entities=False`, `no_network=True`, no DTD load) or adopt `defusedxml`
- [x] 1.2 Apply it in `xml.py`, `kml.py`, `gml.py`, `kmz.py` and any other lxml call sites
- [x] 1.3 Add an XXE regression test proving external entities are not resolved

## 2. Remove eval in validation

- [x] 2.1 Replace `eval(python_type)` in `validation.py:138` with an explicit type-name map
- [x] 2.2 Test type resolution for all supported type names, including rejection of unknown names

## 3. Filter evaluator whitelist

- [x] 3.1 Restrict `ops/filter.py` expression evaluation to a whitelist of AST node types
- [x] 3.2 Add tests asserting injection attempts (attribute access, calls, imports) are rejected

## 4. Pickle trust

- [x] 4.1 Document untrusted-input risk in `picklef.py` docstring and `docs/docs/formats/pickle.md`
- [x] 4.2 Optionally require an explicit `trust=True` to load pickle sources (warning emitted on read unless `trust=True` is passed)

## 5. Verify

- [x] 5.1 Run `bandit -r iterable -ll` and confirm the addressed findings are resolved
- [x] 5.2 Run full test suite and lint
