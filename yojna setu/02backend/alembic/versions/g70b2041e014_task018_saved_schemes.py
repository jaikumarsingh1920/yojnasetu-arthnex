"""task018_saved_schemes

Revision ID: g70b2041e014
Revises: f69a1030d013
Create Date: 2026-08-27 18:02:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'g70b2041e014'
down_revision = 'f69a1030d013'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'saved_schemes',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('user_id', sa.String(length=36), nullable=False),
        sa.Column('scheme_id', sa.String(length=50), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['scheme_id'], ['schemes.scheme_id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.user_id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id', 'scheme_id', name='uq_user_scheme_saved')
    )
    op.create_index('idx_saved_schemes_user_created', 'saved_schemes', ['user_id', 'created_at'], unique=False)
    op.create_index(op.f('ix_saved_schemes_scheme_id'), 'saved_schemes', ['scheme_id'], unique=False)
    op.create_index(op.f('ix_saved_schemes_user_id'), 'saved_schemes', ['user_id'], unique=False)


def downgrade():
    op.drop_index(op.f('ix_saved_schemes_user_id'), table_name='saved_schemes')
    op.drop_index(op.f('ix_saved_schemes_scheme_id'), table_name='saved_schemes')
    op.drop_index('idx_saved_schemes_user_created', table_name='saved_schemes')
    op.drop_table('saved_schemes')
