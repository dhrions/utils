# TODO

Backlog technique du dépôt `utils`, issu de la revue `/review-full` du 2026-08-07.

## README

- [ ] Ajouter une ligne « Version X.Y.Z, DD/MM/YYYY » en en-tête — bloqué : ce dépôt n'a aucun schéma de versionnage (pas de tag git, pas de `pyproject.toml` racine), fabriquer un numéro serait trompeur. Décision à prendre : adopter un versionnage du dépôt, ou documenter explicitement l'absence de version (README.adoc:1-2)

## Documentation Antora

- [ ] Revoir la `category` de `.repo-meta.json` (`Outils de Développement` → archétype 🛠️ Projet applicatif) au regard du layout réel, clairement 🗂️ Collection/infrastructure (nav groupée par domaine, pas de point d'entrée CLI unique) — à trancher explicitement plutôt que corriger à l'aveugle (.repo-meta.json:4)

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
