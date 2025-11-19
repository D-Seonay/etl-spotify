"""
Module d'insertion de données enrichies dans la base de données.

Les données sont déjà enrichies avec l'API Spotify, donc les IDs sont réels.
Plus besoin de mapping complexe.
"""

from sqlalchemy.orm import Session
from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from entity.artist import Artist
from entity.album import Album
from entity.track import Track
from entity.history import History
from entity.feat import Feat
from typing import List, Dict


def insert_artists(session: Session, artists_data: List[Dict]) -> int:
    """
    Insère les artistes dans la base de données.
    Utilise ON CONFLICT DO NOTHING pour éviter les doublons.
    
    Args:
        session: Session SQLAlchemy
        artists_data: Liste de dictionnaires contenant les données des artistes
    
    Returns:
        Nombre d'artistes insérés
    """
    if not artists_data:
        return 0
    
    # Regrouper les artistes par ID pour éviter les doublons
    unique_artists = {artist['id']: artist for artist in artists_data}.values()
    
    # Utiliser PostgreSQL INSERT ... ON CONFLICT DO NOTHING
    stmt = pg_insert(Artist).values(list(unique_artists))
    stmt = stmt.on_conflict_do_nothing(index_elements=['id'])
    
    result = session.execute(stmt)
    session.commit()
    
    return result.rowcount


def insert_albums(session: Session, albums_data: List[Dict]) -> int:
    """
    Insère les albums dans la base de données.
    Utilise ON CONFLICT DO NOTHING pour éviter les doublons.
    
    Args:
        session: Session SQLAlchemy
        albums_data: Liste de dictionnaires contenant les données des albums
    
    Returns:
        Nombre d'albums insérés
    """
    if not albums_data:
        return 0
    
    try:
        # On regroupe les artistes par ID pour éviter les doublons
        unique_albums = {album['id']: album for album in albums_data}.values()

        stmt = pg_insert(Album).values(list(unique_albums))
        stmt = stmt.on_conflict_do_nothing(index_elements=['id'])
    
        result = session.execute(stmt)
        session.commit()
        
        return result.rowcount

    except Exception as e:
        print(f"⚠️  Erreur lors de l'insertion des albums: {e}")
        session.rollback()
        return 0

def insert_tracks(session: Session, tracks_data: List[Dict]) -> int:
    """
    Insère les tracks dans la base de données.
    Utilise ON CONFLICT DO NOTHING pour éviter les doublons.
    
    Args:
        session: Session SQLAlchemy
        tracks_data: Liste de dictionnaires contenant les données des tracks
    
    Returns:
        Nombre de tracks insérées
    """
    if not tracks_data:
        return 0
    
    # Regrouper les tracks par ID pour éviter les doublons
    unique_tracks = {track['id']: track for track in tracks_data}.values()
    
    stmt = pg_insert(Track).values(list(unique_tracks))
    stmt = stmt.on_conflict_do_nothing(index_elements=['id'])
    
    result = session.execute(stmt)
    session.commit()
    
    return result.rowcount


def insert_history(session: Session, history_data: List[Dict]) -> int:
    """
    Insère l'historique d'écoute dans la base de données.
    Utilise ON CONFLICT DO NOTHING sur (user_id, played_at) pour éviter les doublons.
    
    Args:
        session: Session SQLAlchemy
        history_data: Liste de dictionnaires contenant les données de l'historique
    
    Returns:
        Nombre d'entrées d'historique insérées
    """
    if not history_data:
        return 0
    
    stmt = pg_insert(History).values(history_data)
    stmt = stmt.on_conflict_do_nothing(index_elements=['played_at'])
    
    result = session.execute(stmt)
    session.commit()
    
    return result.rowcount


def insert_featuring(session: Session, featuring_data: List[Dict]) -> int:
    """
    Insère les relations de featuring dans la base de données.
    Utilise ON CONFLICT DO NOTHING pour éviter les doublons.
    
    Args:
        session: Session SQLAlchemy
        featuring_data: Liste de dictionnaires {track_id, artist_id}
    
    Returns:
        Nombre de relations insérées
    """
    if not featuring_data:
        return 0
    
    stmt = pg_insert(Feat).values(featuring_data)
    stmt = stmt.on_conflict_do_nothing(index_elements=['track_id', 'artist_id'])
    
    result = session.execute(stmt)
    session.commit()
    
    return result.rowcount
