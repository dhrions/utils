import os
import sys
import logging
from pathlib import Path
from .venv_manager import create_venv
from .requirements_installer import install_requirements
from .wrapper_generator import create_wrapper
from .command_validator import check_structure, is_valid_command_name, is_command_already_exists
from .logger import log_installed_command, remove_installed_command
from .config import DEFAULT_INSTALL_DIR, ERROR_PERMISSION, SUCCESS_MESSAGE

def setup_command(
    module_path: Path,
    command_name: str,
    local: bool = False,
    skip_deps: bool = False,
    force: bool = False,
    venv_base_dir: Path = Path("/opt"),
    python_executable: str = sys.executable,
    no_log: bool = False,
):
    """Installe une commande Linux à partir d'un module Python."""
    if not check_structure(module_path):
        sys.exit(1)
    if is_command_already_exists(command_name):
        logging.error(f"La commande '{command_name}' existe déjà dans $PATH.")
        sys.exit(1)
    if not is_valid_command_name(command_name):
        logging.error(f"Nom de commande invalide : '{command_name}'.")
        sys.exit(1)

    # Détermine les chemins d'installation
    if local:
        venv_base_dir = Path.home() / ".local" / "venv"
        install_dir = Path.home() / ".local" / "bin"
    else:
        if not os.access(DEFAULT_INSTALL_DIR, os.W_OK) or not os.access(venv_base_dir, os.W_OK):
            logging.error(ERROR_PERMISSION)
            sys.exit(1)

    wrapper_path = install_dir / command_name
    if wrapper_path.exists() and not force:
        logging.error(f"La commande '{command_name}' existe déjà. Utilisez --force pour la remplacer.")
        sys.exit(1)

    # Création de l'environnement virtuel
    venv_path = create_venv(command_name, venv_base_dir, python_executable)
    # Installation des dépendances et du module
    install_requirements(venv_path, module_path, skip_deps=skip_deps)
    # Création du wrapper
    if not create_wrapper(module_path, command_name, venv_path, local, force):
        sys.exit(1)
    # Enregistrement de la commande installée
    if not no_log:
        repo_root = Path(__file__).resolve().parent.parent
        log_installed_command(repo_root, command_name, module_path)
    logging.info(SUCCESS_MESSAGE.format(command_name, command_name))

def uninstall_command(command_name: str, local: bool = False, venv_base_dir: Path = Path("/opt")):
    """Désinstalle une commande Linux et son environnement virtuel."""
    logging.info(f"Désinstallation de la commande '{command_name}'...")
    install_dir = Path.home() / ".local/bin" if local else DEFAULT_INSTALL_DIR
    venv_base_dir = Path.home() / ".local/venv" if local else venv_base_dir
    wrapper_path = install_dir / command_name
    venv_path = venv_base_dir / command_name / "env"

    if wrapper_path.exists():
        try:
            wrapper_path.unlink()
            logging.info(f"Wrapper supprimé : {wrapper_path}")
        except Exception as e:
            logging.error(f"Erreur lors de la suppression du wrapper : {e}")
            sys.exit(1)

    if venv_path.exists():
        try:
            venv_parent = venv_path.parent
            if venv_base_dir not in venv_parent.parents:
                logging.error(f"Chemin invalide pour l'environnement virtuel : {venv_parent}")
                sys.exit(1)
            import shutil
            shutil.rmtree(venv_parent)
            logging.info(f"Environnement virtuel supprimé : {venv_parent}")
        except Exception as e:
            logging.error(f"Erreur lors de la suppression de l'environnement virtuel : {e}")
            sys.exit(1)

    # Mise à jour du log
    repo_root = Path(__file__).resolve().parent.parent
    remove_installed_command(repo_root, command_name)
    logging.info(f"La commande '{command_name}' a été désinstallée avec succès.")