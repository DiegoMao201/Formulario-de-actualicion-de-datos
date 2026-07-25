"""Inicialización idempotente: crea el admin y premios por defecto si no existen."""
import logging

from sqlalchemy.orm import Session

from .config import settings
from .models import AdminUser, Channel, Prize
from .security import hash_password
from .utils import slugify

logger = logging.getLogger("seed")

# Premios de ejemplo (editables luego desde el panel admin).
# es_perdedor=True => segmento "Sigue participando" (stock infinito).
PREMIOS_DEFAULT = [
    {"nombre": "Galón Viniltex", "descripcion": "Galón de Viniltex advanced mate",
     "stock_total": 10, "probabilidad": 0.08, "color": "#0A2E57", "orden": 1},
    {"nombre": "Kit Pinceles Pintuco", "descripcion": "Set de brochas y rodillos",
     "stock_total": 25, "probabilidad": 0.15, "color": "#E63329", "orden": 2},
    {"nombre": "Sigue participando", "descripcion": "¡Gracias por participar!",
     "stock_total": 0, "probabilidad": 0.44, "color": "#12386b",
     "es_perdedor": True, "orden": 3},
    {"nombre": "Bono $20.000", "descripcion": "Bono de descuento en tienda",
     "stock_total": 40, "probabilidad": 0.18, "color": "#FFD200", "orden": 4},
    {"nombre": "Camiseta Pintuco", "descripcion": "Camiseta edición inauguración",
     "stock_total": 15, "probabilidad": 0.10, "color": "#1F9E5A", "orden": 5},
    {"nombre": "Balón de fútbol", "descripcion": "Balón equipo ganador Pintuco",
     "stock_total": 5, "probabilidad": 0.05, "color": "#7A2E8E", "orden": 6},
]


def run_seed(db: Session) -> None:
    # Admin
    if not db.query(AdminUser).filter(AdminUser.email == settings.admin_email.lower()).first():
        db.add(AdminUser(
            email=settings.admin_email.lower(),
            hashed_password=hash_password(settings.admin_password),
            nombre="Administrador",
        ))
        logger.info("Admin creado: %s", settings.admin_email)

    # Premios por defecto de la inauguración (solo si NO hay premios sin canal)
    if db.query(Prize).filter(Prize.channel_id.is_(None)).count() == 0:
        for p in PREMIOS_DEFAULT:
            db.add(Prize(**p, stock_restante=p["stock_total"]))
        logger.info("Premios de inauguración sembrados.")

    seed_channels(db)
    db.commit()


# Sedes (mostrador, giran con número de factura) y vendedores externos (nombre + teléfono)
SEDES = ["Laureles", "San Antonio", "San Francisco", "Ópalo", "Cerritos", "Olaya", "Ferrebox"]

# Premios de ejemplo por canal (editables desde el admin)
PREMIOS_CANAL = [
    {"nombre": "Souvenir Pintuco", "stock_total": 100, "probabilidad": 0.25, "color": "#E63329", "orden": 1},
    {"nombre": "Descuento 5%", "stock_total": 200, "probabilidad": 0.25, "color": "#FFD200", "orden": 2},
    {"nombre": "Sigue participando", "stock_total": 0, "probabilidad": 0.40, "color": "#12386b",
     "es_perdedor": True, "orden": 3},
    {"nombre": "Gorra Pintuco", "stock_total": 30, "probabilidad": 0.10, "color": "#1F9E5A", "orden": 4},
]


def _crear_premios_canal(db: Session, channel_id: str) -> None:
    for p in PREMIOS_CANAL:
        db.add(Prize(**p, stock_restante=p["stock_total"], channel_id=channel_id))


def seed_channels(db: Session) -> None:
    """Crea las 7 sedes y 10 vendedores (con premios de ejemplo) si no existen."""
    if db.query(Channel).count() > 0:
        return
    orden = 0
    for nombre in SEDES:
        orden += 1
        ch = Channel(tipo="sede", nombre=nombre, slug=slugify(nombre),
                     modo="factura", orden=orden)
        db.add(ch)
        db.flush()
        _crear_premios_canal(db, ch.id)
    for i in range(1, 11):
        ch = Channel(tipo="vendedor", nombre=f"Vendedor {i}", slug=f"vendedor-{i}",
                     modo="vendedor", orden=i)
        db.add(ch)
        db.flush()
        _crear_premios_canal(db, ch.id)
    logger.info("Canales (7 sedes + 10 vendedores) sembrados.")
