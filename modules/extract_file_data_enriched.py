"""
Module d'extraction de données enrichies avec l'API Spotify.

Ce module utilise l'API Spotify pour récupérer les vraies informations
sur les artistes, albums et tracks au lieu de générer des IDs temporaires.
"""

import json
from typing import Dict, List, Set, Tuple, Optional
from .spotify_api import get_spotify_enricher


def normalize_release_date(date_str: Optional[str]) -> Optional[str]:
    """
    Normalise une date de sortie au format PostgreSQL Date (YYYY-MM-DD).
    
    L'API Spotify peut retourner des dates dans différents formats:
    - "2023" (année seulement)
    - "2023-03" (année et mois)
    - "2023-03-15" (date complète)
    
    Args:
        date_str: Date au format Spotify
    
    Returns:
        Date au format YYYY-MM-DD ou None
    """
    if not date_str:
        return None
    
    # Si déjà au bon format (YYYY-MM-DD), retourner tel quel
    if len(date_str) == 10 and date_str.count('-') == 2:
        return date_str
    
    # Si année seulement (YYYY), ajouter 01-01
    if len(date_str) == 4:
        return f"{date_str}-01-01"
    
    # Si année et mois (YYYY-MM), ajouter 01
    if len(date_str) == 7 and date_str.count('-') == 1:
        return f"{date_str}-01"
    
    # Si format invalide, retourner None
    return None


def extract_spotify_id(uri: str) -> str:
    """
    Extrait l'ID d'un URI Spotify.
    
    Args:
        uri: URI Spotify au format 'spotify:type:id'
    
    Returns:
        ID extrait de l'URI
    """
    if not uri or uri == "null":
        return None
    return uri.split(":")[-1]


def parse_json_file(file_path: str) -> List[Dict]:
    """
    Parse le contenu JSON d'un fichier.
    
    Returns:
        Liste des entrées (List[Dict])
    """
    if isinstance(file_path, str):
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
    else:
        raise TypeError("Unsupported input type for parse_json_file")

    # Normaliser la sortie
    if isinstance(data, list):
        return data
    if isinstance(data, dict):
        for key in ("history", "play_history", "items", "list", "plays"):
            if key in data and isinstance(data[key], list):
                return data[key]
        return [data]

    raise ValueError("JSON did not contain a list or dict")


