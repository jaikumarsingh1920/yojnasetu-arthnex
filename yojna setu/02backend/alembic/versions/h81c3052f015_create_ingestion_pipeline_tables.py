"""create_ingestion_pipeline_tables

Revision ID: h81c3052f015
Revises: g70b2041e014
Create Date: 2026-09-14 00:38:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'h81c3052f015'
down_revision = ('g70b2041e014', '83ac17d36697')
branch_labels = None
depends_on = None


def upgrade():
    # 1. scheme_sources
    op.create_table(
        'scheme_sources',
        sa.Column('source_id', sa.String(length=50), nullable=False),
        sa.Column('scheme_id', sa.String(length=50), nullable=True),
        sa.Column('source_name', sa.String(length=255), nullable=False),
        sa.Column('source_url', sa.Text(), nullable=False),
        sa.Column('authority', sa.String(length=255), nullable=True),
        sa.Column('source_type', sa.String(length=50), nullable=False, server_default='HTML'),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.text('1')),
        sa.Column('fetch_frequency_hours', sa.Integer(), nullable=False, server_default='24'),
        sa.Column('last_fetched_at', sa.DateTime(), nullable=True),
        sa.Column('last_status', sa.String(length=50), nullable=False, server_default='PENDING'),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['scheme_id'], ['schemes.scheme_id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('source_id')
    )
    op.create_index(op.f('ix_scheme_sources_source_id'), 'scheme_sources', ['source_id'], unique=False)
    op.create_index(op.f('ix_scheme_sources_scheme_id'), 'scheme_sources', ['scheme_id'], unique=False)

    # 2. source_snapshots
    op.create_table(
        'source_snapshots',
        sa.Column('snapshot_id', sa.String(length=50), nullable=False),
        sa.Column('source_id', sa.String(length=50), nullable=False),
        sa.Column('fetched_at', sa.DateTime(), nullable=False),
        sa.Column('content_hash', sa.String(length=64), nullable=False),
        sa.Column('content_type', sa.String(length=100), nullable=False, server_default='text/html'),
        sa.Column('raw_content', sa.Text(), nullable=True),
        sa.Column('fetch_status', sa.String(length=50), nullable=False, server_default='SUCCESS'),
        sa.Column('http_status_code', sa.Integer(), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(['source_id'], ['scheme_sources.source_id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('snapshot_id')
    )
    op.create_index(op.f('ix_source_snapshots_snapshot_id'), 'source_snapshots', ['snapshot_id'], unique=False)
    op.create_index(op.f('ix_source_snapshots_source_id'), 'source_snapshots', ['source_id'], unique=False)
    op.create_index(op.f('ix_source_snapshots_content_hash'), 'source_snapshots', ['content_hash'], unique=False)

    # 3. pending_scheme_updates
    op.create_table(
        'pending_scheme_updates',
        sa.Column('update_id', sa.String(length=50), nullable=False),
        sa.Column('scheme_id', sa.String(length=50), nullable=False),
        sa.Column('source_id', sa.String(length=50), nullable=False),
        sa.Column('snapshot_id', sa.String(length=50), nullable=True),
        sa.Column('old_version', sa.String(length=50), nullable=False, server_default='1.0'),
        sa.Column('extracted_data', sa.Text(), nullable=False),
        sa.Column('detected_changes', sa.Text(), nullable=False),
        sa.Column('validation_status', sa.String(length=50), nullable=False, server_default='VALID'),
        sa.Column('validation_errors', sa.Text(), nullable=True),
        sa.Column('status', sa.String(length=50), nullable=False, server_default='PENDING'),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('reviewed_at', sa.DateTime(), nullable=True),
        sa.Column('reviewed_by', sa.String(length=255), nullable=True),
        sa.Column('rejection_reason', sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(['scheme_id'], ['schemes.scheme_id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['source_id'], ['scheme_sources.source_id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['snapshot_id'], ['source_snapshots.snapshot_id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('update_id')
    )
    op.create_index(op.f('ix_pending_scheme_updates_update_id'), 'pending_scheme_updates', ['update_id'], unique=False)
    op.create_index(op.f('ix_pending_scheme_updates_scheme_id'), 'pending_scheme_updates', ['scheme_id'], unique=False)
    op.create_index(op.f('ix_pending_scheme_updates_source_id'), 'pending_scheme_updates', ['source_id'], unique=False)
    op.create_index(op.f('ix_pending_scheme_updates_status'), 'pending_scheme_updates', ['status'], unique=False)


def downgrade():
    op.drop_index(op.f('ix_pending_scheme_updates_status'), table_name='pending_scheme_updates')
    op.drop_index(op.f('ix_pending_scheme_updates_source_id'), table_name='pending_scheme_updates')
    op.drop_index(op.f('ix_pending_scheme_updates_scheme_id'), table_name='pending_scheme_updates')
    op.drop_index(op.f('ix_pending_scheme_updates_update_id'), table_name='pending_scheme_updates')
    op.drop_table('pending_scheme_updates')

    op.drop_index(op.f('ix_source_snapshots_content_hash'), table_name='source_snapshots')
    op.drop_index(op.f('ix_source_snapshots_source_id'), table_name='source_snapshots')
    op.drop_index(op.f('ix_source_snapshots_snapshot_id'), table_name='source_snapshots')
    op.drop_table('source_snapshots')

    op.drop_index(op.f('ix_scheme_sources_scheme_id'), table_name='scheme_sources')
    op.drop_index(op.f('ix_scheme_sources_source_id'), table_name='scheme_sources')
    op.drop_table('scheme_sources')
