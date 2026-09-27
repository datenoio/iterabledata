# Tasks

## 1. Example plugin

- [ ] 1.1 Create `examples/plugins/iterabledata-example/` with a minimal format (or codec) plugin, entry-point metadata, and its own README.

## 2. End-to-end proof

- [ ] 2.1 Test that pip-installs the example into a throwaway venv and verifies discovery plus `open_iterable()` round-trip.
- [ ] 2.2 Keep the test self-contained (no network; pip install from local path).

## 3. Docs and verification

- [ ] 3.1 Plugin author guide references the example; CHANGELOG updated.
- [ ] 3.2 Full serial suite green; plugin test skips cleanly when venv creation is unavailable.
