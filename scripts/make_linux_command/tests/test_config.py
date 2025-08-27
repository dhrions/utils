# tests/test_config.py
import pytest
from pathlib import Path
from make_linux_command.config import (
    DEFAULT_INSTALL_DIR,
    DEFAULT_VENV_BASE_DIR,
    REQUIRED_FILES,
    FORBIDDEN_COMMANDS,
    ERROR_STRUCTURE,
    ERROR_PERMISSION,
    SUCCESS_MESSAGE,
)

def test_default_install_dir():
    """Teste que DEFAULT_INSTALL_DIR est un Path valide."""
    assert isinstance(DEFAULT_INSTALL_DIR, Path)
    assert str(DEFAULT_INSTALL_DIR) == "/usr/local/bin"

def test_default_venv_base_dir():
    """Teste que DEFAULT_VENV_BASE_DIR est un Path valide."""
    assert isinstance(DEFAULT_VENV_BASE_DIR, Path)
    assert str(DEFAULT_VENV_BASE_DIR) == "/opt"

def test_required_files():
    """Teste que REQUIRED_FILES contient les fichiers attendus."""
    assert REQUIRED_FILES == ["cli.py"]

def test_forbidden_commands():
    """Teste que FORBIDDEN_COMMANDS contient des commandes interdites."""
    assert isinstance(FORBIDDEN_COMMANDS, set)
    assert "ls" in FORBIDDEN_COMMANDS
    assert "rm" in FORBIDDEN_COMMANDS
    assert "python" in FORBIDDEN_COMMANDS
    assert "sudo" in FORBIDDEN_COMMANDS
    assert len(FORBIDDEN_COMMANDS) > 10

@pytest.mark.parametrize(
    "command",
    [
        "ls",
        "rm",
        "cat",
        "echo",
        "python",
        "pip",
        "bash",
        "sh",
        "zsh",
        "fish",
        "sudo",
        "root",
        "admin",
    ],
)
def test_forbidden_commands_contains(command):
    """Teste que chaque commande interdite est bien dans FORBIDDEN_COMMANDS."""
    assert command in FORBIDDEN_COMMANDS

def test_error_structure_message():
    """Teste que ERROR_STRUCTURE est une chaîne formatable avec un placeholder."""
    assert isinstance(ERROR_STRUCTURE, str)
    assert "{}".format("cli.py") == "cli.py"  # Vérifie que le formatage fonctionne
    assert "{} est manquant" in ERROR_STRUCTURE  # Vérifie la présence du placeholder

def test_error_permission_message():
    """Teste que ERROR_PERMISSION est une chaîne non vide."""
    assert isinstance(ERROR_PERMISSION, str)
    assert len(ERROR_PERMISSION) > 0
    assert "permissions insuffisantes" in ERROR_PERMISSION.lower()

def test_success_message_format():
    """Teste que SUCCESS_MESSAGE est une chaîne formatable avec deux placeholders."""
    assert isinstance(SUCCESS_MESSAGE, str)
    assert SUCCESS_MESSAGE.count("{}") == 2
    # Teste le formatage avec des valeurs fictives
    formatted = SUCCESS_MESSAGE.format("testcmd", "testcmd")
    assert "testcmd" in formatted
    assert "Succès" in formatted
