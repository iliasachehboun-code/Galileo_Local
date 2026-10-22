# Surface Galileo figée

Source : documentation publique. Index : https://docs.galileo.ai/llms.txt. Page produit : https://docs.galileo.ai/what-is-galileo.

Galileo est une plateforme d’observabilité, d’évaluation et de garde-fous pour des applications GenAI et agentiques. Le parcours d’entrée documenté est : enregistrer une trace, évaluer cette trace, lancer une expérience.

## Ce que la v1 reprend

- Projets, log streams, sessions, traces, spans.
- Types de spans : workflow, agent, llm, retriever, tool.
- Métriques out-of-the-box listées dans `galileo_local/catalog.py`, chacune avec l’URL de sa fiche.
- Métriques custom : juge LLM, code, composite. Forme prévue, aucune métrique custom obligatoire.
- Expériences : un jeu de traces, un run, une comparaison. Guide : https://docs.galileo.ai/getting-started/experiments.

## Ce que la v1 laisse de côté

- Luna-2 et Luna Studio.
- Signals.
- AI Assistant sur les traces.
- Tracing distribué OpenTelemetry.
- Alertes.

## Garde-fous

Dans Galileo, une métrique peut aussi servir de garde-fou au runtime. Ici les métriques scorent les traces déjà enregistrées. Le chat v1 n’utilise pas les scores comme bloqueur d’entrée.

## Mise à jour

Le skill `.cursor/skills/sync-external-context/SKILL.md` est le seul chemin prévu pour modifier ce fichier.
