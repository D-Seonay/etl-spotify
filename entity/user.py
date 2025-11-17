from .base import Base
from sqlalchemy import Column, String
from sqlalchemy.orm import relationship


class User(Base):
    """
    User entity representing a user in the system.

    Description:
    This class defines the structure of the 'users' table in the database.
    It includes attributes such as id, display name, and profile picture URI.
    """
    __tablename__ = 'users'

    id = Column(String, primary_key=True)
    display_name = Column(String, unique=True, nullable=False)
    profile_picture_uri = Column(String, unique=True, nullable=False)

    def __repr__(self):
        return f"<User(id={self.id}, display_name='{self.display_name}', profile_picture_uri='{self.profile_picture_uri}')>"

    # Relationships
    histories = relationship('History', back_populates='user', cascade='all, delete-orphan')
