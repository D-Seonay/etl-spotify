"""remove incorrect unique constraints and fix nullable columns

Revision ID: 0002
Revises: 0001_initial_schema
Create Date: 2025-11-19 00:00:00.000000
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '0002'
down_revision = '0001_initial_schema'
branch_labels = None
depends_on = None


def upgrade():
    """
    Supprime les contraintes UNIQUE incorrectes et rend certaines colonnes nullable.
    
    Problèmes identifiés:
    - artists.name: Plusieurs artistes peuvent avoir le même nom (homonymes)
    - albums.album_name: Plusieurs albums peuvent avoir le même nom (différents artistes)
    - tracks.track_name: Plusieurs tracks peuvent avoir le même nom (versions différentes, albums différents)
    - tracks.track_cover_uri: Doit être nullable et non unique
    - artists.profile_picture_uri, albums.cover_image_uri: peuvent être NULL ou partagés
    - users.display_name, users.profile_picture_uri: peuvent être partagés et nullable
    """
    
    # Drop unique constraint on artists.name
    op.drop_constraint('artists_name_key', 'artists', type_='unique')
    
    # Drop unique constraint on artists.profile_picture_uri
    op.drop_constraint('artists_profile_picture_uri_key', 'artists', type_='unique')
    
    # Drop unique constraint on albums.album_name
    op.drop_constraint('albums_album_name_key', 'albums', type_='unique')
    
    # Drop unique constraint on albums.cover_image_uri
    op.drop_constraint('albums_cover_image_uri_key', 'albums', type_='unique')
    
    # Drop unique constraint on tracks.track_name
    op.drop_constraint('tracks_track_name_key', 'tracks', type_='unique')
    
    # Drop unique constraint on tracks.track_cover_uri
    op.drop_constraint('tracks_track_cover_uri_key', 'tracks', type_='unique')
    
    # Make tracks.track_cover_uri nullable
    op.alter_column('tracks', 'track_cover_uri',
                    existing_type=sa.String(),
                    nullable=True)
    
    # Drop unique constraint on users.display_name
    op.drop_constraint('users_display_name_key', 'users', type_='unique')
    
    # Drop unique constraint on users.profile_picture_uri
    op.drop_constraint('users_profile_picture_uri_key', 'users', type_='unique')
    
    # Make users.profile_picture_uri nullable
    op.alter_column('users', 'profile_picture_uri',
                    existing_type=sa.String(),
                    nullable=True)


def downgrade():
    """
    Remet les contraintes UNIQUE et NOT NULL (non recommandé car elles causent des problèmes)
    """
    # Revert nullable changes
    op.alter_column('tracks', 'track_cover_uri',
                    existing_type=sa.String(),
                    nullable=False)
    
    op.alter_column('users', 'profile_picture_uri',
                    existing_type=sa.String(),
                    nullable=False)
    
    # Recreate unique constraints
    op.create_unique_constraint('artists_name_key', 'artists', ['name'])
    op.create_unique_constraint('artists_profile_picture_uri_key', 'artists', ['profile_picture_uri'])
    op.create_unique_constraint('albums_album_name_key', 'albums', ['album_name'])
    op.create_unique_constraint('albums_cover_image_uri_key', 'albums', ['cover_image_uri'])
    op.create_unique_constraint('tracks_track_name_key', 'tracks', ['track_name'])
    op.create_unique_constraint('tracks_track_cover_uri_key', 'tracks', ['track_cover_uri'])
    op.create_unique_constraint('users_display_name_key', 'users', ['display_name'])
    op.create_unique_constraint('users_profile_picture_uri_key', 'users', ['profile_picture_uri'])
