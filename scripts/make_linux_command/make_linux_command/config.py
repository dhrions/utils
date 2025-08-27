from pathlib import Path

# Chemins par défaut (modifiables via les options CLI)
DEFAULT_INSTALL_DIR = Path("/usr/local/bin")
DEFAULT_VENV_BASE_DIR = Path("/opt")

# Structure attendue du module
REQUIRED_FILES = ["cli.py"]

# Messages d'erreur et de succès
ERROR_STRUCTURE = "Erreur : structure du module invalide. Le fichier {} est manquant."
ERROR_PERMISSION = "Erreur : permissions insuffisantes. Utilisez sudo ou installez localement avec --local."
ERROR_VENV_CREATION = "Erreur lors de la création de l'environnement virtuel : {}"
ERROR_VENV_ACTIVATE = "Erreur : impossible d'activer l'environnement virtuel. Vérifiez que {} existe et est accessible."
ERROR_SYMLINK = "Erreur lors de la création du lien symbolique : {}"
ERROR_WRAPPER = "Erreur lors de la création du wrapper : {}"
ERROR_PIP_MISSING = "Erreur : pip n'est pas disponible dans l'environnement virtuel."
ERROR_PIP_INSTALL = "Erreur lors de l'installation des dépendances : {}"
SUCCESS_MESSAGE = "Succès ! La commande '{}' est maintenant disponible. Utilisez-la avec `{}`."

FORBIDDEN_COMMANDS = {
    "ls", "rm", "cat", "echo", "python", "pip", "bash", "sh", "zsh", "fish",
    "if", "then", "else", "fi", "case", "esac", "for", "while", "do", "done",
    "sudo", "root", "admin", "test", "[", "]", "(", ")", "$", "|", ";", "&"
}
