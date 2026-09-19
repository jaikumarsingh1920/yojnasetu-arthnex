"""production_scale_indexes_and_optimizations

Revision ID: i92d4063a016
Revises: h81c3052f015
Create Date: 2026-09-14 16:30:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'i92d4063a016'
down_revision = 'h81c3052f015'
branch_labels = None
depends_on = None


def create_index_safe(index_name: str, table_name: str, columns: list, unique: bool = False):
    """Safely creates index if it does not already exist."""
    bind = op.get_bind()
    insp = sa.inspect(bind)
    existing = [idx['name'] for idx in insp.get_indexes(table_name)]
    if index_name not in existing:
        op.create_index(index_name, table_name, columns, unique=unique)


def drop_index_safe(index_name: str, table_name: str):
    """Safely drops index if it exists."""
    bind = op.get_bind()
    insp = sa.inspect(bind)
    existing = [idx['name'] for idx in insp.get_indexes(table_name)]
    if index_name in existing:
        op.drop_index(index_name, table_name=table_name)


def upgrade():
    # 1. Indexes on schemes
    create_index_safe('ix_schemes_state_restriction', 'schemes', ['state_restriction'])
    create_index_safe('ix_schemes_sc_required', 'schemes', ['sc_required'])
    create_index_safe('ix_schemes_marginalized_group', 'schemes', ['marginalized_group'])
    create_index_safe('ix_schemes_business_stage', 'schemes', ['business_stage'])
    create_index_safe('ix_schemes_max_loan_amount', 'schemes', ['max_loan_amount'])
    create_index_safe('ix_schemes_created_at', 'schemes', ['created_at'])
    create_index_safe('ix_schemes_status_sector', 'schemes', ['scheme_status', 'sector'])
    create_index_safe('ix_schemes_status_type', 'schemes', ['scheme_status', 'scheme_type'])

    # 2. Indexes on candidate_schemes
    create_index_safe('ix_candidate_schemes_created_at', 'candidate_schemes', ['created_at'])
    create_index_safe('ix_candidate_schemes_status_relevance', 'candidate_schemes', ['candidate_status', 'relevance_status'])

    # 3. Composite index on scheme_rules (scheme_id, active)
    create_index_safe('ix_scheme_rules_scheme_active', 'scheme_rules', ['scheme_id', 'active'])

    # 4. Composite index on scheme_documents (scheme_id, active)
    create_index_safe('ix_scheme_documents_scheme_active', 'scheme_documents', ['scheme_id', 'active'])

    # 5. Composite index on scheme_changelogs (scheme_id, created_at)
    create_index_safe('ix_scheme_changelogs_scheme_created', 'scheme_changelogs', ['scheme_id', 'created_at'])

    # 6. Index on scheme_sources (source_url)
    create_index_safe('ix_scheme_sources_source_url', 'scheme_sources', ['source_url'])


def downgrade():
    # 6. Drop index on scheme_sources
    drop_index_safe('ix_scheme_sources_source_url', 'scheme_sources')

    # 5. Drop index on scheme_changelogs
    drop_index_safe('ix_scheme_changelogs_scheme_created', 'scheme_changelogs')

    # 4. Drop index on scheme_documents
    drop_index_safe('ix_scheme_documents_scheme_active', 'scheme_documents')

    # 3. Drop index on scheme_rules
    drop_index_safe('ix_scheme_rules_scheme_active', 'scheme_rules')

    # 2. Drop indexes on candidate_schemes
    drop_index_safe('ix_candidate_schemes_status_relevance', 'candidate_schemes')
    drop_index_safe('ix_candidate_schemes_created_at', 'candidate_schemes')

    # 1. Drop indexes on schemes
    drop_index_safe('ix_schemes_status_type', 'schemes')
    drop_index_safe('ix_schemes_status_sector', 'schemes')
    drop_index_safe('ix_schemes_created_at', 'schemes')
    drop_index_safe('ix_schemes_max_loan_amount', 'schemes')
    drop_index_safe('ix_schemes_business_stage', 'schemes')
    drop_index_safe('ix_schemes_marginalized_group', 'schemes')
    drop_index_safe('ix_schemes_sc_required', 'schemes')
    drop_index_safe('ix_schemes_state_restriction', 'schemes')
