# Acceptance — « ça ressemble à Galileo »

Le reviewer adverse valide **visuellement** (screenshot ou parcours navigateur), pas seulement les tests API.

## Must-have (bloquant)

1. Sidebar gauche permanente avec marque **Galileo**, project, `Logs: chat` actif sur `/logs`.
2. Breadcrumb `galileo-local > Log Stream: chat`.
3. Table Logs avec au minimum : Created, Name, Input, Output, External Id, **au moins une colonne métrique** avec badge coloré.
4. Switch Sessions / Traces / Spans avec compteurs.
5. Clic ligne → écran détail avec input/output + scores.
6. Même chrome (sidebar) sur Chat et Experiments.
7. Aucune référence UI à un autre produit métier (CIMR, etc.).

## Should-have

- Bouton Configure Metrics → liste métriques du stream
- Search sur la table
- Pagination
- Empty state avec lien Chat
- Onglets Trends/Signals absents ou disabled (pas d’erreur 404 nues)

## Out of scope v1 (ne pas bloquer)

- Agent graph, Signals, Alerts, Playgrounds fonctionnels
- Flowchart SVG parfait
- Luna / Configure Metrics éditeur cloud
- Thème dark

## Test / oracle UI

Mettre à jour `.cursor/skills/ui-explore/SKILL.md` : le parcours doit ouvrir `/logs`, basculer Traces, ouvrir une trace, vérifier badges. Compte-rendu dans `research/runs/ui-<date>.md`.
