## 1. Protocol and negotiation

- [x] 1.1 Define optional native batch reader/writer protocols and capability checks.
- [x] 1.2 Define a typed selection request for columns, predicates, tables/variables, row ranges, slices, and batch size.
- [x] 1.3 Define adapter compatibility, schema negotiation, ownership, fallback, and strict-mode errors.
- [x] 1.4 Add debug/observability reporting for selected conversion path and pushed operations.

## 2. Conversion integration

- [x] 2.1 Add native-path selection to `convert()` without changing its row fallback.
- [x] 2.2 Preserve metrics, errors, progress, atomic output, and cleanup on both paths.
- [x] 2.3 Disable native transfer when flattening, row validation, or other row-only transforms require materialization.

## 3. Backend adapters

- [x] 3.1 Implement Parquet and Arrow IPC/Feather v2 native batch readers and writers.
- [ ] 3.2 Implement ORC batch adaptation where the supported backend permits it.
- [ ] 3.3 Add projection/filter pushdown for Parquet and supported lakehouse scanners.
- [ ] 3.4 Add table/variable/slice pushdown for selected HDF5, NetCDF, and NumPy paths.
- [ ] 3.5 Add Lance, Delta, and Iceberg adapters with documented version requirements.

## 4. Tests and documentation

- [ ] 4.1 Add native-versus-row equivalence tests for nulls, nested data, dates, and schema alignment.
- [x] 4.2 Add fallback and strict unsupported-selection tests.
- [ ] 4.3 Add throughput and peak-memory benchmarks for columnar-to-columnar conversion.
- [x] 4.4 Document the advanced batch API, selection options, supported matrix, and diagnostics.
- [ ] 4.5 Run representative optional-dependency jobs and full regression checks.
