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
    FORBIDDEN_COMMANDS,
)

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")


def check_structure(module_path: Path) -> bool:
    """Vérifie que la structure du module est valide."""
    for f in REQUIRED_FILES:
        if not (module_path / f).exists():
            logging.error(ERROR_STRUCTURE.format(f))
            return False
    return True


def create_venv(command_name: str, venv_base_dir: Path, python_executable: str = sys.executable) -> Path:
    venv_parent = venv_base_dir / command_name
    venv_path = venv_parent / "env"
    try:
        venv_parent.mkdir(parents=True, exist_ok=True)
        # Vérifie que le dossier parent est bien possédé par l'utilisateur
        if not venv_parent.is_relative_to(venv_base_dir):
            raise PermissionError(f"Chemin invalide pour l'environnement virtuel.")
        subprocess.run(
            [python_executable, "-m", "venv", str(venv_path)],
            check=True,
            capture_output=True,
            text=True,
        )
        pip_path = venv_path / "bin" / "pip"
        subprocess.run([str(pip_path), "install", "--upgrade", "pip"], check=True)
        logging.info(f"Environnement virtuel créé : {venv_path}")
        return venv_path.resolve()
    except subprocess.CalledProcessError as e:
        logging.error(f"Erreur lors de la création de l'environnement virtuel : {e.stderr}")
        sys.exit(1)
    except PermissionError as e:
        logging.error(f"Permissions insuffisantes ou chemin invalide : {e}")
        sys.exit(1)




def install_requirements(venv_path: Path, module_path: Path):
    pip_path = venv_path / "bin" / "pip"
    if not pip_path.exists():
        logging.error("pip introuvable dans l'environnement virtuel.")
        sys.exit(1)

    # Cherche requirements.txt de manière sécurisée
    requirements_file = module_path / "requirements.txt"
    if not requirements_file.exists():
        requirements_file = module_path.parent / "requirements.txt"

    # Vérifie que requirements.txt est un fichier régulier et lisible
    if requirements_file.exists():
        if not requirements_file.is_file():
            logging.error(f"{requirements_file} n'est pas un fichier régulier.")
            sys.exit(1)
        try:
            with open(requirements_file, "r") as f:
                content = f.read()
                if not content.strip():
                    logging.warning(f"{requirements_file} est vide.")
                elif len(content) > 10000:  # Limite arbitraire
                    logging.error(f"{requirements_file} semble trop volumineux.")
                    sys.exit(1)
        except (IOError, UnicodeDecodeError) as e:
            logging.error(f"Impossible de lire {requirements_file} : {e}")
            sys.exit(1)

    try:
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
                [str(pip_path), "install", "--no-deps", "-r", str(requirements_file)],
                check=True,
                capture_output=True,
                text=True,
            )
    except subprocess.CalledProcessError as e:
        logging.error(f"Erreur lors de l'installation des dépendances : {e.stderr}")
        sys.exit(1)



