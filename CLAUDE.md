# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Repository Overview

This is a documentation and utilities repository written primarily in French. It contains:
- AsciiDoc (`.adoc`) documentation files covering various computing topics
- Python utility scripts and Jupyter notebooks
- Antora configuration for building documentation sites

## Key Commands

### Antora Documentation Build

Build the Antora documentation site:
```bash
cd docs
npx antora antora-playbook.yml
```
Output is generated to `docs/build/`.

## Architecture

### Documentation Structure

- **`docs/`**: Antora documentation site (source of truth), with a `modules/<topic>/pages/` per topic (git, python, linux, docker, asciidoc, ai, jwt, information-theory, roadmap, ...) and `docs/modules/ROOT/nav.adoc` for navigation
- **Topic directories** (`python/`, `asciidoc/`, etc.) at the repo root: reusable code/snippets referenced from the README, separate from the `docs/` narrative content

### Python Utilities

- **`python/`**: Various Python examples and notebooks organized by topic (dataframe, pdf, json, folium, etc.)
- Each Python subdirectory typically has its own `env/` virtual environment
- The AsciiDoc link checker that used to live in `scripts/adoc_link_check/` moved to its own
  dedicated repo, `~/repos/adoc-link-checker` — use that repo, not a copy in `utils`

### Conventions

- Documentation is written in AsciiDoc format (`.adoc`)
- Use `:toc:` and `:sectnums:` attributes in AsciiDoc files
- French language is used for documentation content
