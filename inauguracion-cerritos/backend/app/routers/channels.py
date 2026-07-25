"""Giro rápido por canal (sede/vendedor). Público, sin registro completo.

- Sede (modo 'factura'): el cliente pone el número de factura y gira. 1 factura = 1 giro.
- Vendedor (modo 'vendedor'): el cliente pone nombre + teléfono y gira. 1 teléfono = 1 giro.
El resultado se decide en el backend. La entrega es inmediata (queda registrada).
"""
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import Channel, Prize, Spin
from ..schemas import ChannelPublic, ChannelSpinRequest, SpinResult, WheelSegment
from ..services import ruleta as ruleta_svc

router = APIRouter(prefix="/channels", tags=["channels"])


def _get_channel(slug: str, db: Session) -> Channel:
    ch = db.query(Channel).filter(Channel.slug == slug).first()
    if not ch:
        raise HTTPException(status_code=404, detail="Canal no encontrado.")
    if not ch.activo:
        raise HTTPException(status_code=403, detail="Este punto de giro está inactivo.")
    return ch


@router.get("/{slug}", response_model=ChannelPublic)
def info_canal(slug: str, db: Session = Depends(get_db)):
    ch = _get_channel(slug, db)
    return ChannelPublic(nombre=ch.nombre, tipo=ch.tipo, modo=ch.modo, activo=ch.activo)


@router.get("/{slug}/ruleta", response_model=list[WheelSegment])
def ruleta_canal(slug: str, db: Session = Depends(get_db)):
    ch = _get_channel(slug, db)
    segmentos = ruleta_svc.segmentos_visibles(db, ch.id)
    return [
        WheelSegment(id=p.id, nombre=p.nombre, color=p.color, es_perdedor=p.es_perdedor)
        for p in segmentos
    ]


@router.post("/{slug}/spin", response_model=SpinResult)
def girar_canal(slug: str, data: ChannelSpinRequest, db: Session = Depends(get_db)):
    ch = _get_channel(slug, db)

    # Validación de datos + anti-duplicado según el modo
    factura = (data.factura or "").strip()
    nombre = (data.nombre or "").strip()
    telefono = (data.telefono or "").strip()

    if ch.modo == "factura":
        if not factura:
            raise HTTPException(status_code=422, detail="Ingresa el número de factura.")
        dup = db.query(Spin).filter(
            Spin.channel_id == ch.id, Spin.factura == factura
        ).first()
        if dup:
            raise HTTPException(status_code=409, detail="Esta factura ya giró la ruleta.")
    else:  # vendedor
        if not (nombre and telefono):
            raise HTTPException(status_code=422, detail="Ingresa nombre y teléfono.")
        dup = db.query(Spin).filter(
            Spin.channel_id == ch.id, Spin.telefono == telefono
        ).first()
        if dup:
            raise HTTPException(status_code=409, detail="Este teléfono ya giró con este vendedor.")

    # Decisión segura en el servidor (premios del canal)
    premio, seed, indice, segmentos = ruleta_svc.elegir_premio(db, ch.id)
    if not segmentos:
        raise HTTPException(status_code=503, detail="Este punto aún no tiene premios configurados.")

    gano = premio is not None and not premio.es_perdedor
    spin = Spin(
        channel_id=ch.id, server_seed=seed, gano=gano,
        nombre=nombre or None, telefono=telefono or None, factura=factura or None,
    )

    if gano:
        locked = db.query(Prize).filter(Prize.id == premio.id).with_for_update().first()
        if locked.stock_restante <= 0:
            gano = False
            premio = None
        else:
            locked.stock_restante -= 1
            spin.prize_id = locked.id
    spin.gano = gano

    # Entrega inmediata (cara a cara): queda registrado como entregado.
    if gano:
        spin.redeemed = True
        spin.redeemed_at = datetime.utcnow()
        spin.redeemed_by = ch.nombre
    db.add(spin)
    db.commit()

    if gano and premio is not None:
        return SpinResult(
            gano=True, prize_id=premio.id, prize_nombre=premio.nombre,
            segment_index=indice,
            mensaje=f"¡Ganaste: {premio.nombre}! Reclámalo aquí mismo. 🎁",
        )
    idx = indice if premio is not None else (
        next((i for i, p in enumerate(segmentos) if p.es_perdedor), 0)
    )
    return SpinResult(
        gano=False, prize_id=None, prize_nombre=None, segment_index=idx,
        mensaje="¡Gracias por participar! 🎉",
    )
