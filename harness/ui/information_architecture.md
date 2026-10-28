# Information architecture — console clone

Aligné sur `harness/external/galileo_console_ui.md` et les objets de `architecture.md`.

## Objets UI

| Objet | Identifiant local | Affichage |
|---|---|---|
| Project | `galileo-local` | sélecteur sidebar + breadcrumb |
| Log stream | `chat` (défaut) | `Logs: chat` dans la sidebar |
| Session | `session_id` | ligne en mode Sessions |
| Trace | `request_id` | ligne en mode Traces (vue par défaut utile) |
| Span | index / name / type | ligne en mode Spans + arbre détail |
| Metric score | `metric_id` + score | colonne table + panneau détail |

## Sidebar (toujours visible)

```
[Galileo]                    ← marque, pas « galileo-local » en hero
Home
▾ galileo-local              ← project
    Overview                 ← v1 : résumé compteurs (sessions/traces/spans)
    Logs: chat               ← actif sur la table Log stream
    Playgrounds              ← disabled / soon
    Experiments              ← actif → page expériences
────────
Datasets                     ← disabled
Prompts                      ← disabled
Annotation Queues            ← disabled
Metrics                      ← lien liste métriques du catalogue (lecture)
Dashboards                   ← disabled
Controls                     ← disabled
```

Pas de bouton « Book a demo » (produit local). Remplacer par un lien discret **Chat** (génération de traces) en bas de sidebar.

## Routes cibles

| Route | Écran |
|---|---|
| `/` | redirect → `/logs` |
| `/logs` | Log stream table (niveau Traces par défaut) |
| `/logs?level=sessions\|traces\|spans` | même table, autre agrégation |
| `/logs/traces/{request_id}` | détail trace (arbre spans + métriques) |
| `/logs/sessions/{session_id}` | détail session (liste de traces) |
| `/experiments` | comparaison de runs (garder, restyler) |
| `/chat` | chat Agno (entrée de données, pas le centre visuel) |
| `/metrics` | catalogue métriques actives du stream (lecture) |

## Flux utilisateur principal (comme Galileo)

1. Ouvrir **Logs: chat**
2. Voir la table (Created, Name, Input, Output, External Id, métriques)
3. Basculer Sessions / Traces / Spans
4. Cliquer une ligne → détail
5. Lire input/output + scores à droite (ou panneau dédié)
6. (Option) Experiments pour comparer des runs

Le chat n’est **pas** la home : c’est un générateur de trafic pour remplir le Log stream.
