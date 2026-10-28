# 07 — Console UI clone Galileo

- Statut : ouverte
- Bloquée par : 01, 03 (API + données traces disponibles)
- Exécution : un agent UI, puis reviewer adverse + skill `ui-explore`

## Tranche

Remplacer la console HTML minimale par une UI dont le chrome et la table Log stream sont reconnaissables comme Galileo, selon `harness/ui/` et `harness/external/galileo_console_ui.md`.

## Stack autorisée

- Soit un frontend moderne (ex. React + Vite) buildé et servi par FastAPI en statique
- Soit du HTML/CSS/JS soigné servi par FastAPI
- L’API existante (`/v1/traces`, scores, experiments, chat) reste la source de vérité ; pas de second backend

## Accepte

- Critères de `harness/ui/acceptance.md` (must-have) tous verts
- `py -m pytest tests -q` reste vert (adapter les tests console HTML si le markup change)
- Compte-rendu `research/runs/ui-*.md` du skill ui-explore

## Oracle

Screenshot ou parcours : sidebar + table avec Input/Output + badge métrique + détail au clic. Le reviewer refuse une page à deux colonnes sans table métriques.
