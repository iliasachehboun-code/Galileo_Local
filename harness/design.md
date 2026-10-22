# Design

Une console lisible : historique à gauche, détail à droite.

En-tête : projet `galileo-local`, stream `chat`, liens chat / expériences.

Liste : heure, `request_id`, statut. Pas besoin d’afficher toute la question dans la liste.

Au clic : spans en arbre. Pour chaque span, nom, type, input, output, scores.

Les scores s’affichent en nombre entre 0 et 1 plus le booléen `passed`. Un `pii` à 0 est montré en premier.

Page chat séparée (`/chat`) : champ message, réponse, lien vers la trace.

Pas de graphique dans la v1. Pas de thème sombre obligatoire.
