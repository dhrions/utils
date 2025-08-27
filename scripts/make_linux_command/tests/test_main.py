import os
import sys
import stat
import shlex
import subprocess
import logging
from pathlib import Path
from unittest.mock import patch, MagicMock, mock_open
import pytest
from make_linux_command.main import (
    check_structure,
    create_venv,
    install_requirements,
    create_wrapper,
    setup_command,
    uninstall_command,
    is_valid_command_name,
)

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

@pytest.fixture
def venv_base_dir(tmp_path):
    """Dossier de base pour les environnements virtuels."""
    return tmp_path / "venv"

@pytest.fixture
def venv_path(tmp_path):
    venv = tmp_path / "env"
    venv.mkdir()
    (venv / "bin").mkdir()
    (venv / "bin" / "pip").touch()
    return venv

@pytest.fixture
def module_path(tmp_path):
    module = tmp_path / "module"
    module.mkdir()
    return module

def test_check_structure(test_module_path):
    assert check_structure(test_module_path) is True
    (test_module_path / "cli.py").unlink()
    assert check_structure(test_module_path) is False

@patch("subprocess.run")
def test_create_venv_success(mock_run, venv_base_dir):
    mock_run.return_value = MagicMock()
    venv_path = venv_base_dir / "test_command" / "env"
    (venv_path / "bin").mkdir(parents=True, exist_ok=True)
    (venv_path / "bin" / "pip").touch()  # Simule la création de pip
    result = create_venv("test_command", venv_base_dir)
    assert result == venv_path
    mock_run.assert_called()

@patch("subprocess.run")
def test_create_venv_permission_error(mock_run, venv_base_dir):
    mock_run.side_effect = PermissionError("Permission denied")
    with pytest.raises(SystemExit):
        create_venv("test_command", Path("/root/venv"))

@patch("subprocess.run")
def test_install_requirements_success(mock_run, test_module_path, venv_base_dir):
    mock_run.return_value = MagicMock()
    venv_path = venv_base_dir / "test_command" / "env"
    venv_path.mkdir(parents=True)
    (venv_path / "bin").mkdir()
    (venv_path / "bin" / "pip").touch()
    install_requirements(venv_path, test_module_path)
    mock_run.assert_called()

def test_is_valid_command_name():
    assert is_valid_command_name("mycommand") is True
    assert is_valid_command_name("python") is False
    assert is_valid_command_name("ls") is False
    assert is_valid_command_name("my-command") is True
    assert is_valid_command_name("my command") is False

@patch("pathlib.Path.resolve")
@patch("pathlib.Path.chmod")
@patch("pathlib.Path.mkdir")
@patch("builtins.open", new_callable=mock_open)
def test_create_wrapper(mock_open_file, mock_mkdir, mock_chmod, mock_resolve, test_module_path):
    # Force le chemin à être dans ~/.local/venv
    mock_resolve.side_effect = lambda *args, **kwargs: Path.home() / ".local/venv/test_command/env"
    venv_path = Path.home() / ".local/venv/test_command/env"
    venv_path.parent.mkdir(parents=True, exist_ok=True)
    (venv_path / "bin").mkdir(exist_ok=True)
    wrapper_path = Path.home() / ".local/bin" / "test_command"
    assert create_wrapper(test_module_path, "test_command", venv_path, local=True, force=True) is True
    mock_open_file.assert_called_once_with(wrapper_path, "w")

@patch("make_linux_command.main.create_venv")
@patch("make_linux_command.main.install_requirements")
@patch("make_linux_command.main.create_wrapper")
def test_setup_command_local(mock_wrapper, mock_install, mock_venv, test_module_path):
    mock_venv.return_value = Path.home() / ".local/venv/test_command/env"
    mock_wrapper.return_value = True
    setup_command(
        module_path=test_module_path,
        command_name="test_command",
        local=True,
        skip_deps=False,
        force=True,
    )
    mock_venv.assert_called_once_with("test_command", Path.home() / ".local/venv", sys.executable)

@patch("os.access", return_value=False)
def test_setup_command_global_no_permission(mock_access, test_module_path):
    with pytest.raises(SystemExit):
        setup_command(
            module_path=test_module_path,
            command_name="test_command",
            local=False,
            skip_deps=False,
            force=True,
            venv_base_dir=Path("/opt"),
        )

