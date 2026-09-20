"""create_scheme_translations_table

Revision ID: k14f6285c018
Revises: j03e5174b017
Create Date: 2026-09-19 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'k14f6285c018'
down_revision = 'j03e5174b017'
branch_labels = None
depends_on = None


def table_exists(table_name: str) -> bool:
    bind = op.get_bind()
    insp = sa.inspect(bind)
    return table_name in insp.get_table_names()


def index_exists(table_name: str, index_name: str) -> bool:
    bind = op.get_bind()
    insp = sa.inspect(bind)
    indexes = [idx['name'] for idx in insp.get_indexes(table_name)]
    return index_name in indexes


def upgrade():
    # 1. Create scheme_translations table if not exists
    if not table_exists('scheme_translations'):
        op.create_table(
            'scheme_translations',
            sa.Column('id', sa.String(length=36), nullable=False),
            sa.Column('scheme_id', sa.String(length=50), nullable=False),
            sa.Column('language_code', sa.String(length=10), nullable=False),
            sa.Column('field_name', sa.String(length=100), nullable=False),
            sa.Column('translated_text', sa.Text(), nullable=False),
            sa.Column('source_hash', sa.String(length=64), nullable=False),
            sa.Column('provider', sa.String(length=50), nullable=True),
            sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
            sa.Column('updated_at', sa.DateTime(), nullable=True),
            sa.ForeignKeyConstraint(['scheme_id'], ['schemes.scheme_id'], ondelete='CASCADE'),
            sa.PrimaryKeyConstraint('id')
        )
        op.create_index('ix_scheme_translations_id', 'scheme_translations', ['id'], unique=False)
        op.create_index('ix_scheme_translations_scheme_id', 'scheme_translations', ['scheme_id'], unique=False)
        op.create_index('ix_scheme_translations_language_code', 'scheme_translations', ['language_code'], unique=False)
        op.create_index('ix_scheme_translations_field_name', 'scheme_translations', ['field_name'], unique=False)
        op.create_index('ix_scheme_translations_source_hash', 'scheme_translations', ['source_hash'], unique=False)
        op.create_index(
            'ix_scheme_translations_lookup',
            'scheme_translations',
            ['scheme_id', 'language_code', 'field_name', 'source_hash'],
            unique=False
        )
        op.create_index(
            'ix_scheme_translations_scheme_lang',
            'scheme_translations',
            ['scheme_id', 'language_code'],
            unique=False
        )


def downgrade():
    if table_exists('scheme_translations'):
        op.drop_table('scheme_translations')
