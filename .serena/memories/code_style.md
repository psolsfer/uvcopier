# Code Style & Conventions

## Python Version
- Minimum: Python 3.12 (per user preferences)
- Use modern syntax throughout

## Type Hints
- Always include static typing in all functions/methods
- Use `|` instead of `Union` (e.g., `str | None`)
- Use lowercase generics: `dict[str, Any]`, `list[int]`, `tuple[str, ...]`
- No `from typing import Dict, List, Optional, Union` — use built-ins and `|`

## Docstrings
- NumPy style only
- Only include when asked or when a relevant change is made

## Formatting
- Max line length: **100 characters**
- Formatter: Ruff
- Linter: Ruff

## Naming
- Variables/functions: `snake_case`
- Classes: `PascalCase`
- Constants: `UPPER_SNAKE_CASE`

## Imports
- Standard library first, then third-party, then local

## General
- Prefer f-strings for string formatting
- Use `Path` from `pathlib` instead of `os.path`
- Use `|` for union types in isinstance checks where applicable (Python 3.10+)
