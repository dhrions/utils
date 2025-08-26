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
)

# Configuration des logs pour les tests
logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

class TestMakeLinuxCommand(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Crée un module de test
        cls.test_module_path = Path("/tmp/test_module")
        cls.test_module_path.mkdir(exist_ok=True)
        (cls.test_module_path / "cli.py").write_text(
            "#!/usr/bin/env python3\nimport click\n@click.command()\ndef main():\n    click.echo('Hello, World!')\nif __name__ == '__main__':\n    main()"
        )
        (cls.test_module_path / "requirements.txt").write_text("click==8.2.1")

    @classmethod
    def tearDownClass(cls):
        # Nettoie le module de test
        if cls.test_module_path.exists():
            for item in cls.test_module_path.iterdir():
                item.unlink()
            cls.test_module_path.rmdir()
        venv_path = Path("/tmp/venv/test_command/env")
        if venv_path.exists():
            for parent in venv_path.parents:
                if parent == Path("/tmp/venv"):
                    break
                try:
                    subprocess.run(["rm", "-rf", str(parent)], check=True)
                except subprocess.CalledProcessError:
                    pass

    def test_check_structure(self):
        # Test avec une structure valide
        self.assertTrue(check_structure(self.test_module_path))
        # Test avec une structure invalide
        (self.test_module_path / "cli.py").unlink()
        self.assertFalse(check_structure(self.test_module_path))
        # Restaure cli.py pour les autres tests
        (self.test_module_path / "cli.py").write_text(
            "#!/usr/bin/env python3\nimport click\n@click.command()\ndef main():\n    click.echo('Hello, World!')\nif __name__ == '__main__':\n    main()"
        )

    @patch("subprocess.run")
    def test_create_venv(self, mock_run):
        mock_run.return_value = MagicMock()
        venv_path = create_venv("test_command", Path("/tmp/venv"))
        mock_run.assert_called_once_with([sys.executable, "-m", "venv", str(venv_path)], check=True)
        self.assertEqual(venv_path, Path("/tmp/venv/test_command/env"))

    @patch("subprocess.run")
    def test_install_requirements(self, mock_run):
        mock_run.return_value = MagicMock()
        venv_path = Path("/tmp/venv/test_command/env")
        venv_path.mkdir(parents=True, exist_ok=True)
        (venv_path / "bin").mkdir(exist_ok=True)
        (venv_path / "bin" / "pip").touch()
        install_requirements(venv_path, self.test_module_path)
        mock_run.assert_any_call([str(venv_path / "bin" / "pip"), "install", "-e", str(self.test_module_path.parent)], check=True, capture_output=True, text=True)

    @patch("pathlib.Path.unlink")
    @patch("pathlib.Path.chmod")
    def test_create_wrapper(self, mock_chmod, mock_unlink):
        m = mock_open()
        with patch("builtins.open", m):
            venv_path = Path("/tmp/venv/test_command/env")
            create_wrapper(self.test_module_path, "test_command", venv_path, local=True, force=False)
            wrapper_path = Path.home() / ".local/bin" / "test_command"
            m.assert_called_once_with(wrapper_path, "w")

    @patch("make_linux_command.main.create_venv")
    @patch("make_linux_command.main.install_requirements")
    @patch("make_linux_command.main.create_wrapper")
    def test_setup_command(self, mock_wrapper, mock_install, mock_venv):
        mock_venv.return_value = Path("/tmp/venv/test_command/env")
        mock_install.return_value = None
        mock_wrapper.return_value = True
        setup_command(
            module_path=self.test_module_path,
            command_name="test_command",
            local=True,
            skip_deps=False,
            force=False,
            venv_base_dir=Path("/tmp/venv"),
        )
        mock_venv.assert_called_once_with("test_command", Path.home() / ".local" / "venv")
        mock_install.assert_called_once_with(mock_venv.return_value, self.test_module_path)
        mock_wrapper.assert_called_once_with(self.test_module_path, "test_command", mock_venv.return_value, True, False)

if __name__ == "__main__":
    unittest.main()
