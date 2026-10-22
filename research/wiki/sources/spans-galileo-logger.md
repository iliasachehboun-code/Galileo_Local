# Galileo Logger

Fiche : `research/raw/spans/01-galileo-logger.md`. Page : https://docs.galileo.ai/sdk-api/logging/galileo-logger

Les cinq types partagent nom, entrée, sortie, durée, tags et métadonnées. `workflow` groupe les enfants jusqu'au `conclude`. `agent` ajoute `agent_type`. `llm` ajoute modèle, température, outils et tokens. `retriever` a une requête en entrée et une liste de documents en sortie. `tool` porte `tool_call_id` et le code de statut.
