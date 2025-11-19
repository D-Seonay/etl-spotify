"""
Module d'import principal pour les fichiers d'historique Spotify.

Utilise l'API Spotify pour enrichir les données avec les vraies informations.
Vérifie d'abord la base de données pour éviter les appels API inutiles.
"""

from sqlalchemy.orm import Session
from sqlalchemy import select
from entity.user import User
from entity.track import Track
from entity.artist import Artist
from entity.album import Album
from typing import Dict, Set
from modules.extract_file_data_enriched import (
    parse_json_file,
    extract_enriched_data,
    extract_history_data,
    extract_featuring_data,
    extract_spotify_id
)
from modules.insert_data_enriched import (
    insert_artists,
    insert_albums,
    insert_tracks,
    insert_history,
    insert_featuring
)


def import_spotify_history_file(session: Session, file_path: str, user_id: str = "default_user") -> Dict[str, int]:
    """
    Fonction principale pour importer un fichier d'historique Spotify dans la base de données.
    
    Cette version utilise l'API Spotify pour enrichir les données avec les vraies informations
    (IDs réels, popularité, genres, images, etc.).
    
    Args:
        session: Session SQLAlchemy
        file_path: Chemin vers le fichier JSON d'historique Spotify
        user_id: ID de l'utilisateur (par défaut "default_user")
    
    Returns:
        Dictionnaire avec le nombre d'entrées insérées par table
    """
    print(f"\n{'='*60}")
    print(f"📂 Import du fichier: {file_path}")
    print(f"{'='*60}\n")
    
    # 1. Parser le fichier JSON
    print("📋 Parsing du fichier JSON...")
    history_entries = parse_json_file(file_path)
    print(f"✅ {len(history_entries)} entrées trouvées\n")
    
    # 2. Collecter les URIs de tracks du fichier
    print("🔍 Identification des tracks du fichier...")
    track_uris_in_file = set()
    for entry in history_entries:
        if entry.get('spotify_track_uri') and entry.get('master_metadata_track_name'):
            track_uris_in_file.add(entry['spotify_track_uri'])
    
    print(f"✅ {len(track_uris_in_file)} tracks uniques trouvées\n")
    
    # 3. Vérifier quelles tracks existent déjà en base
    print("💾 Vérification des tracks existantes en base...")
    track_ids_in_file = {extract_spotify_id(uri) for uri in track_uris_in_file}
    track_ids_in_file.discard(None)  # Enlever les None
    
    existing_track_ids = set()
    if track_ids_in_file:
        existing_tracks = session.execute(
            select(Track.id).where(Track.id.in_(track_ids_in_file))
        ).scalars().all()
        existing_track_ids = set(existing_tracks)
    
    tracks_already_in_db = len(existing_track_ids)
    tracks_to_enrich = len(track_ids_in_file) - tracks_already_in_db
    
    print(f"✅ {tracks_already_in_db} tracks déjà en base")
    print(f"🆕 {tracks_to_enrich} nouvelles tracks à enrichir\n")
    
    # 4. Filtrer les URIs à enrichir (seulement les nouvelles)
    track_uris_to_enrich = [
        uri for uri in track_uris_in_file 
        if extract_spotify_id(uri) not in existing_track_ids
    ]
    
    # 5. Extraire et enrichir seulement les nouvelles données via l'API Spotify
    if track_uris_to_enrich:
        print(f"🌐 Enrichissement de {len(track_uris_to_enrich)} nouvelles tracks via l'API Spotify...")
        artists_data, albums_data, tracks_data, track_uri_to_id, featuring_data = extract_enriched_data(
            history_entries, 
            track_uris_to_enrich
        )
        
        print(f"\n📊 Données enrichies:")
        print(f"   - Artistes: {len(artists_data)}")
        print(f"   - Albums: {len(albums_data)}")
        print(f"   - Tracks: {len(tracks_data)}")
        print(f"   - Featuring: {len(featuring_data)}\n")
    else:
        print("✅ Toutes les tracks sont déjà en base, pas d'enrichissement nécessaire\n")
        artists_data, albums_data, tracks_data, featuring_data = [], [], [], []
        track_uri_to_id = {
            uri: extract_spotify_id(uri) 
            for uri in track_uris_in_file 
            if extract_spotify_id(uri) in existing_track_ids
        }
    
    # 6. Vérifier/créer l'utilisateur
    print("👤 Vérification de l'utilisateur...")
    existing_user = session.execute(
        select(User).where(User.id == user_id)
    ).scalar_one_or_none()
    
    if not existing_user:
        user = User(
            id=user_id,
            display_name="Default User",
            profile_picture_uri=None
        )
        session.add(user)
        session.commit()
        print(f"✅ Utilisateur '{user_id}' créé\n")
    else:
        print(f"✅ Utilisateur '{user_id}' existant\n")
    
    # 7. Extraire l'historique d'écoute
    print("🎧 Extraction de l'historique d'écoute...")
    history_data = extract_history_data(history_entries, user_id, track_uri_to_id)
    print(f"✅ {len(history_data)} écoutes extraites\n")
    
    # 8. Enrichir les artistes et albums (seulement ceux qui ne sont pas en base)
    artists_to_insert = artists_data  # Garder tous les artistes pour l'insertion
    albums_to_insert = albums_data    # Garder tous les albums pour l'insertion
    successfully_enriched_artist_ids = set()  # Track des artistes enrichis avec succès
    
    if artists_data:
        print("🔍 Vérification des artistes existants...")
        artist_ids_to_check = {a['id'] for a in artists_data}
        existing_artists = session.execute(
            select(Artist.id).where(Artist.id.in_(artist_ids_to_check))
        ).scalars().all()
        existing_artist_ids = set(existing_artists)
        successfully_enriched_artist_ids = existing_artist_ids.copy()  # Les artistes déjà en base sont OK
        
        artists_to_enrich = [a for a in artists_data if a['id'] not in existing_artist_ids]
        
        print(f"✅ {len(existing_artist_ids)} artistes déjà en base")
        print(f"🆕 {len(artists_to_enrich)} nouveaux artistes à enrichir\n")
        
        if artists_to_enrich:
            print("👤 Enrichissement des nouveaux artistes...")
            from modules.spotify_api import get_spotify_enricher
            enricher = get_spotify_enricher()
            
            enriched_artists = []
            failed_artists = []
            
            for i, artist_data in enumerate(artists_to_enrich):
                if (i + 1) % 10 == 0:
                    print(f"   {i + 1}/{len(artists_to_enrich)} artistes traités...")
                
                artist_info = enricher.get_artist_info(artist_data['id'])
                if artist_info:
                    artist_data.update({
                        'popularity': artist_info['popularity'],
                        'profile_picture_uri': artist_info['profile_picture_uri'],
                        'genre': artist_info['genres']
                    })
                    enriched_artists.append(artist_data)
                    successfully_enriched_artist_ids.add(artist_data['id'])
                else:
                    failed_artists.append(artist_data['id'])
            
            print(f"✅ {len(enriched_artists)} artistes enrichis avec succès")
            if failed_artists:
                print(f"⚠️  {len(failed_artists)} artistes ignorés (supprimés de Spotify)\n")
            else:
                print()
        
            # Ne garder que les artistes enrichis avec succès
            artists_to_insert = enriched_artists
        else:
            artists_to_insert = []
    
    if albums_data:
        print("🔍 Vérification des albums existants...")
        album_ids_to_check = {a['id'] for a in albums_data}
        existing_albums = session.execute(
            select(Album.id).where(Album.id.in_(album_ids_to_check))
        ).scalars().all()
        existing_album_ids = set(existing_albums)
        
        albums_to_insert = [a for a in albums_data if a['id'] not in existing_album_ids]
        
        # Filtrer les albums dont l'artiste n'a pas pu être enrichi
        albums_with_valid_artists = [
            a for a in albums_to_insert 
            if a['artist_id'] in successfully_enriched_artist_ids
        ]
        
        skipped_albums = len(albums_to_insert) - len(albums_with_valid_artists)
        
        print(f"✅ {len(existing_album_ids)} albums déjà en base")
        print(f"🆕 {len(albums_with_valid_artists)} nouveaux albums à insérer")
        if skipped_albums > 0:
            print(f"⚠️  {skipped_albums} albums ignorés (artiste indisponible)\n")
        else:
            print()
        
        albums_to_insert = albums_with_valid_artists
    
    # Créer un set des albums valides (déjà en base + nouveaux à insérer)
    valid_album_ids = existing_album_ids.copy() if albums_data else set()
    if albums_to_insert:
        valid_album_ids.update(a['id'] for a in albums_to_insert)
    
    # Filtrer les tracks dont l'artiste principal ou l'album n'existe pas
    if tracks_data:
        tracks_with_valid_refs = [
            t for t in tracks_data 
            if t['main_artist_id'] in successfully_enriched_artist_ids
            and t['album_id'] in valid_album_ids
        ]
        
        skipped_tracks = len(tracks_data) - len(tracks_with_valid_refs)
        
        if skipped_tracks > 0:
            print(f"⚠️  {skipped_tracks} tracks ignorées (artiste ou album indisponible)")
        
        tracks_data = tracks_with_valid_refs
    
    # 9. Filtrer l'historique pour ne garder que les tracks valides
    valid_track_ids = existing_track_ids.copy()
    valid_track_ids.update(t['id'] for t in tracks_data)
    
    history_with_valid_tracks = [
        h for h in history_data
        if h['track_id'] in valid_track_ids
    ]
    
    skipped_history = len(history_data) - len(history_with_valid_tracks)
    if skipped_history > 0:
        print(f"⚠️  {skipped_history} écoutes ignorées (track non disponible)")
    
    history_data = history_with_valid_tracks
    
    # Filtrer les featuring pour ne garder que ceux avec artistes et tracks valides
    if featuring_data:
        featuring_with_valid_refs = [
            f for f in featuring_data
            if f['artist_id'] in successfully_enriched_artist_ids
            and f['track_id'] in valid_track_ids
        ]
        
        skipped_feats = len(featuring_data) - len(featuring_with_valid_refs)
        if skipped_feats > 0:
            print(f"⚠️  {skipped_feats} featuring ignorés (artiste ou track non disponible)")
        
        featuring_data = featuring_with_valid_refs
    
    # 10. Insérer dans la base de données (ordre respectant les foreign keys)
    print("💾 Insertion dans la base de données...\n")
    
    if artists_to_insert:
        print("   1️⃣  Insertion des artistes...")
        artists_inserted = insert_artists(session, artists_to_insert)
        print(f"   ✅ {artists_inserted} artistes insérés\n")
    else:
        artists_inserted = 0
        print("   1️⃣  Pas de nouveaux artistes à insérer\n")
    
    if albums_to_insert:
        print("   2️⃣  Insertion des albums...")
        albums_inserted = insert_albums(session, albums_to_insert)
        print(f"   ✅ {albums_inserted} albums insérés\n")
    else:
        albums_inserted = 0
        print("   2️⃣  Pas de nouveaux albums à insérer\n")
    
    if tracks_data:
        print("   3️⃣  Insertion des tracks...")
        tracks_inserted = insert_tracks(session, tracks_data)
        print(f"   ✅ {tracks_inserted} tracks insérées\n")
    else:
        tracks_inserted = 0
        print("   3️⃣  Pas de nouvelles tracks à insérer\n")
    
    print("   4️⃣  Insertion de l'historique...")
    history_inserted = insert_history(session, history_data)
    print(f"   ✅ {history_inserted} écoutes insérées\n")
    
    # 5. Insérer les featuring (relations track-artist pour les artistes secondaires)
    if featuring_data:
        print("   5️⃣  Insertion des featuring...")
        featuring_inserted = insert_featuring(session, featuring_data)
        print(f"   ✅ {featuring_inserted} featuring insérés\n")
    else:
        featuring_inserted = 0
        print("   5️⃣  Pas de featuring à insérer\n")
    
    print(f"\n{'='*60}")
    print(f"✨ Import terminé avec succès!")
    print(f"{'='*60}\n")
    
    return {
        'artists': artists_inserted,
        'albums': albums_inserted,
        'tracks': tracks_inserted,
        'history': history_inserted,
        'featuring': featuring_inserted
    }

