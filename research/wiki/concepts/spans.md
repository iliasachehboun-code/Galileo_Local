# Spans Galileo pour le chat local

Synthèse. Notes : `research/raw/spans/`. Contexte : `harness/external/galileo_surface.md`.

Galileo n’a que cinq types de spans de contenu : `workflow`, `agent`, `llm`, `retriever`, `tool`. La trace est un tour (`request_id`). La session est la conversation (`session_id`). On n’émet pas de span `control`.

## Arbre d’un message chat (v1)

```
trace  (project=galileo-local, stream=chat)
  agent
  llm
```

Les types `workflow`, `retriever` et `tool` restent acceptés par le modèle pour coller à Galileo (RAG, outils) si on les ajoute plus tard.

## Ce que chaque type reçoit

`agent` — tour agentique. Entrée / sortie du message.

`llm` — appel modèle. Prompt, génération, métadonnées `model`, tokens.

`retriever` — requête + documents.

`tool` — arguments + résultat ; `tool_call_id` relie à l’appel outil du `llm`.

`workflow` — étape sans appel modèle.
