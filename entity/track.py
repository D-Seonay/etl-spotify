from .base import Base
from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship


class Track(Base):
    """
    Track entity representing a musical track.

    Description:
    This class defines the structure of the 'tracks' table in the database.
    It includes attributes such as id, title, duration, popularity, and album_id.
    """
    __tablename__ = 'tracks'

    id = Column(String, primary_key=True)
    track_name = Column(String, unique=True, nullable=False)
    album_id = Column(String, ForeignKey('albums.id'), nullable=False)
    duration_ms = Column(Integer, nullable=True)  # duration of the track in milliseconds
    main_artist_id = Column(String, ForeignKey('artists.id'), nullable=False)
    popularity = Column(Integer, nullable=True)
    track_cover_uri = Column(String, unique=True, nullable=False)

    # Relationships
    album = relationship('Album', back_populates='tracks')
    main_artist = relationship('Artist', back_populates='tracks')
    featuring_artists = relationship('Artist', secondary='feats', back_populates='featured_tracks')
    histories = relationship('History', back_populates='track', cascade='all, delete-orphan')

    def __repr__(self):
        return f"<Track(id={self.id}, track_name='{self.track_name}', album_id={self.album_id})>"