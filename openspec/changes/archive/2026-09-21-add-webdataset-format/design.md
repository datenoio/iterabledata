## Context

WebDataset stores samples in TAR archives where members share a key prefix and differ by extension (`0001.jpg`, `0001.json`). IterableData's TAR iterable currently yields members individually; this change groups them into samples.

## Goals / Non-Goals

- Goals:
  - Yield one dict per sample key with suffix keys mapped to bytes or decoded payloads.
  - Work with `.tar`, `.tar.gz`/`.tgz`, and related codec compositions already supported.
- Non-Goals:
  - Full Distributed WebDataset training loader features (reshuffling across many nodes, pipe handlers).
  - Automatic image decoding into arrays (bytes + optional decoder hooks are enough).

## Decisions

### Grouping

Members are grouped by basename without final extension. Each sample dict maps extension/suffix → payload. A `__key__` field stores the sample key.

### Decoding

Default payloads are raw bytes. Optional per-suffix decoders (e.g. `json` → dict, `txt` → str) MAY be configured via iterable args without making them mandatory.

### Relationship to TAR

`format="webdataset"` selects sample grouping. Plain `tar` remains member-oriented. Detection MAY use explicit format or `.wds`/shard naming conventions documented in the format page.

## Risks / Trade-offs

- Incomplete trailing groups at shard end → yield partial sample only if configured; default fail or warn as documented.
- Large binary payloads → keep streaming; do not buffer entire shard.

## Migration Plan

Add experimental profile. No change to default TAR behavior.

## Open Questions

- Auto-detect WebDataset layout from TAR content heuristics, or require explicit format?
- Include write API that emits canonical key.suffix members in v1?
