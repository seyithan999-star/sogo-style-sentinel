"""initial schema

Revision ID: 0001_initial
Revises:
Create Date: 2026-08-08

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0001_initial"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "products",
        sa.Column("id", postgresql.UUID(as_uuid=False), primary_key=True),
        sa.Column("source_name", sa.String(120), index=True),
        sa.Column("brand", sa.String(200), index=True),
        sa.Column("title", sa.String(500)),
        sa.Column("canonical_url", sa.Text),
        sa.Column("canonical_url_hash", sa.String(64), index=True),
        sa.Column("category", sa.String(200), nullable=True),
        sa.Column("price", sa.Float, nullable=True),
        sa.Column("currency", sa.String(10), nullable=True),
        sa.Column("published_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("discovered_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("score_commercial", sa.Float, default=0),
        sa.Column("score_originality", sa.Float, default=0),
        sa.Column("score_premium", sa.Float, default=0),
        sa.Column("score_sogo_fit", sa.Float, default=0),
        sa.Column("score_trend", sa.Float, default=0),
        sa.Column("attributes", sa.JSON, default=dict),
        sa.Column("raw_metadata", sa.JSON, default=dict),
        sa.Column("is_suppressed", sa.Boolean, default=False),
        sa.Column("delivered", sa.Boolean, default=False),
        sa.UniqueConstraint("canonical_url_hash", name="uq_product_url_hash"),
    )
    op.create_index("ix_products_brand_source", "products", ["brand", "source_name"])

    op.create_table(
        "product_images",
        sa.Column("id", postgresql.UUID(as_uuid=False), primary_key=True),
        sa.Column("product_id", postgresql.UUID(as_uuid=False), sa.ForeignKey("products.id", ondelete="CASCADE"), index=True),
        sa.Column("url", sa.Text),
        sa.Column("role", sa.String(30)),
        sa.Column("order_index", sa.Integer, default=0),
        sa.Column("perceptual_hash", sa.String(64), nullable=True, index=True),
        sa.Column("quality_note", sa.String(200), nullable=True),
        sa.UniqueConstraint("product_id", "perceptual_hash", name="uq_image_product_hash"),
    )

    op.create_table(
        "feedback",
        sa.Column("id", postgresql.UUID(as_uuid=False), primary_key=True),
        sa.Column("product_id", postgresql.UUID(as_uuid=False), sa.ForeignKey("products.id", ondelete="CASCADE"), index=True),
        sa.Column("telegram_user_id", sa.String(64), index=True),
        sa.Column("action", sa.String(20)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        "style_signals",
        sa.Column("id", postgresql.UUID(as_uuid=False), primary_key=True),
        sa.Column("signal_type", sa.String(50), index=True),
        sa.Column("signal_value", sa.String(200), index=True),
        sa.Column("weight", sa.Float, default=0.0),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.UniqueConstraint("signal_type", "signal_value", name="uq_signal_type_value"),
    )

    op.create_table(
        "source_runs",
        sa.Column("id", postgresql.UUID(as_uuid=False), primary_key=True),
        sa.Column("source_name", sa.String(120), index=True),
        sa.Column("started_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("status", sa.String(20), default="disabled"),
        sa.Column("items_found", sa.Integer, default=0),
        sa.Column("items_new", sa.Integer, default=0),
        sa.Column("error_message", sa.Text, nullable=True),
    )

    op.create_table(
        "telegram_deliveries",
        sa.Column("id", postgresql.UUID(as_uuid=False), primary_key=True),
        sa.Column("product_id", postgresql.UUID(as_uuid=False), sa.ForeignKey("products.id", ondelete="CASCADE"), index=True),
        sa.Column("chat_id", sa.String(64)),
        sa.Column("status", sa.String(20), default="pending"),
        sa.Column("error_message", sa.Text, nullable=True),
        sa.Column("sent_at", sa.DateTime(timezone=True), nullable=True),
    )

    op.create_table(
        "daily_reports",
        sa.Column("id", postgresql.UUID(as_uuid=False), primary_key=True),
        sa.Column("report_date", sa.String(10), unique=True, index=True),
        sa.Column("summary", sa.JSON, default=dict),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        "bot_settings",
        sa.Column("key", sa.String(100), primary_key=True),
        sa.Column("value", sa.JSON, default=dict),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )


def downgrade():
    op.drop_table("bot_settings")
    op.drop_table("daily_reports")
    op.drop_table("telegram_deliveries")
    op.drop_table("source_runs")
    op.drop_table("style_signals")
    op.drop_table("feedback")
    op.drop_table("product_images")
    op.drop_index("ix_products_brand_source", table_name="products")
    op.drop_table("products")
