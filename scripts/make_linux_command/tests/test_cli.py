# tests/test_cli.py
import pytest
from unittest.mock import patch
from click.testing import CliRunner
from pathlib import Path
from make_linux_command.cli import cli

@pytest.fixture
def runner():
    """Fixture pour exécuter les commandes CLI."""
    return CliRunner()

@pytest.fixture
def test_module_path(tmp_path):
    """Crée un module de test valide."""
    module_path = tmp_path / "test_module"
    module_path.mkdir()
    (module_path / "cli.py").write_text(
        """#!/usr/bin/env python3
import click
@click.command()
def main():
    click.echo('Hello, World!')
if __name__ == '__main__':
    main()
"""
    )
    (module_path / "requirements.txt").write_text("click==8.2.1\n")
    return module_path

def test_cli_help(runner):
    """Teste l'affichage de l'aide générale."""
    result = runner.invoke(cli, ["--help"])
    assert result.exit_code == 0
    assert "Transforme un module Python en commande Linux exécutable." in result.output

def test_install_command_help(runner):
    """Teste l'affichage de l'aide pour la commande 'install'."""
    result = runner.invoke(cli, ["install", "--help"])
    assert result.exit_code == 0
    assert "Installe une commande Linux à partir d'un module Python." in result.output

@patch("make_linux_command.cli.setup_command")
def test_install_command_local_default(mock_setup, runner, test_module_path):
    """Teste l'installation locale par défaut (--local activé par défaut)."""
    result = runner.invoke(cli, ["install", str(test_module_path), "testcmd"])
    assert result.exit_code == 0
    mock_setup.assert_called_once_with(
        module_path=test_module_path,
        command_name="testcmd",
        local=True,
        skip_deps=False,
        force=False,
        venv_base_dir=Path("/opt"),
    )

@patch("make_linux_command.cli.setup_command")
def test_install_command_global(mock_setup, runner, test_module_path):
    """Teste l'installation globale avec --no-local (doit échouer sans sudo)."""
    result = runner.invoke(cli, ["install", str(test_module_path), "testcmd", "--no-local"])
    assert result.exit_code == 2  # Erreur de permission attendue

@patch("make_linux_command.cli.setup_command")
def test_install_command_skip_deps(mock_setup, runner, test_module_path):
    """Teste l'option --skip-deps."""
    result = runner.invoke(cli, ["install", str(test_module_path), "testcmd", "--skip-deps"])
    assert result.exit_code == 0
    mock_setup.assert_called_once_with(
        module_path=test_module_path,
        command_name="testcmd",
        local=True,
        skip_deps=True,
        force=False,
        venv_base_dir=Path("/opt"),
    )

@patch("make_linux_command.cli.setup_command")
def test_install_command_force(mock_setup, runner, test_module_path):
    """Teste l'option --force."""
    result = runner.invoke(cli, ["install", str(test_module_path), "testcmd", "--force"])
    assert result.exit_code == 0
    mock_setup.assert_called_once_with(
        module_path=test_module_path,
        command_name="testcmd",
        local=True,
        skip_deps=False,
        force=True,
        venv_base_dir=Path("/opt"),
    )

@patch("make_linux_command.cli.setup_command")
def test_install_command_custom_venv_dir(mock_setup, runner, test_module_path, tmp_path):
    """Teste l'option --venv-dir."""
    custom_venv_dir = tmp_path / "custom_venv"
    result = runner.invoke(cli, ["install", str(test_module_path), "testcmd", "--venv-dir", str(custom_venv_dir)])
    assert result.exit_code == 0
    mock_setup.assert_called_once_with(
        module_path=test_module_path,
        command_name="testcmd",
        local=True,
        skip_deps=False,
        force=False,
        venv_base_dir=custom_venv_dir,
    )

def test_install_command_missing_args(runner):
    """Teste l'absence d'arguments requis."""
    result = runner.invoke(cli, ["install"])
    assert result.exit_code == 2
    assert "Usage:" in result.output

@patch("make_linux_command.cli.uninstall_command")
def test_uninstall_command(mock_uninstall, runner):
    """Teste la commande uninstall (local=True par défaut)."""
    result = runner.invoke(cli, ["uninstall", "testcmd"])
    assert result.exit_code == 0
    mock_uninstall.assert_called_once_with(
        command_name="testcmd",
        local=True,
        venv_base_dir=Path("/opt"),
    )

@patch("make_linux_command.cli.uninstall_command")
def test_uninstall_command(mock_uninstall, runner):
    """Teste la commande uninstall (local=True par défaut)."""
    result = runner.invoke(cli, ["uninstall", "testcmd"])
    assert result.exit_code == 0
    mock_uninstall.assert_called_once_with(
        command_name="testcmd",
        local=True,
        venv_base_dir=Path("/opt"),
    )

@patch("make_linux_command.cli.uninstall_command")
def test_uninstall_command_global(mock_uninstall, runner):
    """Teste la désinstallation globale avec --global."""
    result = runner.invoke(cli, ["uninstall", "testcmd", "--global"])
    assert result.exit_code == 0
    mock_uninstall.assert_called_once_with(
        command_name="testcmd",
        local=False,
        venv_base_dir=Path("/opt"),
    )

@patch("make_linux_command.cli.uninstall_command")
def test_uninstall_command_custom_venv_dir(mock_uninstall, runner, tmp_path):
    """Teste la désinstallation avec un dossier personnalisé."""
    custom_venv_dir = tmp_path / "custom_venv"
    result = runner.invoke(cli, ["uninstall", "testcmd", "--venv-dir", str(custom_venv_dir)])
    assert result.exit_code == 0
    mock_uninstall.assert_called_once_with(
        command_name="testcmd",
        local=True,
        venv_base_dir=custom_venv_dir,
    )



@patch("make_linux_command.cli.setup_command", side_effect=SystemExit(1))
def test_install_command_error(mock_setup, runner, test_module_path):
    """Teste la gestion des erreurs dans install_command."""
    result = runner.invoke(cli, ["install", str(test_module_path), "testcmd"])
    assert result.exit_code == 1
