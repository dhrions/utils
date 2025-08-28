import os
import re
import subprocess
import logging
from pathlib import Path

def install_requirements(venv_path: Path, module_path: Path, skip_deps: bool = False) -> None:
    """
    Installe les dépendances depuis requirements.txt de manière sécurisée.
    Args:
        venv_path: Chemin vers l'environnement virtuel.
        module_path: Chemin vers le module Python.
        skip_deps: Si True, ne pas installer les dépendances (seulement le module en mode éditable).
    Raises:
        SystemExit: En cas d'erreur critique.
    """
    pip_path = venv_path / "bin" / "pip"
    if not pip_path.exists():
        logging.error("Erreur : pip n'est pas disponible dans l'environnement virtuel.")
        raise SystemExit(1)

    # Installation du module en mode éditable
    try:
        subprocess.run(
            [str(pip_path), "install", "--upgrade", "pip"],
            check=True,
            capture_output=True,
            text=True,
        )
        subprocess.run(
            [str(pip_path), "install", "-e", str(module_path.parent)],
            # [str(pip_path), "install", "-e", str(module_path)],
            check=True,
            capture_output=True,
            text=True,
        )
        logging.info(f"Module installé en mode éditable depuis {module_path.parent}")
    except subprocess.CalledProcessError as e:
        logging.error(f"Échec de l'installation du module : {e.stderr}")
        raise SystemExit(1)

    if skip_deps:
        logging.info("Installation des dépendances ignorée (option --skip-deps).")
        return

    # Recherche du fichier requirements.txt
    requirements_file = module_path / "requirements.txt"
    if not requirements_file.exists():
        requirements_file = module_path.parent / "requirements.txt"
    if not requirements_file.exists():
        logging.info("Aucun fichier requirements.txt trouvé. Installation des dépendances ignorée.")
        return

    # Validation du fichier requirements.txt
    try:
        with open(requirements_file, "r") as f:
            lines = [line.strip() for line in f if line.strip() and not line.startswith("#")]
    except (IOError, UnicodeDecodeError) as e:
        logging.error(f"Impossible de lire {requirements_file} : {e}")
        raise SystemExit(1)

    # Vérification de la taille du fichier (max 10 Ko)
    if requirements_file.stat().st_size > 10 * 1024:
        logging.error(f"Le fichier {requirements_file} est trop volumineux (>10 Ko).")
        raise SystemExit(1)

    # Validation du contenu
    forbidden_patterns = [
        r"^https?://",  # URLs non autorisées
        r";",          # Commandes shell
        r"\|\|",       # Opérateurs logiques
        r"`",          # Command substitution
        r"\$\(.*\)",   # Command substitution
        r"--index-url",  # Options pip dangereuses
        r"--extra-index-url",
    ]
    for line in lines:
        line = line.split("#")[0].strip()
        if not line:
            continue
        if any(re.search(pattern, line) for pattern in forbidden_patterns):
            logging.error(f"Ligne non autorisée dans {requirements_file} : {line}")
            raise SystemExit(1)
        if not re.match(r'^[a-zA-Z0-9_-]+(==|>=|<=|~=|<|>)[^;]+$', line):
            logging.warning(f"Format de dépendance non standard : {line}")

    # Installation des dépendances
    try:
        logging.info(f"Installation des dépendances depuis {requirements_file}...")
        subprocess.run(
            [str(pip_path), "install", "--no-deps", "-r", str(requirements_file)],
            check=True,
            capture_output=True,
            text=True,
        )
    except subprocess.CalledProcessError as e:
        logging.error(f"Échec de l'installation des dépendances : {e.stderr}")
        raise SystemExit(1)
