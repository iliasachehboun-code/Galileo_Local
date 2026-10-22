# Contrat

Statut : clos. Le besoin est assez clair pour implémenter. On ne rouvre pas ces points dans les issues.

| Lecture | Décision | Suffisant |
|---|---|---|
| Clarté du problème | On veut une Galileo locale autonome : chat, traces, métriques, expériences, console. | oui |
| Objectif | Une plateforme locale déployable (local, Azure, GCP) sans dépendance à un autre dépôt applicatif. | oui |
| Critères de succès | Un message chat produit une trace visible scorée. Les 24 métriques du stream ont un score. Les oracles catalogue restent verts. | oui |
| Périmètre | Dedans : objets Galileo, catalogue des 31 métriques, chat Agno, juge Agno, expériences, console :8090. Dehors : Luna-2, Luna Studio, Signals, assistant, alertes, OpenTelemetry. Multimodal et text-to-SQL au catalogue, éteints sur `chat`. | oui |
| Cohérence | Project `galileo-local`, stream `chat`. La métrique `pii` score ; le chat v1 stocke le texte de conversation. | oui |

Validation : ce contrat tient lieu de cadrage pour `harness/spec.md` et `architecture.md`.
