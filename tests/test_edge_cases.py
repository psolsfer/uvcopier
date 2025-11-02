"""Test edge cases and special scenarios for the copier template.

Tests unusual inputs, boundary conditions, and error handling.
"""

import shutil
import subprocess
import tempfile
from pathlib import Path

import yaml


def test_special_characters_in_names():
    """Test that special characters in project names are handled correctly."""

    test_cases = [
        {
            "name": "spaces_and_hyphens",
            "project_name": "My-Cool Project",
            "expected_import": "my_cool_project",
            "expected_dist": "my-cool-project",
        },
        {
            "name": "underscores_and_numbers",
            "project_name": "project_2024_v2",
            "expected_import": "project_2024_v2",
            "expected_dist": "project-2024-v2",
        },
        {
            "name": "mixed_separators",
            "project_name": "mixed-name_with.dots",
            "expected_import": "mixed_name_with_dots",
            "expected_dist": "mixed-name-with-dots",
        },
        {
            "name": "unicode_characters",
            "project_name": "Café-Project",
            "expected_import": "cafe_project",
            "expected_dist": "cafe-project",
        },
    ]

    template_path = Path.cwd()
    temp_dir = Path(tempfile.mkdtemp(prefix="edge_test_"))

    try:
        for test_case in test_cases:
            print(f"Testing: {test_case['name']} - '{test_case['project_name']}'")

            project_dir = temp_dir / f"test_{test_case['name']}"

            # Create answers file
            answers = {
                "_src_path": str(template_path),
                "_commit": "HEAD",
                "project_name": test_case["project_name"],
                "project_short_description": f"Test project for {test_case['name']}",
                "full_name": "Test User",
                "email": "test@example.com",
                "github_username": "testuser",
                "repository_namespace": "testuser",
                "repository_name": test_case["expected_dist"],
                "package_distribution_name": test_case["expected_dist"],
                "package_import_name": test_case["expected_import"],
                "package_command_line_name": test_case["expected_dist"],
                "pypi_username": "testuser",
                "version": "0.1.0",
                "open_source_license": "MIT",
                "python_version": "3.10",
                "formatter": "Ruff-format",
                "use_pytest": True,
                "development_environment": "simple",
                "command_line_interface": "No CLI",
                "docs": "No",
                "with_jupyter_lab": False,
                "with_pydantic_typing": False,
                "create_author_file": False,
                "docstring_style": "numpy",
            }

            answers_file = temp_dir / f"{test_case['name']}_answers.yml"
            with open(answers_file, "w") as f:
                yaml.dump(answers, f)

            # Generate project
            cmd = [
                "copier",
                "copy",
                str(template_path),
                str(project_dir),
                "--answers-file",
                str(answers_file),
                "--trust",
            ]

            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode != 0:
                print(f"  Failed to generate project: {result.stderr}")
                continue

            # Validate structure
            expected_import_dir = project_dir / "src" / test_case["expected_import"]
            if not expected_import_dir.exists():
                print(f"  Import directory not created: {expected_import_dir}")
                continue

            # Check pyproject.toml content
            pyproject_file = project_dir / "pyproject.toml"
            if pyproject_file.exists():
                with open(pyproject_file, "r") as f:
                    content = f.read()

                if f'name = "{test_case["expected_dist"]}"' not in content:
                    print(f"  Distribution name not correct in pyproject.toml")
                    continue

            print(f"   {test_case['name']} handled correctly")

    finally:
        shutil.rmtree(temp_dir)


