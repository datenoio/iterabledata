# Zarr

`ZarrIterable` reads Zarr v2/v3 directory stores in bounded chunks. A store
with multiple arrays must be opened with `iterableargs={"array": "name"}`;
rows are exposed as `{"value": ...}`. Writes append chunk-sized blocks and
require `iterabledata[zarr]`.
