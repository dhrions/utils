import os
import re
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
    venv_parent = venv_base_dir / command_name
    venv_path = venv_parent / "env"
    try:
        venv_parent.mkdir(parents=True, exist_ok=True)
        subprocess.run(
            [sys.executable, "-m", "venv", str(venv_path)],
            check=True,
            capture_output=True,
            text=True,
        )
        # Mise à jour de pip dans l'environnement virtuel
        pip_path = venv_path / "bin" / "pip"
        subprocess.run([str(pip_path), "install", "--upgrade", "pip"], check=True)
        logging.info(f"Environnement virtuel créé : {venv_path}")
        return venv_path
    except subprocess.CalledProcessError as e:
        logging.error(f"Erreur lors de la création de l'environnement virtuel : {e.stderr}")
        sys.exit(1)
    except PermissionError:
        logging.error(f"Permissions insuffisantes pour écrire dans {venv_parent}.")
        sys.exit(1)



def install_requirements(venv_path: Path, module_path: Path):
    pip_path = venv_path / "bin" / "pip"
    if not pip_path.exists():
        logging.error(ERROR_PIP_MISSING)
        sys.exit(1)

    # Cherche d'abord dans module_path, puis dans module_path.parent
    requirements_file = module_path / "requirements.txt"
    if not requirements_file.exists():
        requirements_file = module_path.parent / "requirements.txt"

    try:
        # Installe toujours le module en mode éditable
        subprocess.run(
            [str(pip_path), "install", "--upgrade", "pip"],
            check=True,
            capture_output=True,
            text=True,
        )
        subprocess.run(
            [str(pip_path), "install", "-e", str(module_path.parent)],
            check=True,
            capture_output=True,
            text=True,
        )

        if requirements_file.exists():
            logging.info(f"Installation des dépendances depuis {requirements_file}...")
            subprocess.run(
                [str(pip_path), "install", "-r", str(requirements_file)],
                check=True,
                capture_output=True,
                text=True,
            )
        else:
            logging.warning(f"Aucun fichier requirements.txt trouvé dans {module_path} ou {module_path.parent}.")
    except subprocess.CalledProcessError as e:
        logging.error(f"Erreur lors de l'installation des dépendances : {e.stderr}")
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

def is_valid_command_name(name: str) -> bool:
    """Vérifie que le nom de la commande est valide et sûr."""
    if not re.match(r'^[a-zA-Z0-9_-]+$', name):
        return False
    if name.startswith('-'):
        return False
    # Vérifie que ce n'est pas une commande système existante
    system_commands = {"ls", "rm", "cat", "echo", "python", "pip", "bash"}
    if name in system_commands:
        return False
    return True

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
    if not is_valid_command_name(command_name):
        logging.error(f"Nom de commande invalide : '{command_name}'. Utilisez uniquement des caractères alphanumériques, '_' ou '-'.")
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

def uninstall_command(command_name: str, local: bool = False, venv_base_dir: Path = Path("/opt")):
    """Désinstalle une commande Linux et son environnement virtuel."""
    logging.info(f"Désinstallation de la commande '{command_name}'...")

    # Détermine les chemins en fonction du mode (local ou global)
    if local:
        venv_base_dir = Path.home() / ".local" / "venv"
        install_dir = Path.home() / ".local/bin"
    else:
        install_dir = DEFAULT_INSTALL_DIR

    # Chemin du wrapper
    wrapper_path = install_dir / command_name
    if wrapper_path.exists():
        try:
            wrapper_path.unlink()
            logging.info(f"Wrapper supprimé : {wrapper_path}")
        except Exception as e:
            logging.error(f"Erreur lors de la suppression du wrapper : {e}")
            sys.exit(1)

    # Chemin de l'environnement virtuel
    venv_path = venv_base_dir / command_name / "env"
    if venv_path.exists():
        try:
            # Supprime l'environnement virtuel
            for item in venv_path.parent.iterdir():
                item.unlink() if item.is_file() else _remove_dir(item)
            venv_path.parent.rmdir()
            logging.info(f"Environnement virtuel supprimé : {venv_path.parent}")
        except Exception as e:
            logging.error(f"Erreur lors de la suppression de l'environnement virtuel : {e}")
            sys.exit(1)

    logging.info(f"La commande '{command_name}' a été désinstallée avec succès.")

def _remove_dir(directory: Path):
    """Supprime récursivement un dossier."""
    for item in directory.iterdir():
        if item.is_dir():
            _remove_dir(item)
        else:
            item.unlink()
    directory.rmdir()
