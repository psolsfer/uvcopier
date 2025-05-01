<h1 align="center">uvcopier</h1>

<br/>

<!-- Project Badges -->
[![Documentation Status][docs-read-badge]][docs-read-url]
[![License - BSD-3-Clause][license-badge]][license-url]
[![GitHub stars][stars-badge]][github-url]
[![GitHub forks][forks-badge]][github-url]
[![GitHub issues][issues-badge]][issues-url]
<br/>

<h3 align="center">
  <a href="https://github.com/psolsfer/uvcopier">GitHub</a>
  &middot;
  <a href="https://uvcopier.readthedocs.io/en/stable/">Docs</a>
  &middot;
  <a href="https://github.com/psolsfer/uvcopier/issues">Issues</a>
</h3>

<h3 align="center">
  A Copier template for creating Python packages with uv.
</h3>

A batteries-included template for Python projects using uv for dependency management. Use it to create new packages, upgrade existing ones, or maintain consistency across your Python projects with modern tooling and best practices.

<br/>

---

## Features

### Project Setup and Management

- [copier]: Keep your project templates up-to-date and track template changes
- [uv]: Modern, fast dependency management and packaging tool for Python
- Integrated GitHub Actions workflows for testing, drafting release notes, and publishing to [PyPI] when a release is created
- Project structure following best practices

### Code Quality Assurance

- Managing and maintaining multi-language pre-commit hooks using [Pre-commit] or [prek] to ensure code quality
- [Ruff]: Fast Python linter and formatter, combining multiple linting tools
- Alternative formatter option with [Black]
- Static type checking with [Mypy] and data validation using [Pydantic]
- Automatic dependency updates with [Dependabot]

### Testing

- Testing setup with ``unittest`` and ``pytest``
- [tox] configuration for testing against multiple Python versions (3.10+)
- Test coverage reporting with [Coverage.py]
- Optional [JupyterLab] integration for exploratory testing and analysis

### Documentation

- Documentation generation with [MkDocs] and the [Material for MkDocs] theme with [PyMdown Extensions].
- Code documentation extraction with [mkdocstrings]
- Support for multiple docstring styles (Google, NumPy)
- Hosting options for [Read the Docs] or [GitHub Pages]

### Versioning and Release Notes

- [Commitizen] integration for standardized commit messages and version management
- Semantic versioning with automatic changelog generation
- Automated release notes drafting with [Release Drafter]
- History tracking and changelog management

### Command Line Interface

- Optional CLI integration using [Click], [Typer], or [argparse]

### Development Tasks

- Task automation with [Invoke] for common development workflows
- Standardized commands for testing, linting, formatting, and documentation
- Simplified package publication and versioning tools

## Usage

For a brief tutorial, refer to the refer to the [Tutorial](docs/tutorial.md) section of the documentation.

The prompts that need to be filled during the creation of the package are described in [Prompts](docs/prompts.md).

## Updating a project

An existing project can be updated to the latest template using:

```bash linenums="0"
copier update
```

## Alternatives

[copier-uv](https://github.com/pawamoy/copier-uv) is a copier template for Python projects managed by uv.

[python-copier-template](https://github.com/DiamondLightSource/python-copier-template): Diamond's opinionated copier template for pure Python projects managed by pip.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## Credits

The following templates were used as basis and inspiration for the creation of some parts of this template:

- Initial inspiration from [audreyfeldroy/cookiecutter-pypackage].
- Implementation of [Invoke] is based in [briggySmalls/cookiecutter-pypackage].
- Use of release drafter and dependabot: [TezRomacH/python-package-template].


<!-- MARKDOWN LINKS & IMAGES -->
<!-- https://www.markdownguide.org/basic-syntax/#reference-style-links -->

[docs-read-badge]: https://readthedocs.org/projects/uvcopier/badge/?version=stable&style=for-the-badge
[docs-read-url]: https://uvcopier.readthedocs.io/en/stable/
[license-badge]: https://img.shields.io/github/license/psolsfer/uvcopier?style=for-the-badge
[license-url]: https://spdx.org/licenses/BSD-3-Clause.html
[stars-badge]: https://img.shields.io/github/stars/psolsfer/uvcopier.svg?style=for-the-badge
[forks-badge]: https://img.shields.io/github/forks/psolsfer/uvcopier.svg?style=for-the-badge
[issues-badge]: https://img.shields.io/github/issues/psolsfer/uvcopier.svg?style=for-the-badge
[issues-url]: https://github.com/psolsfer/uvcopier/issues
[github-url]: https://github.com/psolsfer/uvcopier

[argparse]: https://docs.python.org/3/library/argparse.html
[Black]: https://black.readthedocs.io/en/stable/
[Click]: https://click.palletsprojects.com/en/stable/
[Coverage.py]: https://coverage.readthedocs.io/
[Commitizen]: https://commitizen-tools.github.io/commitizen/
[copier]: <https://copier.readthedocs.io/>
[Dependabot]: https://github.com/marketplace/actions/release-drafter
[Invoke]: https://www.pyinvoke.org/
[JupyterLab]: https://jupyter.org/
[Material for MkDocs]: https://squidfunk.github.io/mkdocs-material/
[MkDocs]: https://www.mkdocs.org/
[Mypy]: https://mypy.readthedocs.io/en/stable/
[Pydantic]: https://docs.pydantic.dev
[Pre-commit]: https://pre-commit.com/
[prek]: https://github.com/j178/prek
[Read the Docs]: https://readthedocs.org
[Release Drafter]: https://github.com/marketplace/actions/release-drafter
[PyMdown Extensions]: https://facelessuser.github.io/pymdown-extensions
[PyPi]: https://pypi.org/
[Ruff]: https://docs.astral.sh/ruff/
[tox]: https://tox.wiki/
[Typer]: https://typer.tiangolo.com/
[uv]: https://docs.astral.sh/uv/

[audreyfeldroy/cookiecutter-pypackage]: https://github.com/audreyfeldroy/cookiecutter-pypackage
[briggySmalls/cookiecutter-pypackage]: https://briggysmalls.github.io/cookiecutter-pypackage
[TezRomacH/python-package-template]: https://github.com/TezRomacH/python-package-template
