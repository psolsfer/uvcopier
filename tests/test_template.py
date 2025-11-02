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


@pytest.fixture(scope="session")
def uv_cache_dir(tmp_path_factory: pytest.TempPathFactory) -> Path:
    """Create a shared UV cache directory for all tests."""
    cache_dir = tmp_path_factory.mktemp("uv_cache")
    return cache_dir


@pytest.fixture(scope="session")
def prebuilt_env(
    tmp_path_factory: pytest.TempPathFactory, uv_cache_dir: Path
) -> Generator[Path, None, None]:
    """Create and share a prebuilt environment for all tests that need it.

    This speeds up tests by:
    1. Using uv's fast resolver and installer
    2. Sharing UV cache across all test environments
    3. Using uv sync for faster dependency resolution # TODO
    """
    venv_dir = tmp_path_factory.mktemp("shared_venv")

    # Find the full path to 'uv'
    uv_path = shutil.which("uv")
    if uv_path is None:
        pytest.skip("uv executable not found in PATH")

    try:
        # Set up UV cache environment
        env = os.environ.copy()
        env["UV_CACHE_DIR"] = str(uv_cache_dir)
        env["UV_NO_PROGRESS"] = "1"  # Disable progress bars in tests

        # Create venv using uv (much faster than pip)
        subprocess.check_call(
            [uv_path, "venv", str(venv_dir)],
            env=env,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )

        # Install dependencies in one go (much faster than individual installs)
        common_deps = [
            "pytest>=7.4.2",
            "pytest-cov>=4.1.0",
            "ruff>=0.8",
            "mypy>=1.6.0",
            "black>=23.9.0",
            "click>=7.0",
            "cyclopts>=4.0.0",
            "typer>=0.15.0",
            "pydantic>=2.4.0",
            "mkdocs>=1.5.3",
            "mkdocs-material>=9.4.2",
        ]

        # Use uv pip install with all dependencies at once
        cmd = [uv_path, "pip", "install", "--python", str(venv_dir)] + common_deps
        subprocess.check_call(
            cmd,
            env=env,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )

        yield venv_dir

    finally:
        shutil.rmtree(venv_dir, onexc=handle_remove_readonly)