def create_wrapper(module_path: Path, command_name: str, venv_path: Path, local: bool = False, force: bool = False) -> bool:
    install_dir = Path.home() / ".local/bin" if local else DEFAULT_INSTALL_DIR
    wrapper_path = install_dir / command_name

    # Vérifie que venv_path et module_path sont des chemins absolus et "sains"
    try:
        venv_path = venv_path.resolve(strict=True)
        module_path = module_path.resolve(strict=True)
        script_path = (module_path / "cli.py").resolve(strict=True)
    except (FileNotFoundError, RuntimeError) as e:
        logging.error(f"Chemin invalide : {e}")
        return False

    # Vérifie que venv_path est bien un sous-dossier de venv_base_dir
    venv_base_dir = Path("/opt") if not local else Path.home() / ".local" / "venv"
    if not venv_base_dir in venv_path.parents:
        logging.error(f"L'environnement virtuel doit être dans {venv_base_dir}.")
        return False

    if wrapper_path.exists() and not force:
        logging.error(f"Le wrapper {wrapper_path} existe déjà. Utilisez --force pour le remplacer.")
        return False

    # Échappe les chemins pour le wrapper Bash
    safe_venv_path = str(venv_path).replace("'", "'\\''")
    safe_script_path = str(script_path).replace("'", "'\\''")

    wrapper_content = f"""#!/usr/bin/env bash
set -euo pipefail
VENV_PATH='{safe_venv_path}'
SCRIPT_PATH='{safe_script_path}'

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

# Vérifie que les fichiers sont bien ceux attendus (optionnel mais recommandé)
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



def is_valid_command_name(name: str) -> bool:
    if not name or not isinstance(name, str):
        return False
    if not re.match(r'^[a-zA-Z0-9_-]+$', name):
        return False
    if name.startswith('-'):
        return False
    if name in FORBIDDEN_COMMANDS:
        return False
    if len(name) > 32:
        return False
    return True



def setup_command(
    module_path: Path,
    command_name: str,
    local: bool = False,
    skip_deps: bool = False,
    force: bool = False,
    venv_base_dir: Path = Path("/opt"),
    python_executable: str = sys.executable,
):
    if not check_structure(module_path):
        sys.exit(1)
    if not is_valid_command_name(command_name):
        logging.error(f"Nom de commande invalide : '{command_name}'.")
        sys.exit(1)

    if local:
        venv_base_dir = Path.home() / ".local" / "venv"
        install_dir = Path.home() / ".local" / "bin"
        logging.info(f"Installation locale dans {venv_base_dir} et {install_dir}.")
    else:
        if os.geteuid() != 0:
            logging.error("Permissions insuffisantes. Utilisez sudo ou installez localement avec --local.")
            sys.exit(1)
        install_dir = DEFAULT_INSTALL_DIR

    # Vérifie si la commande existe déjà
    wrapper_path = install_dir / command_name
    if wrapper_path.exists() and not force:
        logging.error(f"La commande '{command_name}' existe déjà. Utilisez --force pour la remplacer.")
        sys.exit(1)

    # Crée l'environnement virtuel
    venv_path = create_venv(command_name, venv_base_dir, python_executable)
    if not skip_deps:
        install_requirements(venv_path, module_path)

    # Crée le wrapper
    if not create_wrapper(module_path, command_name, venv_path, local, force):
        sys.exit(1)

    logging.info(f"Succès ! La commande '{command_name}' est prête. Essayez : {command_name} --help")


def uninstall_command(command_name: str, local: bool = False, venv_base_dir: Path = Path("/opt")):
    """Désinstalle une commande Linux et son environnement virtuel."""
    logging.info(f"Désinstallation de la commande '{command_name}'...")

    if local:
        venv_base_dir = Path.home() / ".local" / "venv"
        install_dir = Path.home() / ".local/bin"
    else:
        install_dir = DEFAULT_INSTALL_DIR

    # Vérifie que les chemins sont valides avant toute suppression
    wrapper_path = install_dir / command_name
    venv_path = venv_base_dir / command_name / "env"

    if wrapper_path.exists():
        try:
            if not wrapper_path.is_symlink() and not wrapper_path.is_file():
                logging.error(f"{wrapper_path} n'est pas un fichier régulier ou un lien symbolique.")
                sys.exit(1)
            wrapper_path.unlink()
            logging.info(f"Wrapper supprimé : {wrapper_path}")
        except Exception as e:
            logging.error(f"Erreur lors de la suppression du wrapper : {e}")
            sys.exit(1)

    if venv_path.exists():
        try:
            venv_parent = venv_path.parent
            # Vérifie que venv_parent est bien un sous-dossier de venv_base_dir
            if not venv_base_dir in venv_parent.parents:
                logging.error(f"Chemin invalide pour l'environnement virtuel : {venv_parent}")
                sys.exit(1)
            # Supprime uniquement le dossier de la commande
            if venv_parent.is_dir():
                import shutil
                shutil.rmtree(venv_parent)
                logging.info(f"Environnement virtuel supprimé : {venv_parent}")
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
