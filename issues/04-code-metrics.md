# 04 — Métriques code

- Statut : ouverte
- Bloquée par : 01
- Exécution : un agent, puis reviewer adverse

## Tranche

À l'enregistrement, calculer les métriques `kind: code` actives sur le stream et applicables au span : `pii`, `tool_error`, `precision_at_k`.

## Accepte

- Chaque score persisté a `metric_id`, `score` entre 0 et 1, `passed`, `rationale`.
- `pii` sur la trace fixture masquée est passant.
- `tool_error` lit le statut du span `tool`, sans juge.
- `precision_at_k` ne s'invente pas un score s'il n'y a pas de labels dans les métadonnées : le score est absent, pas un 1.0 de complaisance.
- Les métriques SQL et multimodales ne sont pas calculées sur le stream `chat`.

## Oracle

Test qui poste la trace fixture et relit les scores `pii`.
