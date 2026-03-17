# uvcopier — Project Overview

## Purpose
A **Copier template** for creating Python packages managed with `uv`. It generates fully configured Python project skeletons with:
- uv-based dependency management
- Ruff (linting + formatting) or Black
- MyPy / Pydantic for type checking
- pytest + tox for testing
- MkDocs + Material theme for documentation
- Commitizen for versioning/changelog
- GitHub Actions CI/CD workflows
- Optional CLI (Click, Typer, argparse)

## Tech Stack
- **Python**: >=3.10 (supports 3.10–3.13)
- **Template engine**: Copier + Jinja2
- **Dependency management**: uv
- **Testing**: pytest, tox, tox-uv
- **Linting/Formatting**: Ruff
- **Type checking**: MyPy
- **Docs**: MkDocs + Material
- **Task runner**: Invoke (tasks.py)
- **Versioning**: Commitizen

## Project Structure
```
uvcopier/
├── template/           # The actual Copier template (Jinja2 files)
│   ├── src/
│   ├── tests/
│   ├── .github/
│   ├── pyproject.toml.jinja
│   ├── tasks.py.jinja
│   └── ...
├── template_tests/     # Tests for the template itself
├── tests/              # pytest tests for this project
│   ├── conftest.py
│   ├── test_template.py
│   └── test_edge_cases.py
├── docs/               # MkDocs documentation source
├── tasks.py            # Invoke tasks for development
├── copier.yml          # Copier configuration / prompts
├── pyproject.toml
└── tox.ini
```
