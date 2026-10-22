# 01 — Magasin de traces

- Statut : ouverte
- Bloquée par : aucune
- Exécution : un agent, puis reviewer adverse

## Tranche

Un client peut enregistrer une trace masquée et la relire. SQLite. Port 8090.

## Accepte

- `POST /v1/traces` avec un corps conforme à `Trace`.
- `GET /v1/traces/{request_id}` renvoie la même trace.
- Un corps avec un e-mail en clair répond 422, et rien n'est écrit.
- `py -m pytest tests -q` reste vert, plus les tests nouveaux de cette issue.

## Oracle

Les tests de `tests/test_masked_span_oracle.py` restent la définition de « masqué ». Le endpoint ne fait pas une seconde politique, il s'appuie sur le modèle.
