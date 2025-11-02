"""Shared pytest fixtures and configuration for template testing."""

import os
import shutil
import subprocess
from pathlib import Path
from typing import Any

import pytest


@pytest.fixture(scope="session")
def template_path():
    """Get the path to the copier template."""
    return Path(__file__).parent.parent


@pytest.fixture(scope="session", autouse=True)
def setup_test_environment():
    """Set up test environment and check dependencies."""
    # Check that required tools are available
    required_tools = ["copier", "uv", "git"]
    missing_tools = []

    for tool in required_tools:
        if not shutil.which(tool):
            missing_tools.append(tool)

    if missing_tools:
        pytest.exit(f"Missing required tools: {', '.join(missing_tools)}")

    # Set environment variables for testing
    os.environ["TESTING"] = "1"
    os.environ["UV_LINK_MODE"] = "symlink"  # Faster linking

    yield

    # Cleanup after all tests
    if "TESTING" in os.environ:
        del os.environ["TESTING"]


@pytest.fixture
def temp_project_dir(tmp_path):
    """Create a temporary directory for project generation."""
    project_dir = tmp_path / "test_project"
    project_dir.mkdir()
    return project_dir


class TestProjectContext:
    """Context manager for test projects with common setup."""

    def __init__(self, project_path: Path):
        self.project_path = project_path
        self.original_cwd = Path.cwd()

    def __enter__(self):
        # Initialize git repo (required by many tools)
        os.chdir(self.project_path)
        subprocess.run(["git", "init"], capture_output=True, check=True)
        subprocess.run(["git", "config", "user.name", "Test User"], capture_output=True, check=True)
        subprocess.run(
            ["git", "config", "user.email", "test@example.com"], capture_output=True, check=True
        )
        subprocess.run(["git", "add", "."], capture_output=True, check=True)
        subprocess.run(["git", "commit", "-m", "Initial commit"], capture_output=True, check=True)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        os.chdir(self.original_cwd)

    def run_command(self, command: str, env: dict[str, str] = None) -> subprocess.CompletedProcess:
        """Run a command in the project directory."""
        import shlex

        cmd_env = os.environ.copy()
        if env:
            cmd_env.update(env)

        return subprocess.run(
            shlex.split(command), capture_output=True, text=True, env=cmd_env, cwd=self.project_path
        )


# ??? Unused
@pytest.fixture
def project_context():
    """Factory fixture for creating test project contexts."""

    def _create_context(project_path: Path):
        return TestProjectContext(project_path)

    return _create_context


# Common test data
COMMON_PROJECT_CONTEXTS = {
    "minimal": {
        "project_name": "Minimal Project",
        "project_short_description": "A minimal test project",
        "command_line_interface": "No CLI",
        "docs": "No",
        "with_jupyter_lab": False,
        "with_pydantic_typing": False,
        "create_author_file": False,
    },
    "full_featured": {
        "project_name": "Full Featured Project",
        "project_short_description": "A full-featured test project",
        "command_line_interface": "Click",
        "docs": "Read the docs",
        "with_jupyter_lab": True,
        "with_pydantic_typing": True,
        "create_author_file": True,
        "development_environment": "strict",
    },
    "cli_cyclopts": {
        "project_name": "Cyclopts CLI Project",
        "project_short_description": "A project with Cyclopts CLI",
        "command_line_interface": "Cyclopts",
        "docs": "Github Pages",
        "with_pydantic_typing": True,
    },
    "cli_test_bake_with_console_script_files": {
        "project_name": "Typer CLI Project",
        "project_short_description": "A project with Typer CLI",
        "command_line_interface": "Typer",
        "docs": "Github Pages",
        "with_pydantic_typing": True,
    },
    "private": {
        "project_name": "Private Project",
        "project_short_description": "A private project",
        "open_source_license": "Not open source",
        "private_package_repository_name": "private-repo",
        "private_package_repository_url": "https://pypi.private.com/simple/",
    },
}


@pytest.fixture(params=COMMON_PROJECT_CONTEXTS.keys())
def project_variant(request):
    """Parametrized fixture providing different project configurations."""
    return request.param, COMMON_PROJECT_CONTEXTS[request.param]


