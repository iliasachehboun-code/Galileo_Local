# Visual tokens — ressembler à Galileo

Référence : capture console Galileo (fond clair, accents lavande / violet, badges verts-rouges).

## Direction

- Clair (light). Pas de thème dark par défaut.
- Densité **dashboard SaaS**, pas landing marketing.
- Une seule composition : sidebar + main. Pas de hero, pas de cards empilées sur Logs.
- Typo UI lisible (éviter Inter/Roboto/Arial « par défaut agent » si possible ; préférer une grotesk proche product — ex. Geist, IBM Plex Sans, ou Source Sans — chargée localement ou via font déjà dispo).
- **Pas** de gradient violet-indigo marketing, pas de glow, pas de pills partout.

## Couleurs (CSS variables cibles)

```css
:root {
  --gal-bg: #f7f7fb;           /* fond page légèrement lavande-gris */
  --gal-surface: #ffffff;      /* table, panneaux */
  --gal-sidebar: #ffffff;      /* ou #fafafa */
  --gal-border: #e6e6ef;
  --gal-text: #1c1c28;
  --gal-muted: #6b6b7b;
  --gal-accent: #6d5efc;       /* violet Configure Metrics / liens actifs */
  --gal-accent-soft: #eef0ff;  /* fond item nav actif */
  --gal-row-hover: #f3f4fb;
  --gal-badge-ok-bg: #e7f8ef;
  --gal-badge-ok-fg: #0f7a45;
  --gal-badge-bad-bg: #fdecee;
  --gal-badge-bad-fg: #c62828;
  --gal-badge-neutral-bg: #eef0f4;
  --gal-badge-neutral-fg: #5c5c6a;
  --gal-na: #9a9aaa;
}
```

Ajuster après comparaison visuelle avec la capture ; l’important est le **système** (accent violet + badges OK/KO), pas le pixel-perfect des hex.

## Composants

| Élément | Règle |
|---|---|
| Nav active | fond `--gal-accent-soft`, texte `--gal-accent`, pas de grosse bordure |
| Bouton primaire | fond `--gal-accent`, texte blanc, radius ~8px (pas pill full) |
| Table header | texte muted, icône métrique violette si judge/AI |
| Badge bool OK | fond ok, texte ok, radius ~999 pour le chip **uniquement** sur badges métriques |
| Badge fail / 0% | fond bad / texte bad |
| N/A | `--gal-na`, pas de chip |
| Truncation | ellipsis CSS ; title/tooltip au survol |

## Motion (2–3 max)

1. Hover row (fond)
2. Transition courte panneau détail / sélection span
3. Skeleton pulse léger au chargement

Pas d’animations décoratives sur la table.

## Anti-patterns (refus reviewer)

- Page unique sans sidebar
- Liste `request_id` sans colonnes Input/Output/métriques
- Scores en texte brut `0.87 true` sans badge
- Chat comme écran d’accueil dominant
- Cards empilées à la place de la data table
- Copier le branding d’un autre produit (CIMR, etc.)
