"""Render templates of the project for testing purposes."""

import logging
import warnings
from pathlib import Path
from typing import Any

import yaml
from copier._jinja_ext import YieldEnvironment
from copier._main import Worker
from jinja2 import Environment, TemplateError, TemplateSyntaxError, UndefinedError

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="%(message)s")

output_folder = Path("template_tests")
template_folder = Path("template")

# TODO # FIXME WHat about using bake_copier_template from test_template instead?


def _looks_like_jinja(value: Any) -> bool:
    """Check if an object looks like a Jinja2 expression."""
    return isinstance(value, str) and ("{{" in value or "{%" in value)


def _render_jinja_string(env: YieldEnvironment, value: str, context: dict[str, Any]) -> str:
    """Render a Jinja2 expression string with the given context.

    Parameters
    ----------
    env : YieldEnvironment
        The Jinja2 environment used to compile and render the template.
        Typically obtained from Copier's `Worker.jinja_env`.
    value : str
        The string containing a Jinja2 expression or template.
        For example: ``"{{ project_name }}-docs"``.
    context : dict[str, Any]
        Dictionary of variables available to the template.

    Returns
    -------
    str
        The rendered string with all Jinja2 expressions evaluated.
    """
    template = env.from_string(value)
    return template.render(context)


def _coerce_scalar(value: str) -> Any:
    """Convert string values into Python scalars where appropriate."""
    lowered = value.strip().lower()
    if lowered in {"true", "yes", "on"}:
        return True
    if lowered in {"false", "no", "off"}:
        return False
    if lowered in {"null", "none"}:
        return None
    # Try number conversion
    try:
        if "." in lowered:
            return float(lowered)
        return int(lowered)
    except ValueError:
        return value


