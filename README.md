# jetsetter

Jetsetter is a tool for managing PyCharm interpreter settings. It allows you to quickly add an interpreter to PyCharm.

## Rationale

PyCharm has the abiltiy to add an interpreter to a project, but it is a multi-step process. This tool aims to make it
simple to do from the command line. It does so by adding the file to the `jdk.table.xml` file in your PyCharm's config directory.



## Installation

```bash
pipx install jetsetter
```

## Usage

```bash
jetsetter interpreter add /path/to/interpreter --name "My Interpreter"
```

Will add in a new interpreter to PyCharm with the name "My Interpreter" and the path `/path/to/interpreter`.

```bash
jetsetter interpreter add
```

Will look for an interpreter in the current directory and add it to PyCharm. Currently it looks for a .venv, venv, or
virtual environment in the current directory. If no name it will use the name of the directory and the Python version.

Note: You'll have to restart PyCharm for the changes to take effect.

## Development

This project uses [Rye](https://github.com/astral-sh/rye) for development. To get
started, [install Rye](https://rye-up.com/guide/installation/) and run the following commands:

```bash
rye sync
```

If you have `direnv` installed, you can run `direnv allow` to activate the environment.

To run the tests, run the following command:

```bash
nox
```

Also you'll need to install the pre-commit hooks:

```bash
pre-commit install --hook-type pre-commit --hook-type pre-push
```
