# Parcours UI de la console

À utiliser quand la console répond sur `http://127.0.0.1:8090`.

1. Ouvre `http://127.0.0.1:8090/` dans le navigateur.
2. Vérifie que la liste des traces s’affiche (projet `galileo-local`, stream `chat`).
3. Ouvre une trace. Lis chaque span et les scores.
4. Ouvre `http://127.0.0.1:8090/chat`, envoie un message court, vérifie la réponse.
5. Reviens sur `/` et confirme qu’une nouvelle trace apparaît.
6. Écris le compte-rendu dans `research/runs/ui-<date>.md` : URL, étapes, bugs.

Si la page ne répond pas, le compte-rendu dit « bloqué » et s’arrête.
