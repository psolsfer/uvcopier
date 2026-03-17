# Suggested Commands

All commands use `uv run` as the runner. On Windows, `pty=False` is used automatically.

## Testing
```
uv run pytest                          # Quick test run with default Python
uv run tox -e py311                    # Run tests in a specific tox env
uv run tox                             # Run tests across all Python versions
```

## Linting & Formatting
```
uv run ruff check hooks/ tests/        # Lint (check only, no fixes)
uv run ruff check --no-fix hooks/ tests/  # Lint (no fix)
uv run ruff format --check hooks/ tests/  # Format check
uv run ruff format hooks/ tests/       # Format (apply)
uv run mypy --junit-xml reports/mypy.xml .  # Type checking
```

## Invoke tasks (shorthand)
```
uv run invoke test                     # Run tox (py311)
uv run invoke test-pytest              # Run pytest directly
uv run invoke test-all                 # Run all tox envs
uv run invoke lint                     # Lint + format + type check
uv run invoke lint-ruff                # Ruff lint only
uv run invoke format-ruff              # Ruff format only
uv run invoke type-check               # MyPy only
uv run invoke docs                     # Build docs
uv run invoke coverage                 # Run coverage
```

## Documentation
```
uv run mkdocs build                    # Build docs
uv run mkdocs serve                    # Serve docs locally
```

## Git / Versioning
```
git log --oneline
cz commit                              # Commitizen commit
cz bump                                # Bump version
```

## Utility (Windows)
- List files: `dir` or `Get-ChildItem` (PowerShell)
- Find files: `Get-ChildItem -Recurse -Filter *.py`
- Path separator: `\`
