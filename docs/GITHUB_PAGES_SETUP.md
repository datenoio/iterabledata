# GitHub Pages Deployment Setup

This document describes how the Iterable Data documentation is deployed to GitHub Pages at `https://datenoio.github.io/iterabledata/`.

## Prerequisites

1. The repository `datenoio/iterabledata` (this repository)
2. GitHub Pages enabled in repository settings with "GitHub Actions" as the source

## Configuration

The documentation is configured in `docs/docusaurus.config.js` for project-site deployment from this repository:

- **URL**: `https://datenoio.github.io`
- **Base URL**: `/iterabledata/`
- **Organization**: `datenoio`
- **Project**: `iterabledata`

The published site is available at `https://datenoio.github.io/iterabledata/`.

## Setup Steps

1. **Enable GitHub Pages**:
   - Go to the repository settings on GitHub
   - Navigate to **Pages** in the left sidebar
   - Under **Source**, select **GitHub Actions** as the source
   - This will automatically create the `github-pages` environment

2. **Push to main branch**:
   - The GitHub Actions workflow (`.github/workflows/deploy-docs.yml`) will automatically:
     - Build the Docusaurus site when changes are pushed to `main`
     - Deploy to GitHub Pages
   - The workflow triggers on:
     - Pushes to `main` branch that affect files in `docs/` directory
     - Manual workflow dispatch

3. **Verify deployment**:
   - After the workflow completes, the site will be available at `https://datenoio.github.io/iterabledata/`
   - The deployment typically takes 1-2 minutes

## Moving to a Custom Domain or User Site

If the documentation should later live at a root domain (e.g. `iterabledata.github.io` or a custom domain), update `docusaurus.config.js`:

```javascript
url: 'https://your-domain.example',
baseUrl: '/',
organizationName: '<org>',
projectName: '<repo>',
```

and configure the domain in the repository's Pages settings.

## Manual Deployment

You can also deploy manually using the Docusaurus CLI:

```bash
cd docs
npm install
npm run build
npm run deploy
```

This requires the `GITHUB_TOKEN` environment variable to be set with appropriate permissions.

## Troubleshooting

- **Environment error**: If you see an error about the `github-pages` environment, make sure GitHub Pages is enabled in your repository settings with "GitHub Actions" as the source
- **Build failures**: Check the GitHub Actions logs for specific error messages
- **404 errors**: Verify the `baseUrl` in `docusaurus.config.js` matches your repository structure
