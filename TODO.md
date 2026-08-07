# TODO

Backlog technique du dépôt `utils`, issu de la revue `/review-full` du 2026-08-07.

## Standards CLI/CI

- [ ] Réécrire les 3 commits sans emoji gitmoji si pertinent : `427d7cf`, `f9dab3d`, `0e897f9` (historique, à évaluer)

## Conception

- [ ] Rendre `FONT_PATH` configurable ou vérifié à l'exécution plutôt qu'en dur (python/image/annotate_ui_screenshot.py:51)

## Dépendances

- [ ] Mettre à jour `python/requirements.txt` (versions datées 2022-2023 : certifi, numpy, pandas, requests)

## 🚫 Écarté en revue (ne pas re-signaler)

- Ligne « Version X.Y.Z, DD/MM/YYYY » absente du README — la norme (review-readme.md, point 5)
  dérive cette version de `pyproject.toml`/`package.json`/tag git le plus récent ; ce dépôt n'a
  aucun des trois, donc rien à afficher. Pas un écart, application correcte de la norme à un
  dépôt sans schéma de versionnage (2026-08-07)
