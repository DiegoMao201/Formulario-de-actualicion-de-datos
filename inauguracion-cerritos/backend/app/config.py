"""Configuración central. Lee variables de entorno (Coolify) con valores por defecto
seguros para desarrollo local. Nunca hardcodear secretos aquí."""
from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # --- Base de datos ---
    database_url: str = "postgresql+psycopg2://cerritos:cerritos@db:5432/cerritos"

    # --- Marca / evento ---
    app_name: str = "Tienda Pintuco Cerritos"
    public_base_url: str = "https://cerritos.ferreinox.co"
    frontend_url: str = "https://cerritos.ferreinox.co"
    store_whatsapp: str = "573102806605"  # 310 280 66 05
    store_address: str = "Av. 30 de Agosto 105-42, Pereira"

    # --- Seguridad ---
    jwt_secret: str = "CAMBIAR-ESTE-SECRETO-EN-PRODUCCION"
    jwt_algorithm: str = "HS256"
    coupon_ttl_days: int = 30
    prize_ttl_days: int = 30
    magic_link_ttl_hours: int = 72
    session_ttl_hours: int = 12

    # --- Admin (bootstrap del primer usuario) ---
    admin_email: str = "admin@ferreinox.co"
    admin_password: str = "cambiar-esta-clave"

    # --- Email: SendGrid (primario) ---
    sendgrid_api_key: str = ""
    sendgrid_from_email: str = "tiendapintucopereira@ferreinox.co"
    sendgrid_from_name: str = "Ferreinox S.A.S. BIC"
    # Correo interno que recibe TODA la información de participación
    store_notify_email: str = "tiendapintucocerritos@ferreinox.co"

    # --- Email: SMTP Gmail (respaldo) ---
    smtp_server: str = ""
    smtp_port: int = 465
    smtp_user: str = ""
    smtp_password: str = ""

    # --- CORS ---
    cors_origins: str = "https://cerritos.ferreinox.co,http://localhost:3000"

    @property
    def cors_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
