import os
import re
import subprocess
import logging
from pathlib import Path
from .config import REQUIRED_FILES, FORBIDDEN_COMMANDS

def check_structure(module_path: Path) -> bool:
    """Vérifie que la structure du module est valide."""
    for f in REQUIRED_FILES:
        if not (module_path / f).exists():
            logging.error(f"Erreur : structure du module invalide. Le fichier {f} est manquant.")
            return False
    return True

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

def is_command_already_exists(command_name: str) -> bool:
    return subprocess.run(["which", command_name], capture_output=True).returncode == 0