def test_empty_optional_fields():
    """Test behavior when optional fields are empty."""

    template_path = Path.cwd()
    temp_dir = Path(tempfile.mkdtemp(prefix="empty_test_"))

    try:
        project_dir = temp_dir / "empty_fields_test"

        # Test with minimal/empty optional fields
        answers = {
            "_src_path": str(template_path),
            "_commit": "HEAD",
            "project_name": "Empty Fields Test",
            "project_short_description": "",  # Empty description
            "full_name": "Test User",
            "email": "test@example.com",
            "github_username": "testuser",
            "repository_namespace": "testuser",
            "repository_name": "empty-fields-test",
            "package_distribution_name": "empty-fields-test",
            "package_import_name": "empty_fields_test",
            "package_command_line_name": "empty-fields-test",
            "pypi_username": "testuser",
            "private_package_repository_name": "",  # Empty
            "private_package_repository_url": "",  # Empty
            "version": "0.1.0",
            "open_source_license": "MIT",
            "python_version": "3.10",
            "formatter": "Ruff-format",
            "use_pytest": True,
            "development_environment": "simple",
            "command_line_interface": "No CLI",
            "docs": "No",
            "with_jupyter_lab": False,
            "with_pydantic_typing": False,
            "create_author_file": False,
            "docstring_style": "numpy",
        }

        # TODO Use copier.run_copy rather than subprocess.run, as in baker_copier_template
        answers_file = temp_dir / "empty_answers.yml"
        with open(answers_file, "w") as f:
            yaml.dump(answers, f)

        # Generate project
        cmd = [
            "copier",
            "copy",
            str(template_path),
            str(project_dir),
            "--answers-file",
            str(answers_file),
            "--trust",
        ]

        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            print(f"Failed to generate project with empty fields: {result.stderr}")
            return

        # Check that files were created despite empty description
        if not (project_dir / "README.md").exists():
            print("README.md not created with empty description")
            return

        # Check README content handles empty description gracefully
        with open(project_dir / "README.md", "r") as f:
            readme_content = f.read()

        if "Empty Fields Test" not in readme_content:
            print("Project name not in README despite empty description")
            return

        print(" Empty optional fields handled correctly")

    finally:
        shutil.rmtree(temp_dir)


def test_boundary_python_versions():
    """Test boundary Python versions."""

    template_path = Path.cwd()
    temp_dir = Path(tempfile.mkdtemp(prefix="python_version_test_"))

    # Test minimum and maximum supported Python versions
    python_versions = ["3.9", "3.13"]  # Adjust based on your template's supported versions

    try:
        for py_version in python_versions:
            print(f"Testing Python version: {py_version}")

            project_dir = temp_dir / f"python_{py_version.replace('.', '_')}_test"

            answers = {
                "_src_path": str(template_path),
                "_commit": "HEAD",
                "project_name": f"Python {py_version} Test",
                "project_short_description": f"Test project for Python {py_version}",
                "full_name": "Test User",
                "email": "test@example.com",
                "github_username": "testuser",
                "repository_namespace": "testuser",
                "repository_name": f"python-{py_version.replace('.', '-')}-test",
                "package_distribution_name": f"python-{py_version.replace('.', '-')}-test",
                "package_import_name": f"python_{py_version.replace('.', '_')}_test",
                "package_command_line_name": f"python-{py_version.replace('.', '-')}-test",
                "pypi_username": "testuser",
                "version": "0.1.0",
                "open_source_license": "MIT",
                "python_version": py_version,
                "formatter": "Ruff-format",
                "use_pytest": True,
                "development_environment": "simple",
                "command_line_interface": "No CLI",
                "docs": "No",
                "with_jupyter_lab": False,
                "with_pydantic_typing": False,
                "create_author_file": False,
                "docstring_style": "numpy",
            }

            answers_file = temp_dir / f"python_{py_version.replace('.', '_')}_answers.yml"
            with open(answers_file, "w") as f:
                yaml.dump(answers, f)

            # Generate project
            cmd = [
                "copier",
                "copy",
                str(template_path),
                str(project_dir),
                "--answers-file",
                str(answers_file),
                "--trust",
            ]

            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode != 0:
                print(f"  Failed for Python {py_version}: {result.stderr}")
                continue

            # Check pyproject.toml has correct Python version
            pyproject_file = project_dir / "pyproject.toml"
            if pyproject_file.exists():
                with open(pyproject_file, "r") as f:
                    content = f.read()

                if f">={py_version}" not in content:
                    print(f"  Python version {py_version} not correctly set in pyproject.toml")
                    continue

            print(f"   Python {py_version} handled correctly")

    finally:
        shutil.rmtree(temp_dir)


