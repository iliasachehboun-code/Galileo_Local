# galileo-local — carte agent

## Invariants

- Ce dépôt est autonome : chat Agno + API traces + console. Pas de dépendance à un autre projet applicatif.
- Project / stream par défaut : `galileo-local` / `chat`.
- Le catalogue `galileo_local/catalog.py` reste aligné sur les métriques publiques Galileo. On n’invente pas un id, on n’en retire pas un.
- Le stream `chat` active les 24 métriques texte. Multimodal et text-to-SQL restent au catalogue, éteints sur ce stream.
- `user_id` et `session_id` sont des identifiants opaques. Pas d’e-mail, pas de téléphone dans ces champs.
- La métrique `pii` score la présence de données personnelles dans les spans ; le chat v1 accepte le texte clair.
- Jamais ignorer un test flaky. Si un test passe puis échoue sans changement de code, on corrige le test avant de continuer.
- Un oracle rouge bloque l’écriture suivante. On ne modifie pas un test d’oracle pour le faire passer.
- Le juge Agno ne reconstruit pas une valeur personnelle à partir d’un jeton masqué s’il en voit un.

## Stack

- Python 3.12, Pydantic v2, FastAPI, SQLite local, Agno (chat + juge de métriques).
- Console : UI clone Galileo (`harness/ui/`) servie sur `http://127.0.0.1:8090`. Frontend moderne (ex. React) autorisé s’il est buildé et servi par FastAPI ; l’API `/v1/*` reste le backend unique.
- La home visuelle est le **Log stream**, pas le chat.

## Commandes

```bash
py -m pytest tests -q
py -m galileo_local.app
```

Installation : coller `harness/INSTALL_AGENT_PROMPT.md` dans un coding agent, ou `py -m pip install -r requirements.txt` puis les commandes ci-dessus.

## Harness

- Contrat : `harness/CONTRACT.md`
- Spec par phases : `harness/spec.md`
- Produit, design, règles : `harness/product.md`, `harness/design.md`, `harness/business_rules.md`
- UI clone : `harness/ui/`, surface console cloud : `harness/external/galileo_console_ui.md`
- Contexte Galileo figé : `harness/external/galileo_surface.md`
- Backlog : `issues/`
- Boucle Ralph : `harness/ralph.ps1` et `harness/PROMPT.md`
- Skill adversarial : `.cursor/skills/adversarial-feature/SKILL.md`
- Commande : `.cursor/commands/feature.md`