def validate_project_structure(project_path: Path, context: dict[str, Any]) -> None:
    """Validate that a generated project has the expected structure."""
    import_name = context.get("package_import_name", "test_project")

    # Core files that should always exist
    required_files = [
        "pyproject.toml",
        "README.md",
        "HISTORY.md",
        "CONTRIBUTING.md",
        f"src/{import_name}/__init__.py",
        f"src/{import_name}/py.typed",
    ]

    for file_path in required_files:
        full_path = project_path / file_path
        assert full_path.exists(), f"Required file missing: {file_path}"

    # Conditional files
    if context.get("command_line_interface", "No CLI") != "No CLI":
        cli_file = project_path / f"src/{import_name}/cli.py"
        assert cli_file.exists(), "CLI file should exist when CLI is enabled"

    if context.get("docs", "No") != "No":
        docs_dir = project_path / "docs"
        assert docs_dir.exists(), "Docs directory should exist when docs are enabled"
        assert (project_path / "mkdocs.yml").exists(), "mkdocs.yml should exist"

    if context.get("open_source_license", "MIT") != "Not open source":
        license_file = project_path / "LICENSE"
        assert license_file.exists(), "LICENSE file should exist for open source projects"

    if context.get("create_author_file", False):
        authors_file = project_path / "AUTHORS.md"
        assert authors_file.exists(), "AUTHORS.md should exist when enabled"


def validate_pyproject_toml(project_path: Path, context: dict[str, Any]) -> None:
    """Validate pyproject.toml content matches the project context."""
    import sys

    if sys.version_info < (3, 11):
        from tomli import load as toml_load
    else:
        from tomllib import load as toml_load

    pyproject_file = project_path / "pyproject.toml"
    assert pyproject_file.exists(), "pyproject.toml should exist"

    with open(pyproject_file, "rb") as f:
        data = toml_load(f)

    # Validate project metadata
    project_data = data.get("project", {})
    assert project_data.get("name") == context.get("package_distribution_name")
    assert project_data.get("version") == context.get("version", "0.1.0")

    # Validate dependencies based on choices
    dependencies = project_data.get("dependencies", [])

    cli_choice = context.get("command_line_interface", "No CLI")
    if cli_choice == "Click":
        assert any("click" in dep for dep in dependencies), "Click dependency should be present"
    elif cli_choice == "Cyclopts":
        assert any("cyclopts" in dep for dep in dependencies), "Cyclopts dependency should be present"
    elif cli_choice == "Typer":
        assert any("typer" in dep for dep in dependencies), "Typer dependency should be present"

    if context.get("with_pydantic_typing", False):
        assert any("pydantic" in dep for dep in dependencies), (
            "Pydantic dependency should be present"
        )

    # Validate development dependencies
    dep_groups = data.get("dependency-groups", {})
    dev_deps = dep_groups.get("dev", [])

    formatter = context.get("formatter", "Ruff-format")
    if formatter == "Black":
        assert any("black" in dep for dep in dev_deps), "Black should be in dev dependencies"

    # Ruff should usually be present for linting
    assert any("ruff" in dep for dep in dev_deps), "Ruff should be in dev dependencies"

    if context.get("use_pytest", True):
        assert any("pytest" in dep for dep in dev_deps), "Pytest should be in dev dependencies"


def get_cli_module(project_path: Path, import_name: str):
    """Import and return the CLI module from a generated project."""
    import importlib.util
    import sys

    cli_file = project_path / f"src/{import_name}/cli.py"
    if not cli_file.exists():
        return None

    # Add project to Python path
    src_path = str(project_path / "src")
    if src_path not in sys.path:
        sys.path.insert(0, src_path)

    try:
        module_name = f"{import_name}.cli"
        spec = importlib.util.spec_from_file_location(module_name, cli_file)
        if spec is None:
            return None

        cli_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(cli_module)
        return cli_module

    finally:
        if src_path in sys.path:
            sys.path.remove(src_path)


# Pytest marks for categorizing tests
pytest_marks = {
    "slow": pytest.mark.slow,
    "integration": pytest.mark.integration,
    "cli": pytest.mark.cli,
    "docs": pytest.mark.docs,
}
