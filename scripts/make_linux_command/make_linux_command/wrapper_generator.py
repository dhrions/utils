import os
import stat
import shlex
import logging
from pathlib import Path

def create_wrapper(module_path: Path, command_name: str, venv_path: Path, local: bool = False, force: bool = False) -> bool:
    """Crée un wrapper Bash sécurisé."""
    install_dir = Path.home() / ".local/bin" if local else Path("/usr/local/bin")
    wrapper_path = install_dir / command_name
    try:
        venv_path = venv_path.resolve(strict=True)
        module_path = module_path.resolve(strict=True)
        script_path = (module_path / "cli.py").resolve(strict=True)
    except (FileNotFoundError, RuntimeError) as e:
        logging.error(f"Chemin invalide : {e}")
        return False

    venv_base_dir = Path.home() / ".local/venv" if local else Path("/opt")
    if venv_base_dir not in venv_path.parents:
        logging.error(f"L'environnement virtuel doit être dans {venv_base_dir}.")
        return False

    if wrapper_path.exists() and not force:
        logging.error(f"Le wrapper {wrapper_path} existe déjà. Utilisez --force pour le remplacer.")
        return False

    safe_venv_path = shlex.quote(str(venv_path))
    safe_script_path = shlex.quote(str(script_path))
    wrapper_content = f"""#!/usr/bin/env bash
set -euo pipefail
VENV_PATH={safe_venv_path}
SCRIPT_PATH={safe_script_path}
if [ ! -d "$VENV_PATH" ]; then
    echo "Erreur : environnement virtuel introuvable à $VENV_PATH" >&2
    exit 1
fi
if [ ! -f "$VENV_PATH/bin/activate" ]; then
    echo "Erreur : impossible de trouver $VENV_PATH/bin/activate" >&2
    exit 1
fi
if [ ! -f "$SCRIPT_PATH" ]; then
    echo "Erreur : script introuvable à $SCRIPT_PATH" >&2
    exit 1
fi
if [ ! -O "$VENV_PATH/bin/activate" ] || [ ! -O "$SCRIPT_PATH" ]; then
    echo "Erreur : fichiers non possédés par l'utilisateur actuel" >&2
    exit 1
fi
source "$VENV_PATH/bin/activate" || {{ echo "Échec de l'activation de l'environnement virtuel." >&2; exit 1; }}
exec "$VENV_PATH/bin/python" "$SCRIPT_PATH" "$@"
"""

    try:
        install_dir.mkdir(parents=True, exist_ok=True)
        with open(wrapper_path, "w") as f:
            f.write(wrapper_content)
        wrapper_path.chmod(wrapper_path.stat().st_mode | stat.S_IEXEC)
        logging.info(f"Wrapper créé : {wrapper_path}")
        return True
    except Exception as e:
        logging.error(f"Erreur lors de la création du wrapper : {e}")
        return False
