"""Edge-case and boundary tests for the copier template.

All generation goes through the same ``bake_copier_template`` helper used in
``test_template.py`` so we get the Python API (``copier.run_copy``) rather than
a subprocess, proper cleanup, and a consistent default context.
"""

import sys
from pathlib import Path

import pytest

from tests.test_template import bake_copier_template, project_info

if sys.version_info < (3, 11):
    from tomli import load as toml_load
else:
    from tomllib import load as toml_load


# Special characters in project / author names


@pytest.mark.parametrize(
    "extra_context,expected_import,expected_dist",
    [
        pytest.param(
            {
                "project_name": "My-Cool Project",
                "package_import_name": "my_cool_project",
                "package_distribution_name": "my-cool-project",
            },
            "my_cool_project",
            "my-cool-project",
            id="spaces_and_hyphens",
        ),
        pytest.param(
            {
                "project_name": "project_2024_v2",
                "package_import_name": "project_2024_v2",
                "package_distribution_name": "project-2024-v2",
            },
            "project_2024_v2",
            "project-2024-v2",
            id="underscores_and_numbers",
        ),
        pytest.param(
            {
                "project_name": "mixed-name_with_dots",
                "package_import_name": "mixed_name_with_dots",
                "package_distribution_name": "mixed-name-with-dots",
            },
            "mixed_name_with_dots",
            "mixed-name-with-dots",
            id="mixed_separators",
        ),
        pytest.param(
            {"full_name": 'Name "Quoted" User'},
            "test_project",
            "test-project",
            id="double_quotes_in_author",
        ),
        pytest.param(
            {"full_name": "O'Connor"},
            "test_project",
            "test-project",
            id="apostrophe_in_author",
        ),
    ],
)
def test_special_characters(
    template_path: Path,
    tmp_path: Path,
    extra_context: dict,
    expected_import: str,
    expected_dist: str,
) -> None:
    """Special characters in names must not break generation or pyproject.toml."""
    with bake_copier_template(template_path, extra_context, temp_dir=tmp_path) as result:
        assert result.exit_code == 0, f"Copier failed: {result.exception}"
        assert result.project_path.exists()

        import_dir = result.project_path / "src" / expected_import
        assert import_dir.exists(), f"Import dir missing: {import_dir}"

        pyproject = (result.project_path / "pyproject.toml").read_text(encoding="utf-8")
        assert f'name = "{expected_dist}"' in pyproject


# Empty / blank optional fields


def test_empty_description(template_path: Path, tmp_path: Path) -> None:
    """An empty project description must still produce a valid project."""
    extra: dict = {"project_short_description": ""}
    with bake_copier_template(template_path, extra, temp_dir=tmp_path) as result:
        assert result.exit_code == 0, f"Copier failed: {result.exception}"
        assert (result.project_path / "README.md").exists()
        assert (result.project_path / "pyproject.toml").exists()


def test_empty_private_repo_fields(template_path: Path, tmp_path: Path) -> None:
    """Leaving private repository fields blank must not produce broken config."""
    extra: dict = {
        "private_package_repository_name": "",
        "private_package_repository_url": "",
    }
    with bake_copier_template(template_path, extra, temp_dir=tmp_path) as result:
        assert result.exit_code == 0, f"Copier failed: {result.exception}"
        pyproject = (result.project_path / "pyproject.toml").read_text(encoding="utf-8")
        assert "tool.uv.index" not in pyproject


# Python version boundaries


@pytest.mark.parametrize("py_version", ["3.9", "3.13"])
def test_boundary_python_versions(template_path: Path, tmp_path: Path, py_version: str) -> None:
    """Minimum and maximum supported Python versions must appear in pyproject.toml."""
    extra = {
        "project_name": f"Python {py_version} Test",
        "python_version": py_version,
    }
    with bake_copier_template(template_path, extra, temp_dir=tmp_path) as result:
        assert result.exit_code == 0, f"Copier failed for Python {py_version}: {result.exception}"

        pyproject = (result.project_path / "pyproject.toml").read_text(encoding="utf-8")
        assert f">={py_version}" in pyproject, (
            f"Python {py_version} lower-bound not found in pyproject.toml"
        )


# All CLI framework options

_CLI_CHOICE_MAP = {"click": "Click", "typer": "Typer", "argparse": "Argparse"}


