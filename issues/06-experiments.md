# 06 — Expériences

- Statut : ouverte / en cours selon l’état du code
- Bloquée par : 05
- Exécution : un agent, puis reviewer adverse

## Tranche

Relancer les scores d’un lot de traces déjà stockées et comparer deux runs. Pas de nouvel appel au LLM du chat.

## Accepte

- `POST /v1/experiments` crée un run nommé à partir de `request_id` existants.
- `GET` de deux runs montre, par métrique, les deux scores.
- Une trace inconnue dans le lot répond 404 sans créer de run partiel.
- La console a un lien vers cette comparaison.

## Oracle

Deux runs sur la même fixture : les métriques code sont identiques. Le test l’affirme.
