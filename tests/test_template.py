"""Template Tests."""

import importlib.util
import os
import shlex
import shutil
import stat
import subprocess
import sys
import tempfile
import warnings
from collections.abc import Generator
from contextlib import contextmanager
from pathlib import Path
from typing import Any

import copier
import pytest
from click.testing import CliRunner as ClickCliRunner
from typer.testing import CliRunner as TyperCliRunner

if sys.version_info < (3, 11):
    from tomli import load as toml_load
else:
    from tomllib import load as toml_load


warnings.filterwarnings("ignore", category=copier.errors.DirtyLocalWarning)


class CopierResult:
    """Represents the result of a copier template generation."""

    def __init__(self, project_path: Path, exit_code: int = 0, exception: Exception = None):
        self.project_path = project_path
        self.exit_code = exit_code
        self.exception = exception


def handle_remove_readonly(func, path_str, exc):
    """Handle removal of read-only files on Windows."""
    if os.path.exists(path_str):
        os.chmod(path_str, stat.S_IWRITE)
        func(path_str)


def run_with_uv(command: str, project_path: Path | str) -> int:
    """Run a command in a generated project directory via uv.

    - Commands already starting with ``uv`` (e.g. ``uv build``, ``uv run pytest``) are forwarded to
    the uv executable directly.
    - Every other command (``ruff check .``, ``mypy .``, …) is wrapped with
      ``uv run --isolated --with <exe>`` so that uv pulls the tool straight from its global package
      cache without creating or syncing the project's own venv.

    No shared prebuilt venv is needed — uv's cache is the cache.
    """
    uv_path = shutil.which("uv")
    if uv_path is None:
        raise FileNotFoundError("uv not found on PATH")

    parts = shlex.split(command)
    if parts[0] == "uv":
        cmd = [uv_path, *parts[1:]]
    else:
        # --isolated: skip project-venv sync entirely
        # --with <exe>: inject the tool from uv's cache
        cmd = [uv_path, "run", "--isolated", "--with", parts[0], *parts]

    result = subprocess.run(cmd, cwd=str(project_path), capture_output=True, text=True)
    # Uncomment for debugging:
    # print(f"\nSTDOUT:\n{result.stdout}")
    # print(f"\nSTDERR:\n{result.stderr}")
    return result.returncode


@contextmanager
def inside_dir(dirpath: str | Path) -> Generator[None, None, None]:
    """Execute code from inside the given directory."""
    old_path = Path.cwd()
    try:
        os.chdir(dirpath)
        yield
    finally:
        os.chdir(old_path)


@contextmanager
def bake_copier_template(
    template_path: Path, extra_context: dict[str, Any] | None = None, temp_dir: Path | None = None
) -> Generator[CopierResult, None, None]:
    """Generate a project using Copier and clean up afterward."""

    if temp_dir is None:
        base_dir = template_path.drive + "\\"  # ensures same drive as template
        temp_dir = Path(tempfile.mkdtemp(prefix="copier_test_", dir=base_dir))
        cleanup_temp = True
    else:
        cleanup_temp = False

    project_name = (
        extra_context.get("project_name", "test-project") if extra_context else "test-project"
    )
    project_slug = project_name.lower().replace(" ", "-").replace("_", "-")
    project_dir = temp_dir / project_slug

    # Default context
    default_context = {
        "project_name": "Test Project",
        "project_short_description": "A test project",
        "full_name": "Test User",
        "email": "test@example.com",
        "github_username": "testuser",
        "repository_provider": "github.com",
        "repository_namespace": "testuser",
        "repository_name": project_slug,
        "package_distribution_name": project_slug,
        "package_import_name": project_slug.replace("-", "_"),
        "package_command_line_name": project_slug,
        "pypi_username": "testuser",
        "private_package_repository_name": "",
        "version": "0.1.0",
        "open_source_license": "BSD-3-Clause",
        "python_version": "3.10",
        "formatter": "Ruff-format",
        "hooks_tool": "prek",
        "use_pytest": True,
        "development_environment": "simple",
        "command_line_interface": "No CLI",
        "docs": "No",
        "with_jupyter": "No Jupyter",
        "with_pydantic_typing": False,
        "create_author_file": False,
        "docstring_style": "numpy",
    }

    if extra_context:
        default_context.update(extra_context)
        # Re-derive slug-based values, but never stomp keys the caller supplied explicitly.
        project_name = default_context["project_name"]
        project_slug = project_name.lower().replace(" ", "-").replace("_", "-")
        project_dir = temp_dir / project_slug
        derived = {
            "repository_name": project_slug,
            "package_distribution_name": project_slug,
            "package_import_name": project_slug.replace("-", "_"),
            "package_command_line_name": project_slug,
        }
        for key, val in derived.items():
            if key not in extra_context:
                default_context[key] = val

    # Run copier — capture failures without yielding inside the except clause,
    # which would cause "generator didn't stop after throw()" if the with-body
    # later raises (e.g. a failing assert re-enters the generator).
    _exception: Exception | None = None
    try:
        copier.run_copy(
            src_path=str(template_path),
            dst_path=str(project_dir),
            data=default_context,
            defaults=True,  # use copier.yml defaults for anything not in data
            unsafe=True,  # allow hooks / equivalent to --trust
            quiet=True,
            vcs_ref="HEAD",  # read from working tree, bypasses git clone
        )
    except Exception as e:
        _exception = e

    if _exception is None and project_dir.exists():
        bake_result = CopierResult(project_dir, exit_code=0)
    elif _exception is None:
        _exception = Exception("Project directory was not created")
        bake_result = CopierResult(project_dir, exit_code=1, exception=_exception)
    else:
        bake_result = CopierResult(project_dir, exit_code=1, exception=_exception)

    try:
        yield bake_result
    finally:
        if cleanup_temp and temp_dir.exists():
            shutil.rmtree(temp_dir, onexc=handle_remove_readonly)


