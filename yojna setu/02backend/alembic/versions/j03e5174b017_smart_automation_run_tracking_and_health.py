"""smart_automation_run_tracking_and_health

Revision ID: j03e5174b017
Revises: i92d4063a016
Create Date: 2026-09-14 17:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'j03e5174b017'
down_revision = 'i92d4063a016'
branch_labels = None
depends_on = None


def table_exists(table_name: str) -> bool:
    bind = op.get_bind()
    insp = sa.inspect(bind)
    return table_name in insp.get_table_names()


def column_exists(table_name: str, column_name: str) -> bool:
    bind = op.get_bind()
    insp = sa.inspect(bind)
    columns = [col['name'] for col in insp.get_columns(table_name)]
    return column_name in columns


def upgrade():
    # 1. Create ingestion_runs table if not exists
    if not table_exists('ingestion_runs'):
        op.create_table(
            'ingestion_runs',
            sa.Column('run_id', sa.String(length=50), nullable=False),
            sa.Column('started_at', sa.DateTime(), nullable=False),
            sa.Column('completed_at', sa.DateTime(), nullable=True),
            sa.Column('status', sa.String(length=50), nullable=False, server_default='RUNNING'),
            sa.Column('records_seen', sa.Integer(), nullable=False, server_default='0'),
            sa.Column('records_changed', sa.Integer(), nullable=False, server_default='0'),
            sa.Column('records_unchanged', sa.Integer(), nullable=False, server_default='0'),
            sa.Column('records_failed', sa.Integer(), nullable=False, server_default='0'),
            sa.Column('records_staged', sa.Integer(), nullable=False, server_default='0'),
            sa.Column('records_promoted', sa.Integer(), nullable=False, server_default='0'),
            sa.Column('records_needing_review', sa.Integer(), nullable=False, server_default='0'),
            sa.Column('checkpoint_data', sa.Text(), nullable=True),
            sa.Column('error_summary', sa.Text(), nullable=True),
            sa.PrimaryKeyConstraint('run_id')
        )
        op.create_index('ix_ingestion_runs_run_id', 'ingestion_runs', ['run_id'], unique=False)
        op.create_index('ix_ingestion_runs_status', 'ingestion_runs', ['status'], unique=False)
        op.create_index('ix_ingestion_runs_started_at', 'ingestion_runs', ['started_at'], unique=False)

    # 2. Create source_health_logs table if not exists
    if not table_exists('source_health_logs'):
        op.create_table(
            'source_health_logs',
            sa.Column('log_id', sa.String(length=50), nullable=False),
            sa.Column('source_id', sa.String(length=50), nullable=False),
            sa.Column('run_id', sa.String(length=50), nullable=True),
            sa.Column('status', sa.String(length=50), nullable=False),
            sa.Column('error_category', sa.String(length=50), nullable=True),
            sa.Column('http_status_code', sa.Integer(), nullable=True),
            sa.Column('latency_ms', sa.Integer(), nullable=False, server_default='0'),
            sa.Column('error_message', sa.Text(), nullable=True),
            sa.Column('recorded_at', sa.DateTime(), nullable=False),
            sa.ForeignKeyConstraint(['source_id'], ['scheme_sources.source_id'], ondelete='CASCADE'),
            sa.ForeignKeyConstraint(['run_id'], ['ingestion_runs.run_id'], ondelete='SET NULL'),
            sa.PrimaryKeyConstraint('log_id')
        )
        op.create_index('ix_source_health_logs_log_id', 'source_health_logs', ['log_id'], unique=False)
        op.create_index('ix_source_health_logs_source_id', 'source_health_logs', ['source_id'], unique=False)
        op.create_index('ix_source_health_logs_run_id', 'source_health_logs', ['run_id'], unique=False)
        op.create_index('ix_source_health_logs_recorded_at', 'source_health_logs', ['recorded_at'], unique=False)

    # 3. Add health columns to scheme_sources if missing
    if table_exists('scheme_sources'):
        if not column_exists('scheme_sources', 'consecutive_failures'):
            op.add_column('scheme_sources', sa.Column('consecutive_failures', sa.Integer(), nullable=False, server_default='0'))
        if not column_exists('scheme_sources', 'health_status'):
            op.add_column('scheme_sources', sa.Column('health_status', sa.String(length=50), nullable=False, server_default='HEALTHY'))

    # 4. Add governance_category to pending_scheme_updates if missing
    if table_exists('pending_scheme_updates'):
        if not column_exists('pending_scheme_updates', 'governance_category'):
            op.add_column('pending_scheme_updates', sa.Column('governance_category', sa.String(length=50), nullable=False, server_default='NEEDS_REVIEW'))


def downgrade():
    bind = op.get_bind()
    is_sqlite = bind.dialect.name == 'sqlite'

    if table_exists('source_health_logs'):
        op.drop_table('source_health_logs')

    if table_exists('ingestion_runs'):
        op.drop_table('ingestion_runs')

    # Dropping columns on SQLite requires batch mode or alter
    if not is_sqlite:
        if table_exists('scheme_sources') and column_exists('scheme_sources', 'consecutive_failures'):
            op.drop_column('scheme_sources', 'consecutive_failures')
        if table_exists('scheme_sources') and column_exists('scheme_sources', 'health_status'):
            op.drop_column('scheme_sources', 'health_status')
        if table_exists('pending_scheme_updates') and column_exists('pending_scheme_updates', 'governance_category'):
            op.drop_column('pending_scheme_updates', 'governance_category')
