# tests/test_command_validator.py
import pytest
from pathlib import Path
from make_linux_command.command_validator import (
    check_structure,
    is_valid_command_name,
    is_command_already_exists,
)

@pytest.fixture
def tmp_module_path(tmp_path):
    """Crée une structure de module temporaire pour les tests."""
    module_path = tmp_path / "test_module"
    module_path.mkdir()
    (module_path / "cli.py").write_text("#!/usr/bin/env python3\nprint('Hello')")
    return module_path

def test_check_structure_valid(tmp_module_path):
    """Teste la validation d'une structure de module valide."""
    assert check_structure(tmp_module_path) is True

def test_check_structure_missing_cli(tmp_path):
    """Teste la détection d'une structure invalide (fichier cli.py manquant)."""
    module_path = tmp_path / "invalid_module"
    module_path.mkdir()
    assert check_structure(module_path) is False

def test_is_valid_command_name_valid():
    """Teste des noms de commande valides."""
    valid_names = ["mycmd", "my-command", "my_command", "cmd123"]
    for name in valid_names:
        assert is_valid_command_name(name) is True

def test_is_valid_command_name_invalid():
    """Teste des noms de commande invalides."""
    invalid_names = [
        "",  # vide
        "my cmd",  # espace
        "-invalid",  # commence par un tiret
        "python",  # mot réservé
        "a" * 33,  # trop long
        "test[",  # caractère interdit
        "sudo",  # commande interdite
    ]
    for name in invalid_names:
        assert is_valid_command_name(name) is False

@pytest.mark.parametrize(
    "name,expected",
    [
        ("ls", False),  # commande système interdite
        ("mycmd", True),
        ("123cmd", True),
        ("my_cmd", True),
        ("my-command", True),
        ("MyCmd", True),  # majuscules autorisées
        ("mycmd123", True),
        ("_cmd", True),
        ("-cmd", False),  # commence par un tiret
        ("python3", False),  # préfixe interdit
        ("pip-install", False),  # préfixe interdit
    ],
)
def test_is_valid_command_name_parametrized(name, expected):
    """Teste la validation des noms de commande avec des cas paramétrés."""
    assert is_valid_command_name(name) is expected

@pytest.mark.skipif(not Path("/usr/bin").exists(), reason="Système non Unix")
def test_is_command_already_exists_true():
    """Teste la détection d'une commande existante (ex: 'ls')."""
    assert is_command_already_exists("ls") is True

@pytest.mark.skipif(not Path("/usr/bin").exists(), reason="Système non Unix")
def test_is_command_already_exists_false():
    """Teste la détection d'une commande inexistante."""
    assert is_command_already_exists("this_command_should_not_exist_12345") is False

def test_is_command_already_exists_with_mock(monkeypatch):
    """Teste is_command_already_exists en mockant subprocess.run."""
    def mock_run(*args, **kwargs):
        class MockResult:
            returncode = 1  # commande non trouvée
        return MockResult()
    monkeypatch.setattr("subprocess.run", mock_run)
    assert is_command_already_exists("fake_cmd") is False
