# Spec

Référence : `harness/CONTRACT.md` et `architecture.md`. Une phase = une issue.

## Phase 1 — Magasin de traces

API locale `127.0.0.1:8090`. `POST /v1/traces` accepte un `Trace`. `GET /v1/traces/{request_id}` le rend. SQLite dans `data/galileo.db`. Projet et log stream créés à la volée (`galileo-local` / `chat`).

## Phase 3 — Console

`GET /` sert la console : traces du stream, clic, arbre des spans, scores. `GET /chat` sert le chat. Le skill `ui-explore` joue le parcours.

## Phase 4 — Métriques code

À l’enregistrement d’une trace, calculer `pii`, `tool_error`, `precision_at_k` quand le span s’y prête. Persister `metric_id`, `score`, `passed`, `rationale`.

## Phase 5 — Juge Agno

Pour chaque métrique `llm_judge` active sur le stream et applicable au type de span, appeler le juge. Température 0. Stocker le `MetricScore`. Une panne du juge laisse la trace enregistrée et le score en erreur.

## Phase 6 — Expériences

`POST /v1/experiments` prend une liste de `request_id` déjà stockés et un nom de run. Recalcule les scores. `GET` compare deux runs. Pas de nouvel appel au LLM du chat.
