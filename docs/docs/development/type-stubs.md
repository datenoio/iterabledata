# Type Stubs for Optional Dependencies

This document lists type stubs available for optional dependencies used by IterableData.

## Type Stubs Installed

The following type stub packages are installed as development dependencies:

- **types-chardet**: Type stubs for `chardet` (character encoding detection)
- **types-openpyxl**: Type stubs for `openpyxl` (Excel XLSX format)
- **types-pyyaml**: Type stubs for `pyyaml` (YAML format)
- **types-requests**: Type stubs for `requests` (HTTP library, used by AI features)
- **types-python-dateutil**: Type stubs for `python-dateutil` (date parsing)
- **types-setuptools**: Type stubs for `setuptools` (build system)

## Packages with Separate Type Stub Packages

The following packages have type stubs available as separate packages (should be added to dev dependencies):

- **pandas**: `pandas-stubs` (separate package, maintained by pandas team)
- **pyarrow**: `pyarrow-stubs` (separate package)
- **lxml**: `lxml-stubs` (available on GitHub, may need to be added)

## Packages with Built-in Type Stubs

The following packages include type stubs in their main distribution:

- **pydantic**: Built-in type stubs (PEP 561 compliant)
- **duckdb**: Built-in type stubs (PEP 561 compliant)

## Packages Without Type Stubs

The following optional dependencies do not have type stubs available and are configured with `ignore_missing_imports = true` in mypy configuration:

- **pyorc**: ORC format support
- **lxml**: XML/HTML parsing
- **pymongo**: MongoDB support
- **h5py**: HDF5 format support
- **netCDF4**: NetCDF format support
- **pyreadstat**: SAS/Stata/SPSS format support
- **protobuf**: Protocol Buffers support
- **msgpack**: MessagePack format support
- **warcio**: WARC format support
- **dpkt**: PCAP format support
- **ijson**: Streaming JSON parser
- **feedparser**: RSS/Atom feed parsing
- **beautifulsoup4**: HTML parsing
- **ezdxf**: DXF format support
- **mapbox-vector-tile**: MVT format support
- **topojson**: TopoJSON format support
- **fiona**: Geospatial format support
- **pyshp**: Shapefile format support
- **geojson**: GeoJSON format support
- **vortex-data**: Vortex format support
- **paimon-mosaic**: Paimon Mosaic format support
- **pypaimon**: Apache Paimon table support
- **pyducklake**: DuckLake table format support
- **zstandard**: Paimon Row format support (also used by compression codecs)
- **laspy**: LAS LiDAR format support
- **segyio**: SEG-Y seismic format support
- **cfgrib** / **xarray**: GRIB2 meteorological format support
- **obspy**: miniSEED seismological format support
- **access-parser**: Microsoft Access (MDB/ACCDB) format support
- **fst**: R fst columnar format support
- **hdt**: RDF HDT compact triple store support
- **spacepy**: NASA CDF format support
- **pyxlsb**: Excel Binary (XLSB) format support
- **networkx**: GraphML / GEXF / DOT format support
- **pysam**: BAM / SAM alignment format support
- **scipy**: MATLAB MAT format support
- **ion-python**: Ion format support
- **avro-python3**: Avro format support
- **pycapnp**: Cap'n Proto format support
- **flatbuffers**: FlatBuffers format support
- **thrift**: Apache Thrift format support
- **deltalake**: Delta Lake format support
- **pyiceberg**: Apache Iceberg format support
- **pyhudi**: Apache Hudi format support
- **lance**: Lance format support
- **rdflib**: RDF format support
- **vobject**: VCF/iCal format support
- **icalendar**: iCal format support
- **liac-arff**: ARFF format support
- **dbfread**: DBF format support
- **xlrd**: Excel XLS format support
- **odfpy**: ODS format support
- **tomli/tomli-w**: TOML format support
- **toml**: TOML format support (alternative)
- **pyhocon**: HOCON format support
- **edn_format/pyedn**: EDN format support
- **py-ubjson**: UBJSON format support
- **cbor2/cbor**: CBOR format support
- **smile-json**: SMILE format support
- **flexbuffers**: FlexBuffers format support
- **pyasn1**: ASN.1 format support
- **bencode/bencodepy**: Bencode format support
- **pyreadr**: RData/RDS format support
- **psycopg2-binary**: PostgreSQL support
- **pymysql**: MySQL support
- **pyodbc**: SQL Server support
- **clickhouse-connect**: ClickHouse support
- **elasticsearch**: Elasticsearch support
- **kafka-python**: Kafka support
- **pulsar-client**: Pulsar support
- **fsspec**: Cloud storage support
- **s3fs**: S3 support
- **gcsfs**: GCS support
- **adlfs**: Azure support
- **openai**: OpenAI API support

## Mypy Configuration

The mypy configuration in `pyproject.toml` includes:

1. **Per-module overrides** for optional dependencies:
   ```toml
   [[tool.mypy.overrides]]
   module = [
       "iterable.datatypes.*",
       "iterable.codecs.*",
       "iterable.db.*",
       "iterable.engines.*",
   ]
   ignore_missing_imports = true
   ```

2. This allows type checking to work even when optional dependencies are not installed.

## Adding New Type Stubs

When adding support for a new optional dependency:

1. Check if type stubs are available:
   - Search PyPI for `types-<package-name>`
   - Check if the package includes built-in type stubs (PEP 561)

2. If type stubs are available:
   - Add `types-<package-name>` to `dev` dependencies in `pyproject.toml`
   - Remove the module from `ignore_missing_imports` override if it was there

3. If type stubs are not available:
   - The module will continue to use `ignore_missing_imports = true`
   - Consider contributing type stubs to the typeshed project or creating a `types-*` package

## Benefits

Type stubs provide:

- **Better IDE support**: Autocomplete and type checking in IDEs
- **Static type checking**: Catch type errors before runtime
- **Documentation**: Type stubs serve as inline documentation
- **Refactoring safety**: IDEs can safely refactor code with type information

## Resources

- [PEP 561 - Distributing and Packaging Type Information](https://peps.python.org/pep-0561/)
- [typeshed - Collection of type stubs](https://github.com/python/typeshed)
- [mypy documentation](https://mypy.readthedocs.io/)
