# Écrans v1

## 1. Log stream — table (`/logs`)

Doit coller à la capture Galileo :

**Chrome**
- Sidebar (voir IA)
- Breadcrumb : `galileo-local > Log Stream: chat`
- Onglet **Logs** actif ; autres onglets cloud absents ou `disabled`
- Bouton **Configure Metrics** (ouvre `/metrics` ou un panneau listant les métriques du stream — pas un éditeur Luna)

**Toolbar table**
- Chips / tabs : Default View · Sessions (n) · Traces (n) · Spans (n)  
  Compteurs = données SQLite réelles
- Sélecteur période (filtre `created_at` ; défaut « Last 30 days » si peu de data)
- Filters (statut score / metric failed) — minimal v1
- Search (sous-chaîne sur input, output, request_id, name)

**Colonnes obligatoires**
1. checkbox (peut être no-op v1 sauf sélection visuelle)
2. Created
3. Name (`trace.name` ou span name selon niveau)
4. Input (tronqué ~60–80 chars, tooltip full)
5. Output (idem)
6. External Id (`request_id` ou `session_id` selon niveau)
7. **Colonnes métriques dynamiques** : chaque métrique scorée présente sur le lot affiché (ou les métriques actives du stream). Badges selon `visual_tokens.md`.

**Lignes**
- Densité type SaaS : une ligne ~48–56px, bordures fines gris clair
- Clic ligne → navigation détail
- Hover fond gris très léger

**Footer**
- Pagination Previous / 1…N / Next

### Agrégations

| Level | Une ligne = | Input / Output |
|---|---|---|
| Sessions | `session_id` | 1er input / dernier output de la session, ou concat courte |
| Traces | `request_id` | input/output du span racine ou premier agent/llm |
| Spans | un span | `input_masked` / `output_masked` |

## 2. Détail trace (`/logs/traces/{request_id}`)

Inspiration Galileo (flowchart + panneau droit), v1 pragmatique :

**Gauche (60%)**
- Fil d’Ariane retour Logs
- Arbre / liste ordonnée des spans (nom, type, durée si dispo)
- Span sélectionné mis en évidence

**Droite (40%)**
- Onglets : Input · Output · Metrics
- Metrics : liste `metric_id`, score 0–1 ou %, badge passed/failed, rationale courte

Pas obligatoire de coder un vrai flowchart SVG en v1 ; une timeline verticale type Galileo Messages est acceptée **si** le chrome (sidebar + breadcrumb + panneau droit) est là.

## 3. Détail session (`/logs/sessions/{session_id}`)

Liste des traces de la session (mini-table) ; clic → détail trace.

## 4. Experiments (`/experiments`)

Conserver la fonction existante ; appliquer le même shell (sidebar + header) pour ne pas casser l’illusion Galileo.

## 5. Chat (`/chat`)

Même shell. Titre discret. Après envoi : lien « View in Logs » vers la trace créée.

## 6. Overview (`/overview` ou `/`)

Trois compteurs : Sessions · Traces · Spans + dernier événement. Pas de dashboard marketing.

## États

| État | UI |
|---|---|
| Vide | illustration légère + CTA « Open Chat to create a trace » |
| Chargement | skeleton rows (pas de spinner plein écran) |
| Erreur API | bandeau rouge discret au-dessus de la table |
| Métrique absente | `-` ou `N/A` |
