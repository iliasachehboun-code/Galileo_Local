# Automatisations Cursor

À créer dans https://cursor.com/automations une fois l'issue 01 mergée. Pas avant : il n'y a pas encore de service à surveiller.

## Oracles chaque matin

- Dépôt : ce projet.
- Déclencheur : cron, chaque jour ouvré à 8 h, heure de Paris.
- Instruction : lance `py -m pytest tests -q` dans `galileo-local`. Si un test échoue, ouvre une pull request qui ne change rien au produit et décrit l'échec, puis préviens sur Slack. Si tout passe, un message Slack « oracles verts » suffit. Ne modifie pas `tests/test_masked_span_oracle.py` ni `tests/test_catalog.py`.

## Revue à l'ouverture d'une pull request

- Déclencheur : pull request ouverte sur ce dépôt.
- Instruction : lis le diff. Cherche une valeur personnelle en clair, un span de couche 8 avec du texte, une métrique ajoutée sans URL Galileo, un oracle affaibli. Commente la pull request. N'approuve pas à la place de l'humain.
