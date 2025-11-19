# Guide d'utilisation de l'API d'import

## 🚀 Démarrer l'API

```bash
uvicorn main:app --reload --host 127.0.0.1 --port 8000
```

L'API sera accessible sur `http://127.0.0.1:8000`

**Documentation interactive:**
- Swagger UI: http://127.0.0.1:8000/docs
- ReDoc: http://127.0.0.1:8000/redoc

## 🔑 Authentification

Tous les endpoints d'import nécessitent une authentification par Bearer Token.

Le token est défini dans votre fichier `.env`:
```bash
API_KEY=votre_cle_api_ici
```

**Utilisation dans les requêtes:**
```
Authorization: Bearer votre_cle_api_ici
```

## 📡 Endpoints disponibles

### 1. Import d'un fichier unique

**Endpoint:** `POST /api/v1/import-data`

**Description:** Importe un fichier JSON d'historique Spotify et enrichit les données avec l'API Spotify.

**Paramètres:**
- `file` (FormData): Fichier JSON à importer
- `user_id` (FormData, optionnel): ID utilisateur (défaut: "default_user")

**Headers:**
```
Authorization: Bearer votre_api_key
```

**Exemple avec curl:**
```bash
curl -X POST "http://127.0.0.1:8000/api/v1/import-data" \
  -H "Authorization: Bearer votre_api_key" \
  -F "file=@data/Streaming_History_Audio_2021-2024_0.json" \
  -F "user_id=mon_user_id"
```

**Exemple avec Python (requests):**
```python
import requests

url = "http://127.0.0.1:8000/api/v1/import-data"
headers = {
    "Authorization": "Bearer votre_api_key"
}

with open("data/Streaming_History_Audio_2021-2024_0.json", "rb") as f:
    files = {
        'file': ('history.json', f, 'application/json')
    }
    data = {
        'user_id': 'mon_user_id'
    }
    
    response = requests.post(url, headers=headers, files=files, data=data)
    print(response.json())
```

**Réponse (succès):**
```json
{
  "status": "success",
  "message": "Data from Streaming_History_Audio_2021-2024_0.json imported successfully.",
  "statistics": {
    "artists_imported": 95,
    "albums_imported": 145,
    "tracks_imported": 220,
    "history_entries_imported": 1500
  }
}
```

### 2. Import de plusieurs fichiers

**Endpoint:** `POST /api/v1/import-multiple`

**Description:** Importe plusieurs fichiers JSON en une seule requête.

**Paramètres:**
- `files` (FormData): Liste de fichiers JSON
- `user_id` (FormData, optionnel): ID utilisateur (défaut: "default_user")

**Headers:**
```
Authorization: Bearer votre_api_key
```

**Exemple avec curl:**
```bash
curl -X POST "http://127.0.0.1:8000/api/v1/import-multiple" \
  -H "Authorization: Bearer votre_api_key" \
  -F "files=@data/Streaming_History_Audio_2021-2024_0.json" \
  -F "files=@data/Streaming_History_Audio_2024-2025_1.json" \
  -F "user_id=mon_user_id"
```

**Exemple avec Python (requests):**
```python
import requests

url = "http://127.0.0.1:8000/api/v1/import-multiple"
headers = {
    "Authorization": "Bearer votre_api_key"
}

files_to_import = [
    "data/Streaming_History_Audio_2021-2024_0.json",
    "data/Streaming_History_Audio_2024-2025_1.json"
]

files = [
    ('files', (f, open(f, 'rb'), 'application/json'))
    for f in files_to_import
]

data = {
    'user_id': 'mon_user_id'
}

response = requests.post(url, headers=headers, files=files, data=data)
print(response.json())

# Fermer les fichiers
for _, (_, f, _) in files:
    f.close()
```

**Réponse (succès):**
```json
{
  "status": "success",
  "message": "2 file(s) imported successfully.",
  "imported_files": [
    "Streaming_History_Audio_2021-2024_0.json",
    "Streaming_History_Audio_2024-2025_1.json"
  ],
  "errors": null,
  "total_statistics": {
    "artists_imported": 180,
    "albums_imported": 290,
    "tracks_imported": 450,
    "history_entries_imported": 3200
  }
}
```

### 3. Health Check

**Endpoint:** `GET /health`

**Description:** Vérifie que l'API est opérationnelle.

**Exemple:**
```bash
curl http://127.0.0.1:8000/health
```

**Réponse:**
```json
{
  "status": "ok"
}
```

### 4. Version

**Endpoint:** `GET /version`

**Description:** Retourne la version de l'API.