def load_template_defaults(config_file: Path) -> dict[str, Any]:
    """Load default values from copier.yml/copier.yaml.

    Parameters
    ----------
    config_file : Path
        Path to the copier.yml or copier.yaml file

    Returns
    -------
    dict[str, Any]
        Dictionary of default values from the template configuration
    """
    if not config_file.exists():
        return {}

    # Load the YAML configuration
    with open(config_file, "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)

    if not config:
        return {}

    # Extract default values from questions
    defaults = {}
    for key, value in config.items():
        # Skip internal copier settings (start with _)
        if key.startswith("_"):
            continue

        # If it's a question definition (dict)
        if isinstance(value, dict):
            # Try to get default, fallback to placeholder
            if "default" in value:
                defaults[key] = value["default"]
            elif "placeholder" in value:
                defaults[key] = value["placeholder"]
        # If it's a simple key-value pair, use it as default
        else:
            defaults[key] = value

    return defaults


def render_jinja_in_defaults(defaults: dict[str, Any], context: dict[str, Any]) -> dict[str, Any]:
    """Render any Jinja2 expressions in default values.

    Some defaults in copier.yml contain Jinja2 expressions like "{{ docs != 'False' }}".
    This function renders those expressions using the current context.

    Parameters
    ----------
    defaults : dict[str, Any]
        Dictionary of default values, potentially containing Jinja2 expressions
    context : dict[str, Any]
        Context to use for rendering Jinja2 expressions

    Returns
    -------
    dict[str, Any]
        Dictionary with Jinja2 expressions rendered
    """
    env = Environment()
    rendered = {}

    for key, value in defaults.items():
        if _looks_like_jinja(value):
            # This looks like a Jinja2 template string
            try:
                rendered_value = _render_jinja_string(env=env, value=value, context=context)
                rendered[key] = _coerce_scalar(rendered_value)
            except (TemplateError, UndefinedError, TemplateSyntaxError) as e:
                logger.warning("Could not render Jinja2 expression in '%s': %s - %s", key, value, e)
                rendered[key] = value
        else:
            rendered[key] = value

    return rendered


def render_path_with_jinja(
    file_path: Path, env: YieldEnvironment, context: dict[str, Any]
) -> Path | None:
    """Render a path that may contain Jinja2 expressions.

    Renders each part of the path separately. If any part renders to empty, returns None to indicate
    the file should be skipped.

    Parameters
    ----------
    path_str : str
        Path string that may contain Jinja2 expressions
    env : jinja2.Environment
        Copier's Jinja2 environment
    context : dict[str, Any]
        Context for rendering

    Returns
    -------
    Path | None
        Rendered path, or None if any part evaluated to empty
    """
    # First, remove .jinja extension if present
    if file_path.suffix == ".jinja":
        file_path = file_path.with_suffix("")

    # Split into parts and render each
    parts = file_path.parts
    rendered_parts = []

    for part in parts:
        if _looks_like_jinja(part):
            try:
                rendered_part = _render_jinja_string(env=env, value=part, context=context)

                # If any part renders to empty, the file should be skipped
                if not rendered_part:
                    return None

                rendered_parts.append(rendered_part)
            except (TemplateError, UndefinedError, TemplateSyntaxError) as e:
                logger.warning(f"Warning: Could not render path part '{part}': {e}")
                return None
        else:
            rendered_parts.append(part)

    if not rendered_parts:
        return None

    return Path(*rendered_parts)


def render_templates(
    context: dict[str, Any] | None = None,
    template_files: list[Path] | None = None,
    template_base: Path = template_folder,
    template_root: Path = None,
    output_base: Path = output_folder,
) -> None:
    """Render multiple Jinja2 templates with the given context.

    If no template files are specified, automatically discovers and renders all .jinja files in the
    template_base directory.

    Parameters
    ----------
    context : dict[str, Any], optional
        Dictionary of variables to pass to the templates.
        Default is None (empty context).
    template_files : list[Path] | None, optional
        List of template file paths relative to template_base.
        If None or empty, all .jinja files in template_base will be rendered.
        Default is None.
    template_base : Path, default=template_folder
        Base directory containing the templates.
    template_root : Path, optional
        Root directory containing copier.yml. If None, assumes it's the parent
        of template_base. Default is None.
    output_base : Path, default=output_folder
        Base directory where rendered files will be saved.

    Returns
    -------
    None

    Examples
    --------
    Render specific templates:
    >>> render_templates(
    ...     template_files=[Path("README.md.jinja")],
    ...     context={"project_name": "MyProject"}
    ... )

    Auto-discover and render all templates:
    >>> render_templates(context={"project_name": "MyProject"})
    """
    if context is None:
        context = {}

    # Determine template root (where copier.yml is)
    if template_root is None:
        template_root = template_base.parent

    # Auto-discover templates if none provided
    if not template_files:
        template_files = [
            path.relative_to(template_base) for path in template_base.rglob("*.jinja")
        ]
        logger.info("Auto-discovered %d template(s)", len(template_files))

    # Find and load copier.yml
    config_file = None
    for filename in ["copier.yml", "copier.yaml"]:
        potential_file = template_root / filename
        if potential_file.exists():
            config_file = potential_file
            break

    if config_file:
        defaults = load_template_defaults(config_file)
        logger.info("Loaded %d default values from %s", len(template_files), config_file.name)
    else:
        defaults = {}
        logger.warning("No copier.yml/copier.yaml found")

    # Merge defaults with user context (user context takes precedence)
    combined_context = {**defaults, **context}
    rendered_defaults = render_jinja_in_defaults(defaults, combined_context)
    full_context = {**rendered_defaults, **context}

    # Suppress the DirtyLocalWarning from Copier
    with warnings.catch_warnings():
        warnings.filterwarnings("ignore", category=UserWarning, module="copier._vcs")

        # Create a Worker instance to access Copier's Jinja environment
        # Use template_root as src_path (where copier.yml is)
        worker = Worker(src_path=str(template_root), dst_path=str(output_base), data=full_context)

        # Get Copier's configured Jinja2 environment with all filters and extensions
        env = worker.jinja_env

    output_base.mkdir(exist_ok=True, parents=True)

    for template_file in template_files:
        # Skip the answers file template
        if "_copier_conf.answers_file" in str(template_file) or "copier-answers" in str(
            template_file
        ):
            continue

        # Render the output path (handles Jinja2 in path and conditionals)
        output_relative = render_path_with_jinja(template_file, env, context=full_context)

        if output_relative is None:
            logger.warning("Skipped: %s (conditional path part evaluated to empty)", template_file)
            continue

        output_path = output_base / output_relative
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Construct the full path relative to template_root
        relative_from_root = template_base.relative_to(template_root) / template_file

        # Load the template manually
        full_template_path = template_root / relative_from_root
        with open(full_template_path, "r") as f:
            template_content = f.read()

        # Render the template using Copier's environment from string instead of loading through env
        template_jinja = env.from_string(template_content)
        result = template_jinja.render(full_context)

        # Write the rendered file
        with output_path.open("w", encoding="utf8") as f:
            f.write(result)

        logger.info("Rendered: %s -> %s", template_file, output_path)


context = {
    "project_name": "uvcopier template",
    "project_short_description": "Project created with `uvcopier`, a Copier template for creating Python packages with uv.",
    "is_open_source": True,
    "uses_docs": True,
    "uses_readthedocs": True,
    "docs": "Read the docs",
    "package_distribution_name": "uvcopiertemplate",
    "repository_namespace": "githubnamespace",
    "repository_provider": "github.com",
    "repository_name": "uvcopiertemplate",
    "formatter": "No",
    "open_source_license": "BSD-3-Clause",
    "private_package_repository_name": None,
    "command_line_interface": "Cyclopts",
}


# List of templates to render
templates_to_render = [
    Path("README.md.jinja"),
    Path(".github/workflows/python-publish.yml.jinja"),
    # Add more templates here as needed
]

if __name__ == "__main__":
    # Render all templates
    # render_templates(context=context, template_files=templates_to_render)
    render_templates(context=context)
