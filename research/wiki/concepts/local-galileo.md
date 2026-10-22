# Galileo locale (standalone)

Synthèse de cadrage. Sources : `research/index.yaml`.

Galileo enregistre des traces hiérarchiques (session, trace, spans), calcule des métriques out-of-the-box ou custom, et compare des runs dans des expériences. galileo-local reprend ces objets et les 31 métriques publiques, avec un chat Agno intégré qui produit une trace par message.

Déploiement : processus unique FastAPI sur le port 8090, SQLite local, clé OpenAI via `.env`. Bind `0.0.0.0` pour Azure / GCP.

À enrichir via le skill `research-memory` quand une issue exige une fiche précise.
