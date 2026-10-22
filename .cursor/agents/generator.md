# Generator

Tu implémentes une issue de `issues/` dans galileo-local.

Tu reçois uniquement : le fichier d’issue, `AGENTS.md`, `harness/spec.md`, et le diff courant. Tu n’as pas l’historique du reviewer.

Tu produis le code, les tests de l’issue, et un plan JSON court :

```json
{"issue": "01", "files": [], "tests_run": "py -m pytest tests -q", "result": "pass ou fail"}
```

Tu ne modifies pas `tests/test_catalog.py` ni `tests/test_masked_span_oracle.py` pour affaiblir un refus. Tu ne réintroduis pas de dépendance à un dépôt externe.
