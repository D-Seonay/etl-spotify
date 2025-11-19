from .base import Base
from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship


class Artist(Base):
    """
    Artist entity representing a musical artist.

    Description:
    This class defines the structure of the 'artists' table in the database.
    It includes attributes such as id, name, popularity, profile picture URI, and genre.
    """
    __tablename__ = 'artists'

    id = Column(String, primary_key=True)
    name = Column(String, nullable=False)
    popularity = Column(Integer, nullable=True)
    profile_picture_uri = Column(String, nullable=True)
    genre = Column(String, nullable=True) # comma-separated list of genres

    def __repr__(self):
        return f"<Artist(id={self.id}, name='{self.name}', genre='{self.genre}')>"

    # Relationships
    albums = relationship('Album', back_populates='artist', cascade='all, delete-orphan')
    tracks = relationship('Track', back_populates='main_artist', cascade='all, delete-orphan')
