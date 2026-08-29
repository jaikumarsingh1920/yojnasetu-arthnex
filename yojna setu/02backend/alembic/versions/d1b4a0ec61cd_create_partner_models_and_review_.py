"""create partner models and review workflow extensions

Revision ID: d1b4a0ec61cd
Revises: cb50a85f4845
Create Date: 2026-08-27 13:18:01.658713

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'd1b4a0ec61cd'
down_revision: Union[str, Sequence[str], None] = 'cb50a85f4845'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # 1. Create partners table
    op.create_table(
        'partners',
        sa.Column('partner_id', sa.String(length=36), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('code', sa.String(length=50), nullable=False),
        sa.Column('partner_type', sa.String(length=50), nullable=False, server_default='CHANNELIZING_AGENCY'),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.text('1')),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('partner_id'),
        sa.UniqueConstraint('code')
    )
    op.create_index(op.f('ix_partners_code'), 'partners', ['code'], unique=True)
    op.create_index(op.f('ix_partners_name'), 'partners', ['name'], unique=False)
    op.create_index(op.f('ix_partners_partner_id'), 'partners', ['partner_id'], unique=False)

    # 2. Add partner_id to users
    with op.batch_alter_table('users', schema=None) as batch_op:
        batch_op.add_column(sa.Column('partner_id', sa.String(length=36), nullable=True))
        batch_op.create_index(batch_op.f('ix_users_partner_id'), ['partner_id'], unique=False)
        batch_op.create_foreign_key('fk_users_partner_id', 'partners', ['partner_id'], ['partner_id'], ondelete='SET NULL')

    # 3. Add assignment columns to applications
    with op.batch_alter_table('applications', schema=None) as batch_op:
        batch_op.add_column(sa.Column('assigned_partner_id', sa.String(length=36), nullable=True))
        batch_op.add_column(sa.Column('assigned_reviewer_id', sa.String(length=36), nullable=True))
        batch_op.create_index(batch_op.f('ix_applications_assigned_partner_id'), ['assigned_partner_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_applications_assigned_reviewer_id'), ['assigned_reviewer_id'], unique=False)
        batch_op.create_foreign_key('fk_apps_assigned_partner', 'partners', ['assigned_partner_id'], ['partner_id'], ondelete='SET NULL')
        batch_op.create_foreign_key('fk_apps_assigned_reviewer', 'users', ['assigned_reviewer_id'], ['user_id'], ondelete='SET NULL')

    # 4. Add verification columns to application_documents
    with op.batch_alter_table('application_documents', schema=None) as batch_op:
        batch_op.add_column(sa.Column('rejection_reason', sa.Text(), nullable=True))
        batch_op.add_column(sa.Column('verified_by', sa.String(length=36), nullable=True))
        batch_op.add_column(sa.Column('verified_at', sa.DateTime(timezone=True), nullable=True))
        batch_op.create_foreign_key('fk_app_docs_verified_by', 'users', ['verified_by'], ['user_id'], ondelete='SET NULL')

    # 5. Create application_review_notes table
    op.create_table(
        'application_review_notes',
        sa.Column('note_id', sa.String(length=36), nullable=False),
        sa.Column('application_id', sa.String(length=36), nullable=False),
        sa.Column('author_id', sa.String(length=36), nullable=False),
        sa.Column('author_role', sa.String(length=50), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['application_id'], ['applications.application_id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['author_id'], ['users.user_id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('note_id')
    )
    op.create_index(op.f('ix_application_review_notes_application_id'), 'application_review_notes', ['application_id'], unique=False)
    op.create_index(op.f('ix_application_review_notes_note_id'), 'application_review_notes', ['note_id'], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(op.f('ix_application_review_notes_note_id'), table_name='application_review_notes')
    op.drop_index(op.f('ix_application_review_notes_application_id'), table_name='application_review_notes')
    op.drop_table('application_review_notes')

    with op.batch_alter_table('application_documents', schema=None) as batch_op:
        batch_op.drop_constraint('fk_app_docs_verified_by', type_='foreignkey')
        batch_op.drop_column('verified_at')
        batch_op.drop_column('verified_by')
        batch_op.drop_column('rejection_reason')

    with op.batch_alter_table('applications', schema=None) as batch_op:
        batch_op.drop_constraint('fk_apps_assigned_reviewer', type_='foreignkey')
        batch_op.drop_constraint('fk_apps_assigned_partner', type_='foreignkey')
        batch_op.drop_index(batch_op.f('ix_applications_assigned_reviewer_id'))
        batch_op.drop_index(batch_op.f('ix_applications_assigned_partner_id'))
        batch_op.drop_column('assigned_reviewer_id')
        batch_op.drop_column('assigned_partner_id')

    with op.batch_alter_table('users', schema=None) as batch_op:
        batch_op.drop_constraint('fk_users_partner_id', type_='foreignkey')
        batch_op.drop_index(batch_op.f('ix_users_partner_id'))
        batch_op.drop_column('partner_id')

    op.drop_index(op.f('ix_partners_partner_id'), table_name='partners')
    op.drop_index(op.f('ix_partners_name'), table_name='partners')
    op.drop_index(op.f('ix_partners_code'), table_name='partners')
    op.drop_table('partners')