def extract_enriched_data(
    history_entries: List[Dict], 
    track_uris_to_enrich: Optional[List[str]] = None
) -> Tuple[List[Dict], List[Dict], List[Dict], Dict[str, str], List[Dict]]:
    """
    Extrait et enrichit les données depuis l'historique en utilisant l'API Spotify.
    
    Cette fonction traite les entrées d'historique en batch pour minimiser les appels API.
    Si track_uris_to_enrich est fourni, enrichit seulement ces tracks (optimisation).
    
    Args:
        history_entries: Liste des entrées d'historique Spotify
        track_uris_to_enrich: Liste optionnelle des URIs à enrichir (si None, enrichit tout)
    
    Returns:
        Tuple (artists_data, albums_data, tracks_data, track_uri_to_id_map, featuring_data)
    """
    enricher = get_spotify_enricher()
    
    # Collecter les URIs de tracks à enrichir
    if track_uris_to_enrich is None:
        # Mode legacy: enrichir toutes les tracks du fichier
        track_uris = set()
        for entry in history_entries:
            if entry.get('spotify_track_uri') and entry.get('master_metadata_track_name'):
                track_uris.add(entry['spotify_track_uri'])
        track_uris_list = list(track_uris)
    else:
        # Mode optimisé: enrichir seulement les tracks demandées
        track_uris_list = track_uris_to_enrich
    
    if not track_uris_list:
        print("⚠️  Aucune track à enrichir")
        return [], [], [], {}
    
    print(f"🎵 {len(track_uris_list)} tracks à enrichir via l'API Spotify...")
    
    # Enrichir les tracks en batch (par lots de 50)
    enriched_tracks = enricher.batch_enrich_tracks(track_uris_list)
    
    print(f"✅ {len(enriched_tracks)} tracks enrichies avec succès")
    
    # Extraire les données uniques
    artists_dict = {}  # id -> artist_data
    albums_dict = {}   # id -> album_data
    tracks_list = []
    track_uri_to_id = {}  # uri -> track_id
    
    for track_uri, track_data in enriched_tracks.items():
        # Track
        track_id = track_data['id']
        track_uri_to_id[track_uri] = track_id
        
        tracks_list.append({
            'id': track_id,
            'track_name': track_data['name'],
            'album_id': track_data['album']['id'],
            'duration_ms': track_data['duration_ms'],
            'main_artist_id': track_data['artists'][0]['id'],
            'popularity': track_data['popularity'],
            'track_cover_uri': track_data['album']['cover_image_uri']
        })
        
        # Album
        album_id = track_data['album']['id']
        if album_id not in albums_dict:
            albums_dict[album_id] = {
                'id': album_id,
                'album_name': track_data['album']['name'],
                'artist_id': track_data['album']['artist_id'],
                'release_date': normalize_release_date(track_data['album']['release_date']),
                'cover_image_uri': track_data['album']['cover_image_uri'],
                'total_tracks': track_data['album']['total_tracks']
            }
        
        # Artistes (main + featuring)
        for artist in track_data['artists']:
            artist_id = artist['id']
            if artist_id not in artists_dict:
                # On devra enrichir les artistes séparément pour avoir genres, popularity, etc.
                artists_dict[artist_id] = {
                    'id': artist_id,
                    'name': artist['name'],
                    'popularity': None,  # Sera enrichi après
                    'profile_picture_uri': None,
                    'genre': None
                }
    
    # Les artistes et albums seront enrichis seulement s'ils ne sont pas déjà en base
    # Cette vérification sera faite dans import_file_module.py
    # Ici on retourne les données minimales, l'enrichissement se fera après
    
    # Extraire les featuring (artistes secondaires)
    featuring_data = []
    for track_uri, track_data in enriched_tracks.items():
        track_id = track_data['id']
        # Skip le premier artiste (main artist), prendre les featuring
        for artist in track_data['artists'][1:]:
            featuring_data.append({
                'track_id': track_id,
                'artist_id': artist['id']
            })
    
    print(f"📊 {len(artists_dict)} artistes uniques trouvés")
    print(f"📊 {len(albums_dict)} albums uniques trouvés")
    print(f"📊 {len(featuring_data)} featuring trouvés")
    
    return (
        list(artists_dict.values()),
        list(albums_dict.values()),
        tracks_list,
        track_uri_to_id,
        featuring_data
    )


def extract_history_data(history_entries: List[Dict], user_id: str, track_uri_to_id: Dict[str, str]) -> List[Dict]:
    """
    Extrait les données de l'historique d'écoute.
    
    Args:
        history_entries: Liste des entrées d'historique Spotify
        user_id: ID de l'utilisateur
        track_uri_to_id: Mapping des URIs de tracks vers leurs IDs
    
    Returns:
        Liste de dictionnaires contenant les données de l'historique
    """
    history_data = []
    
    for entry in history_entries:
        track_uri = entry.get('spotify_track_uri')
        if track_uri and track_uri in track_uri_to_id:
            track_id = track_uri_to_id[track_uri]
            
            history_data.append({
                'user_id': user_id,
                'track_id': track_id,
                'played_at': entry.get('ts'),
                'ms_played': entry.get('ms_played'),
                'platform': entry.get('platform'),
                'country': entry.get('conn_country'),
                'ip_address': entry.get('ip_addr'),
                'reason_start': entry.get('reason_start'),
                'reason_end': entry.get('reason_end'),
                'skipped': entry.get('skipped'),
                'shuffle': entry.get('shuffle'),
                'offline': entry.get('offline'),
                'incognito': entry.get('incognito_mode')
            })
    
    return history_data


def extract_featuring_data(enriched_tracks: Dict[str, Dict]) -> List[Dict]:
    """
    Extrait les relations de featuring depuis les tracks enrichies.
    
    Args:
        enriched_tracks: Dictionnaire {track_uri: track_data} depuis l'API
    
    Returns:
        Liste de dictionnaires {track_id, artist_id} pour la table feat
    """
    featuring_data = []
    
    for track_data in enriched_tracks.values():
        track_id = track_data['id']
        # Skip le premier artiste (main artist), prendre les featuring
        for artist in track_data['artists'][1:]:
            featuring_data.append({
                'track_id': track_id,
                'artist_id': artist['id']
            })
    
    return featuring_data
