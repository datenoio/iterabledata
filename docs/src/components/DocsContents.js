import React from 'react';
import Link from '@docusaurus/Link';
import styles from './DocsContents.module.css';

const sections = [
  {
    title: 'Getting Started',
    to: '/getting-started/installation',
    description: 'Install the library and learn the basic streaming workflow.',
    links: [
      {label: 'Installation', to: '/getting-started/installation'},
      {label: 'Quick start', to: '/getting-started/quick-start'},
      {label: 'When to use', to: '/getting-started/when-to-use'},
      {label: 'Cookbook', to: '/getting-started/cookbook'},
      {label: 'Basic usage', to: '/getting-started/basic-usage'},
      {label: 'Performance', to: '/getting-started/performance'},
      {label: 'Troubleshooting', to: '/getting-started/troubleshooting'},
      {label: 'Migration guide', to: '/getting-started/migration-guide'},
      {label: 'Best practices', to: '/getting-started/best-practices'},
    ],
  },
  {
    title: 'AI & agents',
    to: '/integrations/BUILDING_AGENTS',
    description: 'Tooling, MCP, discovery indexes, and LLM documentation.',
    links: [
      {label: 'Building agents', to: '/integrations/BUILDING_AGENTS'},
      {label: 'Cookbook', to: '/getting-started/cookbook'},
      {label: 'MCP server', to: '/integrations/MCP'},
      {label: 'Agent discovery', to: '/integrations/DISCOVERY'},
      {label: 'Directory submissions', to: '/integrations/DIRECTORY_SUBMISSIONS'},
      {label: 'Agent tools', to: '/api/tools'},
      {label: 'Catalog', to: '/api/catalog'},
      {label: 'AI documentation', to: '/api/ai'},
    ],
  },
  {
    title: 'Use Cases',
    to: '/use-cases/format-conversion',
    description: 'End-to-end examples for conversion, pipelines, and DuckDB.',
    links: [
      {label: 'Format conversion', to: '/use-cases/format-conversion'},
      {label: 'Data pipelines', to: '/use-cases/data-pipelines'},
      {label: 'Wikipedia processing', to: '/use-cases/wikipedia-processing'},
      {label: 'DuckDB integration', to: '/use-cases/duckdb-integration'},
      {label: 'WARC to Parquet', to: '/use-cases/warc-to-parquet'},
    ],
  },
  {
    title: 'API Reference',
    to: '/api/open-iterable',
    description: 'Python API for opening, converting, inspecting, and transforming data.',
    links: [
      {label: 'open_iterable()', to: '/api/open-iterable'},
      {label: 'convert()', to: '/api/convert'},
      {label: 'Pipeline', to: '/api/pipeline'},
      {label: 'Engines', to: '/api/engines'},
      {label: 'Inspect / stats / schema', to: '/api/ops-inspect'},
      {label: 'Transform / filter', to: '/api/ops-transform'},
      {label: 'Validate / ingest', to: '/api/validate'},
      {label: 'Codecs', to: '/api/codecs'},
      {label: 'Cloud storage', to: '/api/cloud-storage'},
      {label: 'Database engines', to: '/api/database-engines'},
    ],
  },
  {
    title: 'Data File Formats',
    to: '/formats/',
    description: 'Per-format pages for 100+ readers and writers.',
    links: [
      {label: 'All formats', to: '/formats/'},
      {label: 'CSV', to: '/formats/csv'},
      {label: 'JSON / JSONL', to: '/formats/jsonl'},
      {label: 'Parquet', to: '/formats/parquet'},
      {label: 'XML', to: '/formats/xml'},
      {label: 'Excel', to: '/formats/xlsx'},
      {label: 'GeoJSON', to: '/formats/geojson'},
      {label: 'WARC', to: '/formats/warc'},
    ],
  },
  {
    title: 'Development',
    to: '/development/releasing',
    description: 'Release process, type stubs, and contributing notes.',
    links: [
      {label: 'Releasing', to: '/development/releasing'},
      {label: 'Type stubs', to: '/development/type-stubs'},
      {label: 'License', to: '/license'},
    ],
  },
];

function Section({title, to, description, links}) {
  return (
    <article className={styles.card}>
      <h3 className={styles.cardTitle}>
        <Link to={to}>{title}</Link>
      </h3>
      <p className={styles.cardDescription}>{description}</p>
      <ul className={styles.linkList}>
        {links.map((item) => (
          <li key={item.to}>
            <Link to={item.to}>{item.label}</Link>
          </li>
        ))}
      </ul>
    </article>
  );
}

export default function DocsContents() {
  return (
    <section className={styles.contents}>
      <div className="container">
        <h2 className={styles.heading}>Documentation contents</h2>
        <p className={styles.intro}>
          Start with a section below, or use the sidebar from any page. The PyPI package is{' '}
          <code>iterabledata</code>; the import package is <code>iterable</code>.
        </p>
        <div className={styles.grid}>
          {sections.map((section) => (
            <Section key={section.title} {...section} />
          ))}
        </div>
      </div>
    </section>
  );
}
