# GeoParquet and FlatGeobuf

`GeoParquetIterable` is a metadata-preserving profile over Parquet. Geometry
is exposed as raw WKB unless an application decodes it, and the `geo` schema
metadata records the primary geometry column and CRS.

`FlatGeobufIterable` streams features through Fiona/GDAL and accepts a
`bbox=(minx, miny, maxx, maxy)` selection. It is read-only in this release.
