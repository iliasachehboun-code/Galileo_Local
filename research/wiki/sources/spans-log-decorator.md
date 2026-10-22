# Log decorator

Fiche : `research/raw/spans/02-log-decorator.md`. Page : https://docs.galileo.ai/sdk-api/logging/log-decorator/log-decorator

Le type par défaut est `workflow`. Un retour de type tableau sur un `retriever` devient la liste de documents. `model`, `temperature` et `tools` ne se posent que sur un `llm`. `tool_call_id` ne se pose que sur un `tool`. L'imbrication parent-enfant est le moyen de représenter une couche qui contient d'autres appels.
