# Prompts

----

When you create a package, you are prompted to enter these values.

## Templated Values

The following appear in various parts of your generated project.

/// define
``project_name``

- The name of your new Python package project. This is used in documentation, so spaces and any characters are fine here. [Check the availability](http://ivantomic.com/projects/ospnc/) of possible names before creating the project.

``project_short_description``

- A one-sentence description of what your Python package does.

``full_name``

- Author full name.

``email``

- Author email

``github_username``

- Your GitHub username.

``repository_provider``

- Repository provider.

``repository_namespace``

- Repository namespace (usually your username/organization). Defaults to ``github_username``.

``repository_name``

- Name to be used for the GitHub repository.

``package_distribution_name``

- PyPI distribution name (pip install ``package_distribution_name``) - use hyphens.

``package_import_name``

- Python import name (import ``package_import_name``) - use underscores.

``package_command_line_name``

- CLI command name (use in shell) - use hyphens.

``pypi_username``

- Your Python Package Index account username.

``private_package_repository_name``

- Optional name of a private package repository to install packages from and publish this package to.

``private_package_repository_url``

- Optional URL of a private package repository to install packages from and publish this package to. Make sure to include the /simple suffix. For instance, when using a GitLab Package Registry this value should be of the form <https://gitlab.com/api/v4/projects/> {project_id} /packages/pypi/simple.

``version``

- The starting version number of the package.

``python_version``

- Minimum Python version to support.

///

## Options

The following package configuration options set up different features for your project.

/// define
``formatter``

- Whether a formatter is used or not. Options: ['Black', 'Ruff-format', 'No']. Note that the Ruff formater is still experimental. For more information see [Ruff formatter](https://github.com/astral-sh/ruff/blob/main/crates/ruff_python_formatter/README.md)

``use_pytest``

- Whether to use [pytest](https://docs.pytest.org/en/latest/)

``development_environment``

- Whether to configure the development environment with a focus on simplicity or with a focus on strictness. In strict mode, additional are added, and tools such as Mypy and Pytest are set to strict mode. Options: ['simple', 'strics']

``command_line_interface``

- Whether to create a console script using Cyclopts, Click, Typer or argparse. Console script entry point will match the project_slug. Options: ['No CLI', 'Cyclopts', 'Click', 'Typer', 'Argparse']

``docs``

- Whether to initialize documentation, and where to host it. Options: ['Read the Docs', 'Github Pages', 'No']

``with_jupyter_lab``

- Adds to JupyterLab to uv's dev dependencies, and an Invoke's task to start Jupyter Lab in the `notebooks/` directory.

``with_pydantic_typing``

- Use pydantic's mypy plugin

``create_author_file``

- Whether to create an authors file

``docstring_style``

- Select the style of the docstrings. Options: ['numpy', 'Google']

``open_source_license``

- Choose a [license](https://choosealicense.com/).

///
