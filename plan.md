# Plan de travail

Le produit standalone est en place (chat, magasin, console, métriques, juges, expériences). Les issues restantes sont du durcissement et de la doc de harness — pas un branchement vers un autre dépôt.

## Ordre (historique des tranches)

```
01 Magasin de traces
    |-- 03 Console + test UI autonome
    |-- 04 Métriques code
            |-- 05 Juge Agno sur les 24 métriques du stream
                    |-- 06 Expériences
```

(L’ancienne tranche « brancher une gateway externe » a été retirée : galileo-local est autonome.)

Chaque issue se joue ainsi :

1. Ouvrir l’issue. Lire le critère d’acceptation.
2. Lancer `/feature` avec le titre de l’issue. Generator puis reviewer adverse.
3. Si les tests échouent encore, `harness/ralph.ps1` jusqu’au signal COMPLETE.
4. Montrer le test oracle vert, puis l’écran.

## Definition of done de la v1

- `py -m pytest tests -q` est vert.
- Un message sur `http://127.0.0.1:8090/chat` crée une trace visible sur `http://127.0.0.1:8090/`.
- La trace montre les spans agent/llm et les scores (code + juges).
- Une expérience relance ces scores et affiche l’écart avec le run précédent.

## Hors de cette v1

Luna Studio, Signals, assistant sur les traces, alertes, OpenTelemetry. On les note dans `research/wiki` si on les étudie, on ne les code pas dans ces issues.
