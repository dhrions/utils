# tests/test_installer.py
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock
from make_linux_command.installer import setup_command, uninstall_command

@pytest.fixture
def mock_module_path(tmp_path):
    """Crée un module Python valide pour les tests."""
    module_path = tmp_path / "test_module"
    module_path.mkdir()
    (module_path / "cli.py").write_text("#!/usr/bin/env python3\nprint('Hello')")
    (module_path / "requirements.txt").write_text("click==8.2.1\n")
    return module_path

def test_setup_command_valid(tmp_path, mock_module_path, mocker):
    """Teste l'installation avec un module valide (mock des dépendances)."""
    # Mock des fonctions externes
    mocker.patch(
        "make_linux_command.installer.check_structure",
        return_value=True
    )
    mocker.patch(
        "make_linux_command.installer.is_command_already_exists",
        return_value=False
    )
    mocker.patch(
        "make_linux_command.installer.is_valid_command_name",
        return_value=True
    )
    mocker.patch(
        "make_linux_command.installer.create_venv",
        return_value=tmp_path / "fake_venv"
    )
    mock_install_req = mocker.patch(
        "make_linux_command.installer.install_requirements"
    )
    mock_create_wrapper = mocker.patch(
        "make_linux_command.installer.create_wrapper",
        return_value=True
    )
    mock_log = mocker.patch(
        "make_linux_command.installer.log_installed_command"
    )
    mocker.patch(
        "make_linux_command.installer.os.access",
        return_value=True
    )

    # Exécution
    setup_command(
        module_path=mock_module_path,
        command_name="testcmd",
        local=True,
        skip_deps=False,
        force=False,
        venv_base_dir=tmp_path / "venv"
    )

    # Vérifications
    mock_install_req.assert_called_once()
    mock_create_wrapper.assert_called_once()
    mock_log.assert_called_once()

def test_setup_command_invalid_structure(mock_module_path, mocker):
    """Teste l'échec si la structure du module est invalide."""
    mocker.patch(
        "make_linux_command.installer.check_structure",
        return_value=False
    )
    mocker.patch(
        "make_linux_command.installer.logging.error"
    )
    mocker.patch(
        "make_linux_command.installer.sys.exit"
    )

    with pytest.raises(SystemExit) as excinfo:
        setup_command(
            module_path=mock_module_path,
            command_name="testcmd",
            local=True
        )
    assert excinfo.value.code == 1

def test_setup_command_command_exists(mock_module_path, mocker):
    """Teste l'échec si la commande existe déjà."""
    mocker.patch(
        "make_linux_command.installer.check_structure",
        return_value=True
    )
    mocker.patch(
        "make_linux_command.installer.is_command_already_exists",
        return_value=True
    )
    mocker.patch(
        "make_linux_command.installer.logging.error"
    )

    with pytest.raises(SystemExit) as excinfo:
        setup_command(
            module_path=mock_module_path,
            command_name="testcmd",
            local=True
        )
    assert excinfo.value.code == 1

def test_setup_command_invalid_name(mock_module_path, mocker):
    """Teste l'échec si le nom de commande est invalide."""
    mocker.patch(
        "make_linux_command.installer.check_structure",
        return_value=True
    )
    mocker.patch(
        "make_linux_command.installer.is_command_already_exists",
        return_value=False
    )
    mocker.patch(
        "make_linux_command.installer.is_valid_command_name",
        return_value=False
    )
    mocker.patch(
        "make_linux_command.installer.logging.error"
    )

    with pytest.raises(SystemExit) as excinfo:
        setup_command(
            module_path=mock_module_path,
            command_name="invalid name",
            local=True
        )
    assert excinfo.value.code == 1

def test_setup_command_permission_error(mock_module_path, mocker):
    """Teste l'échec si permissions insuffisantes (installation globale)."""
    mocker.patch(
        "make_linux_command.installer.check_structure",
        return_value=True
    )
    mocker.patch(
        "make_linux_command.installer.is_command_already_exists",
        return_value=False
    )
    mocker.patch(
        "make_linux_command.installer.is_valid_command_name",
        return_value=True
    )
    mocker.patch(
        "make_linux_command.installer.os.access",
        return_value=False
    )
    mocker.patch(
        "make_linux_command.installer.logging.error"
    )

    with pytest.raises(SystemExit) as excinfo:
        setup_command(
            module_path=mock_module_path,
            command_name="testcmd",
            local=False
        )
    assert excinfo.value.code == 1

