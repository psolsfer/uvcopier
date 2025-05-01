# Tutorial

----

!!! note

    Did you find any of these instructions confusing? [Edit this file](https://github.com/psolsfer/uvcopier/blob/master/docs/tutorial.md) and submit a pull request with your improvements!

To start with, you will need a [GitHub] account and an account on [PyPI]. Create these before you get started on this tutorial. If you are new to Git and GitHub, you should probably spend a few minutes on some of the tutorials at the top of the page at [GitHub Help].

## Step 1: Install Copier

First, install [copier]. [uv] will handle this for you:

```bash linenums="0"
uv tool install copier
```

## Step 2: Generate Your Package

Now it's time to generate your Python package using [copier], pointing it at the [uvcopier] repo:

```bash linenums="0"
copier copy https://github.com/psolsfer/uvcopier mypackage
```

A ``mypackage`` folder will be created with the project.

You’ll be prompted for some values to configure the package.
If unsure, stick with the defaults.

## Step 3: Initialize uv and Install Pre-commit Hooks

A project folder named ``mypackage`` was created. Move into this folder:

```bash linenums="0"
cd mypackage
```

Initialize your environment and dependencies with [uv]:

```bash linenums="0"
uv sync
```

Now you can initialize [uv], which sets up a new Python environment for your project and creates a `pyproject.toml` file to manage dependencies. You can also install pre-commit hooks, which are scripts that automatically check your code for errors before each commit:

```bash linenums="0"
uv run prek install
```
or

```bash linenums="0"
uv run pre-commit install
```

Using Invoke (Optional):

The template includes [Invoke] tasks to automate common actions. If you want to use them:

```bash linenums="0"
uv run invoke install
```

This will run setup steps (dependencies + pre-commit) automatically.
If you prefer to stay lightweight, just use the uv commands above.

The easiest way to achieve this is using the included [Invoke]'s automations:

/// details | Installing Invoke
    type: tip

If you don't have [Invoke] installed, it can be easily installed with [uv]:

```bash linenums="0"
uv tool install invoke
```

///

The Invoke automations are designed to streamline the installation process by running multiple commands at once. However, if you prefer to have more control over the installation process or if you’re not planning to use Invoke for other tasks, you might find it simpler to use uv directly. Refer to the [Automated tasks](automated_tasks.md) section for more information about the usage of Invoke.

## Step 4: Create a GitHub Repo

Create a new repo named `mypackage` on GitHub, where `mypackage` matches the `[project_slug]` from your answers to running copier.

Within the project folder, setup git to use your GitHub repo and upload the code:

```bash linenums="0"
git init .
git add .
git commit -m "Initial skeleton."
git remote add origin git@github.com:myusername/mypackage.git
git push -u origin main
```

Where `myusername` and `mypackage` are adjusted for your username and package name.

!!! note

       GitHub has changed the default branch name from 'master' to 'main'. If you are using another Git repository hosting service that uses the Git branch naming defaults, you might need to use 'master' instead of 'main'.

You'll need a ssh key to push the repo. You can [generate] a key or [add] an existing one.

[generate]: https://help.github.com/articles/generating-a-new-ssh-key-and-adding-it-to-the-ssh-agent/
[add]: https://help.github.com/articles/adding-a-new-ssh-key-to-your-github-account/

## Step 5: Set Up Read the Docs (Optional)

[Read the Docs] hosts documentation for the open source community.

1. Create an account (if don't have one) and log into your account at [Read the Docs].
2. If you are not at your dashboard, choose the pull-down next to your username in the upper right, and select "My Projects".
3. Choose the button to import the repository and follow the directions.

Now your documentation will get rebuilt when you make documentation changes to your package.

## Step 6: Release on PyPI (Optional)

The Python Package Index or [PyPI] is the official third-party software repository for the Python programming language. Python developers intend it to be a comprehensive catalog of all open source Python packages. For more information, visit the [PyPI release checklist]

When you are ready, release your package the standard Python way. Here's a more detailed [release checklist](pypi_release_checklist.md) you can use.

You can use the Invoke task to publish your package to PyPI:

```bash linenums="0"
invoke release
```

This command will run `uv publish` and upload your package to PyPI.

Alternatively, you have a GitHub workflow (`python-publish.yml`) set up in your project that should automatically publish your package to PyPI when a release is published or a new tag is created.

See [PyPI Help] for more information about submitting a package.

## Having problems?

Visit our [troubleshooting](troubleshooting.md) page for help. If that doesn't help, go to our [Issues] page and create a new Issue. Be sure to give as much information as possible.

[copier]: <https://copier.readthedocs.io/>
[GitHub]: https://github.com/
[GitHub Help]: https://help.github.com/
[Invoke]: https://www.pyinvoke.org/
[Issues]: <https://github.com/psolsfer/uvcopier/issues>
[uv]: <https://docs.astral.sh/uv/>
[PyPI]: https://pypi.python.org/pypi
[PyPI Help]: https://pypi.org/help/#publishing
[PyPI release checklist]: pypi_release_checklist.md
[Read the Docs]: <https://readthedocs.org/>
[uvcopier]: https://github.com/psolsfer/uvcopier
