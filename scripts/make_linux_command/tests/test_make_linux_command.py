import os
import sys
import stat
import subprocess
import logging
from pathlib import Path
from unittest.mock import patch, MagicMock, mock_open
import unittest
from make_linux_command.main import (
    check_structure,
    create_venv,
    install_requirements,
    create_wrapper,
    setup_command,
    uninstall_command,
)

class TestMakeLinuxCommand(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Utilise un chemin temporaire unique pour éviter les conflits
        cls.test_module_path = Path("/tmp/test_module_unique")
        cls.test_module_path.mkdir(parents=True, exist_ok=True)
        (cls.test_module_path / "cli.py").write_text(
            """#!/usr/bin/env python3
import click
@click.command()
def main():
    click.echo('Hello, World!')
if __name__ == '__main__':
    main()
"""
        )
        (cls.test_module_path / "requirements.txt").write_text("click==8.2.1")
        # Crée un chemin temporaire unique pour l'environnement virtuel
        cls.venv_base_dir = Path("/tmp/venv_unique")
        cls.venv_base_dir.mkdir(parents=True, exist_ok=True)

    @classmethod
    def tearDownClass(cls):
        # Nettoie les fichiers et dossiers créés
        if cls.test_module_path.exists():
            for item in cls.test_module_path.iterdir():
                item.unlink()
            cls.test_module_path.rmdir()
        if cls.venv_base_dir.exists():
            for item in cls.venv_base_dir.iterdir():
                if item.is_dir():
                    subprocess.run(["rm", "-rf", str(item)], check=False)

    def setUp(self):
        # Nettoie avant chaque test
        wrapper_path = Path.home() / ".local/bin" / "test_command"
        if wrapper_path.exists():
            wrapper_path.unlink()

    def test_check_structure(self):
        self.assertTrue(check_structure(self.test_module_path))
        (self.test_module_path / "cli.py").unlink()
        self.assertFalse(check_structure(self.test_module_path))
        (self.test_module_path / "cli.py").write_text(
            """#!/usr/bin/env python3
import click
@click.command()
def main():
    click.echo('Hello, World!')
if __name__ == '__main__':
    main()
"""
        )

    @patch("subprocess.run")
    def test_create_venv_success(self, mock_run):
        mock_run.return_value = MagicMock()
        venv_path = create_venv("test_command", self.venv_base_dir)
        # Vérifie les deux appels : création du venv et mise à jour de pip
        mock_run.assert_any_call([sys.executable, "-m", "venv", str(venv_path)], check=True, capture_output=True, text=True)
        mock_run.assert_any_call([str(venv_path / "bin" / "pip"), "install", "--upgrade", "pip"], check=True)

    @patch("subprocess.run")
    def test_create_venv_permission_error(self, mock_run):
        mock_run.side_effect = PermissionError("Permission denied")
        with self.assertRaises(SystemExit):
            create_venv("test_command", Path("/root/venv"))

    @patch("subprocess.run")
    def test_install_requirements_no_requirements(self, mock_run):
        mock_run.return_value = MagicMock()
        venv_path = self.venv_base_dir / "test_command" / "env"
        venv_path.mkdir(parents=True, exist_ok=True)
        (venv_path / "bin").mkdir(exist_ok=True)
        (venv_path / "bin" / "pip").touch()
        (self.test_module_path / "requirements.txt").unlink()
        install_requirements(venv_path, self.test_module_path)
        calls = [call[0][0] for call in mock_run.call_args_list]
        expected_call = [str(venv_path / "bin" / "pip"), "install", "-r", str(self.test_module_path / "requirements.txt")]
        self.assertNotIn(expected_call, calls)

    @patch("subprocess.run")
    def test_install_requirements_success(self, mock_run):
        mock_run.return_value = MagicMock()
        venv_path = self.venv_base_dir / "test_command" / "env"
        venv_path.mkdir(parents=True, exist_ok=True)
        (venv_path / "bin").mkdir(exist_ok=True)
        (venv_path / "bin" / "pip").touch()
        (self.test_module_path / "requirements.txt").touch()
        install_requirements(venv_path, self.test_module_path)
        mock_run.assert_any_call([str(venv_path / "bin" / "pip"), "install", "-e", str(self.test_module_path.parent)], check=True, capture_output=True, text=True)
        mock_run.assert_any_call([str(venv_path / "bin" / "pip"), "install", "-r", str(self.test_module_path / "requirements.txt")], check=True, capture_output=True, text=True)

    @patch("pathlib.Path.unlink")
    @patch("pathlib.Path.chmod")
    @patch("pathlib.Path.mkdir")
    def test_create_wrapper_local(self, mock_mkdir, mock_chmod, mock_unlink):
        m = mock_open()
        with patch("builtins.open", m):
            venv_path = self.venv_base_dir / "test_command" / "env"
            create_wrapper(self.test_module_path, "test_command", venv_path, local=True, force=True)
            wrapper_path = Path.home() / ".local/bin" / "test_command"
            m.assert_called_once_with(wrapper_path, "w")

    @patch("pathlib.Path.unlink")
    @patch("pathlib.Path.chmod")
    @patch("pathlib.Path.mkdir")
    def test_create_wrapper_global(self, mock_mkdir, mock_chmod, mock_unlink):
        m = mock_open()
        with patch("builtins.open", m):
            venv_path = self.venv_base_dir / "test_command" / "env"
            create_wrapper(self.test_module_path, "test_command", venv_path, local=False, force=True)
            wrapper_path = Path("/usr/local/bin/test_command")
            m.assert_called_once_with(wrapper_path, "w")

    @patch("make_linux_command.main.create_venv")
    @patch("make_linux_command.main.install_requirements")
    @patch("make_linux_command.main.create_wrapper")
    def test_setup_command_local(self, mock_wrapper, mock_install, mock_venv):
        mock_venv.return_value = self.venv_base_dir / "test_command" / "env"
        mock_install.return_value = None
        mock_wrapper.return_value = True
        setup_command(
            module_path=self.test_module_path,
            command_name="test_command",
            local=True,
            skip_deps=False,
            force=True,
            venv_base_dir=self.venv_base_dir,
        )
        mock_venv.assert_called_once_with("test_command", Path.home() / ".local" / "venv")
        mock_install.assert_called_once_with(mock_venv.return_value, self.test_module_path)
        mock_wrapper.assert_called_once_with(self.test_module_path, "test_command", mock_venv.return_value, True, True)

    @patch("make_linux_command.main.create_venv")
    @patch("make_linux_command.main.install_requirements")
    @patch("make_linux_command.main.create_wrapper")
    def test_setup_command_global_no_permission(self, mock_wrapper, mock_install, mock_venv):
        with patch("os.geteuid", return_value=1000):
            with self.assertRaises(SystemExit):
                setup_command(
                    module_path=self.test_module_path,
                    command_name="test_command",
                    local=False,
                    skip_deps=False,
                    force=True,
                    venv_base_dir=self.venv_base_dir,
                )

    @patch("make_linux_command.main.check_structure", return_value=False)
    def test_setup_command_invalid_structure(self, mock_check):
        with self.assertRaises(SystemExit):
            setup_command(
                module_path=self.test_module_path,
                command_name="test_command",
                local=True,
                skip_deps=False,
                force=True,
                venv_base_dir=self.venv_base_dir,
            )

    @patch("pathlib.Path.unlink")
    @patch("make_linux_command.main._remove_dir")
    @patch("pathlib.Path.rmdir")
    def test_uninstall_command_local(self, mock_rmdir, mock_remove_dir, mock_unlink):
        # Crée les chemins nécessaires
        wrapper_path = Path.home() / ".local/bin" / "test_command"
        wrapper_path.parent.mkdir(parents=True, exist_ok=True)
        wrapper_path.touch()
        venv_path = Path.home() / ".local/venv/test_command/env"
        venv_path.parent.mkdir(parents=True, exist_ok=True)
        (venv_path).mkdir(exist_ok=True)

        # Simule la suppression récursive et la suppression du répertoire
        mock_remove_dir.return_value = None
        mock_rmdir.return_value = None

        # Appelle la fonction
        with patch("sys.exit") as mock_exit:
            uninstall_command(command_name="test_command", local=True)

        # Vérifie que les appels ont bien eu lieu
        mock_unlink.assert_called_once_with()
        mock_remove_dir.assert_called()
        mock_rmdir.assert_called_once_with()
        mock_exit.assert_not_called()



if __name__ == "__main__":
    unittest.main()
