"""
Script de test pour vérifier l'intégration de l'API Spotify.

Ce script teste la connexion à l'API Spotify et l'enrichissement des données.
"""

import sys
import os
from dotenv import load_dotenv

# Charger les variables d'environnement
load_dotenv()


def test_spotify_api():
    """Teste la connexion à l'API Spotify."""
    print("\n" + "="*60)
    print("🧪 Test de l'API Spotify")
    print("="*60 + "\n")
    
    # Vérifier les credentials
    client_id = os.getenv('SPOTIFY_CLIENT_ID')
    client_secret = os.getenv('SPOTIFY_CLIENT_SECRET')
    
    print("1️⃣  Vérification des credentials...")
    if not client_id or client_id == 'your_client_id_here':
        print("❌ SPOTIFY_CLIENT_ID non configuré dans .env")
        print("   ➜ Voir SPOTIFY_API_SETUP.md pour les instructions")
        return False
    
    if not client_secret or client_secret == 'your_client_secret_here':
        print("❌ SPOTIFY_CLIENT_SECRET non configuré dans .env")
        print("   ➜ Voir SPOTIFY_API_SETUP.md pour les instructions")
        return False
    
    print(f"✅ Client ID: {client_id[:10]}...")
    print(f"✅ Client Secret: ***************\n")
    
    # Tester la connexion
    print("2️⃣  Test de connexion à l'API Spotify...")
    try:
        from modules.spotify_api import get_spotify_enricher
        enricher = get_spotify_enricher()
        print("✅ Connexion établie\n")
    except Exception as e:
        print(f"❌ Erreur de connexion: {e}")
        return False
    
    # Tester l'enrichissement d'une track
    print("3️⃣  Test d'enrichissement d'une track...")
    test_track_uri = "spotify:track:3n3Ppam7vgaVa1iaRUc9Lp"  # Mr. Brightside - The Killers
    
    try:
        track_info = enricher.get_track_info(test_track_uri)
        if track_info:
            print(f"✅ Track enrichie: {track_info['name']}")
            print(f"   Artiste: {track_info['main_artist_name']}")
            print(f"   Album: {track_info['album_name']}")
            print(f"   Popularité: {track_info['popularity']}/100")
            print(f"   Durée: {track_info['duration_ms']}ms\n")
        else:
            print("❌ Impossible d'enrichir la track")
            return False
    except Exception as e:
        print(f"❌ Erreur lors de l'enrichissement: {e}")
        return False
    
    # Tester l'enrichissement d'un artiste
    print("4️⃣  Test d'enrichissement d'un artiste...")
    
    try:
        artist_id = track_info['main_artist_id']
        artist_info = enricher.get_artist_info(artist_id)
        if artist_info:
            print(f"✅ Artiste enrichi: {artist_info['name']}")
            print(f"   Popularité: {artist_info['popularity']}/100")
            print(f"   Genres: {artist_info['genres'] or 'N/A'}\n")
        else:
            print("⚠️  Impossible d'enrichir l'artiste (peut être normal)")
    except Exception as e:
        print(f"⚠️  Erreur lors de l'enrichissement de l'artiste: {e}\n")
    
    # Tester le batch enrichment
    print("5️⃣  Test de batch enrichment...")
    test_uris = [
        "spotify:track:3n3Ppam7vgaVa1iaRUc9Lp",  # Mr. Brightside
        "spotify:track:0VjIjW4GlUZAMYd2vXMi3b",  # Blinding Lights
        "spotify:track:4VqPOruhp5EdPBeR92t6lQ"   # Midnight City
    ]
    
    try:
        enriched = enricher.batch_enrich_tracks(test_uris)
        print(f"✅ {len(enriched)}/{len(test_uris)} tracks enrichies en batch")
        for uri, data in enriched.items():
            print(f"   - {data['name']} by {data['artists'][0]['name']}")
        print()
    except Exception as e:
        print(f"❌ Erreur lors du batch enrichment: {e}")
        return False
    
    print("="*60)
    print("✨ Tous les tests sont passés avec succès!")
    print("="*60 + "\n")
    
    return True


if __name__ == "__main__":
    success = test_spotify_api()
    sys.exit(0 if success else 1)
