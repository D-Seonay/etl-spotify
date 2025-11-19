"""initial schema

Revision ID: 0001_initial_schema
Revises: 
Create Date: 2025-11-17 00:00:00.000000
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '0001_initial_schema'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # Create artists
    op.create_table(
        'artists',
        sa.Column('id', sa.String(), primary_key=True),
        sa.Column('name', sa.String(), nullable=False, unique=True),
        sa.Column('popularity', sa.Integer(), nullable=True),
        sa.Column('profile_picture_uri', sa.String(), nullable=True, unique=True),
        sa.Column('genre', sa.String(), nullable=True),
    )

    # Create users
    op.create_table(
        'users',
        sa.Column('id', sa.String(), primary_key=True),
        sa.Column('display_name', sa.String(), nullable=False, unique=True),
        sa.Column('profile_picture_uri', sa.String(), nullable=False, unique=True),
    )

    # Create albums
    op.create_table(
        'albums',
        sa.Column('id', sa.String(), primary_key=True),
        sa.Column('album_name', sa.String(), nullable=False, unique=True),
        sa.Column('artist_id', sa.String(), sa.ForeignKey('artists.id'), nullable=False),
        sa.Column('release_date', sa.Date(), nullable=True),
        sa.Column('cover_image_uri', sa.String(), nullable=True, unique=True),
        sa.Column('total_tracks', sa.Integer(), nullable=True),
    )

    # Create tracks
    op.create_table(
        'tracks',
        sa.Column('id', sa.String(), primary_key=True),
        sa.Column('track_name', sa.String(), nullable=False, unique=True),
        sa.Column('album_id', sa.String(), sa.ForeignKey('albums.id'), nullable=False),
        sa.Column('duration_ms', sa.Integer(), nullable=True),
        sa.Column('main_artist_id', sa.String(), sa.ForeignKey('artists.id'), nullable=False),
        sa.Column('popularity', sa.Integer(), nullable=True),
        sa.Column('track_cover_uri', sa.String(), nullable=False, unique=True),
    )

    # Create feats (association)
    op.create_table(
        'feats',
        sa.Column('track_id', sa.String(), sa.ForeignKey('tracks.id'), primary_key=True, nullable=False),
        sa.Column('artist_id', sa.String(), sa.ForeignKey('artists.id'), primary_key=True, nullable=False),
    )

    # Create history
    op.create_table(
        'history',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('user_id', sa.String(), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('track_id', sa.String(), sa.ForeignKey('tracks.id'), nullable=False),
        sa.Column('played_at', sa.String(), nullable=False, unique=True),
        sa.Column('ms_played', sa.Integer(), nullable=True),
        sa.Column('platform', sa.String(), nullable=True),
        sa.Column('country', sa.String(), nullable=True),
        sa.Column('ip_address', sa.String(), nullable=True),
        sa.Column('reason_start', sa.String(), nullable=True),
        sa.Column('reason_end', sa.String(), nullable=True),
        sa.Column('skipped', sa.Boolean(), nullable=True),
        sa.Column('shuffle', sa.Boolean(), nullable=True),
        sa.Column('offline', sa.Boolean(), nullable=True),
        sa.Column('incognito', sa.Boolean(), nullable=True),
    )


def downgrade():
    op.drop_table('history')
    op.drop_table('feats')
    op.drop_table('tracks')
    op.drop_table('albums')
    op.drop_table('users')
    op.drop_table('artists')
