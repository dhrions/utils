# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Repository Overview

This is a documentation and utilities repository written primarily in French. It contains:
- AsciiDoc (`.adoc`) documentation files covering various computing topics
- Python utility scripts and Jupyter notebooks
- Antora configuration for building documentation sites

## Key Commands

### AsciiDoc Link Checker

Check broken links in AsciiDoc files:
```bash
cd scripts/adoc_link_check
pip install -r requirements.txt
python cli.py [directory] [--timeout 15] [--max-workers 5] [--verbose]
```

### Antora Documentation Build

Build the Antora documentation site:
```bash
cd antora
npx antora antora-playbook.yml
```
Output is generated to `antora/build/`.

## Architecture

### Documentation Structure

- **Topic directories** (`python/`, `linux/`, `git/`, `docker/`, etc.): Each contains a `README.adoc` with documentation on that topic
- **`computing-learner-roadmap/`**: Educational roadmap with subdirectories for dev, ops, sec, signals, and self-hosted content
- **`antora/`**: Antora documentation site configuration with `modules/` containing structured content

### Python Utilities

- **`scripts/adoc_link_check/`**: CLI tool to verify links in AsciiDoc files (uses Click framework)
- **`python/`**: Various Python examples and notebooks organized by topic (dataframe, pdf, json, folium, etc.)
- Each Python subdirectory typically has its own `env/` virtual environment

### Conventions

- Documentation is written in AsciiDoc format (`.adoc`)
- Use `:toc:` and `:sectnums:` attributes in AsciiDoc files
- French language is used for documentation content