def project_info(result: CopierResult):
    """Get project information from copier result."""
    project_path = result.project_path
    project_slug = project_path.name

    # Find the source directory
    src_dir = project_path / "src"
    if src_dir.exists():
        # Find the package directory inside src
        package_dirs = [d for d in src_dir.iterdir() if d.is_dir() and not d.name.startswith(".")]
        if package_dirs:
            project_dir = package_dirs[0]  # Take the first (should be only one)
        else:
            project_dir = src_dir
    else:
        project_dir = project_path

    return project_path, project_slug, project_dir


class TestCopierTemplate:
    """Main test class for the copier template."""

    @pytest.fixture(scope="class")
    def baked_default_project(
        self, template_path: Path, tmp_path_factory: pytest.TempPathFactory
    ) -> Generator[CopierResult, None, None]:
        """Bake the default template once, git-init it, and share across all run/build/check tests."""
        tmp_dir = tmp_path_factory.mktemp("baked_default")
        with bake_copier_template(template_path, temp_dir=tmp_dir) as result:
            assert result.exit_code == 0, f"Shared bake failed: {result.exception}"
            with inside_dir(result.project_path):
                for cmd in [
                    ["git", "init"],
                    ["git", "config", "user.name", "Test"],
                    ["git", "config", "user.email", "test@example.com"],
                    ["git", "add", "."],
                    ["git", "commit", "-m", "initial"],
                ]:
                    subprocess.run(cmd, capture_output=True)
            yield result

    def test_bake_with_defaults(self, template_path):
        """Test the default structure and configuration of the baked project."""
        with bake_copier_template(template_path) as result:
            assert result.project_path.exists()
            assert result.exit_code == 0
            assert result.exception is None

            project_path, project_slug, project_dir = project_info(result)

            # Check required files exist
            assert (project_path / "pyproject.toml").exists()
            assert (project_path / "src").exists()
            assert (project_path / "tests").exists()
            assert (project_path / "README.md").exists()
            assert (project_path / "HISTORY.md").exists()

    def test_bake_with_special_chars(self, template_path):
        """Ensure that special characters in names are handled correctly."""
        test_cases = [
            {"full_name": 'name "quote" name'},
            {"full_name": "O'connor"},
            {"project_name": "My-Cool Project_2024"},
        ]

        for extra_context in test_cases:
            with bake_copier_template(template_path, extra_context) as result:
                assert result.project_path.exists()
                assert result.exit_code == 0

    def test_bake_selecting_license(self, template_path):
        """Test that licenses render correctly with expected content."""
        license_strings = {
            "MIT": "MIT License",
            "BSD-3-Clause": "Redistributions of source code must retain the above copyright notice",
            "Apache-2.0": "Licensed under the Apache License, Version 2.0",
            "GPL-3.0": "GNU General Public License",
        }

        for license_name, target_string in license_strings.items():
            context = {"open_source_license": license_name}

            with bake_copier_template(template_path, context) as result:
                license_file = result.project_path / "LICENSE"
                assert license_file.exists(), f"LICENSE file missing for {license_name}"

                content = license_file.read_text(encoding="utf-8")
                assert target_string in content, (
                    f"Expected text not found in {license_name} license"
                )

                # Also check pyproject.toml has correct license
                pyproject_file = result.project_path / "pyproject.toml"
                if pyproject_file.exists():
                    pyproject_content = pyproject_file.read_text(encoding="utf-8")
                    assert license_name in pyproject_content

    def test_bake_not_open_source(self, template_path):
        """Test that LICENSE is not created for non-open-source projects."""
        context = {"open_source_license": "Not open source"}

        with bake_copier_template(template_path, context) as result:
            license_file = result.project_path / "LICENSE"
            assert not license_file.exists(), (
                "LICENSE should not exist for non-open-source projects"
            )

            readme_file = result.project_path / "README.md"
            if readme_file.exists():
                readme_content = readme_file.read_text()
                assert "License" not in readme_content

    @pytest.mark.parametrize("interface", ["No CLI", "Click", "Typer", "Argparse"])
    def test_bake_with_console_script_files(self, template_path, interface):
        """Test that CLI files are created correctly based on interface choice."""
        context = {"command_line_interface": interface}

        with bake_copier_template(template_path, context) as result:
            project_path, project_slug, project_dir = project_info(result)

            cli_file = project_dir / "cli.py"
            pyproject_file = project_path / "pyproject.toml"

            if interface == "No CLI":
                assert not cli_file.exists(), "CLI file should not exist for 'No CLI'"

                if pyproject_file.exists():
                    pyproject_content = pyproject_file.read_text()
                    assert "[project.scripts]" not in pyproject_content
            else:
                assert cli_file.exists(), f"CLI file should exist for {interface}"

                if pyproject_file.exists():
                    pyproject_content = pyproject_file.read_text()
                    assert "[project.scripts]" in pyproject_content

    def test_bake_with_click_cli(self, template_path):
        """Test the generated Click CLI actually works."""
        context = {"command_line_interface": "Click"}

        with bake_copier_template(template_path, context) as result:
            project_path, project_slug, project_dir = project_info(result)

            # Import and test the CLI module
            cli_file = project_dir / "cli.py"
            if not cli_file.exists():
                pytest.skip("CLI file not generated")

            # Add the project to Python path and import CLI
            sys.path.insert(0, str(project_path / "src"))
            try:
                module_name = f"{project_slug.replace('-', '_')}.cli"
                spec = importlib.util.spec_from_file_location(module_name, cli_file)
                cli_module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(cli_module)

                # Test CLI with Click runner
                runner = ClickCliRunner()

                # Test help command
                help_result = runner.invoke(cli_module.main, ["--help"])
                assert help_result.exit_code == 0
                assert "Show this message" in help_result.output

                # Test default command
                default_result = runner.invoke(cli_module.main)
                assert default_result.exit_code == 0

            finally:
                sys.path.remove(str(project_path / "src"))

    def test_bake_with_typer_cli(self, template_path):
        """Test the generated Typer CLI actually works."""
        context = {"command_line_interface": "Typer"}

        with bake_copier_template(template_path, context) as result:
            project_path, project_slug, project_dir = project_info(result)

            cli_file = project_dir / "cli.py"
            if not cli_file.exists():
                pytest.skip("CLI file not generated")

            sys.path.insert(0, str(project_path / "src"))
            try:
                module_name = f"{project_slug.replace('-', '_')}.cli"
                spec = importlib.util.spec_from_file_location(module_name, cli_file)
                cli_module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(cli_module)

                # Test CLI with Typer runner
                runner = TyperCliRunner()

                # Test help command
                help_result = runner.invoke(cli_module.app, ["--help"])
                assert help_result.exit_code == 0
                assert "Show this message" in help_result.output

                # Test default command
                default_result = runner.invoke(cli_module.app)
                assert default_result.exit_code == 0

            finally:
                sys.path.remove(str(project_path / "src"))

    @pytest.mark.parametrize("formatter", ["No", "Black", "Ruff-format"])
    def test_formatter_configuration(self, template_path, formatter):
        """Test that formatter dependencies are correctly configured."""
        context = {"formatter": formatter}

        with bake_copier_template(template_path, context) as result:
            pyproject_file = result.project_path / "pyproject.toml"
            assert pyproject_file.exists()

            with open(pyproject_file, "rb") as f:
                pyproject_content = toml_load(f)

            dev_deps = pyproject_content.get("dependency-groups", {}).get("dev", [])

            if formatter == "Black":
                assert any("black" in dep for dep in dev_deps), (
                    "Black should be in dev dependencies"
                )
            elif formatter == "Ruff-format":
                assert any("ruff" in dep for dep in dev_deps), "Ruff should be in dev dependencies"
            # Note: Ruff is often included even with "No" formatter for linting

    @pytest.mark.parametrize(
        "command",
        [
            "ruff check .",
            "mypy .",
        ],
    )
    def test_bake_and_run_quality_checks(self, baked_default_project: CopierResult, command: str):
        """Test that quality checks pass on generated projects."""
        return_code = run_with_uv(command, baked_default_project.project_path)
        assert return_code == 0, f"Quality check '{command}' should pass"

    def test_bake_and_build_project(self, baked_default_project: CopierResult):
        """Test that the generated project can be built."""
        return_code = run_with_uv("uv build", baked_default_project.project_path)
        assert return_code == 0, "Project should build successfully"

        dist_dir = baked_default_project.project_path / "dist"
        assert dist_dir.exists(), "dist directory should be created"
        assert len(list(dist_dir.glob("*"))) >= 1, "Should create at least one distribution file"

    def test_bake_and_run_tests(self, baked_default_project: CopierResult):
        """Test that generated project's tests can run.

        ``uv run pytest`` (without --isolated) lets uv sync the generated project's
        own venv so the package is importable from within its tests.
        """
        return_code = run_with_uv("uv run pytest", baked_default_project.project_path)
        assert return_code == 0, "Generated project tests should pass"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
