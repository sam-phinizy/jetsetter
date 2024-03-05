import shutil

import pytest
from typer.testing import CliRunner
from xmldiff import main

import jetsetter.cli as cli

runner = CliRunner()


@pytest.fixture
def set_up_jetbrains_config(tmp_path):
    config_path = tmp_path / "JetBrains"
    config_path.mkdir(parents=True)

    shutil.copytree("fixtures", config_path / "PyCharm2021.1" / "options")

    return config_path


def test_add_interpreter(set_up_jetbrains_config, monkeypatch):
    def mock_get_python_version(interpreter_path):
        return "3.8.8"

    monkeypatch.setattr(cli, "get_python_version", mock_get_python_version)
    monkeypatch.setattr(cli, "DEFAULT_CONFIG_PATH", set_up_jetbrains_config)

    result = runner.invoke(
        cli.app,
        [
            "interpreter",
            "add",
            "python",
            "--name",
            "test",
            "--config-directory",
            set_up_jetbrains_config,
            "--ide-version",
            "PyCharm2021.1",
            "--no-confirm",
        ],
    )
    assert result.exit_code == 0
    assert (
        main.diff_files(
            "fixtures/expected_pycharm.xml",
            str(
                set_up_jetbrains_config / "PyCharm2021.1" / "options" / "jdk.table.xml"
            ),
        )
        == []
    )
