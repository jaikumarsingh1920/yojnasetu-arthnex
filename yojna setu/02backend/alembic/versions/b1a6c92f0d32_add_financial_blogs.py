"""add financial blogs

Revision ID: b1a6c92f0d32
Revises: 3ba96b5c61ae
"""
from alembic import op
import sqlalchemy as sa

revision = "b1a6c92f0d32"
down_revision = "3ba96b5c61ae"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "financial_blogs",
        sa.Column("blog_id", sa.String(length=36), nullable=False),
        sa.Column("title", sa.String(length=180), nullable=False),
        sa.Column("summary", sa.String(length=500), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("author_id", sa.String(length=36), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["author_id"], ["users.user_id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("blog_id"),
    )
    op.create_index("ix_financial_blogs_created_at", "financial_blogs", ["created_at"])


def downgrade():
    op.drop_index("ix_financial_blogs_created_at", table_name="financial_blogs")
    op.drop_table("financial_blogs")
