# Change: Add GeoJSON Text Sequence (GeoJSONSeq) format

## Why

The review identified GeoJSON Text Sequences (RFC 8142, `.geojsonl`/`.geojsons`) as a low-effort, high-value geospatial gap: it is the streaming-friendly counterpart to GeoJSON (which is hybrid/full-load for large files) and maps naturally onto the existing JSONL line-oriented reader. Streaming feature-per-line geospatial data is common in tiling and ETL pipelines.

## What Changes

- Add a `geojsonseq` format descriptor and `GeoJSONSeqIterable` that reads one GeoJSON Feature per line (RFC 8142, optionally with the `RS` record separator prefix `\x1e`), yielding each feature as a record.
- Support write: emit one Feature JSON object per line.
- Register extensions `.geojsonl`, `.geojsons`; detect content as a JSON object per line beginning with a `Feature` type.
- True streaming read and write, reusing the JSONL machinery where practical.
- Fixtures and docs.

## Impact

- Affected specs: `geospatial-formats`
- Affected code: `iterable/datatypes/geojsonseq.py` (new), `iterable/helpers/format_registry.py`, `docs/docs/formats/geojsonseq.md`, `tests/test_geojsonseq.py`
- No dependency beyond stdlib `json`; no impact on existing `geojson` format.
