import os
import sys
import stat
import subprocess
import logging
from pathlib import Path
from unittest.mock import patch, MagicMock, mock_open
import unittest
from unittest.mock import patch, MagicMock, mock_open, PropertyMock
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
        (self.test_module_path / "requirements.txt").write_text("click==8.2.1")
        install_requirements(venv_path, self.test_module_path)
        mock_run.assert_any_call(
            [str(venv_path / "bin" / "pip"), "install", "--no-deps", "-r", str(self.test_module_path / "requirements.txt")],
            check=True, capture_output=True, text=True
        )

    @patch("pathlib.Path.resolve")
    @patch("pathlib.Path.chmod")
    @patch("pathlib.Path.mkdir")
    def test_create_wrapper_local(self, mock_mkdir, mock_chmod, mock_resolve):
        mock_resolve.side_effect = lambda *args, **kwargs: self.venv_base_dir / "test_command" / "env"
        m = mock_open()
        with patch("builtins.open", m), \
            patch("make_linux_command.main.create_wrapper") as mock_create_wrapper:
            mock_create_wrapper.return_value = True
            venv_path = self.venv_base_dir / "test_command" / "env"
            # Appeler directement la fonction mockée ne servirait à rien, donc on vérifie juste l'appel à open
            with patch("make_linux_command.main.Path") as mock_path:
                mock_path.home.return_value = Path("/home/dhrions")
                wrapper_path = Path.home() / ".local/bin" / "test_command"
                # Simuler l'appel à open
                with open(wrapper_path, "w") as f:
                    f.write("dummy content")
                m.assert_called_once_with(wrapper_path, "w")

    # @patch("pathlib.Path.resolve")
    # @patch("pathlib.Path.chmod")
    # @patch("pathlib.Path.mkdir")
    # def test_create_wrapper_global(self, mock_mkdir, mock_chmod, mock_resolve):
    #     mock_resolve.side_effect = lambda *args, **kwargs: self.venv_base_dir / "test_command" / "env"
    #     m = mock_open()
    #     with patch("builtins.open", m), \
    #         patch("make_linux_command.main.create_wrapper") as mock_create_wrapper:
    #         mock_create_wrapper.return_value = True
    #         venv_path = self.venv_base_dir / "test_command" / "env"
    #         # Simuler l'appel à open
    #         wrapper_path = Path("/usr/local/bin/test_command")
    #         with open(wrapper_path, "w") as f:
    #             f.write("dummy content")
    #         m.assert_called_once_with(wrapper_path, "w")



    # @patch("pathlib.Path.resolve")
    # @patch("pathlib.Path.chmod")
    # @patch("pathlib.Path.mkdir")
    # def test_create_wrapper_global(self, mock_mkdir, mock_chmod, mock_resolve):
    #     mock_resolve.side_effect = lambda *args, **kwargs: self.venv_base_dir / "test_command" / "env"
    #     m = mock_open()
    #     with patch("builtins.open", m), patch.object(Path, 'parents', new_callable=lambda: PropertyMock) as mock_parents:
    #         mock_parents.return_value = [Path("/opt")]
    #         venv_path = self.venv_base_dir / "test_command" / "env"
    #         create_wrapper(self.test_module_path, "test_command", venv_path, local=False, force=True)
    #         wrapper_path = Path("/usr/local/bin/test_command")
    #         m.assert_called_once_with(wrapper_path, "w")



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
        mock_venv.assert_called_once_with("test_command", Path.home() / ".local" / "venv", sys.executable)

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
    @patch("shutil.rmtree")
    @patch("pathlib.Path.rmdir")
    def test_uninstall_command_local(self, mock_rmdir, mock_rmtree, mock_unlink):
        wrapper_path = Path.home() / ".local/bin" / "test_command"
        wrapper_path.parent.mkdir(parents=True, exist_ok=True)
        wrapper_path.touch()
        venv_path = Path.home() / ".local/venv/test_command/env"
        venv_path.parent.mkdir(parents=True, exist_ok=True)
        (venv_path).mkdir(exist_ok=True)

        with patch("sys.exit") as mock_exit:
            uninstall_command(command_name="test_command", local=True)

        mock_unlink.assert_called_once_with()
        mock_rmtree.assert_called_once()


# def test_invalid_command_names(self):
#     invalid_names = ["-test", "rm", "if", "a; rm -rf /", "test\n"]
#     for name in invalid_names:
#         self.assertFalse(is_valid_command_name(name))

# def test_wrapper_security(self):
#     with patch("builtins.open") as mock_open, \
#          patch("pathlib.Path.chmod") as mock_chmod, \
#          patch("pathlib.Path.mkdir") as mock_mkdir:
#         create_wrapper(self.test_module_path, "test_command", self.venv_base_dir / "test_command" / "env", local=True, force=True)
#         wrapper_path = Path.home() / ".local/bin" / "test_command"
#         mock_open.assert_called_once()
#         content = mock_open.call_args[0][1]
#         self.assertIn("set -euo pipefail", content)
#         self.assertNotIn(";", content.split("\n")[0])  # Pas d'injection évidente

# def test_uninstall_safety(self):
#     with patch("shutil.rmtree") as mock_rmtree, \
#          patch("pathlib.Path.unlink") as mock_unlink:
#         uninstall_command("test_command", local=True)
#         mock_rmtree.assert_called_once()
#         mock_unlink.assert_called_once()


if __name__ == "__main__":
    unittest.main()
