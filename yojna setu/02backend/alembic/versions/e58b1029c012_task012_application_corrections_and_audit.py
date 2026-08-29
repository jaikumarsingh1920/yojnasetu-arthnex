"""task012 application corrections and audit

Revision ID: e58b1029c012
Revises: d1b4a0ec61cd
Create Date: 2026-08-27 16:15:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = 'e58b1029c012'
down_revision: Union[str, None] = 'd1b4a0ec61cd'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add decision & correction columns to applications table
    with op.batch_alter_table('applications', schema=None) as batch_op:
        batch_op.add_column(sa.Column('rejection_reason', sa.Text(), nullable=True))
        batch_op.add_column(sa.Column('correction_reason', sa.Text(), nullable=True))
        batch_op.add_column(sa.Column('correction_fields', sa.Text(), nullable=True))
        batch_op.add_column(sa.Column('review_started_at', sa.DateTime(timezone=True), nullable=True))
        batch_op.add_column(sa.Column('decision_at', sa.DateTime(timezone=True), nullable=True))
        batch_op.add_column(sa.Column('decision_by', sa.String(length=36), nullable=True))

    # Create audit_logs table
    op.create_table(
        'audit_logs',
        sa.Column('log_id', sa.String(length=36), nullable=False),
        sa.Column('actor_user_id', sa.String(length=36), nullable=True),
        sa.Column('actor_role', sa.String(length=50), nullable=False),
        sa.Column('application_id', sa.String(length=36), nullable=True),
        sa.Column('action', sa.String(length=100), nullable=False),
        sa.Column('old_value', sa.Text(), nullable=True),
        sa.Column('new_value', sa.Text(), nullable=True),
        sa.Column('reason', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['actor_user_id'], ['users.user_id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['application_id'], ['applications.application_id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('log_id')
    )
    op.create_index(op.f('ix_audit_logs_log_id'), 'audit_logs', ['log_id'], unique=False)
    op.create_index(op.f('ix_audit_logs_actor_user_id'), 'audit_logs', ['actor_user_id'], unique=False)
    op.create_index(op.f('ix_audit_logs_application_id'), 'audit_logs', ['application_id'], unique=False)
    op.create_index(op.f('ix_audit_logs_action'), 'audit_logs', ['action'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_audit_logs_action'), table_name='audit_logs')
    op.drop_index(op.f('ix_audit_logs_application_id'), table_name='audit_logs')
    op.drop_index(op.f('ix_audit_logs_actor_user_id'), table_name='audit_logs')
    op.drop_index(op.f('ix_audit_logs_log_id'), table_name='audit_logs')
    op.drop_table('audit_logs')

    with op.batch_alter_table('applications', schema=None) as batch_op:
        batch_op.drop_column('decision_by')
        batch_op.drop_column('decision_at')
        batch_op.drop_column('review_started_at')
        batch_op.drop_column('correction_fields')
        batch_op.drop_column('correction_reason')
        batch_op.drop_column('rejection_reason')
