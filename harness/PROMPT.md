# Ralph — implémentation d'une issue

Tu es une itération à contexte neuf. La mémoire est le disque.

Lis dans l'ordre :
1. `AGENTS.md`
2. `harness/spec.md`
3. `harness/state/progress.txt`
4. la première issue de `issues/` encore ouverte dont les blocages sont faits

Règles :
- Une seule issue dans ce tour.
- Lance `py -m pytest tests -q`.
- N'affaiblis pas `tests/test_catalog.py` ni `tests/test_masked_span_oracle.py`.
- Pas de valeur personnelle en clair dans les fixtures. Utilise des jetons.
- Si les tests de l'issue passent, marque-la faite dans `harness/state/progress.txt` et écris exactement `<promise>COMPLETE</promise>`.
- Si tu es bloqué deux fois sur la même erreur, écris le blocage dans `progress.txt` et sors sans le signal COMPLETE.

Le reviewer adverse se lance avec `/feature`, pas dans cette boucle. Cette boucle ne sert qu'à finir une issue dont le cadre est déjà accepté et dont les tests résistent.
