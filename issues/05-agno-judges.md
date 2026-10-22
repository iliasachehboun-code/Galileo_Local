# 05 — Juge Agno

- Statut : ouverte
- Bloquée par : 04
- Exécution : un agent, puis reviewer adverse

## Tranche

Scorer les métriques `llm_judge` du stream `chat` avec `build_metric_judge`, température 0, sur les spans dont le type est dans `span_types`.

## Accepte

- Une trace fixture reçoit un score pour chaque métrique applicable, ou un statut d'erreur de juge explicite.
- Aucun score passant n'est inventé si le modèle est injoignable.
- La rationale stockée ne contient pas d'e-mail, de téléphone, ni d'IBAN. L'oracle `find_clear_pii` est relu sur la rationale avant écriture.
- `tests/test_metric_judge.py` reste vert.

## Oracle

Test avec un faux modèle qui renvoie un `MetricScore` fixe, pour le chemin de persistance, plus un test qui rejette une rationale contenant un e-mail.
