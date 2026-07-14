"""Punto de entrada FastAPI. Crea tablas, siembra datos y monta routers."""
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response

from .config import settings
from .database import Base, SessionLocal, engine
from sqlalchemy import text

from .routers import admin, leads, magic, ruleta, validar
from .seed import run_seed
from .services import qr as qr_svc

# Migración ligera idempotente para bases ya existentes (columnas nuevas de canje)
_MIGRACIONES = [
    "ALTER TABLE leads ADD COLUMN IF NOT EXISTS coupon_token VARCHAR(40)",
    "ALTER TABLE leads ADD COLUMN IF NOT EXISTS coupon_redeemed BOOLEAN DEFAULT FALSE",
    "ALTER TABLE leads ADD COLUMN IF NOT EXISTS coupon_redeemed_at TIMESTAMP",
    "ALTER TABLE leads ADD COLUMN IF NOT EXISTS coupon_redeemed_by VARCHAR(160)",
    "ALTER TABLE spins ADD COLUMN IF NOT EXISTS redeem_token VARCHAR(40)",
]

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("main")


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Crea tablas (idempotente) y siembra admin + premios por defecto.
    Base.metadata.create_all(bind=engine)
    # Migración ligera para bases ya existentes
    try:
        with engine.begin() as conn:
            for stmt in _MIGRACIONES:
                conn.execute(text(stmt))
    except Exception as e:  # noqa: BLE001
        logger.error("Migración falló: %s", e)
    db = SessionLocal()
    try:
        run_seed(db)
    except Exception as e:  # noqa: BLE001
        logger.error("Seed falló: %s", e)
    finally:
        db.close()
    yield


app = FastAPI(title=settings.app_name, lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(leads.router)
app.include_router(magic.router)
app.include_router(ruleta.router)
app.include_router(validar.router)
app.include_router(admin.router)


@app.get("/health")
def health():
    return {"status": "ok", "app": settings.app_name}


@app.get("/qr/registro.png")
def qr_registro():
    """QR fijo hacia el formulario de registro (para compartir por colaboradores)."""
    url = f"{settings.public_base_url}/registro"
    png = qr_svc.qr_png_bytes(url)
    return Response(content=png, media_type="image/png",
                    headers={"Cache-Control": "public, max-age=3600"})