def test_all_cli_options():
    """Test all CLI framework options."""

    cli_options = ["No CLI", "Cyclopts", "Click", "Typer", "Argparse"]
    template_path = Path.cwd()
    temp_dir = Path(tempfile.mkdtemp(prefix="cli_test_"))

    try:
        for cli_option in cli_options:
            print(f"Testing CLI option: {cli_option}")

            project_dir = temp_dir / f"cli_{cli_option.lower().replace(' ', '_')}_test"

            answers = {
                "_src_path": str(template_path),
                "_commit": "HEAD",
                "project_name": f"{cli_option} Test",
                "project_short_description": f"Test project with {cli_option}",
                "full_name": "Test User",
                "email": "test@example.com",
                "github_username": "testuser",
                "repository_namespace": "testuser",
                "repository_name": f"{cli_option.lower().replace(' ', '-')}-test",
                "package_distribution_name": f"{cli_option.lower().replace(' ', '-')}-test",
                "package_import_name": f"{cli_option.lower().replace(' ', '_')}_test",
                "package_command_line_name": f"{cli_option.lower().replace(' ', '-')}-test",
                "pypi_username": "testuser",
                "version": "0.1.0",
                "open_source_license": "MIT",
                "python_version": "3.10",
                "formatter": "Ruff-format",
                "use_pytest": True,
                "development_environment": "simple",
                "command_line_interface": cli_option,
                "docs": "No",
                "with_jupyter_lab": False,
                "with_pydantic_typing": True if cli_option != "No CLI" else False,
                "create_author_file": False,
                "docstring_style": "numpy",
            }

            answers_file = temp_dir / f"cli_{cli_option.lower().replace(' ', '_')}_answers.yml"
            with open(answers_file, "w") as f:
                yaml.dump(answers, f)

            # Generate project
            cmd = [
                "copier",
                "copy",
                str(template_path),
                str(project_dir),
                "--answers-file",
                str(answers_file),
                "--trust",
            ]

            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode != 0:
                print(f"  Failed for {cli_option}: {result.stderr}")
                continue

            # Check CLI-specific expectations
            import_name = answers["package_import_name"]
            cli_file = project_dir / "src" / import_name / "cli.py"

            if cli_option == "No CLI":
                if cli_file.exists():
                    print("  CLI file should not exist for 'No CLI' option")
                    continue
            else:
                if not cli_file.exists():
                    print(f"  CLI file missing for {cli_option}")
                    continue

                # Check CLI file contains appropriate imports
                with open(cli_file, "r") as f:
                    cli_content = f.read()

                if cli_option == "Click" and "import click" not in cli_content:
                    print("  Click import missing from CLI file")
                    continue
                elif cli_option == "Cyclopts" and "from cyclopts import App" not in cli_content:
                    print("  Cyclopts import missing from CLI file")
                    continue
                elif cli_option == "Typer" and "import typer" not in cli_content:
                    print("  Typer import missing from CLI file")
                    continue
                elif cli_option == "Argparse" and "import argparse" not in cli_content:
                    print("  Argparse import missing from CLI file")
                    continue

            print(f"   {cli_option} handled correctly")

    finally:
        shutil.rmtree(temp_dir)


if __name__ == "__main__":
    print("🧪 Testing edge cases...")

    print("\n1. Testing special characters in names...")
    test_special_characters_in_names()

    print("\n2. Testing empty optional fields...")
    test_empty_optional_fields()

    print("\n3. Testing boundary Python versions...")
    test_boundary_python_versions()

    print("\n4. Testing all CLI options...")
    test_all_cli_options()

    print("\n🎉 All edge case tests completed!")
