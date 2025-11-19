# 🔧 Correction des contraintes UNIQUE

## Problème identifié

Les contraintes `UNIQUE` de la migration initiale étaient trop restrictives :
- ❌ `artists.name` unique → Plusieurs artistes peuvent avoir le même nom
- ❌ `albums.album_name` unique → Plusieurs albums peuvent avoir le même nom
- ❌ `tracks.track_name` unique → Plusieurs tracks peuvent avoir le même nom
- ❌ Plusieurs autres contraintes incorrectes

## Solution

Une nouvelle migration `0002_remove_incorrect_unique_constraints.py` a été créée pour corriger cela.

## Étapes pour appliquer la correction

### Option 1 : Base de données vide ou test

Si votre base de données est vide ou en test, vous pouvez repartir de zéro :

```bash
# 1. Supprimer toutes les tables
alembic downgrade base

# 2. Appliquer la migration corrigée
alembic upgrade head
```

### Option 2 : Base de données avec données existantes

Si vous avez déjà des données, appliquez simplement la nouvelle migration :

```bash
# Appliquer la migration de correction
alembic upgrade head
```

Cette migration supprimera les contraintes UNIQUE problématiques tout en préservant vos données.

## Vérification

Après application, vérifiez que la migration est appliquée :

```bash
alembic current
```

Vous devriez voir :
```
0002_remove_incorrect_unique_constraints (head)
```

## Nouvelles contraintes (après correction)

✅ **Seules les vraies contraintes d'unicité restent :**
- `tracks.id` (PK - URI Spotify unique)
- `artists.id` (PK)
- `albums.id` (PK)
- `users.id` (PK)
- `history.played_at` (timestamp unique d'écoute)

✅ **Les champs suivants peuvent maintenant avoir des doublons :**
- Noms d'artistes, d'albums, de tracks
- URIs d'images (peuvent être partagées ou NULL)
- Noms d'utilisateurs

## Test de l'import

Après avoir appliqué la migration, testez l'import :

```bash
python test_import.py --file data/Streaming_History_Audio_2021-2024_0.json
```

Ou via l'API :

```bash
curl -X POST "http://localhost:8000/api/v1/import-data" \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -F "file=@data/Streaming_History_Audio_2021-2024_0.json"
```

L'import devrait maintenant fonctionner sans erreurs de contraintes UNIQUE ! 🎉
