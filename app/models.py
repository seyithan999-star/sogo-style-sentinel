import enum
import uuid
from datetime import datetime

from sqlalchemy import (
    String, Integer, Float, Boolean, DateTime, ForeignKey, Text, JSON,
    UniqueConstraint, Index, func
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


def gen_uuid():
    return str(uuid.uuid4())


class SourceHealthStatus(str, enum.Enum):
    healthy = "healthy"
    degraded = "degraded"
    blocked = "blocked"
    disabled = "disabled"


class Product(Base):
    __tablename__ = "products"

    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, default=gen_uuid)

    source_name: Mapped[str] = mapped_column(String(120), index=True)
    brand: Mapped[str] = mapped_column(String(200), index=True)
    title: Mapped[str] = mapped_column(String(500))
    canonical_url: Mapped[str] = mapped_column(Text)
    canonical_url_hash: Mapped[str] = mapped_column(String(64), index=True)

    category: Mapped[str | None] = mapped_column(String(200), nullable=True)
    price: Mapped[float | None] = mapped_column(Float, nullable=True)
    currency: Mapped[str | None] = mapped_column(String(10), nullable=True)

    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    discovered_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    # Puanlama
    score_commercial: Mapped[float] = mapped_column(Float, default=0)
    score_originality: Mapped[float] = mapped_column(Float, default=0)
    score_premium: Mapped[float] = mapped_column(Float, default=0)
    score_sogo_fit: Mapped[float] = mapped_column(Float, default=0)  # 0-100
    score_trend: Mapped[float] = mapped_column(Float, default=0)

    # Öznitelikler (öğrenme sisteminin kullandığı sinyaller)
    attributes: Mapped[dict] = mapped_column(JSON, default=dict)  # renk, kumaş, yaka, kol, siluet, nakış vb.
    raw_metadata: Mapped[dict] = mapped_column(JSON, default=dict)

    is_suppressed: Mapped[bool] = mapped_column(Boolean, default=False)  # "Gösterme" ile baskılanmış
    delivered: Mapped[bool] = mapped_column(Boolean, default=False)

    images: Mapped[list["ProductImage"]] = relationship(back_populates="product", cascade="all, delete-orphan")
    feedback: Mapped[list["Feedback"]] = relationship(back_populates="product", cascade="all, delete-orphan")
    deliveries: Mapped[list["TelegramDelivery"]] = relationship(back_populates="product", cascade="all, delete-orphan")

    __table_args__ = (
        UniqueConstraint("canonical_url_hash", name="uq_product_url_hash"),
        Index("ix_products_brand_source", "brand", "source_name"),
    )


class ProductImage(Base):
    __tablename__ = "product_images"

    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, default=gen_uuid)
    product_id: Mapped[str] = mapped_column(ForeignKey("products.id", ondelete="CASCADE"), index=True)

    url: Mapped[str] = mapped_column(Text)
    role: Mapped[str] = mapped_column(String(30))  # main | detail | back_or_angle
    order_index: Mapped[int] = mapped_column(Integer, default=0)
    perceptual_hash: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    quality_note: Mapped[str | None] = mapped_column(String(200), nullable=True)

    product: Mapped["Product"] = relationship(back_populates="images")

    __table_args__ = (
        UniqueConstraint("product_id", "perceptual_hash", name="uq_image_product_hash"),
    )


class FeedbackAction(str, enum.Enum):
    love = "love"          # Çok Beğendim
    like = "like"           # Beğendim
    favorite = "favorite"   # Favori
    dislike = "dislike"     # Beğenmedim
    hide = "hide"           # Gösterme
    save = "save"           # Kaydet


class Feedback(Base):
    __tablename__ = "feedback"

    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, default=gen_uuid)
    product_id: Mapped[str] = mapped_column(ForeignKey("products.id", ondelete="CASCADE"), index=True)
    telegram_user_id: Mapped[str] = mapped_column(String(64), index=True)
    action: Mapped[str] = mapped_column(String(20))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    product: Mapped["Product"] = relationship(back_populates="feedback")


class StyleSignal(Base):
    """Ürün tipi / renk / kumaş / yaka / kol / siluet / nakış / fiyat bandı / kaynak bazlı öğrenilen ağırlıklar."""
    __tablename__ = "style_signals"

    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, default=gen_uuid)
    signal_type: Mapped[str] = mapped_column(String(50), index=True)  # e.g. "color", "fabric", "collar", "source"
    signal_value: Mapped[str] = mapped_column(String(200), index=True)  # e.g. "ekru", "velour", "half_zip"
    weight: Mapped[float] = mapped_column(Float, default=0.0)  # -100..+100 arası öğrenilen ağırlık
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), onupdate=func.now(), server_default=func.now())

    __table_args__ = (
        UniqueConstraint("signal_type", "signal_value", name="uq_signal_type_value"),
    )


class SourceRun(Base):
    __tablename__ = "source_runs"

    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, default=gen_uuid)
    source_name: Mapped[str] = mapped_column(String(120), index=True)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    status: Mapped[str] = mapped_column(String(20), default=SourceHealthStatus.disabled.value)
    items_found: Mapped[int] = mapped_column(Integer, default=0)
    items_new: Mapped[int] = mapped_column(Integer, default=0)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)


class TelegramDelivery(Base):
    __tablename__ = "telegram_deliveries"

    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, default=gen_uuid)
    product_id: Mapped[str] = mapped_column(ForeignKey("products.id", ondelete="CASCADE"), index=True)
    chat_id: Mapped[str] = mapped_column(String(64))
    status: Mapped[str] = mapped_column(String(20), default="pending")  # pending|sent|failed
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    sent_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    product: Mapped["Product"] = relationship(back_populates="deliveries")


class DailyReport(Base):
    __tablename__ = "daily_reports"

    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, default=gen_uuid)
    report_date: Mapped[str] = mapped_column(String(10), unique=True, index=True)  # YYYY-MM-DD (idempotency key)
    summary: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class BotSetting(Base):
    __tablename__ = "bot_settings"

    key: Mapped[str] = mapped_column(String(100), primary_key=True)
    value: Mapped[dict] = mapped_column(JSON, default=dict)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), onupdate=func.now(), server_default=func.now())
