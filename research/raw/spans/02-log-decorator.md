# Log decorator — choix du type et imbrication

- URL : https://docs.galileo.ai/sdk-api/logging/log-decorator/log-decorator
- Lu le 22 octobre 2026
- Question : comment un appel devient un span, et quand la sortie retriever compte comme des documents ?

Le décorateur `@log` crée un span `workflow` par défaut. Les valeurs explicites sont `agent`, `llm`, `retriever`, `tool`, `workflow`. L'entrée est l'ensemble des paramètres non réservés ; la sortie est la valeur de retour. Un tableau renvoyé par un retriever est enregistré comme documents.

`params` recopie un argument de fonction vers un champ de span. Champs communs : `name`, `input`, `metadata`, `tags`. Réservés au span `llm` : `model`, `temperature`, `tools`. Réservé au span `tool` : `tool_call_id`.

Les fonctions décorées s'imbriquent : un `workflow` parent contient les spans des appels enfants. C'est le modèle à suivre pour un agent qui enveloppe un retriever, un outil et un appel de modèle.
