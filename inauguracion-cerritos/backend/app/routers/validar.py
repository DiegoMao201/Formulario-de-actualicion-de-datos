"""Validación pública de QR (solo lectura, sin canjear)."""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ..database import get_db
from ..services import redeem as redeem_svc

router = APIRouter(prefix="/validar", tags=["validar"])


@router.get("/{token}")
def validar(token: str, db: Session = Depends(get_db)):
    tk = redeem_svc.extraer_token(token)
    return redeem_svc.estado(db, tk)
