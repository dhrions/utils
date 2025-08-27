#!/usr/bin/env python3
import click
from pathlib import Path
from make_linux_command.main import setup_command, uninstall_command

@click.group(invoke_without_command=True)
@click.pass_context
def cli(ctx):
    """Transforme un module Python en commande Linux exécutable."""
    if ctx.invoked_subcommand is None:
        # Vérifie que les arguments requis sont présents
        if not ctx.params.get("module_path") or not ctx.params.get("command_name"):
            click.echo(ctx.get_help(), err=True)
            ctx.exit(1)
        ctx.invoke(install_command, **ctx.params)



@cli.command()
@click.argument("module_path", type=click.Path(exists=True, file_okay=False, resolve_path=True))
@click.argument("command_name", type=str)
@click.option("--local", is_flag=True, help="Installe la commande et l'environnement virtuel localement (~/.local/venv).")
@click.option("--skip-deps", is_flag=True, help="Ne pas installer les dépendances depuis requirements.txt.")
@click.option("--force", is_flag=True, help="Remplace les fichiers existants (lien symbolique et wrapper).")
@click.option("--venv-dir", type=click.Path(), default="/opt", help="Dossier pour l'environnement virtuel (défaut : /opt).")
@click.pass_context
def install_command(ctx, module_path, command_name, local, skip_deps, force, venv_dir):
    """Installe une commande Linux à partir d'un module Python."""
    setup_command(
        module_path=Path(module_path),
        command_name=command_name,
        local=local,
        skip_deps=skip_deps,
        force=force,
        venv_base_dir=Path(venv_dir),
    )

@cli.command()
@click.argument("command_name", type=str)
@click.option("--local", is_flag=True, help="Désinstalle une commande installée localement.")
@click.option("--venv-dir", type=click.Path(), default="/opt", help="Dossier de l'environnement virtuel (défaut : /opt).")
def uninstall(command_name, local, venv_dir):
    """Désinstalle une commande Linux précédemment installée."""
    uninstall_command(
        command_name=command_name,
        local=local,
        venv_base_dir=Path(venv_dir),
    )

# Renommez la fonction `install` en `install_command` pour éviter les conflits
cli.add_command(install_command, name="install")

if __name__ == "__main__":
    cli()
