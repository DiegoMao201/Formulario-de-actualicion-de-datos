"""Inicialización idempotente: crea el admin y premios por defecto si no existen."""
import logging

from sqlalchemy.orm import Session

from .config import settings
from .models import AdminUser, Prize
from .security import hash_password

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

    # Premios por defecto (solo si la tabla está vacía)
    if db.query(Prize).count() == 0:
        for p in PREMIOS_DEFAULT:
            db.add(Prize(**p, stock_restante=p["stock_total"]))
        logger.info("Premios por defecto sembrados.")

    db.commit()
