# Parcours UI de la console (clone Galileo)

À utiliser quand la console répond sur `http://127.0.0.1:8090`.

Référence d’acceptance : `harness/ui/acceptance.md`.

1. Ouvre `http://127.0.0.1:8090/logs` (ou `/`).
2. Vérifie la **sidebar** (marque Galileo, project, `Logs: chat` actif).
3. Vérifie le breadcrumb `galileo-local > Log Stream: chat`.
4. Vérifie la **table** : Created, Name, Input, Output, External Id, au moins une colonne métrique avec badge.
5. Bascule Sessions / Traces / Spans ; les compteurs changent ou filtrent.
6. Ouvre une trace ; lis Input / Output / Metrics dans le détail.
7. Ouvre `/chat`, envoie un message court, suis le lien vers Logs si présent.
8. Écris le compte-rendu dans `research/runs/ui-<date>.md` : URL, étapes, bugs, **et** si le must-have acceptance est respecté.

Si la page est encore l’ancienne console à deux colonnes sans table métriques : statut **FAIL acceptance**, pas seulement « bugs mineurs ».
