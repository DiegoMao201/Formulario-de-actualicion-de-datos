"""Validación de Magic Links (público)."""
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import Lead, MagicLink, Spin

router = APIRouter(prefix="/api/magic", tags=["magic"])


@router.get("/{token}")
def validar_magic(token: str, db: Session = Depends(get_db)):
    """Comprueba si el enlace es válido SIN consumirlo (se consume al girar)."""
    ml = db.query(MagicLink).filter(MagicLink.token == token).first()
    if not ml:
        raise HTTPException(status_code=404, detail="Enlace inválido.")
    if ml.expires_at < datetime.utcnow():
        raise HTTPException(status_code=410, detail="Este enlace ha expirado.")

    lead = db.query(Lead).filter(Lead.id == ml.lead_id).first()
    # ¿Ya usó su giro? (un solo giro por magic link)
    ya_giro = (
        db.query(Spin).filter(Spin.lead_id == ml.lead_id).first() is not None
        or ml.used
    )
    return {
        "valido": True,
        "usado": ya_giro,
        "nombre": lead.nombre if lead else None,
    }
