/**
 * Creating a sidebar enables you to:
 - create an ordered group of docs
 - render a sidebar for each doc of that group
 - provide next/previous navigation

 The sidebars can be generated from the filesystem, or explicitly defined here.

 Create as many sidebars as you want.
 */

// @ts-check

/** @type {import('@docusaurus/plugin-content-docs').SidebarsConfig} */
const sidebars = {
  docs: [
    {
      type: 'category',
      label: 'Getting Started',
      items: [
        'getting-started/installation',
        'getting-started/quick-start',
        'getting-started/basic-usage',
        'getting-started/performance',
        'getting-started/troubleshooting',
        'getting-started/migration-guide',
        'getting-started/best-practices',
      ],
    },
    {
      type: 'category',
      label: 'Use Cases',
      items: [
        'use-cases/format-conversion',
        'use-cases/data-pipelines',
        'use-cases/wikipedia-processing',
        'use-cases/duckdb-integration',
        'use-cases/warc-to-parquet',
      ],
    },
    {
      type: 'category',
      label: 'API Reference',
      items: [
        'api/open-iterable',
        'api/convert',
        'api/pipeline',
        'api/engines',
        'api/base-iterable',
        'api/capabilities',
        'api/exceptions',
        'api/ops-inspect',
        'api/ops-stats',
        'api/ops-transform',
        'api/ops-filter',
        'api/ops-schema',
        'api/validate',
        'api/ingest',
        'api/ai',
        'api/catalog',
        'api/tools',
        'api/type-system',
      ],
    },
    {
      type: 'category',
      label: 'Data File Formats',
      items: [
        'formats/index',
        {
          type: 'category',
          label: 'Tabular Formats',
          items: [
            'formats/csv',
            'formats/psv',
            'formats/ssv',
            'formats/fwf',
            'formats/xls',
            'formats/xlsx',
            'formats/ods',
            'formats/dbf',
            'formats/csvw',
          ],
        },
        {
          type: 'category',
          label: 'JSON Formats',
          items: [
            'formats/json',
            'formats/jsonl',
            'formats/jsonld',
            'formats/geojson',
            'formats/ubjson',
            'formats/smile',
          ],
        },
        {
          type: 'category',
          label: 'Binary Formats',
          items: [
            'formats/parquet',
            'formats/avro',
            'formats/orc',
            'formats/arrow',
            'formats/lance',
            'formats/bson',
            'formats/msgpack',
            'formats/cbor',
            'formats/pickle',
          ],
        },
        {
          type: 'category',
          label: 'Statistical Formats',
          items: [
            'formats/sas',
            'formats/stata',
            'formats/spss',
            'formats/hdf5',
            'formats/rdata',
            'formats/rds',
            'formats/px',
          ],
        },
        {
          type: 'category',
          label: 'Columnar Storage',
          items: [
            'formats/parquet',
            'formats/orc',
            'formats/arrow',
            'formats/lance',
            'formats/delta',
            'formats/iceberg',
            'formats/hudi',
          ],
          collapsed: true,
        },
        {
          type: 'category',
          label: 'Serialization Formats',
          items: [
            'formats/protobuf',
            'formats/capnp',
            'formats/thrift',
            'formats/flatbuffers',
            'formats/flexbuffers',
          ],
        },
        {
          type: 'category',
          label: 'XML/RDF Formats',
          items: [
            'formats/xml',
            'formats/rdfxml',
            'formats/turtle',
            'formats/ntriples',
            'formats/nquads',
          ],
        },
        {
          type: 'category',
          label: 'Geospatial Formats',
          items: [
            'formats/geojson',
            'formats/kml',
            'formats/gml',
            'formats/shapefile',
            'formats/geopackage',
            'formats/csvw',
          ],
        },
        {
          type: 'category',
          label: 'Log Formats',
          items: [
            'formats/apachelog',
            'formats/gelf',
            'formats/cef',
            'formats/ilp',
          ],
        },
        {
          type: 'category',
          label: 'Web Formats',
          items: [
            'formats/warc',
            'formats/cdx',
            'formats/mhtml',
          ],
        },
        {
          type: 'category',
          label: 'Email Formats',
          items: [
            'formats/eml',
            'formats/mbox',
          ],
        },
        {
          type: 'category',
          label: 'Configuration Formats',
          items: [
            'formats/yaml',
            'formats/toml',
            'formats/ini',
            'formats/hocon',
            'formats/edn',
          ],
        },
        {
          type: 'category',
          label: 'Database Formats',
          items: [
            'formats/sqlite',
            'formats/duckdb',
            'formats/mysqldump',
            'formats/pgcopy',
          ],
        },
        {
          type: 'category',
          label: 'Other Formats',
          items: [
            'formats/ical',
            'formats/vcf',
            'formats/ldif',
            'formats/asn1',
            'formats/bencode',
            'formats/tfrecord',
            'formats/sequencefile',
            'formats/txt',
            'formats/ltsv',
            'formats/annotatedcsv',
            'formats/ion',
            'formats/recordio',
            'formats/kafka',
            'formats/pulsar',
            'formats/flink',
            'formats/beam',
          ],
        },
      ],
    },
  ],
};

module.exports = sidebars;
