from jinja2 import Template

context = {
    "project_short_description": "Project created with `uvcopier`, a Copier template for creating Python packages with uv.",
    "is_open_source": True,
    "uses_docs": True,
    "uses_readthedocs": True,
    "docs": "Read the docs",
    "package_distribution_name": "uvcopiertemplate",
    "repository_namespace": "githubnamespace",
    "repository_provider": "github.com",
    "repository_name": "uvcopiertemplate",
    "project_name": "uvcopier template",
    "formatter": "No",
    "open_source_license": "BSD-3-Clause",
    "private_package_repository_name": None,
}

with open("template/README.md.jinja", encoding="utf8") as f:
    template = Template(f.read())

result = template.render(context)

with open("README_preview.md", "w", encoding="utf8") as f:
    f.write(result)
