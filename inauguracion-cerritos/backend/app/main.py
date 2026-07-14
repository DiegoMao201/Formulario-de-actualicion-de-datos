"""Punto de entrada FastAPI. Crea tablas, siembra datos y monta routers."""
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .config import settings
from .database import Base, SessionLocal, engine
from .routers import admin, leads, magic, ruleta
from .seed import run_seed

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("main")


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Crea tablas (idempotente) y siembra admin + premios por defecto.
    Base.metadata.create_all(bind=engine)
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
app.include_router(admin.router)


@app.get("/api/health")
def health():
    return {"status": "ok", "app": settings.app_name}
