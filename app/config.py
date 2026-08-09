"""
Merkezi yapılandırma. Tüm secret/ayarlar environment variable'lardan okunur.
Hiçbir token veya şifre bu dosyada / kodun içinde sabit yazılmaz.
"""
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # Telegram
    telegram_bot_token: str
    telegram_admin_ids: str = ""
    telegram_report_chat_id: str = ""

    # Database
    database_url: str
    database_url_sync: str

    # App behaviour
    app_timezone: str = "Europe/Istanbul"
    daily_report_hour: int = 8
    daily_report_minute: int = 0
    daily_target_min: int = 100
    daily_target_max: int = 200
    min_sogo_score: int = 55

    # Dashboard
    dashboard_username: str = "admin"
    dashboard_password: str = "change-this-password"
    secret_key: str = "change-this"

    # Webhook
    use_webhook: bool = False
    webhook_base_url: str = ""
    webhook_secret: str = "change-this-webhook-secret"
    port: int = 8000

    @property
    def admin_ids(self) -> list[int]:
        return [int(x.strip()) for x in self.telegram_admin_ids.split(",") if x.strip()]


settings = Settings()
