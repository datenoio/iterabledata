# Iterable Data Documentation

This directory contains the Docusaurus documentation site for Iterable Data.

## Development

### Prerequisites

- Node.js 18+ and npm

### Installation

```bash
cd docs
npm install
```

### Local Development

Start the development server:

```bash
npm start
```

This starts a local development server and opens up a browser window. Most changes are reflected live without having to restart the server.

### Build

Build the site for production:

```bash
npm run build
```

This generates static content into the `build` directory and can be served using any static contents hosting service.

### Serve

Serve the built site locally:

```bash
npm run serve
```

## Project Structure

```
docs/
├── docusaurus.config.js    # Docusaurus configuration
├── sidebars.js              # Sidebar navigation
├── package.json             # Node.js dependencies
├── babel.config.js          # Babel configuration
├── LICENSE                  # CC BY 4.0 notice for documentation
├── src/
│   ├── css/
│   │   └── custom.css       # Custom styles
│   ├── pages/
│   │   └── index.js         # Homepage (documentation contents)
│   └── components/          # React components
├── static/img/              # Logo and favicon
└── docs/                    # Documentation content
    ├── getting-started/     # Getting started guides
    ├── use-cases/          # Use case examples
    ├── api/                # API documentation
    ├── formats/            # Format documentation
    └── license.md          # License and attribution
```

## Deployment

The documentation is automatically deployed to GitHub Pages at [datenoio.github.io/iterabledata](https://datenoio.github.io/iterabledata/) when changes are pushed to the `main` branch. The deployment is handled by the GitHub Actions workflow in `.github/workflows/deploy-docs.yml`.

### GitHub Pages Setup

To enable GitHub Pages deployment:

1. Go to your repository settings on GitHub
2. Navigate to **Pages** in the left sidebar
3. Under **Source**, select **GitHub Actions** as the source
4. The workflow will automatically build and deploy the docs when you push to `main`

**Note**: The site is published as a project site at `https://datenoio.github.io/iterabledata/`. If the repository is renamed or moved, adjust `url`, `baseUrl`, `organizationName`, and `projectName` in `docusaurus.config.js` accordingly (see `GITHUB_PAGES_SETUP.md`).

## Documentation Structure

- **Getting Started**: Installation, quick start, and basic usage
- **Use Cases**: Real-world examples and use cases
- **API Reference**: Complete API documentation
- **Data File Formats**: Documentation for all supported formats
- **License**: MIT for code; CC BY 4.0 for documentation and data

## Contributing

When adding or updating documentation:

1. Edit the markdown files in the `docs/` directory
2. Follow the existing frontmatter format
3. Test locally with `npm start`
4. Commit and push changes
