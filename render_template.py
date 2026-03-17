"""Render the Copier template for inspection/testing purposes.

Run with:
    uv run python render_template.py

The rendered output is written to ``template_tests/preview/`` by default.
"""

import shutil
from pathlib import Path
from typing import Any

import copier
import yaml

TEMPLATE_ROOT = Path(".")
DEFAULT_OUTPUT = Path("template_tests") / "preview"


def _placeholder_defaults(config_file: Path) -> dict[str, Any]:
    """Return placeholder values for questions that have no explicit default.

    Copier treats questions with only a ``placeholder`` (and no ``default``) as required, so they
    raise ``ValueError`` even when ``defaults=True``. This function extracts the placeholder text
    and uses it as a synthetic default so that the template can be rendered non-interactively.

    Parameters
    ----------
    config_file : Path
        Path to ``copier.yml`` / ``copier.yaml``.

    Returns
    -------
    dict[str, Any]
        Mapping of question name → placeholder string for every question that has a ``placeholder``
        but no ``default``.
    """
    with config_file.open(encoding="utf-8") as fh:
        config: dict[str, Any] = yaml.safe_load(fh) or {}

    result: dict[str, Any] = {}
    for key, value in config.items():
        if key.startswith("_") or not isinstance(value, dict):
            continue
        if "default" not in value and "placeholder" in value:
            result[key] = value["placeholder"]

    return result


def render_template(
    context: dict[str, Any] | None = None,
    output_dir: Path = DEFAULT_OUTPUT,
    template_root: Path = TEMPLATE_ROOT,
    overwrite: bool = True,
    cleanup: bool = False,
) -> Path:
    """Render the Copier template with the given context.

    Unspecified questions fall back to their ``default`` from ``copier.yml`` (via ``defaults=True``).
    Questions that only carry a ``placeholder`` use that placeholder text as a synthetic default so
    the render never blocks on interactive prompts.

    Parameters
    ----------
    context : dict[str, Any] | None, optional
        Variables to pass to the template. Takes highest precedence.
    output_dir : Path, optional
        Directory where the rendered project will be written.
    template_root : Path, optional
        Directory containing ``copier.yml`` (the template root).
    overwrite : bool, optional
        Whether to overwrite files that already exist in ``output_dir``.
    cleanup : bool, optional
        If ``True``, delete ``output_dir`` before rendering for a clean slate.

    Returns
    -------
    Path
        The output directory containing the rendered project.
    """
    if context is None:
        context = {}

    # Resolve copier.yml location
    config_file: Path | None = None
    for name in ("copier.yml", "copier.yaml"):
        candidate = template_root / name
        if candidate.exists():
            config_file = candidate
            break

    # Build data: placeholder fallbacks < user context
    # Copier's own defaults are applied on top via defaults=True
    data: dict[str, Any] = {}
    if config_file is not None:
        data.update(_placeholder_defaults(config_file))
    data.update(context)

    if cleanup and output_dir.exists():
        shutil.rmtree(output_dir)

    output_dir.mkdir(parents=True, exist_ok=True)

    copier.run_copy(
        src_path=str(template_root),
        dst_path=str(output_dir),
        data=data,
        defaults=True,  # use copier.yml defaults for anything not in data
        overwrite=overwrite,
        unsafe=True,  # allow hooks to run
        quiet=True,
        vcs_ref="HEAD",  # read directly from working tree, bypasses git clone
    )

    print(f"Template rendered to: {output_dir.resolve()}")
    return output_dir


# Edit the context below to preview specific configurations
context: dict[str, Any] = {
    "project_name": "uvcopier template",
    "project_short_description": (
        "Project created with `uvcopier`, a Copier template for creating Python packages with uv."
    ),
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
    "private_package_repository_name": "",
}

if __name__ == "__main__":
    render_template(context=context, cleanup=True)
