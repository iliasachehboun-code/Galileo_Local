# Prompt à coller dans l’agent (issue 07)

Copie le bloc ci-dessous tel quel.

---

Tu travailles dans le dépôt **galileo-local** uniquement.

## Mission

Implémenter l’issue `issues/07-galileo-console-ui.md` : remplacer la console actuelle par une UI **clone de la console Galileo cloud** (Log stream), pas une page debug maison.

## Lis d’abord (dans cet ordre)

1. `harness/external/galileo_console_ui.md` — ce que montre le vrai Galileo
2. `harness/ui/README.md`
3. `harness/ui/information_architecture.md`
4. `harness/ui/screens.md`
5. `harness/ui/visual_tokens.md`
6. `harness/ui/acceptance.md`
7. `AGENTS.md`, `harness/design.md`

## Contraintes

- Backend existant inchangé dans son rôle : FastAPI + SQLite + `/v1/traces`, scores, chat, experiments.
- Tu peux ajouter un frontend (React+Vite ou équivalent) **buildé et servi** par FastAPI, ou du HTML/CSS/JS soigné — le résultat doit passer `harness/ui/acceptance.md`.
- Home visuelle = `/logs` (table Log stream). Chat n’est pas le centre.
- Sidebar + breadcrumb + table (Created, Name, Input, Output, External Id, colonnes métriques en badges) + switch Sessions/Traces/Spans + détail au clic.
- Tokens : light, accent violet, badges vert/rouge/gris — voir `visual_tokens.md`.
- Pas de dépendance à CIMR ni autre projet.
- Adapter les tests console si le markup change ; `pytest` doit rester vert.
- Mettre à jour le skill ui-explore si besoin ; produire `research/runs/ui-<date>.md`.

## Hors scope

Trends, Agent graph, Signals, Alerts, Playgrounds fonctionnels, Book a demo, Luna.

## Definition of done

- Must-have de `harness/ui/acceptance.md` OK
- `py -m pytest tests -q` vert
- Compte-rendu ui-explore écrit
- Résumé JSON : `{"issue":"07","files":[...],"tests_run":"py -m pytest tests -q","result":"pass|fail"}`

---
