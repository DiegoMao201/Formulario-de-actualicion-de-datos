"""Generación y verificación de QRs firmados con JWT (HS256)."""
import base64
from datetime import datetime, timedelta, timezone
from io import BytesIO
from typing import Optional

import jwt
import qrcode

from ..config import settings


def _encode(payload: dict) -> str:
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def firmar_cupon(lead_id: str, code: str) -> str:
    now = datetime.now(timezone.utc)
    return _encode({
        "typ": "coupon",
        "lead_id": lead_id,
        "code": code,
        "iat": now,
        "exp": now + timedelta(days=settings.coupon_ttl_days),
    })


def firmar_premio(spin_id: str, lead_id: str, premio: str, cedula: str) -> str:
    now = datetime.now(timezone.utc)
    return _encode({
        "typ": "prize",
        "spin_id": spin_id,
        "lead_id": lead_id,
        "prize": premio,
        "cedula_last4": cedula[-4:] if cedula else "",
        "iat": now,
        "exp": now + timedelta(days=settings.prize_ttl_days),
    })


def verificar(token: str, tipo_esperado: str) -> Optional[dict]:
    """Devuelve el payload si la firma, expiración y tipo son válidos; si no, None."""
    try:
        payload = jwt.decode(
            token, settings.jwt_secret, algorithms=[settings.jwt_algorithm]
        )
        if payload.get("typ") != tipo_esperado:
            return None
        return payload
    except Exception:
        return None


def qr_data_uri(contenido: str) -> str:
    """Genera un PNG del QR y lo devuelve como data URI base64 (para email/HTML)."""
    qr = qrcode.QRCode(
        version=None,
        error_correction=qrcode.constants.ERROR_CORRECT_M,
        box_size=8,
        border=2,
    )
    qr.add_data(contenido)
    qr.make(fit=True)
    img = qr.make_image(fill_color="#0A2E57", back_color="white")
    buf = BytesIO()
    img.save(buf, format="PNG")
    b64 = base64.b64encode(buf.getvalue()).decode()
    return f"data:image/png;base64,{b64}"


def qr_png_bytes(contenido: str) -> bytes:
    qr = qrcode.make(contenido)
    buf = BytesIO()
    qr.save(buf, format="PNG")
    return buf.getvalue()


def url_validar(token: str) -> str:
    """URL corta que abre la página de validación al escanear el QR."""
    return f"{settings.public_base_url}/validar?t={token}"
