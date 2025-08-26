import os
import sys
import stat
import subprocess
import logging
from pathlib import Path
from make_linux_command.config import (
    REQUIRED_FILES,
    DEFAULT_INSTALL_DIR,
    ERROR_STRUCTURE,
    ERROR_PERMISSION,
    ERROR_VENV_CREATION,
    ERROR_VENV_ACTIVATE,
    ERROR_SYMLINK,
    ERROR_WRAPPER,
    ERROR_PIP_MISSING,
    ERROR_PIP_INSTALL,
    SUCCESS_MESSAGE,
)

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")


def check_structure(module_path: Path) -> bool:
    """Vérifie que la structure du module est valide."""
    for f in REQUIRED_FILES:
        if not (module_path / f).exists():
            logging.error(ERROR_STRUCTURE.format(f))
            return False
    return True


def create_venv(command_name: str, venv_base_dir: Path) -> Path:
    """Crée un environnement virtuel dans venv_base_dir/<command_name>/env."""
    venv_parent = venv_base_dir / command_name
    venv_path = venv_parent / "env"
    try:
        venv_parent.mkdir(parents=True, exist_ok=True)
        subprocess.run([sys.executable, "-m", "venv",
                       str(venv_path)], check=True)
        logging.info(f"Environnement virtuel créé : {venv_path}")
        return venv_path
    except subprocess.CalledProcessError as e:
        logging.error(ERROR_VENV_CREATION.format(e))
        sys.exit(1)
    except PermissionError:
        logging.error(
            f"Permissions insuffisantes pour écrire dans {venv_parent}. Utilisez sudo ou un autre dossier.")
        sys.exit(1)


def install_requirements(venv_path: Path, module_path: Path):
    pip_path = venv_path / "bin" / "pip"
    if not pip_path.exists():
        logging.error(ERROR_PIP_MISSING)
        sys.exit(1)
    try:
        # Installer le module en mode editable
        subprocess.run(
            [str(pip_path), "install", "-e", str(module_path.parent)],
            check=True,
            capture_output=True,
            text=True,
        )
        # Installer les dépendances si requirements.txt existe
        requirements_file = module_path / "requirements.txt"
        if requirements_file.exists():
            subprocess.run(
                [str(pip_path), "install", "-r", str(requirements_file)],
                check=True,
                capture_output=True,
                text=True,
            )
            logging.info("Dépendances installées.")
        else:
            logging.warning(
                "Aucun fichier requirements.txt trouvé. Aucune dépendance supplémentaire installée.")
    except subprocess.CalledProcessError as e:
        logging.error(f"Erreur lors de l'installation : {e.stderr}")
        sys.exit(1)


def create_wrapper(module_path: Path, command_name: str, venv_path: Path, local: bool = False, force: bool = False) -> bool:
    install_dir = Path.home() / ".local/bin" if local else DEFAULT_INSTALL_DIR
    install_dir.mkdir(parents=True, exist_ok=True)
    wrapper_path = install_dir / command_name
    if wrapper_path.exists() and not force:
        logging.error(f"Le wrapper {wrapper_path} existe déjà. Utilisez --force pour le remplacer.")
        return False
    script_path = (module_path / "cli.py").resolve()
    wrapper_content = f"""#!/usr/bin/env bash
VENV_PATH="{venv_path}"
SCRIPT_PATH="{script_path}"
if [ ! -d "$VENV_PATH" ]; then
    echo "Erreur : environnement virtuel introuvable à $VENV_PATH" >&2
    exit 1
fi
if [ ! -f "$VENV_PATH/bin/activate" ]; then
    echo "Erreur : impossible de trouver $VENV_PATH/bin/activate" >&2
    exit 1
fi
source "$VENV_PATH/bin/activate" || {{ echo "Échec de l'activation de l'environnement virtuel." >&2; exit 1; }}
exec "$VENV_PATH/bin/python" "$SCRIPT_PATH" "$@"
"""
    try:
        with open(wrapper_path, "w") as f:
            f.write(wrapper_content)
        wrapper_path.chmod(wrapper_path.stat().st_mode | stat.S_IEXEC)
        logging.info(f"Wrapper créé : {wrapper_path}")
        return True
    except Exception as e:
        logging.error(f"Erreur lors de la création du wrapper : {e}")
        return False



def setup_command(
    module_path: Path,
    command_name: str,
    local: bool = False,
    skip_deps: bool = False,
    force: bool = False,
    venv_base_dir: Path = Path("/opt"),
):
    if not check_structure(module_path):
        sys.exit(1)
    if local:
        venv_base_dir = Path.home() / ".local" / "venv"
        logging.info(
            f"Installation locale : l'environnement virtuel sera créé dans {venv_base_dir}")
    if not local and os.geteuid() != 0:
        logging.error(ERROR_PERMISSION)
        sys.exit(1)
    venv_path = create_venv(command_name, venv_base_dir)
    if not skip_deps:
        install_requirements(venv_path, module_path)
    if not create_wrapper(module_path, command_name, venv_path, local, force):
        sys.exit(1)
    logging.info(SUCCESS_MESSAGE.format(command_name, command_name))
