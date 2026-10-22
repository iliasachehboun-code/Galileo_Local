# Architecture

Clone local de [Galileo](https://docs.galileo.ai/what-is-galileo) : chat Agno, traces, métriques, expériences, console. Indépendant de tout autre projet applicatif.

```
Utilisateur
    |
    |  GET /chat  ·  POST /v1/chat
    v
galileo-local  :8090
    agent Agno (réponse claire)
         |
         |  une Trace par message
         v
    ingest  ->  SQLite (data/galileo.db)
    métriques code (pii, tool_error, precision@k, …)
    juge Agno (métriques llm_judge du catalogue)
    expériences (rejouer un jeu de traces, comparer deux runs)
    console GET /  (historique, détail, scores)
```

## Objets, comme Galileo

| Objet | Rôle ici |
|---|---|
| Project | `galileo-local` |
| Log stream | `chat` pour le trafic du chat. Un stream par expérience. |
| Session | Une conversation (`session_id`). |
| Trace | Un message chat (`request_id`). |
| Span | `agent` + `llm` pour le chat v1. Les types `workflow`, `retriever`, `tool` restent acceptés pour coller au modèle Galileo. |

Chaque span a `input_masked`, `output_masked` et `metadata` (noms de champs Galileo). Le chat v1 y écrit le texte clair de la conversation. La métrique `pii` note la présence de données personnelles ; elle ne bloque pas l’écriture du chat.

## Métriques

31 métriques, les familles publiques Galileo : agentic, expression, multimodal, response quality, RAG retrieval, RAG generation, safety, text-to-SQL. Le détail et l’URL de chaque fiche sont dans `galileo_local/catalog.py`.

Deux façons de les calculer, comme Galileo :

- **Code** — `pii`, `tool_error`, `precision_at_k`, `sql_correctness`, `sql_injection`. Déterministes.
- **Juge LLM** — le reste. Un agent Agno (`galileo_local/judges.py`) score un span et renvoie `MetricScore`.
- **Custom** — les trois formes Galileo restent ouvertes : juge, code, composite. Aucune métrique custom n’est requise pour la v1.

Le stream `chat` active les 24 métriques texte. Il laisse éteintes les 3 multimodales et les 4 text-to-SQL (pas d’image, audio ni SQL dans le chat v1).

## Expériences

Un jeu de traces déjà stockées. On relance le calcul des métriques, on garde le run, on compare deux runs sur les mêmes `request_id`. Pas de nouvel appel au LLM du chat dans l’expérience : on évalue des traces déjà produites.

## Console

- `GET /chat` — saisie d’un message, réponse Agno.
- `GET /` — liste des traces du stream, détail en arbre de spans, scores.
- `GET /experiments` — comparaison de runs.

Bind : `127.0.0.1:8090` par défaut ; `GALILEO_BIND_HOST=0.0.0.0` pour Azure / GCP.

## Ce que cette v1 ne construit pas

Luna-2 et Luna Studio, Signals, l’assistant qui interroge les traces, les alertes Slack, le tracing distribué OpenTelemetry. Le catalogue multimodal et SQL est là ; leur calcul sur le chat, non.

## Les 12 concepts dans cette architecture

| Concept | Où il vit |
|---|---|
| Requirement Confidence Validation | `harness/CONTRACT.md` |
| Customize your coding agent | `AGENTS.md`, `.cursor/rules/`, `.cursor/commands/feature.md` |
| Latest Documentation Control | URLs dans le catalogue ; skill `get-api-docs` (Context Hub) |
| Intelligent Software Installation | `harness/INSTALL_AGENT_PROMPT.md` |
| HIL-to-AFK Workflow | Backlog `issues/` + `harness/ralph.ps1` |
| Coding Agent Automations | `harness/automations.md` |
| Ralph loop | `harness/ralph.ps1`, `harness/PROMPT.md` |
| Adversarial loop | `.cursor/agents/generator.md`, `.cursor/agents/adversarial-reviewer.md` |
| Autonomous UI Testing with AI | `.cursor/skills/ui-explore` |
| Autonomous Tests : Oracles | `tests/test_masked_span_oracle.py`, `tests/test_catalog.py` |
| External Context Synchronization | `harness/external/galileo_surface.md` |
| Persistent Research Memory | `research/index.yaml`, `research/wiki/` |
