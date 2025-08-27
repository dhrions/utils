import logging
import datetime
from pathlib import Path

def log_installed_command(repo_root: Path, command_name: str, module_path: Path) -> None:
    """
    Enregistre les informations de la commande installée dans un fichier de log.
    """
    log_file = repo_root / "installed_commands.log"
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_entry = f"{timestamp} | Command: {command_name} | Module: {module_path}\n"
    try:
        with open(log_file, "a") as f:
            f.write(log_entry)
        logging.info(f"Commande enregistrée dans {log_file}.")
    except IOError as e:
        logging.warning(f"Impossible d'écrire dans le fichier de log : {e}")

def remove_installed_command(repo_root: Path, command_name: str) -> None:
    """
    Supprime l'entrée d'une commande désinstallée du fichier de log.
    """
    log_file = repo_root / "installed_commands.log"
    if not log_file.exists():
        return
    try:
        with open(log_file, "r") as f:
            lines = f.readlines()
        with open(log_file, "w") as f:
            for line in lines:
                if command_name not in line:
                    f.write(line)
        logging.info(f"Entrée pour la commande '{command_name}' supprimée du log.")
    except IOError as e:
        logging.warning(f"Impossible de mettre à jour le fichier de log : {e}")
