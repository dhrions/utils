import os
import re
import sys
import stat
import shlex
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
        logging.error(f"{ERROR_VENV_CREATION.format(e)}")
        sys.exit(1)

def install_requirements(venv_path: Path, module_path: Path):
    """Installe les dépendances depuis requirements.txt de manière sécurisée."""
    pip_path = venv_path / "bin" / "pip"
    if not pip_path.exists():
        logging.error(ERROR_PIP_MISSING)
        sys.exit(1)

    requirements_file = module_path / "requirements.txt"
    if not requirements_file.exists():
        requirements_file = module_path.parent / "requirements.txt"

    if requirements_file.exists():
        try:
            if requirements_file.stat().st_size > 10 * 1024:  # 10 Ko max
                logging.error(f"{requirements_file} est trop volumineux (>10 Ko).")
                sys.exit(1)
            with open(requirements_file, "r") as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith("#"):
                        continue
                    if not re.match(r'^[a-zA-Z0-9_-]+(==|>=|<=|~=|<|>)[^;]+$', line):
                        logging.warning(f"Ligne suspecte dans {requirements_file} : {line}")
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
        logging.error(f"{ERROR_PIP_INSTALL.format(e.stderr)}")
        sys.exit(1)

def create_wrapper(module_path: Path, command_name: str, venv_path: Path, local: bool = False, force: bool = False) -> bool:
    """Crée un wrapper Bash sécurisé."""
    install_dir = Path.home() / ".local/bin" if local else DEFAULT_INSTALL_DIR
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
        logging.error(f"{ERROR_WRAPPER.format(e)}")
        return False

def is_valid_command_name(name: str) -> bool:
    """Valide le nom de la commande."""
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
    forbidden_patterns = ["python", "pip", "apt", "yum", "dnf", "brew", "npm"]
    if any(name.startswith(cmd) for cmd in forbidden_patterns):
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
    """Installe une commande Linux à partir d'un module Python."""
    if not check_structure(module_path):
        sys.exit(1)
    if not is_valid_command_name(command_name):
        logging.error(f"Nom de commande invalide : '{command_name}'.")
        sys.exit(1)

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

    venv_path = create_venv(command_name, venv_base_dir, python_executable)
    if not skip_deps:
        install_requirements(venv_path, module_path)
    if not create_wrapper(module_path, command_name, venv_path, local, force):
        sys.exit(1)
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
    logging.info(f"La commande '{command_name}' a été désinstallée avec succès.")
