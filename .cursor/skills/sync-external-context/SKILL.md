# Synchroniser le contexte Galileo

Tu maintiens `harness/external/galileo_surface.md` aligné sur la documentation publique.

1. Lis `galileo_local/catalog.py` et relève chaque `doc`.
2. Relis https://docs.galileo.ai/what-is-galileo et les fiches dont l'URL a changé de sens (métrique renommée, famille déplacée, métrique ajoutée).
3. Mets à jour le résumé et, si une métrique publique manque au catalogue, ajoute-la dans `catalog.py` avec son URL et un test dans `tests/test_catalog.py`.
4. N'ajoute pas Luna Studio, Signals ou l'assistant au périmètre v1. Note-les dans la section « laissé de côté » s'ils bougent.
5. Ne copie pas de page Galileo dans le dépôt. Résume et lie.

Déclenchement prévu : commande `/loop` toutes les semaines, ou à la main avant une issue qui touche les métriques.