@pytest.mark.parametrize("cli_option", ["click", "typer", "argparse"])
def test_cli_file_contains_correct_import(
    template_path: Path,
    tmp_path: Path,
    cli_option: str,
) -> None:
    """Generated cli.py must import the declared framework."""
    extra = {"command_line_interface": _CLI_CHOICE_MAP[cli_option]}

    with bake_copier_template(template_path, extra, temp_dir=tmp_path) as result:
        assert result.exit_code == 0, f"Copier failed for {cli_option}: {result.exception}"

        _, _, project_dir = project_info(result)
        cli_file = project_dir / "cli.py"

        assert cli_file.exists(), f"cli.py missing for {cli_option}"

        cli_content = cli_file.read_text(encoding="utf-8")
        assert f"import {cli_option}" in cli_content, (
            f"Expected 'import {cli_option}' not found in cli.py"
        )

        pyproject = (result.project_path / "pyproject.toml").read_text(encoding="utf-8")
        assert "[project.scripts]" in pyproject


def test_no_cli_produces_no_cli_file(template_path: Path, tmp_path: Path) -> None:
    """'No CLI' must not produce cli.py or a [project.scripts] entry."""
    extra: dict = {"command_line_interface": "No CLI"}
    with bake_copier_template(template_path, extra, temp_dir=tmp_path) as result:
        assert result.exit_code == 0, f"Copier failed: {result.exception}"

        _, _, project_dir = project_info(result)
        assert not (project_dir / "cli.py").exists(), "cli.py must not exist for 'No CLI'"

        pyproject = (result.project_path / "pyproject.toml").read_text(encoding="utf-8")
        assert "[project.scripts]" not in pyproject


# Docs options


@pytest.mark.parametrize("docs_option", ["Read the docs", "Github Pages"])
def test_docs_generates_mkdocs(template_path: Path, tmp_path: Path, docs_option: str) -> None:
    """Selecting a docs platform must create docs/ and mkdocs.yml."""
    extra = {"docs": docs_option}
    with bake_copier_template(template_path, extra, temp_dir=tmp_path) as result:
        assert result.exit_code == 0, f"Copier failed: {result.exception}"
        assert (result.project_path / "docs").exists()
        assert (result.project_path / "mkdocs.yml").exists()


def test_no_docs_produces_no_mkdocs(template_path: Path, tmp_path: Path) -> None:
    """'No' docs must not produce docs/ or mkdocs.yml."""
    extra: dict = {"docs": "No"}
    with bake_copier_template(template_path, extra, temp_dir=tmp_path) as result:
        assert result.exit_code == 0, f"Copier failed: {result.exception}"
        assert not (result.project_path / "mkdocs.yml").exists()


# Pydantic typing option


@pytest.mark.parametrize("with_pydantic", [True, False])
def test_pydantic_typing(template_path: Path, tmp_path: Path, with_pydantic: bool) -> None:
    """Pydantic dependency must appear in pyproject.toml if and only if requested."""
    extra = {"with_pydantic_typing": with_pydantic}
    with bake_copier_template(template_path, extra, temp_dir=tmp_path) as result:
        assert result.exit_code == 0, f"Copier failed: {result.exception}"

        with open(result.project_path / "pyproject.toml", "rb") as f:
            data = toml_load(f)

        deps = data.get("project", {}).get("dependencies", [])
        has_pydantic = any("pydantic" in d for d in deps)

        if with_pydantic:
            assert has_pydantic, "pydantic must be in dependencies when with_pydantic_typing=True"
        else:
            assert not has_pydantic, (
                "pydantic must not be in dependencies when with_pydantic_typing=False"
            )


# Author file option


@pytest.mark.parametrize("create_author", [True, False])
def test_author_file(template_path: Path, tmp_path: Path, create_author: bool) -> None:
    """AUTHORS.md must exist if and only if create_author_file=True."""
    extra = {"create_author_file": create_author}
    with bake_copier_template(template_path, extra, temp_dir=tmp_path) as result:
        assert result.exit_code == 0, f"Copier failed: {result.exception}"

        authors_file = result.project_path / "AUTHORS.md"
        if create_author:
            assert authors_file.exists(), "AUTHORS.md must exist when create_author_file=True"
        else:
            assert not authors_file.exists(), (
                "AUTHORS.md must not exist when create_author_file=False"
            )
