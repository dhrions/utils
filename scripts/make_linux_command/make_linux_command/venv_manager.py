import os
import sys
import subprocess
import logging
from pathlib import Path

def create_venv(command_name: str, venv_base_dir: Path, python_executable: str = sys.executable) -> Path:
    """Crée un environnement virtuel de manière sécurisée."""
    venv_parent = venv_base_dir / command_name
    venv_path = venv_parent / "env"
    try:
        venv_parent.mkdir(parents=True, exist_ok=True)
        if not os.access(venv_parent, os.W_OK | os.X_OK):
            raise PermissionError(f"Permissions insuffisantes pour {venv_parent}.")
        subprocess.run(
            [python_executable, "-m", "venv", str(venv_path)],
            check=True,
            capture_output=True,
            text=True,
        )
        pip_path = venv_path / "bin" / "pip"
        if not pip_path.exists():
            raise RuntimeError("Échec de la création de l'environnement virtuel.")
        subprocess.run([str(pip_path), "install", "--upgrade", "pip"], check=True)
        logging.info(f"Environnement virtuel créé : {venv_path}")
        return venv_path.resolve()
    except (subprocess.CalledProcessError, PermissionError, RuntimeError) as e:
        logging.error(f"Erreur lors de la création de l'environnement virtuel : {e}")
        raise