@patch("pathlib.Path.unlink")
@patch("shutil.rmtree")
def test_uninstall_command_local(mock_rmtree, mock_unlink):
    wrapper_path = Path.home() / ".local/bin" / "test_command"
    wrapper_path.parent.mkdir(parents=True, exist_ok=True)
    wrapper_path.touch()
    venv_path = Path.home() / ".local/venv/test_command/env"
    venv_path.parent.mkdir(parents=True, exist_ok=True)
    (venv_path).mkdir(exist_ok=True)
    uninstall_command(command_name="test_command", local=True)
    mock_unlink.assert_called_once_with()
    mock_rmtree.assert_called_once_with(venv_path.parent)

@patch("subprocess.run")
def test_install_requirements_large_file(mock_run, test_module_path, venv_base_dir):
    venv_path = venv_base_dir / "test_command" / "env"
    venv_path.mkdir(parents=True)
    (venv_path / "bin").mkdir()
    (venv_path / "bin" / "pip").touch()
    requirements_file = test_module_path / "requirements.txt"
    requirements_file.write_text("x" * 11 * 1024)  # 11 Ko (trop gros)
    with pytest.raises(SystemExit):
        install_requirements(venv_path, test_module_path)

def test_install_requirements_no_requirements_file(module_path, venv_path):
    """Teste l'installation sans fichier requirements.txt."""
    with patch("subprocess.run") as mock_run:
        mock_run.return_value = MagicMock()
        install_requirements(venv_path, module_path)
        assert mock_run.call_count == 2  # pip upgrade + install -e

def test_install_requirements_valid(module_path, venv_path):
    """Teste l'installation avec un fichier requirements.txt valide."""
    requirements_file = module_path / "requirements.txt"
    requirements_file.write_text("click==8.2.1\nrequests==2.31.0\n")

    with patch("subprocess.run") as mock_run:
        mock_run.return_value = MagicMock()
        install_requirements(venv_path, module_path)
        assert mock_run.call_count == 3  # pip upgrade + install -e + install -r

def test_install_requirements_invalid_line(module_path, venv_path):
    """Teste la détection de lignes non autorisées dans requirements.txt."""
    requirements_file = module_path / "requirements.txt"
    requirements_file.write_text("https://example.com/malicious-package\n")

    with patch("subprocess.run") as mock_run, pytest.raises(SystemExit):
        mock_run.return_value = MagicMock()
        install_requirements(venv_path, module_path)

def test_install_requirements_large_file(module_path, venv_path):
    """Teste la détection d'un fichier requirements.txt trop volumineux."""
    requirements_file = module_path / "requirements.txt"
    requirements_file.write_text("x" * 11 * 1024)  # 11 Ko

    with patch("subprocess.run") as mock_run, pytest.raises(SystemExit):
        mock_run.return_value = MagicMock()
        install_requirements(venv_path, module_path)

def test_install_requirements_skip_deps(module_path, venv_path):
    """Teste l'option --skip-deps."""
    requirements_file = module_path / "requirements.txt"
    requirements_file.write_text("click==8.2.1\n")

    with patch("subprocess.run") as mock_run:
        mock_run.return_value = MagicMock()
        install_requirements(venv_path, module_path, skip_deps=True)
        assert mock_run.call_count == 2  # pip upgrade + install -e (pas d'install -r)

def test_install_requirements_pip_error(module_path, venv_path):
    """Teste l'échec de l'installation avec pip."""
    requirements_file = module_path / "requirements.txt"
    requirements_file.write_text("click==8.2.1\n")

    with patch("subprocess.run") as mock_run, pytest.raises(SystemExit):
        mock_run.side_effect = subprocess.CalledProcessError(1, ["pip"], "Error output")
        install_requirements(venv_path, module_path)

def test_install_requirements_malformed_line(module_path, venv_path):
    """Teste une ligne mal formatée dans requirements.txt."""
    requirements_file = module_path / "requirements.txt"
    requirements_file.write_text("click; os.system('rm -rf /')\n")

    with patch("subprocess.run") as mock_run, pytest.raises(SystemExit):
        mock_run.return_value = MagicMock()
        install_requirements(venv_path, module_path)