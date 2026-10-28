# galileo-local

Clone local de [Galileo](https://docs.galileo.ai/what-is-galileo) : chat Agno, traces, métriques, expériences, console.

Produit autonome. Chaque message du chat crée une trace scorée.

## Démarrage

```powershell
cd galileo-local
copy .env.example .env
# Mets ta clé OpenAI dans .env (OPENAI_API_KEY=...)
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m galileo_local.app
```

- Chat : http://127.0.0.1:8090/chat  
- Traces / métriques : http://127.0.0.1:8090/  
- Expériences : http://127.0.0.1:8090/experiments  

Pour Azure / GCP, mets `GALILEO_BIND_HOST=0.0.0.0` dans `.env`.

## Déploiement Azure (Container Apps)

```powershell
cd galileo-local
docker build -t galileo-local:local .
# Puis : ACR + Container App (voir script deploy-azure.ps1)
.\deploy-azure.ps1
```

L’app écoute sur le port `8080` dans le conteneur. La clé `OPENAI_API_KEY` est injectée comme secret Azure (pas dans l’image).

## Tests

```powershell
.\.venv\Scripts\python.exe -m pytest tests -q
```

