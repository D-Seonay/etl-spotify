from .base import Base
from sqlalchemy import Column, Integer, String, Boolean, ForeignKey
from sqlalchemy.orm import relationship


class History(Base):
    """
    History entity representing a user's listening history.

    Description:
    This class defines the structure of the 'history' table in the database.
    It includes attributes such as id, user_id, track_id, played_at, ms_played, platform, country, ip_address,
    reason_start, reason_end, skipped, shuffle, offline, and incognito.
    """
    __tablename__ = 'history'

    id = Column(Integer, primary_key=True)
    user_id = Column(String, ForeignKey('users.id'), nullable=False)
    track_id = Column(String, ForeignKey('tracks.id'), nullable=False)
    played_at = Column(String, unique=True, nullable=False)  # ISO 8601 format timestamp
    ms_played = Column(Integer, nullable=True)  # duration played in milliseconds
    platform = Column(String, nullable=True)  # platform used to play the track
    country = Column(String, nullable=True)  # country code where the track was played
    ip_address = Column(String, nullable=True)  # IP address of the user when the track was played
    reason_start = Column(String, nullable=True)  # reason for starting the track
    reason_end = Column(String, nullable=True)  # reason for ending the track
    skipped = Column(Boolean, nullable=True)  # number of times the track was skipped
    shuffle = Column(Boolean, nullable=True)  # whether shuffle was enabled
    offline = Column(Boolean, nullable=True)  # whether the track was played offline
    incognito = Column(Boolean, nullable=True)  # whether the user was in incognito mode


    def __repr__(self):
        return f"<History(id={self.id}, user_id={self.user_id}, track_id={self.track_id}, played_at='{self.played_at}')>"

    # Relationships
    user = relationship('User', back_populates='histories')
    track = relationship('Track', back_populates='histories')