"""Ruleta: config visible + giro seguro (resultado decidido en backend)."""
from datetime import datetime

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import Lead, MagicLink, Prize, Spin
from ..schemas import SpinResult, WheelSegment
from ..services import email as email_svc
from ..services import qr as qr_svc
from ..services import ruleta as ruleta_svc
from ..utils import token_corto

router = APIRouter(prefix="/ruleta", tags=["ruleta"])


@router.get("/config", response_model=list[WheelSegment])
def config_ruleta(db: Session = Depends(get_db)):
    """Segmentos a dibujar. NO expone probabilidades ni stock (anti-trampa)."""
    segmentos = ruleta_svc.segmentos_visibles(db)
    return [
        WheelSegment(id=p.id, nombre=p.nombre, color=p.color, es_perdedor=p.es_perdedor)
        for p in segmentos
    ]


@router.post("/spin/{token}", response_model=SpinResult)
def girar(token: str, background: BackgroundTasks, db: Session = Depends(get_db)):
    ml = db.query(MagicLink).filter(MagicLink.token == token).with_for_update().first()
    if not ml:
        raise HTTPException(status_code=404, detail="Enlace inválido.")
    if ml.expires_at < datetime.utcnow():
        raise HTTPException(status_code=410, detail="Enlace expirado.")
    if ml.used:
        raise HTTPException(status_code=409, detail="Ya usaste tu giro.")

    lead = db.query(Lead).filter(Lead.id == ml.lead_id).first()
    if not lead:
        raise HTTPException(status_code=404, detail="Participante no encontrado.")
    if db.query(Spin).filter(Spin.lead_id == lead.id).first():
        ml.used = True
        db.commit()
        raise HTTPException(status_code=409, detail="Ya usaste tu giro.")

    # --- Decisión SEGURA en servidor ---
    premio, seed, indice, segmentos = ruleta_svc.elegir_premio(db)
    if not segmentos:
        raise HTTPException(status_code=503, detail="La ruleta no está configurada aún.")

    gano = premio is not None and not premio.es_perdedor
    spin = Spin(lead_id=lead.id, server_seed=seed, gano=gano)

    if gano:
        # Descuento atómico de stock (lock de fila)
        locked = db.query(Prize).filter(Prize.id == premio.id).with_for_update().first()
        if locked.stock_restante <= 0:
            # Se agotó entre la selección y el lock -> cae a "sigue participando"
            gano = False
            premio = None
            spin.gano = False
        else:
            locked.stock_restante -= 1
            spin.prize_id = locked.id

    spin.gano = gano
    ml.used = True
    db.add(spin)
    db.flush()

    if gano and premio is not None:
        spin.prize_jwt = qr_svc.firmar_premio(spin.id, lead.id, premio.nombre, lead.cedula)
        spin.redeem_token = token_corto()
        db.commit()
        db.refresh(spin)
        qr_png = qr_svc.qr_png_bytes(qr_svc.url_validar(spin.redeem_token))
        background.add_task(
            email_svc.enviar_premio, lead.correo, lead.nombre, premio.nombre, qr_png
        )
        # Notificación interna del premio ganado
        background.add_task(email_svc.notificar_premio, lead, premio.nombre)
        return SpinResult(
            gano=True,
            prize_id=premio.id,
            prize_nombre=premio.nombre,
            segment_index=indice,
            mensaje=f"¡Felicitaciones! Ganaste: {premio.nombre}. Te enviamos el QR por correo.",
        )

    db.commit()
    # Segmento sobre el que se detiene la animación cuando no gana premio físico
    idx_perdedor = indice if premio is not None else (
        next((i for i, p in enumerate(segmentos) if p.es_perdedor), 0)
    )
    return SpinResult(
        gano=False,
        prize_id=None,
        prize_nombre=None,
        segment_index=idx_perdedor,
        mensaje="¡Gracias por participar! Sigue disfrutando la inauguración. 🎉",
    )
