import functools
import os
import pathlib
import platform
import shutil
import subprocess
import sys
import xml.etree.ElementTree as ElementTree
from typing import Annotated, Optional

import questionary
import typer

match platform.system():
    case "Darwin":
        DEFAULT_CONFIG_PATH = (
            pathlib.Path.home() / "Library/Application Support/JetBrains"
        )
    case "Windows":
        app_data = os.environ.get("APPDATA")
        if app_data is None:
            typer.echo("APPDATA environment variable not found.")
            raise typer.Exit(code=1)
        app_data_path = pathlib.Path(app_data).resolve()
        DEFAULT_CONFIG_PATH = app_data_path / "JetBrains"
    case "Linux":
        DEFAULT_CONFIG_PATH = pathlib.Path.home() / ".config/JetBrains"
    case _:
        typer.echo("Unsupported OS. Exiting")
        raise typer.Exit(code=1)

SUPPORTED_IDE_PREFIXES = "PyCharm"


def in_venv():
    return sys.prefix != sys.base_prefix


def add_interpreter_to_xml(xml_path: pathlib.Path, jdk_elements: dict[str, str]) -> str:
    # Parse XML
    root = ElementTree.parse(str(xml_path)).getroot()

    # Locate your component
    component = root.find("component")

    if component is None:
        raise ValueError("No component found in the XML file")

    # Create new jdk elements
    new_jdk = ElementTree.SubElement(component, "jdk", {"version": "2"})

    # Add child elements to your new jdk
    for name, value in jdk_elements.items():
        ElementTree.SubElement(new_jdk, name, {"value": value})

    ElementTree.SubElement(new_jdk, "roots")
    # Generate and return manipulated XML string
    return ElementTree.tostring(root, encoding="unicode")


def get_installed_ides(config_path: pathlib.Path) -> list[str]:
    skip_list = [".DS_Store", "bl", "cl"]
    return sorted(
        [
            path.name
            for path in config_path.glob("*")
            if path.name not in skip_list
            and path.name.startswith(SUPPORTED_IDE_PREFIXES)
        ]
    )


def guess_interpreter_path() -> Optional[pathlib.Path]:
    current_dir = pathlib.Path.cwd()

    if (current_dir / "venv").exists():
        venv_python = current_dir / "venv" / "bin" / "python"
        if typer.confirm(
            f"Found `./venv`. Use `{venv_python}` as the interpreter?", default=True
        ):
            return current_dir / "venv" / "bin" / "python"
    elif (current_dir / ".venv").exists():
        venv_python = current_dir / ".venv" / "bin" / "python"
        if typer.confirm(
            f"Found `./.venv`. Use {venv_python} as the interpreter?", default=True
        ):
            return current_dir / ".venv" / "bin" / "python"

    return None


def get_python_version(interpreter_path: pathlib.Path) -> str:
    """
    Given a path to a Python interpreter, this function returns the Python version it is running.
    If the path does not point to a valid Python interpreter, an error is printed and the program exits.

    Parameters:
    interpreter_path (pathlib.Path): Path to a Python interpreter.

    Returns:
    str: The output of '[interpreter_path] --version' command, or exits the program in case of error.

    Raises:
    typer.Exit: If the interpreter_path is not a path to a valid Python interpreter.
    """
    try:
        out = subprocess.check_output([str(interpreter_path.absolute()), "--version"])
    except subprocess.CalledProcessError:
        typer.echo(f"{interpreter_path} is not a valid python interpreter. Exiting...")
        raise typer.Exit(code=1)
    return out.decode("utf-8").strip()


interpreter_app = typer.Typer()
add_app = typer.Typer()


@interpreter_app.command(help="Add a new python interpreter")
def add(
    interpreter_path: Annotated[
        Optional[pathlib.Path], typer.Argument(help="The path to the interpreter.")
    ] = None,
    name: str = typer.Option(None, help="The name of the interpreter in your IDE."),
    ide_version: str = typer.Option(
        None, help="The version of the IDE you want to add the interpreter to"
    ),
    config_directory: pathlib.Path = DEFAULT_CONFIG_PATH,
    backup: bool = typer.Option(
        True, help="Create a backup of the config file before modifying"
    ),
    confirm: bool = typer.Option(True, help="Confirm before modifying the config file"),
) -> None:
    interpreter_path = interpreter_path or guess_interpreter_path()
    if interpreter_path is None:
        typer.echo("No interpreter path provided. Exiting.", err=True)
        raise typer.Exit(code=1)

    python_version = get_python_version(interpreter_path)

    ide_version = ide_version or get_ide_version(config_directory)
    if ide_version is None:
        typer.echo("No IDE version provided. Exiting.", err=True)
        raise typer.Exit(code=1)

    if config_directory is None or not pathlib.Path(config_directory).exists():
        typer.echo("Config directory not found. Exiting.", err=True)
        raise typer.Exit(code=1)

    config_file_path = pathlib.Path(
        DEFAULT_CONFIG_PATH / ide_version / "options/jdk.table.xml"
    )

    if not config_file_path.exists():
        typer.echo(
            f"IDE {ide_version} config not found. Try running {ide_version} first. Exiting."
        )
        raise typer.Exit(code=1)

    final_path = str(interpreter_path.absolute()).replace(
        str(pathlib.Path.home()), "$USER_HOME$"
    )

    jdk_elements = dict(
        name=name or f"({pathlib.Path().absolute().name}) - {python_version}",
        version=python_version,
        homePath=final_path,
        type="Python SDK",
    )

    final_xml = add_interpreter_to_xml(
        pathlib.Path(config_file_path),
        jdk_elements,
    )

    if backup:
        backup_path = config_file_path.with_suffix(".bak")
        if backup_path.exists():
            backup_path.unlink()
        shutil.copy(config_file_path, backup_path)

    if confirm:
        typer.confirm(
            f"Are you sure you want to add {interpreter_path} to {ide_version} as {name or python_version}?",
            abort=True,
        )

    with pathlib.Path(config_file_path).open("w") as f:
        f.write(final_xml)

    typer.echo(f"Added {interpreter_path} to {ide_version} as {name or python_version}")


@add_app.command("interpreter")
@functools.wraps(add)
def add_interpreter(*args, **kwargs):
    return add(*args, **kwargs)


def get_ide_version(config_directory: pathlib.Path) -> str:
    return questionary.select(
        "Select IDE",
        choices=sorted(
            get_installed_ides(pathlib.Path(config_directory), reverse=True)
        ),
    ).ask()


app = typer.Typer()
app.add_typer(interpreter_app, name="interpreter", help="Manage python interpreters")
app.add_typer(add_app, name="add", help="Add new interpreters to your IDE")

if __name__ == "__main__":
    app()
