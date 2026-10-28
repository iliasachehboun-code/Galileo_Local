# Design

La console clone **doit ressembler à la console Galileo cloud**, pas à une page debug interne.

Référence figée : `harness/external/galileo_console_ui.md`  
Spec d’implémentation : `harness/ui/` (IA, écrans, tokens, acceptance).

## Résumé v1

- Shell : sidebar + breadcrumb + zone principale.
- Écran central : **Log stream table** (`/logs`) avec niveaux Sessions / Traces / Spans et colonnes métriques en badges.
- Détail : spans + panneau Input / Output / Metrics.
- Chat (`/chat`) et Experiments restent, dans le même shell.
- Light theme, accent violet, badges vert / rouge / gris.

## Non-négociable

Si on enlève le logo « Galileo » et que la page pourrait être n’importe quel admin CRUD, le design a échoué.

Détail opérationnel → `harness/ui/screens.md` et `harness/ui/visual_tokens.md`.
