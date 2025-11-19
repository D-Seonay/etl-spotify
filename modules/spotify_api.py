"""
Module pour enrichir les données avec l'API Spotify.

Ce module utilise l'API Spotify pour récupérer les vraies informations
sur les artistes, albums et tracks à partir des URIs Spotify.
"""

import os
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
from typing import Dict, Optional, List
from dotenv import load_dotenv

load_dotenv()


class SpotifyEnricher:
    """Classe pour enrichir les données avec l'API Spotify."""
    
    def __init__(self):
        """Initialise le client Spotify avec les credentials."""
        client_id = os.getenv('SPOTIFY_CLIENT_ID')
        client_secret = os.getenv('SPOTIFY_CLIENT_SECRET')
        
        if not client_id or not client_secret:
            raise ValueError(
                "SPOTIFY_CLIENT_ID et SPOTIFY_CLIENT_SECRET doivent être définis dans .env\n"
                "Obtenez vos credentials sur: https://developer.spotify.com/dashboard"
            )
        
        credentials = SpotifyClientCredentials(
            client_id=client_id,
            client_secret=client_secret
        )
        self.sp = spotipy.Spotify(client_credentials_manager=credentials)
    
    def get_track_info(self, track_uri: str) -> Optional[Dict]:
        """
        Récupère les informations d'une track depuis l'API Spotify.
        
        Args:
            track_uri: URI Spotify de la track (ex: spotify:track:xxx)
        
        Returns:
            Dictionnaire avec les infos de la track ou None si erreur
        """
        try:
            track_id = track_uri.split(':')[-1]
            track = self.sp.track(track_id)
            
            # Extraire les infos principales
            return {
                'id': track['id'],
                'name': track['name'],
                'duration_ms': track['duration_ms'],
                'popularity': track['popularity'],
                'album_id': track['album']['id'],
                'album_name': track['album']['name'],
                'album_release_date': track['album']['release_date'],
                'album_total_tracks': track['album']['total_tracks'],
                'album_images': track['album']['images'],
                'artists': [
                    {
                        'id': artist['id'],
                        'name': artist['name'],
                        'uri': artist['uri']
                    }
                    for artist in track['artists']
                ],
                'main_artist_id': track['artists'][0]['id'] if track['artists'] else None,
                'main_artist_name': track['artists'][0]['name'] if track['artists'] else None
            }
        except Exception as e:
            print(f"⚠️  Erreur lors de la récupération de {track_uri}: {e}")
            return None
    
    def get_artist_info(self, artist_id: str) -> Optional[Dict]:
        """
        Récupère les informations d'un artiste depuis l'API Spotify.
        
        Args:
            artist_id: ID Spotify de l'artiste
        
        Returns:
            Dictionnaire avec les infos de l'artiste ou None si erreur
        """
        try:
            artist = self.sp.artist(artist_id)
            
            return {
                'id': artist['id'],
                'name': artist['name'],
                'popularity': artist['popularity'],
                'genres': ', '.join(artist['genres']) if artist['genres'] else None,
                'profile_picture_uri': artist['images'][0]['url'] if artist['images'] else None
            }
        except Exception as e:
            print(f"⚠️  Erreur lors de la récupération de l'artiste {artist_id}: {e}")
            return None
    
    def get_album_info(self, album_id: str) -> Optional[Dict]:
        """
        Récupère les informations d'un album depuis l'API Spotify.
        
        Args:
            album_id: ID Spotify de l'album
        
        Returns:
            Dictionnaire avec les infos de l'album ou None si erreur
        """
        try:
            album = self.sp.album(album_id)
            
            return {
                'id': album['id'],
                'name': album['name'],
                'artist_id': album['artists'][0]['id'] if album['artists'] else None,
                'artist_name': album['artists'][0]['name'] if album['artists'] else None,
                'release_date': album['release_date'],
                'total_tracks': album['total_tracks'],
                'cover_image_uri': album['images'][0]['url'] if album['images'] else None
            }
        except Exception as e:
            print(f"⚠️  Erreur lors de la récupération de l'album {album_id}: {e}")
            return None
    
    def enrich_track_data(self, track_uri: str) -> Optional[Dict]:
        """
        Enrichit les données d'une track avec toutes les informations liées.
        
        Args:
            track_uri: URI Spotify de la track
        
        Returns:
            Dictionnaire complet avec track, album, et artistes ou None si erreur
        """
        track_info = self.get_track_info(track_uri)
        if not track_info:
            return None
        
        # Récupérer les infos de l'artiste principal
        main_artist_info = None
        if track_info['main_artist_id']:
            main_artist_info = self.get_artist_info(track_info['main_artist_id'])
        
        # Récupérer les infos des featuring artists
        featuring_artists = []
        for artist in track_info['artists'][1:]:  # Skip le premier (main artist)
            artist_info = self.get_artist_info(artist['id'])
            if artist_info:
                featuring_artists.append(artist_info)
        
        return {
            'track': track_info,
            'main_artist': main_artist_info,
            'featuring_artists': featuring_artists,
            'album': {
                'id': track_info['album_id'],
                'name': track_info['album_name'],
                'release_date': track_info['album_release_date'],
                'total_tracks': track_info['album_total_tracks'],
                'cover_image_uri': track_info['album_images'][0]['url'] if track_info['album_images'] else None,
                'artist_id': track_info['main_artist_id']
            }
        }
    
    def batch_enrich_tracks(self, track_uris: List[str], max_tracks: int = 50) -> Dict[str, Dict]:
        """
        Enrichit plusieurs tracks en batch (optimisé pour réduire les appels API).
        
        Args:
            track_uris: Liste des URIs Spotify
            max_tracks: Nombre maximum de tracks à traiter par batch (limite API: 50)
        
        Returns:
            Dictionnaire {track_uri: données enrichies}
        """
        results = {}
        
        # Traiter par batches de 50 (limite API Spotify)
        for i in range(0, len(track_uris), max_tracks):
            batch = track_uris[i:i + max_tracks]
            track_ids = [uri.split(':')[-1] for uri in batch]
            
            try:
                tracks = self.sp.tracks(track_ids)
                
                for track_uri, track_data in zip(batch, tracks['tracks']):
                    if track_data:
                        results[track_uri] = {
                            'id': track_data['id'],
                            'name': track_data['name'],
                            'duration_ms': track_data['duration_ms'],
                            'popularity': track_data['popularity'],
                            'album': {
                                'id': track_data['album']['id'],
                                'name': track_data['album']['name'],
                                'release_date': track_data['album']['release_date'],
                                'total_tracks': track_data['album']['total_tracks'],
                                'cover_image_uri': track_data['album']['images'][0]['url'] if track_data['album']['images'] else None,
                                'artist_id': track_data['album']['artists'][0]['id'] if track_data['album']['artists'] else None
                            },
                            'artists': [
                                {
                                    'id': artist['id'],
                                    'name': artist['name']
                                }
                                for artist in track_data['artists']
                            ]
                        }
            except Exception as e:
                print(f"⚠️  Erreur lors du batch enrichment: {e}")
        
        return results


# Instance globale (singleton) pour réutiliser la connexion
_enricher_instance = None


def get_spotify_enricher() -> SpotifyEnricher:
    """Retourne une instance singleton de SpotifyEnricher."""
    global _enricher_instance
    if _enricher_instance is None:
        _enricher_instance = SpotifyEnricher()
    return _enricher_instance
