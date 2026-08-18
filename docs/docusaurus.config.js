// @ts-check
// Note: type annotations allow type checking and IDEs autocompletion

const lightCodeTheme = require('prism-react-renderer').themes.github;
const darkCodeTheme = require('prism-react-renderer').themes.dracula;

/** @type {import('@docusaurus/types').Config} */
const config = {
  title: 'Iterable Data',
  tagline: 'Unified API for reading and writing data files',
  favicon: 'img/favicon.ico',

  // Set the production url of your site here
  url: 'https://datenoio.github.io',
  // Set the /<baseUrl>/ pathname under which your site is served
  // For GitHub pages deployments, it is often '/<projectName>/'
  baseUrl: '/iterabledata/',

  // GitHub pages deployment config.
  organizationName: 'datenoio',
  projectName: 'iterabledata',
  deploymentBranch: 'gh-pages',
  trailingSlash: false,

  onBrokenLinks: 'throw',
  markdown: {
    hooks: {
      onBrokenMarkdownLinks: 'warn',
    },
  },

  // Even if you don't use internationalization, you can use this field to set
  // useful metadata like html lang. For example, if your site is Chinese, you
  // may want to replace "en" with "zh-Hans".
  i18n: {
    defaultLocale: 'en',
    locales: ['en'],
  },

  presets: [
    [
      'classic',
      /** @type {import('@docusaurus/preset-classic').Options} */
      ({
        docs: {
          sidebarPath: require.resolve('./sidebars.js'),
          // Please change this to your repo.
          // Remove this to remove the "edit this page" links.
          editUrl: 'https://github.com/datenoio/iterabledata/tree/main/',
          routeBasePath: '/',
        },
        blog: false,
        theme: {
          customCss: require.resolve('./src/css/custom.css'),
        },
      }),
    ],
  ],

  themeConfig:
    /** @type {import('@docusaurus/preset-classic').ThemeConfig} */
    ({
      // Replace with your project's social card
      image: 'img/docusaurus-social-card.jpg',
      navbar: {
        title: 'Iterable Data',
        logo: {
          alt: 'Iterable Data Logo',
          src: 'img/logo.svg',
        },
        items: [
          {
            type: 'docSidebar',
            sidebarId: 'docs',
            position: 'left',
            label: 'Documentation',
          },
          {
            to: '/getting-started/cookbook',
            label: 'Cookbook',
            position: 'left',
          },
          {
            href: 'https://datenoio.github.io/iterabledata/llms.txt',
            label: 'llms.txt',
            position: 'right',
          },
          {
            href: 'https://github.com/datenoio/iterabledata',
            label: 'GitHub',
            position: 'right',
          },
        ],
      },
      footer: {
        style: 'dark',
        links: [
          {
            title: 'Docs',
            items: [
              {
                label: 'Getting Started',
                to: '/getting-started/installation',
              },
              {
                label: 'API Reference',
                to: '/api/open-iterable',
              },
              {
                label: 'Data Formats',
                to: '/formats/',
              },
              {
                label: 'Cookbook',
                to: '/getting-started/cookbook',
              },
            ],
          },
          {
            title: 'For coding agents',
            items: [
              {
                label: 'llms.txt',
                href: 'https://datenoio.github.io/iterabledata/llms.txt',
              },
              {
                label: 'llms-full.txt',
                href: 'https://datenoio.github.io/iterabledata/llms-full.txt',
              },
              {
                label: 'Building agents',
                to: '/integrations/BUILDING_AGENTS',
              },
              {
                label: 'Agent discovery',
                to: '/integrations/DISCOVERY',
              },
            ],
          },
          {
            title: 'Community',
            items: [
              {
                label: 'GitHub',
                href: 'https://github.com/datenoio/iterabledata',
              },
            ],
          },
        ],
        copyright: `Copyright © ${new Date().getFullYear()} Iterable Data. Built with Docusaurus.`,
      },
      prism: {
        theme: lightCodeTheme,
        darkTheme: darkCodeTheme,
        additionalLanguages: ['python', 'bash'],
      },
    }),
};

module.exports = config;
