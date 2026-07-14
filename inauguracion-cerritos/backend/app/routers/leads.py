"""Registro de participantes (público)."""
from datetime import datetime, timedelta
from urllib.parse import quote

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from sqlalchemy.orm import Session

from ..config import settings
from ..database import get_db
from ..models import Lead, MagicLink
from ..schemas import LeadCreate, LeadResponse
from ..services import email as email_svc
from ..services import qr as qr_svc
from ..utils import codigo_cupon, codigo_referido, token_url

router = APIRouter(prefix="/leads", tags=["leads"])


def _whatsapp_url(nombre: str, magic_token: str) -> str:
    """Enlace wa.me para que el usuario se auto-envíe su Magic Link a la ruleta."""
    link = f"{settings.public_base_url}/ruleta?token={magic_token}"
    texto = (
        f"🎡 ¡Hola {nombre}! Este es tu enlace exclusivo para girar la ruleta de la "
        f"Tienda Pintuco Cerritos y ganar premios: {link}"
    )
    return f"https://wa.me/?text={quote(texto)}"


@router.post("", response_model=LeadResponse)
def registrar_lead(
    data: LeadCreate,
    background: BackgroundTasks,
    db: Session = Depends(get_db),
):
    # Anti-duplicado por cédula
    if db.query(Lead).filter(Lead.cedula == data.cedula).first():
        raise HTTPException(status_code=409, detail="Esta cédula ya está registrada.")

    # Referido (opcional)
    referred_by = None
    if data.referral_code:
        ref = db.query(Lead).filter(Lead.referral_code == data.referral_code).first()
        if ref:
            referred_by = ref.id

    # Códigos únicos
    coupon = codigo_cupon()
    while db.query(Lead).filter(Lead.coupon_code == coupon).first():
        coupon = codigo_cupon()
    referral = codigo_referido()
    while db.query(Lead).filter(Lead.referral_code == referral).first():
        referral = codigo_referido()

    lead = Lead(
        nombre=data.nombre.strip(),
        telefono=data.telefono.strip(),
        correo=str(data.correo).lower().strip(),
        cedula=data.cedula.strip(),
        direccion=(data.direccion or "").strip() or None,
        consentimiento_datos=True,
        consentimiento_ts=datetime.utcnow(),
        coupon_code=coupon,
        referral_code=referral,
        referred_by=referred_by,
    )
    db.add(lead)
    db.flush()  # obtiene lead.id

    # Firma del cupón (JWT) para el QR
    lead.coupon_jwt = qr_svc.firmar_cupon(lead.id, coupon)

    # Magic link de un solo uso hacia la ruleta
    magic = MagicLink(
        lead_id=lead.id,
        token=token_url(),
        expires_at=datetime.utcnow() + timedelta(hours=settings.magic_link_ttl_hours),
    )
    db.add(magic)
    db.commit()
    db.refresh(lead)

    # Email 1 (cupón + QR) en segundo plano para no bloquear la respuesta
    qr_png = qr_svc.qr_png_bytes(lead.coupon_jwt)
    background.add_task(email_svc.enviar_cupon, lead.correo, lead.nombre, coupon, qr_png)

    return LeadResponse(
        id=lead.id,
        nombre=lead.nombre,
        coupon_code=coupon,
        referral_code=referral,
        magic_token=magic.token,
        whatsapp_url=_whatsapp_url(lead.nombre, magic.token),
    )
