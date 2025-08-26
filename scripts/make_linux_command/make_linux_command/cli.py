#!/usr/bin/env python3
import click
from pathlib import Path
from make_linux_command.main import setup_command

@click.command()
@click.argument("module_path", type=click.Path(exists=True, file_okay=False, resolve_path=True))
@click.argument("command_name", type=str)
@click.option("--local", is_flag=True, help="Installe la commande et l'environnement virtuel localement (~/.local/venv).")
@click.option("--skip-deps", is_flag=True, help="Ne pas installer les dépendances depuis requirements.txt.")
@click.option("--force", is_flag=True, help="Remplace les fichiers existants (lien symbolique et wrapper).")
@click.option("--venv-dir", type=click.Path(), default="/opt", help="Dossier pour l'environnement virtuel (défaut : /opt).")
def main(module_path: str, command_name: str, local: bool, skip_deps: bool, force: bool, venv_dir: str):
    """Transforme un module Python en commande Linux exécutable."""
    setup_command(
        module_path=Path(module_path),
        command_name=command_name,
        local=local,
        skip_deps=skip_deps,
        force=force,
        venv_base_dir=Path(venv_dir),
    )

if __name__ == "__main__":
    main()
