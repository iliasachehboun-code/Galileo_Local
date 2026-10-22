# Mémoire de recherche

Tu capitalises une recherche au lieu de la laisser dans le chat.

1. Le sujet est celui demandé, plus `harness/external/galileo_surface.md` comme contexte déjà connu.
2. Découpe en questions. Pour chaque question, garde au plus 15 sources utiles.
3. Écris les sources brutes dans `research/raw/<sujet>/`.
4. Écris une synthèse par source dans `research/wiki/sources/` et une synthèse transverse dans `research/wiki/concepts/`.
5. Mets à jour `research/index.yaml` : résumé, liste des sources, chemins.
6. Ne stocke pas de secrets (clés API). Un exemple de span peut utiliser du texte fictif ou des jetons.

Commandes équivalentes, à la main : `/research`, puis `/research-distill` pour resserrer les synthèses, `/research-lint` pour les liens cassés et les doublons.
