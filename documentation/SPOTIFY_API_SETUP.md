# Configuration de l'API Spotify

## Obtenir vos credentials Spotify

1. Allez sur [Spotify Developer Dashboard](https://developer.spotify.com/dashboard)
2. Connectez-vous avec votre compte Spotify
3. Cliquez sur **"Create app"**
4. Remplissez les informations:
   - **App name**: `ETL Spotify Dashboard` (ou autre nom)
   - **App description**: `Application pour analyser mon historique Spotify`
   - **Redirect URI**: `http://localhost:8888/callback` (requis mais non utilisé)
   - Cochez **"Web API"**
   - Acceptez les conditions
5. Cliquez sur **Settings**
6. Notez votre **Client ID** et **Client Secret**

## Configuration dans .env

Ajoutez vos credentials dans le fichier `.env`:

```bash
# Spotify API Credentials
SPOTIFY_CLIENT_ID=votre_client_id_ici
SPOTIFY_CLIENT_SECRET=votre_client_secret_ici
```

⚠️ **Important**: Ne commitez JAMAIS votre fichier `.env` dans Git. Assurez-vous qu'il est dans `.gitignore`.

## Fonctionnalités de l'API

Le module `modules/spotify_api.py` fournit:

### SpotifyEnricher

Classe principale pour enrichir les données avec l'API Spotify:

```python
from modules.spotify_api import get_spotify_enricher

enricher = get_spotify_enricher()

# Récupérer les infos d'une track
track_info = enricher.get_track_info("spotify:track:3n3Ppam7vgaVa1iaRUc9Lp")

# Récupérer les infos d'un artiste
artist_info = enricher.get_artist_info("0TnOYISbd1XYRBk9myaseg")

# Récupérer les infos d'un album
album_info = enricher.get_album_info("2ODvWsOgouMbaA5xf0RkJe")

# Enrichir une track complète (track + album + artistes)
enriched = enricher.enrich_track_data("spotify:track:3n3Ppam7vgaVa1iaRUc9Lp")

# Batch enrichment (optimisé)
track_uris = [
    "spotify:track:3n3Ppam7vgaVa1iaRUc9Lp",
    "spotify:track:4VqPOruhp5EdPBeR92t6lQ"
]
enriched_tracks = enricher.batch_enrich_tracks(track_uris)
```

## Données enrichies

L'API Spotify permet de récupérer:

### Pour les tracks:
- ✅ ID réel Spotify (pas de hash généré)
- ✅ Nom
- ✅ Durée en ms
- ✅ Popularité (0-100)
- ✅ Image de couverture (URL)
- ✅ Album associé
- ✅ Artistes (principal + featuring)

### Pour les albums:
- ✅ ID réel Spotify
- ✅ Nom
- ✅ Date de sortie
- ✅ Nombre de tracks
- ✅ Image de couverture (URL)
- ✅ Artiste principal

### Pour les artistes:
- ✅ ID réel Spotify
- ✅ Nom
- ✅ Popularité (0-100)
- ✅ Genres (liste)
- ✅ Photo de profil (URL)

## Limites de l'API

- **Rate limits**: L'API Spotify a des limites de taux
- **Batch size**: Maximum 50 tracks par appel batch
- **Retry**: Le module gère automatiquement les erreurs et continue

## Optimisations

Le module utilise:
- ✅ **Batch processing**: Récupère 50 tracks à la fois
- ✅ **Singleton pattern**: Réutilise la même connexion
- ✅ **Error handling**: Continue même en cas d'erreur sur une track
- ✅ **Progress feedback**: Affiche la progression pour les grandes imports

## Workflow d'import

Avec l'API Spotify, le workflow devient:

```
1. Parser le JSON ────────────┐
                              │
2. Extraire les URIs ─────────┤
                              │
3. API Spotify (batch) ───────┤──► Données enrichies
                              │    (IDs réels)
4. Structurer les données ────┘
                              │
5. Insertion DB ──────────────┘
   (avec ON CONFLICT DO NOTHING)
```

Plus besoin de:
- ❌ Générer des IDs temporaires (hash)
- ❌ Mapper les IDs entre extraction et insertion
- ❌ Gérer les conflits de foreign keys

## Dépannage

### Erreur: "SPOTIFY_CLIENT_ID et SPOTIFY_CLIENT_SECRET doivent être définis"

➜ Vérifiez que vos credentials sont dans `.env` et que le fichier est à la racine du projet.

### Erreur: "Invalid client"

➜ Vérifiez que vos Client ID et Client Secret sont corrects dans Spotify Dashboard.

### Rate limit exceeded

➜ L'API Spotify limite le nombre de requêtes. Attendez quelques minutes et réessayez.

### Tracks non trouvées

➜ Certaines tracks peuvent ne plus être disponibles sur Spotify. Le module continue avec les autres.
