# 03 — Console

- Statut : ouverte / en cours selon l’état du code
- Bloquée par : 01
- Exécution : un agent, puis reviewer adverse, puis parcours navigateur

## Tranche

`GET /` sur le port 8090 affiche les traces du stream `chat` et le détail d’une trace, selon `harness/design.md`. `GET /chat` sert le chat.

## Accepte

- La liste montre identifiant, heure, statut.
- Le détail montre input et output de chaque span et les scores.
- Le skill `.cursor/skills/ui-explore/SKILL.md` a été exécuté et son compte-rendu est dans `research/runs/`.

## Oracle

Le parcours navigateur ouvre une trace et vérifie que la console est lisible. Le compte-rendu le dit.
