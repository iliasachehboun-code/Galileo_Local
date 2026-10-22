# Prompt d'installation

Colle le bloc ci-dessous dans Claude Code, Cursor ou Codex, à la racine de `galileo-local`. L'agent prépare la machine et s'arrête quand les tests passent. Il n'implémente aucune issue.

```
Tu installes galileo-local, une plateforme Python 3.12 locale.

Contexte : le dossier courant contient requirements.txt, pytest.ini et le package galileo_local.

Fais ceci, dans l'ordre, en t'adaptant à Windows et à ce qui est déjà installé :
1. Vérifie que Python 3.12 ou plus est disponible (py ou python).
2. Crée un virtualenv .venv dans ce dossier s'il n'existe pas.
3. Installe requirements.txt dans ce virtualenv.
4. Lance py -m pytest tests -q avec l'interpréteur du virtualenv.
5. Si un test échoue, lis l'erreur, corrige l'environnement (paquet manquant, PYTHONPATH), relance. Ne modifie pas galileo_local ni tests pour faire passer un oracle.
6. Arrête-toi quand les 16 tests passent, et résume les commandes qui ont marché.

N'ajoute pas de service, de base, ni de code d'issue. N'ouvre pas de port.
```
