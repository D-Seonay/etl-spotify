from .base import Base
from sqlalchemy import Column, Integer, String, Date, ForeignKey
from sqlalchemy.orm import relationship


class Album(Base):
    """
    Album entity representing a musical album.

    Description:
    This class defines the structure of the 'albums' table in the database.
    It includes attributes such as id, title, release year, cover image URI, and genre.
    """
    __tablename__ = 'albums'

    id = Column(String, primary_key=True)
    album_name = Column(String, nullable=False)
    artist_id = Column(String, ForeignKey('artists.id'), nullable=False)
    release_date = Column(Date, nullable=True)
    cover_image_uri = Column(String, nullable=True)
    total_tracks = Column(Integer, nullable=True)  # total number of tracks in the album

    def __repr__(self):
        return f"<Album(id={self.id}, album_name='{self.album_name}', total_tracks={self.total_tracks})>"

    # Relationships
    artist = relationship('Artist', back_populates='albums')
    tracks = relationship('Track', back_populates='album', cascade='all, delete-orphan')