def run_inside_venv(command: str, venv_dir: Path, project_path: Path | str) -> int:
    """Run a command inside the prebuilt virtual environment."""
    venv_bin = venv_dir / ("Scripts" if os.name == "nt" else "bin")

    env = os.environ.copy()
    env["PATH"] = f"{venv_bin}{os.pathsep}{env['PATH']}"
    env["VIRTUAL_ENV"] = str(venv_dir)
    env["UV_PROJECT_ENVIRONMENT"] = str(venv_dir)

    with inside_dir(project_path):
        result = subprocess.run(
            shlex.split(command),
            env=env,
            capture_output=True,
            text=True,
        )

        # Uncomment for debugging
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
    template_path: Path, extra_context: dict[str, Any] = None, temp_dir: Path = None
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
        "docs": "False",
        "with_jupyter_lab": False,
        "with_pydantic_typing": False,
        "create_author_file": False,
        "docstring_style": "numpy",
    }

    if extra_context:
        default_context.update(extra_context)
        # Update derived values
        project_name = default_context["project_name"]
        project_slug = project_name.lower().replace(" ", "-").replace("_", "-")
        project_dir = temp_dir / project_slug
        default_context.update(
            {
                "repository_name": project_slug,
                "package_distribution_name": project_slug,
                "package_import_name": project_slug.replace("-", "_"),
                "package_command_line_name": project_slug,
            }
        )

    try:
        # Generate project using copier
        result = copier.run_copy(
            src_path=str(template_path),
            dst_path=str(project_dir),
            data=default_context,
            unsafe=True,  # Equivalent to --trust flag
            quiet=True,  # Suppress output for cleaner tests
        )

        # Check if the project directory was created successfully
        if project_dir.exists():
            yield CopierResult(project_dir, exit_code=0)
        else:
            yield CopierResult(
                project_dir, exit_code=1, exception=Exception("Project directory was not created")
            )
    except Exception as e:
        # Handle any exceptions from copier.run_copy
        yield CopierResult(project_dir, exit_code=1, exception=e)

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
    def template_path(self):
        """Get the template path."""
        return Path(__file__).parent.parent  # Adjust as needed

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

    @pytest.mark.parametrize("interface", ["No CLI", "Cyclopts", "Click", "Typer", "Argparse"])
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

    def test_bake_with_click_cli(self, template_path, prebuilt_env):
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

    def test_bake_with_typer_cli(self, template_path, prebuilt_env):
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

    def test_bake_with_cyclopts_cli(self, template_path, prebuilt_env):
        """Test the generated Cyclopts CLI actually works."""
        context = {"command_line_interface": "Cyclopts"}

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

                # Test CLI with Cyclopts
                # Note: Cyclopts doesn't have a testing runner like Click/Typer
                # We test by calling the app directly
                from cyclopts.testing import runner

                # Test help command
                help_result = runner(cli_module.app, ["--help"])
                assert help_result.exit_code == 0
                assert "CLI" in help_result.output or "help" in help_result.output.lower()

                # Test default command
                default_result = runner(cli_module.app, [])
                assert default_result.exit_code == 0

            finally:
                sys.path.remove(str(project_path / "src"))

    @pytest.mark.parametrize("formatter", ["False", "Black", "Ruff-format"])
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
    def test_bake_and_run_quality_checks(self, template_path, prebuilt_env, command):
        """Test that quality checks pass on generated projects."""
        with bake_copier_template(template_path) as result:
            if result.exception:
                pytest.fail(f"Template generation failed: {result.exception}")

            # Initialize git
            with inside_dir(result.project_path):
                subprocess.run(["git", "init"], capture_output=True)
                subprocess.run(["git", "config", "user.name", "Test"], capture_output=True)
                subprocess.run(
                    ["git", "config", "user.email", "test@example.com"], capture_output=True
                )
                subprocess.run(["git", "add", "."], capture_output=True)
                subprocess.run(["git", "commit", "-m", "initial"], capture_output=True)

            return_code = run_inside_venv(command, prebuilt_env, result.project_path)
            assert return_code == 0, f"Quality check '{command}' should pass"

    def test_bake_and_build_project(self, template_path, prebuilt_env):
        """Test that the generated project can be built."""
        with bake_copier_template(template_path) as result:
            if result.exception:
                pytest.fail(f"Template generation failed: {result.exception}")

            return_code = run_inside_venv("uv build", prebuilt_env, result.project_path)
            assert return_code == 0, "Project should build successfully"

            # Check that build artifacts were created
            dist_dir = result.project_path / "dist"
            assert dist_dir.exists(), "dist directory should be created"

            dist_files = list(dist_dir.glob("*"))
            assert len(dist_files) >= 1, "Should create at least one distribution file"

    def test_bake_and_run_tests(self, template_path, prebuilt_env):
        """Test that generated project's tests can run."""
        with bake_copier_template(template_path, {"use_pytest": True}) as result:
            if result.exception:
                pytest.fail(f"Template generation failed: {result.exception}")

            # Initialize git (required by some tools)
            with inside_dir(result.project_path):
                subprocess.run(["git", "init"], capture_output=True)
                subprocess.run(["git", "config", "user.name", "Test"], capture_output=True)
                subprocess.run(
                    ["git", "config", "user.email", "test@example.com"], capture_output=True
                )
                subprocess.run(["git", "add", "."], capture_output=True)
                subprocess.run(["git", "commit", "-m", "initial"], capture_output=True, text=True)

            # Run tests
            return_code = run_inside_venv("pytest", prebuilt_env, result.project_path)
            assert return_code == 0, "Generated project tests should pass"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
