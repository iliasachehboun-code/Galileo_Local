# Feature adversariale

Orchestre une issue de `galileo-local/issues/`.

1. Lis l'issue demandée et `harness/spec.md`.
2. Lance le generator dans un contexte isolé (Task tool, agent `generator`). Passe-lui l'issue, `AGENTS.md`, la spec, et rien d'autre.
3. Récupère le plan JSON, le diff et la sortie pytest. Ne transmets pas la conversation du generator.
4. Lance le reviewer dans un contexte isolé (agent `adversarial-reviewer`) avec ces artefacts seulement.
5. Si le verdict est FAIL, renvoie uniquement les findings au generator et recommence. Maximum 4 tours.
6. Si le verdict est PASS, arrête-toi et résume les fichiers et la commande de test.
7. Si le plafond est atteint sans PASS, arrête-toi et demande un arbitrage humain. N'invente pas un PASS.

Le generator et le reviewer ne partagent pas leur mémoire.
