# TODO

Backlog technique du dépôt `utils`, issu de la revue `/review-full` du 2026-08-07.

## README

- [ ] Ajouter une ligne « Version X.Y.Z, DD/MM/YYYY » en en-tête (README.adoc:1-4)
- [ ] Ajouter un bloc ⚡ TL;DR (README.adoc:1)
- [ ] Vérifier si le titre H1 avec émoji nécessite une dérogation explicite (README.adoc:1, non vérifié)
- [ ] Afficher l'image du dépôt (`utils.png`) dans le README (README.adoc:1)
- [ ] Ajouter une section Installation/Utilisation pour le CLI `adoc_link_check` (README.adoc:1-17)
- [ ] Ajouter des émojis aux éléments de liste (README.adoc:8-9,15-17)
- [ ] Ajouter un émoji au titre « Liens utiles » (README.adoc:13)

## Documentation Antora

- [ ] Déplacer `nav.adoc` vers l'emplacement canonique `docs/modules/ROOT/nav.adoc` (actuel : `docs/modules/nav.adoc`)
- [ ] Ajouter des émojis aux entrées de `nav.adoc` (docs/modules/nav.adoc:1-45)
- [ ] Ajouter une section TL;DR à `index.adoc` (docs/modules/ROOT/pages/index.adoc:1-4)
- [ ] Afficher l'image d'illustration du dépôt dans `index.adoc` (symlink `docs/modules/ROOT/images/utils.png` manquant)
- [ ] Renseigner le champ `category` dans `.repo-meta.json` (archétype documentaire ambigu)
- [ ] Clarifier/supprimer le dossier `antora/` résiduel (juste un `build/`), qui contredit la commande documentée dans CLAUDE.md:20-24

## Standards CLI/CI

- [ ] Corriger l'entry point invalide `adoc-link-checker.cli:cli` (module avec tiret, casse `pip install .`) (scripts/adoc_link_check/setup.py:25)
- [ ] Synchroniser la version : `cli.py:50` (1.0.0) vs `setup.py:8` (0.1.0)
- [ ] Faire respecter XDG à `config.py` et ajouter une option `--config` à `cli.py`
- [ ] Réécrire les 3 commits sans emoji gitmoji si pertinent : `427d7cf`, `f9dab3d`, `0e897f9` (historique, à évaluer)
- [ ] Ajouter un `.gitea/workflows/audit.yml` pour auditer les dépendances de `setup.py`

## Conception

- [ ] Corriger le log `✅ URL checked` trompeur, émis même après un échec (scripts/adoc_link_check/main.py:74-77)
- [ ] Retirer l'import mort `ROOT_DIR` depuis `config.py` (scripts/adoc_link_check/main.py:12-14)
- [ ] Rendre `FONT_PATH` configurable ou vérifié à l'exécution plutôt qu'en dur (python/image/annotate_ui_screenshot.py:51)

## Dépendances

- [ ] Remplacer les épingles exactes de `adoc_link_check` (setup.py/requirements.txt) par un plancher (`click>=8.x`, `requests>=2.30`, etc.)
- [ ] Mettre à jour `python/requirements.txt` (versions datées 2022-2023 : certifi, numpy, pandas, requests)
- [ ] Vérifier les vulnérabilités connues une fois `audit.yml` en place (non vérifié faute d'accès réseau pendant la revue)

## Tests

- [ ] Ajouter une suite de tests pour le CLI `adoc_link_check` (aucun test dans tout le dépôt)
