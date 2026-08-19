import React from 'react';
import useBaseUrl from '@docusaurus/useBaseUrl';
import useDocusaurusContext from '@docusaurus/useDocusaurusContext';
import Layout from '@theme/Layout';
import DocsContents from '@site/src/components/DocsContents';

import styles from './index.module.css';

function HomepageHeader() {
  const {siteConfig} = useDocusaurusContext();
  const logoSrc = useBaseUrl('img/logo.svg');
  return (
    <header className={styles.hero}>
      <div className="container">
        <img className={styles.heroLogo} src={logoSrc} alt="" width="72" height="72" />
        <h1 className={styles.heroTitle}>{siteConfig.title}</h1>
        <p className={styles.heroTagline}>{siteConfig.tagline}</p>
        <p className={styles.heroNote}>
          Part of the{' '}
          <a href="https://dateno.io" target="_blank" rel="noopener noreferrer">
            Dateno
          </a>{' '}
          open-source project.
        </p>
        <pre className={styles.install}>
          <code>pip install iterabledata{'\n'}from iterable import open_iterable</code>
        </pre>
      </div>
    </header>
  );
}

export default function Home() {
  const {siteConfig} = useDocusaurusContext();
  return (
    <Layout
      title="Documentation"
      description={siteConfig.tagline}>
      <HomepageHeader />
      <main>
        <DocsContents />
      </main>
    </Layout>
  );
}
