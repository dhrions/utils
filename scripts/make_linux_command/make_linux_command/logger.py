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
