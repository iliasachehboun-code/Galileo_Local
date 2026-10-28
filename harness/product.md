# Produit

galileo-local est une console Galileo locale pour un ingénieur qui veut tracer un chat agentique, scorer les tours, et comparer des runs — sans compte Galileo cloud.

L’UI doit être **reconnaissable comme Galileo** (sidebar, Log stream, badges métriques). Voir `harness/ui/` et `harness/external/galileo_console_ui.md`.

Il peut :

- ouvrir le Log stream (`/logs`) comme dans la console cloud (Sessions / Traces / Spans) ;
- envoyer un message sur `/chat` pour générer des traces ;
- ouvrir une trace (spans + métriques) ;
- relancer les scores sur un lot et comparer deux runs.

Il ne peut pas (v1) :

- Luna Studio, Signals, assistant sur les traces ;
- remplacer un produit cloud Galileo complet.

Utilisateur de la v1 : développeur local ou déploiement Azure / GCP du même binaire.
