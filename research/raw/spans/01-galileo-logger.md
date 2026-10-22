# Galileo Logger — types de spans

- URL : https://docs.galileo.ai/sdk-api/logging/galileo-logger
- Lu le 22 octobre 2026
- Question : que met Galileo dans chaque type de span ?

Hiérarchie d'envoi : session, puis trace (`start_trace`), puis spans, puis `conclude` et `flush`. Tous les spans portent un nom, une entrée, une sortie, une durée, des tags et des métadonnées.

| Type | Rôle documenté | Champs propres |
|---|---|---|
| `workflow` | Regrouper des spans d'un même flux. Les spans ajoutés ensuite en sont les enfants, jusqu'au `conclude` qui fixe la sortie. | entrée, sortie (peut arriver plus tard), métadonnées |
| `agent` | Entrée et sortie d'un agent. | `agent_type` : supervisor, planner, router ou judge |
| `llm` | Un appel de modèle. | `model`, `temperature`, `tools`, comptes de tokens, `time_to_first_token_ns`, `status_code` |
| `retriever` | Un appel RAG. La sortie alimente des métriques comme Context Adherence. | entrée = requête ; sortie = liste des documents renvoyés ; `status_code` |
| `tool` | Un appel d'outil, y compris MCP. | `tool_call_id` pour le relier à l'appel d'outil du span `llm` ; `status_code` |

Les exemples de la page sont en texte clair. Le chat v1 de galileo-local y écrit le texte de conversation ; les jetons masqués restent valides si un producteur en envoie.
