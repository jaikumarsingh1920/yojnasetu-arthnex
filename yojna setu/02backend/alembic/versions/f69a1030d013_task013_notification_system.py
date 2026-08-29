"""task013 notification system

Revision ID: f69a1030d013
Revises: e58b1029c012
Create Date: 2026-08-27 16:30:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = 'f69a1030d013'
down_revision: Union[str, None] = 'e58b1029c012'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create notifications table
    op.create_table(
        'notifications',
        sa.Column('notification_id', sa.String(length=50), nullable=False, primary_key=True),
        sa.Column('recipient_user_id', sa.String(length=50), sa.ForeignKey('users.user_id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('application_id', sa.String(length=50), sa.ForeignKey('applications.application_id', ondelete='SET NULL'), nullable=True, index=True),
        sa.Column('notification_type', sa.String(length=50), nullable=False, index=True),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('message', sa.Text(), nullable=False),
        sa.Column('priority', sa.String(length=20), nullable=False, server_default='NORMAL'),
        sa.Column('is_read', sa.Boolean(), nullable=False, server_default=sa.text('0'), index=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, index=True),
        sa.Column('read_at', sa.DateTime(), nullable=True),
        sa.Column('metadata_json', sa.Text(), nullable=True),
        sa.Column('channel', sa.String(length=20), nullable=False, server_default='IN_APP'),
        sa.Column('delivery_status', sa.String(length=20), nullable=False, server_default='DELIVERED'),
    )

    # Create notification_preferences table
    op.create_table(
        'notification_preferences',
        sa.Column('user_id', sa.String(length=50), sa.ForeignKey('users.user_id', ondelete='CASCADE'), nullable=False, primary_key=True),
        sa.Column('in_app_enabled', sa.Boolean(), nullable=False, server_default=sa.text('1')),
        sa.Column('email_enabled', sa.Boolean(), nullable=False, server_default=sa.text('1')),
        sa.Column('sms_enabled', sa.Boolean(), nullable=False, server_default=sa.text('1')),
        sa.Column('whatsapp_enabled', sa.Boolean(), nullable=False, server_default=sa.text('0')),
        sa.Column('push_enabled', sa.Boolean(), nullable=False, server_default=sa.text('0')),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
    )


def downgrade() -> None:
    op.drop_table('notification_preferences')
    op.drop_table('notifications')
