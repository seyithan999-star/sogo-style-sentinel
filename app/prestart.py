"""Safe Railway pre-start database migration runner.

Goals:
- fail fast with useful logs instead of hanging forever on DB locks;
- preserve existing data;
- handle the legacy case where tables were created by SQLAlchemy create_all()
  before Alembic's version table existed;
- run the normal Alembic upgrade for fresh or already-versioned databases.
"""
from __future__ import annotations

import logging
from urllib.parse import urlparse

from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.exc import SQLAlchemyError

from app.config import settings

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
logger = logging.getLogger("sogo.prestart")

EXPECTED_COLUMNS = {
    "products": {"id", "source_name", "brand", "title", "canonical_url", "canonical_url_hash", "category", "price", "currency", "published_at", "discovered_at", "score_commercial", "score_originality", "score_premium", "score_sogo_fit", "score_trend", "attributes", "raw_metadata", "is_suppressed", "delivered"},
    "product_images": {"id", "product_id", "url", "role", "order_index", "perceptual_hash", "quality_note"},
    "feedback": {"id", "product_id", "telegram_user_id", "action", "created_at"},
    "style_signals": {"id", "signal_type", "signal_value", "weight", "updated_at"},
    "source_runs": {"id", "source_name", "started_at", "finished_at", "status", "items_found", "items_new", "error_message"},
    "telegram_deliveries": {"id", "product_id", "chat_id", "status", "error_message", "sent_at"},
    "daily_reports": {"id", "report_date", "summary", "created_at"},
    "bot_settings": {"key", "value", "updated_at"},
}
EXPECTED_TABLES = set(EXPECTED_COLUMNS)


def _safe_db_label(url: str) -> str:
    """Return host/database only; never log credentials."""
    try:
        # SQLAlchemy driver suffix is not understood by urlparse as a special case,
        # but hostname/path parsing still works.
        parsed = urlparse(url)
        host = parsed.hostname or "unknown-host"
        database = (parsed.path or "").lstrip("/") or "unknown-db"
        return f"{host}/{database}"
    except Exception:
        return "configured database"


def _alembic_config() -> Config:
    cfg = Config("alembic.ini")
    cfg.set_main_option("sqlalchemy.url", settings.database_url_sync)
    return cfg


def _stamp_head() -> None:
    logger.warning(
        "All expected application tables exist but Alembic is not versioned. "
        "Stamping the existing schema as head; no tables or rows will be dropped."
    )
    command.stamp(_alembic_config(), "head")
    logger.info("Alembic stamp completed.")


def _upgrade_head() -> None:
    logger.info("Running Alembic upgrade to head...")
    command.upgrade(_alembic_config(), "head")
    logger.info("Alembic upgrade completed.")


def main() -> None:
    logger.info("Checking PostgreSQL before application startup (%s)...", _safe_db_label(settings.database_url_sync))

    # pool_pre_ping + short connection timeout avoids an indefinite-looking startup.
    engine = create_engine(
        settings.database_url_sync,
        pool_pre_ping=True,
        connect_args={"connect_timeout": 10},
    )

    try:
        with engine.connect() as conn:
            # PostgreSQL values are milliseconds. A blocked migration now becomes a
            # visible error instead of waiting indefinitely.
            conn.execute(text("SET lock_timeout = '10s'"))
            conn.execute(text("SET statement_timeout = '60s'"))
            conn.execute(text("SELECT 1"))
            logger.info("PostgreSQL connection is healthy.")

            inspector = inspect(conn)
            existing = set(inspector.get_table_names(schema="public"))
            has_version_table = "alembic_version" in existing
            existing_app_tables = EXPECTED_TABLES & existing

            logger.info(
                "Schema state: %d/%d app tables present; alembic_version=%s",
                len(existing_app_tables),
                len(EXPECTED_TABLES),
                has_version_table,
            )

            # Legacy deployment compatibility: previous app.main called create_all(),
            # which can leave a complete schema without alembic_version. We only
            # stamp when every expected table AND every expected column is present.
            if not has_version_table and existing_app_tables == EXPECTED_TABLES:
                schema_mismatches = {}
                for table_name, required_columns in EXPECTED_COLUMNS.items():
                    actual_columns = {c["name"] for c in inspector.get_columns(table_name, schema="public")}
                    missing_columns = sorted(required_columns - actual_columns)
                    if missing_columns:
                        schema_mismatches[table_name] = missing_columns

                if schema_mismatches:
                    raise RuntimeError(
                        "All SOGO table names exist but required columns are missing. "
                        f"Refusing to stamp an incompatible schema: {schema_mismatches}"
                    )

                # Release this inspection transaction before Alembic opens its own.
                conn.rollback()
                _stamp_head()
                return

            if not has_version_table and existing_app_tables:
                missing = sorted(EXPECTED_TABLES - existing_app_tables)
                raise RuntimeError(
                    "Database has a PARTIAL unversioned SOGO schema. Refusing to guess or "
                    f"overwrite data. Present={sorted(existing_app_tables)} Missing={missing}. "
                    "Manual schema inspection is required."
                )

            conn.rollback()

        _upgrade_head()
    except Exception as exc:
        logger.exception("Database pre-start check/migration failed: %s", exc)
        raise
    finally:
        engine.dispose()


if __name__ == "__main__":
    main()
