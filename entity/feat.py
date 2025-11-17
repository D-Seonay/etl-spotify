from base import Base
from sqlalchemy import Column, String, ForeignKey


class Feat(Base):
    """
    Feat entity representing a featured artist on a track.

    Description:
    This class defines the structure of the 'feats' table in the database.
    It includes attributes such as id, track_id, and artist_id.
    """
    __tablename__ = 'feats'

    track_id = Column(String, ForeignKey('tracks.id'), nullable=False, primary_key=True)
    artist_id = Column(String, ForeignKey('artists.id'), nullable=False, primary_key=True)

    def __repr__(self):
        return f"<Feat(track_id={self.track_id}, artist_id={self.artist_id})>"