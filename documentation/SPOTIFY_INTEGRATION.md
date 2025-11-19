# Migration vers l'API Spotify - Documentation

## 🎯 Objectif

Remplacer le système de génération d'IDs temporaires (basé sur des hash) par l'utilisation de l'API Spotify pour obtenir les vraies données et IDs.

## ✅ Fichiers créés

### 1. `modules/spotify_api.py`
Module principal pour l'intégration de l'API Spotify.

**Fonctionnalités:**
- `SpotifyEnricher` : Classe principale pour enrichir les données
- `get_track_info()` : Récupère les infos d'une track
- `get_artist_info()` : Récupère les infos d'un artiste  
- `get_album_info()` : Récupère les infos d'un album
- `batch_enrich_tracks()` : Enrichit plusieurs tracks en batch (optimisé)
- `get_spotify_enricher()` : Singleton pour réutiliser la connexion

**Dépendances:** `spotipy` (installé)

### 2. `modules/extract_file_data_enriched.py`
Nouvelle version du module d'extraction qui utilise l'API Spotify.

**Fonctionnalités:**
- `extract_enriched_data()` : Extrait et enrichit en un seul appel
- Traite les tracks en batch (50 à la fois)
- Enrichit les artistes avec genres, popularité, etc.
- Retourne les vraies données Spotify (pas de hash)

**Avantages:**
- ✅ IDs réels Spotify
- ✅ Données complètes (popularité, genres, images)
- ✅ Pas de FK violations
- ✅ Optimisé avec batch processing

### 3. `modules/insert_data_enriched.py`
Module d'insertion simplifié pour les données enrichies.

**Fonctionnalités:**
- `insert_artists()` : Insertion avec ON CONFLICT DO NOTHING
- `insert_albums()` : Insertion avec ON CONFLICT DO NOTHING
- `insert_tracks()` : Insertion avec ON CONFLICT DO NOTHING
- `insert_history()` : Insertion avec ON CONFLICT DO NOTHING
- `insert_featuring()` : Insertion des relations featuring

**Avantages:**
- ✅ Plus besoin de mapping d'IDs
- ✅ Code simplifié
- ✅ Gestion automatique des doublons

### 4. `modules/import_file_module.py` (modifié)
Mise à jour du module principal pour utiliser les nouvelles fonctions.

**Changements:**
- Utilise `extract_file_data_enriched` au lieu de `extract_file_data`
- Utilise `insert_data_enriched` au lieu de `insert_data`
- Affiche des messages de progression détaillés
- Plus de complexité de mapping d'IDs

### 5. `test_spotify_api.py`
Script de test pour vérifier la connexion à l'API Spotify.

**Tests:**
- ✅ Vérification des credentials
- ✅ Connexion à l'API
- ✅ Enrichissement d'une track
- ✅ Enrichissement d'un artiste
- ✅ Batch enrichment

**Usage:** `python test_spotify_api.py`

### 6. `SPOTIFY_API_SETUP.md`
Documentation complète pour configurer l'API Spotify.

**Contenu:**
- Instructions pour obtenir les credentials
- Configuration dans `.env`
- Exemples d'utilisation
- Liste des données enrichies
- Limites de l'API
- Dépannage

### 7. `.env` (modifié)
Ajout des variables pour l'API Spotify:

```bash
SPOTIFY_CLIENT_ID=your_client_id_here
SPOTIFY_CLIENT_SECRET=your_client_secret_here
```

### 8. `README.md` (modifié)
Mise à jour avec:
- Section "Spotify API Setup"
- Instructions pour tester l'API
- Lien vers la documentation détaillée

## 🔄 Workflow avant vs après

### ❌ Avant (avec hash)

```
1. Parser JSON
2. Extraire artistes → générer artist_id = hash(name)
3. Extraire albums → générer album_id = hash(album+artist)
4. Extraire tracks → utiliser les IDs générés
5. Insertion → ❌ Foreign Key violations
```

**Problèmes:**
- IDs générés différents entre extraction et insertion
- Pas de données enrichies (popularité, genres, etc.)
- Foreign Key violations fréquentes

### ✅ Après (avec API Spotify)

```
1. Parser JSON
2. Collecter tous les URIs de tracks
3. API Spotify (batch) → données complètes avec IDs réels
4. Structurer les données (artists, albums, tracks)
5. Insertion → ✅ Pas de FK violations
```

**Avantages:**
- ✅ IDs réels Spotify
- ✅ Données enrichies (popularité, genres, images, durée)
- ✅ Pas de Foreign Key violations
- ✅ Code plus simple

## 📊 Données enrichies

### Tracks
- `id` : ID réel Spotify
- `track_name` : Nom
- `duration_ms` : Durée en ms
- `popularity` : Score 0-100
- `track_cover_uri` : URL de la cover
- `album_id` : ID album (réel)
- `main_artist_id` : ID artiste principal (réel)

### Albums
- `id` : ID réel Spotify
- `album_name` : Nom
- `release_date` : Date de sortie
- `total_tracks` : Nombre de tracks
- `cover_image_uri` : URL de la cover
- `artist_id` : ID artiste (réel)

### Artists
- `id` : ID réel Spotify
- `name` : Nom
- `popularity` : Score 0-100
- `genre` : Genres (séparés par virgule)
- `profile_picture_uri` : URL de la photo

## 🚀 Prochaines étapes

1. **Obtenir les credentials Spotify:**
   - Aller sur https://developer.spotify.com/dashboard
   - Créer une app
   - Copier Client ID et Client Secret

2. **Configurer .env:**
   ```bash
   SPOTIFY_CLIENT_ID=votre_client_id
   SPOTIFY_CLIENT_SECRET=votre_client_secret
   ```

3. **Tester la connexion:**
   ```bash
   python test_spotify_api.py
   ```

4. **Tester l'import:**
   ```bash
   python test_import.py data/Streaming_History_Audio_2021-2024_0.json
   ```

## 🔧 Optimisations

### Batch Processing
- Récupère 50 tracks à la fois (limite API)
- Réduit le nombre d'appels API
- Plus rapide pour les gros fichiers

### Singleton Pattern
- Une seule connexion réutilisée
- Pas de reconnexion à chaque appel

### Error Handling
- Continue même si une track n'est pas trouvée
- Affiche des warnings pour les erreurs
- Ne bloque pas tout l'import

### Progress Feedback
- Affiche la progression pour les artistes
- Messages détaillés par étape
- Retours visuels (emojis)

## 📝 Notes importantes

- **Rate limits:** L'API Spotify a des limites de taux. Pour les très gros imports, il peut y avoir des pauses.
- **Tracks manquantes:** Certaines tracks peuvent ne plus être disponibles sur Spotify.
- **Credentials:** Ne jamais committer le fichier `.env` avec les vraies credentials.

## 🐛 Dépannage

### "SPOTIFY_CLIENT_ID et SPOTIFY_CLIENT_SECRET doivent être définis"
➜ Vérifiez que vos credentials sont dans `.env`

### "Invalid client"
➜ Vérifiez que vos credentials sont corrects

### Rate limit exceeded
➜ Attendez quelques minutes et réessayez

### Tracks non trouvées
➜ Normal, certaines tracks ne sont plus disponibles

## 📚 Documentation

- `SPOTIFY_API_SETUP.md` : Guide complet de configuration
- `README.md` : Documentation principale du projet
- `modules/README_IMPORT.md` : Documentation de l'ancien système (référence)
