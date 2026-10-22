# Union Span et StepType

- URL : https://docs.galileo.ai/sdk-api/typescript/reference/types/type-aliases/Span
- URL liée : https://docs.galileo.ai/sdk-api/typescript/reference/types/variables/StepType
- Lu le 22 octobre 2026
- Question : le jeu `workflow`, `agent`, `llm`, `retriever`, `tool` est-il fermé ?

`Span` est l'union `WorkflowSpan | AgentSpan | LlmSpan | RetrieverSpan | ToolSpan`.

`StepType` est plus large. Il ajoute `control`, `trace` et `session` à côté des cinq types de spans. Trace et session sont les parents, pas des spans de contenu. `control` n'est pas un type que galileo-local émet.

La v1 locale s'en tient aux cinq membres de l'union `Span`, comme `harness/external/galileo_surface.md`.
