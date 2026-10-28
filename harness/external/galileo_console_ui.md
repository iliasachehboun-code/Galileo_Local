# Surface UI Galileo (console réelle) — figée

Sources :
- Capture console Galileo (Log stream `gateway`, projet type `IA-cimr-gpt`), 2026.
- Docs : [Sessions overview](https://docs.galileo.ai/concepts/logging/sessions/sessions-overview), [Logging overview](https://docs.galileo.ai/concepts/logging/overview), [Instrumentation / Log streams](https://docs.galileo.ai/sdk-api/logging/logging-basics).

Ce fichier décrit **ce que la console cloud Galileo montre**. Ce n’est pas la spec d’implémentation locale (voir `harness/ui/`).

## Hiérarchie d’objets (inchangée)

```
Project
  └── Log stream
        └── Sessions
              └── Traces
                    └── Spans
```

Métriques configurées **au niveau du Log stream**. Expériences ≈ session d’évaluation avec plusieurs traces.

## Shell de la console

| Zone | Contenu observé |
|---|---|
| Logo | « Galileo » en haut à gauche de la sidebar |
| Sidebar | Home · Project (sélecteur) · sous-menu projet · section globale · CTA bas |
| Sous-menu projet | Overview · **Logs: &lt;stream&gt;** · Playgrounds · Experiments |
| Section globale | Datasets · Prompts · Annotation Queues · Metrics · Dashboards · Controls |
| Header droit | Email utilisateur + avatar |
| Breadcrumb | `Project > Log Stream: &lt;name&gt;` |
| CTA header | bouton violet **Configure Metrics** |

## Vue Log stream (écran principal)

Onglets horizontaux sous le breadcrumb :

| Onglet | Rôle cloud | Clone v1 |
|---|---|---|
| **Logs** | table des événements | **à implémenter** |
| Trends | analytics | hors v1 (onglet visible désactivé ou absent) |
| Agent graph | graphe d’agent | hors v1 |
| Signals | motifs d’échec | hors v1 |
| Controls | garde-fous runtime | hors v1 |
| Alerts | alertes | hors v1 |

Contrôles au-dessus de la table :

1. **Niveau d’agrégation** : Default View · Sessions (n) · Traces (n) · Spans (n)  
   Doc : le contrôle en haut à gauche change le groupement Session / Trace / Span.
2. **Période** : ex. « Last 6 months »
3. **Filters** + **Search**
4. Indicateur optionnel « Compute Metrics »

### Colonnes de la table Logs (observées)

| Colonne | Contenu |
|---|---|
| checkbox | sélection multi-lignes |
| Created | timestamp local |
| Name | nom de la trace / entrée (ex. `cimr_gateway`) |
| Input | extrait du prompt (tronqué) |
| Output | extrait de la réponse (tronqué) |
| External Id | id externe opaque |
| colonnes métriques | une colonne par métrique active du stream |

### Badges métriques (visuel)

- Booléen OK / absence de risque → pastille **verte** (`false` pour sexism/toxicity = bon)
- Valeur neutre catégorielle → pastille **grise** (`neutral`)
- Score faible / échec → texte ou pastille **rouge** (`0%`)
- Score fort / succès → texte ou pastille **verte** (`100%`)
- Non applicable → `N/A` ou `-` gris
- En-tête de métrique « AI » : petite icône violette (type snowflake / brain)

Pagination en bas : Previous · pages · Next.

## Drill-down (doc + console)

1. Clic sur une **Session** → flowchart des traces ; panneau droit input/output du nœud sélectionné.
2. Onglet **Messages** → liste traces + spans enfants ; clic span → métriques à droite.
3. Toggle **Condense Steps** (cloud) : hors v1 clone sauf si déjà trivial.

## Ce que la console cloud a et que le clone v1 n’imite pas

Book a demo, Playgrounds complets, Datasets, Prompts, Annotation Queues, Dashboards riches, Signals, Alerts, Agent graph traffic, Luna Studio.  
Ils peuvent apparaître dans la sidebar comme **entrées grisées / « soon »** pour coller à l’IA visuelle, sans pages fonctionnelles.

## Mise à jour

Toute nouvelle capture ou doc UI passe par une révision humaine, puis mise à jour de ce fichier **avant** de changer `harness/ui/`.