**Exemple:**
```bash
curl http://127.0.0.1:8000/version
```

**Réponse:**
```json
{
  "version": "1.0.0"
}
```

## ⏱️ Temps de traitement

L'enrichissement via l'API Spotify prend du temps:
- ~5-10 secondes pour 50 tracks
- ~2-3 minutes pour 500 tracks
- ~5-10 minutes pour 2000 tracks

**Recommandations:**
- Utilisez des timeouts généreux (5-10 minutes)
- Pour de très gros fichiers, surveillez les logs de l'API
- L'API affiche la progression dans les logs

## 🐛 Gestion des erreurs

### Erreur 400: Bad Request
```json
{
  "detail": "File must be a JSON file."
}
```
➜ Le fichier n'est pas un JSON

### Erreur 403: Forbidden
```json
{
  "detail": "Invalid or missing token."
}
```
➜ Token d'authentification invalide ou manquant

### Erreur 500: Internal Server Error
```json
{
  "detail": "Import failed: ..."
}
```
➜ Erreur durant l'import (vérifiez les logs)

**Causes fréquentes:**
- Credentials Spotify manquants ou invalides
- Base de données inaccessible
- Fichier JSON mal formaté
- Rate limit API Spotify atteint

## 📊 Monitoring

### Logs de l'API

Lancez l'API avec logging détaillé:
```bash
uvicorn main:app --reload --log-level debug
```

### Progression de l'import

L'API affiche dans les logs:
```
🎵 250 tracks uniques à enrichir via l'API Spotify...
✅ 250 tracks enrichies avec succès
👤 Enrichissement de 120 artistes...
   10/120 artistes enrichis...
   20/120 artistes enrichis...
```

## 🧪 Script de test

Un script de test complet est disponible:

```bash
python test_api_endpoint.py
```

Ce script teste:
1. La connexion à l'API
2. L'import d'un fichier unique
3. L'import de plusieurs fichiers (optionnel)

## 🔐 Sécurité

### Bonnes pratiques

1. **Générer une clé API sécurisée:**
   ```bash
   python -c "import secrets; print(secrets.token_urlsafe(64))"
   ```

2. **Ne jamais commiter `.env`:**
   - Vérifiez que `.env` est dans `.gitignore`
   - Utilisez `.env.example` comme template

3. **HTTPS en production:**
   - En production, utilisez HTTPS (reverse proxy nginx/traefik)
   - Stockez les secrets dans un gestionnaire de secrets

4. **Rate limiting:**
   - Considérez l'ajout de rate limiting
   - Limitez les tailles de fichiers

## 🚀 Déploiement en production

### Avec Gunicorn

```bash
pip install gunicorn
gunicorn main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```

### Avec Docker

```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Variables d'environnement

En production, utilisez des variables d'environnement:
```bash
export DATABASE_URL="postgresql://user:pass@host:port/db"
export API_KEY="votre_cle_securisee"
export SPOTIFY_CLIENT_ID="votre_client_id"
export SPOTIFY_CLIENT_SECRET="votre_client_secret"
```

## 📚 Documentation

- **Swagger UI:** http://127.0.0.1:8000/docs (interface interactive)
- **ReDoc:** http://127.0.0.1:8000/redoc (documentation détaillée)

## 💡 Exemples d'utilisation

### Import automatique de tous les fichiers d'un dossier

```python
import os
import requests

api_url = "http://127.0.0.1:8000/api/v1/import-multiple"
api_key = "votre_api_key"
data_dir = "data/"

# Récupérer tous les fichiers JSON
json_files = [
    os.path.join(data_dir, f)
    for f in os.listdir(data_dir)
    if f.endswith('.json')
]

# Préparer la requête
files = [
    ('files', (os.path.basename(f), open(f, 'rb'), 'application/json'))
    for f in json_files
]

headers = {"Authorization": f"Bearer {api_key}"}
data = {"user_id": "mon_user_id"}

# Envoyer
response = requests.post(api_url, headers=headers, files=files, data=data)
print(response.json())

# Fermer les fichiers
for _, (_, f, _) in files:
    f.close()
```

### Intégration dans un workflow CI/CD

```yaml
# .github/workflows/import-data.yml
name: Import Spotify Data

on:
  workflow_dispatch:
    inputs:
      files:
        description: 'Files to import'
        required: true

jobs:
  import:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      
      - name: Import data
        run: |
          curl -X POST "${{ secrets.API_URL }}/api/v1/import-data" \
            -H "Authorization: Bearer ${{ secrets.API_KEY }}" \
            -F "file=@${{ github.event.inputs.files }}"
```
