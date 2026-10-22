# Règles

1. `user_id` / `session_id` / `request_id` ne portent pas d’e-mail, téléphone ou IBAN.
2. Les clés de métadonnées `email`, `cin`, `rib`, `phone`, `plaintext`, `clear_value`, `raw_pii`, `secret` sont interdites sur l’API traces stricte (oracle).
3. Un score de juge ne cite pas une valeur personnelle en clair. Il nomme au plus le type de donnée.
4. Un échec du juge ne supprime pas la trace et ne fabrique pas un score passant.
5. Le stream `chat` ne calcule pas `visual_quality`, `visual_fidelity`, `interruption_detection`, `sql_correctness`, `sql_adherence`, `sql_injection`, `sql_efficiency`.
6. On n’ajoute pas de métrique hors catalogue sans une fiche dans `harness/external/galileo_surface.md`.
7. Les tests d’oracle de `tests/test_masked_span_oracle.py` et `tests/test_catalog.py` ne se contournent pas pour « faire passer » une régression.
8. Ce dépôt ne dépend d’aucun autre projet applicatif : le chat et la console sont autosuffisants.
