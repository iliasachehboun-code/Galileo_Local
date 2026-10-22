# Niveaux de span attendus par les métriques

- URL : https://docs.galileo.ai/concepts/metrics/custom-metrics/custom-metrics-ui-llm
- URL liée : https://docs.galileo.ai/concepts/metrics/custom-metrics/custom-metrics-ui-code
- Lu le 22 octobre 2026
- Question : quel contenu chaque type doit-il avoir pour qu'une métrique puisse le lire ?

Niveaux documentés pour une métrique :

| Niveau | Contenu attendu |
|---|---|
| Session | Plusieurs traces, une conversation. |
| Trace | Un tour : message, appels internes, première réponse. |
| Retriever | Entrée = requête. Sortie = documents retrouvés. |
| LLM | Entrée = historique jusqu'à cet appel. Sortie = dernière génération. |
| Tool | Entrée = arguments. Sortie = résultat de l'outil. |

Le scorer code reçoit un `step_object` parmi `Session`, `Trace`, `WorkflowSpan`, `AgentSpan`, `LlmSpan`, `RetrieverSpan`, `ToolSpan`. Il lit entrée, sortie, métadonnées et, pour un workflow, les enfants. Un span `workflow` ou `agent` sert donc à juger une trajectoire, pas un seul document.

Conséquence locale : le span `llm` doit contenir le prompt réellement envoyé au modèle, et le span `retriever` les extraits. Un juge ne doit pas reconstruire une valeur personnelle derrière un jeton masqué.
