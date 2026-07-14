"""Lógica de validación y canje de QRs (cupón y premio) por token corto."""
from datetime import datetime
from urllib.parse import parse_qs, urlparse

from sqlalchemy.orm import Session

from ..models import Lead, Prize, Spin


def extraer_token(raw: str) -> str:
    """Acepta el token pelado o una URL /validar?t=XXX (lo que devuelve el escáner)."""
    raw = (raw or "").strip()
    if "t=" in raw and ("http" in raw or "/validar" in raw):
        try:
            q = parse_qs(urlparse(raw).query)
            if q.get("t"):
                return q["t"][0]
        except Exception:
            pass
    # A veces el escáner devuelve solo la query
    if raw.startswith("t="):
        return raw[2:]
    return raw


def buscar(db: Session, token: str, lock: bool = False):
    """Devuelve ('premio', Spin) o ('cupon', Lead) o (None, None)."""
    q_spin = db.query(Spin).filter(Spin.redeem_token == token)
    if lock:
        q_spin = q_spin.with_for_update()
    spin = q_spin.first()
    if spin:
        return "premio", spin

    q_lead = db.query(Lead).filter(Lead.coupon_token == token)
    if lock:
        q_lead = q_lead.with_for_update()
    lead = q_lead.first()
    if lead:
        return "cupon", lead
    return None, None


def estado(db: Session, token: str) -> dict:
    """Estado de solo lectura (para la página pública /validar)."""
    tipo, obj = buscar(db, token)
    if not obj:
        return {"encontrado": False, "tipo": None, "titulo": None,
                "cliente": None, "redimido": False, "fecha_redencion": None}

    if tipo == "premio":
        lead = db.query(Lead).filter(Lead.id == obj.lead_id).first()
        prize = db.query(Prize).filter(Prize.id == obj.prize_id).first()
        return {
            "encontrado": True, "tipo": "premio",
            "titulo": prize.nombre if prize else "Premio",
            "cliente": lead.nombre if lead else None,
            "redimido": obj.redeemed,
            "fecha_redencion": obj.redeemed_at,
        }
    # cupón
    return {
        "encontrado": True, "tipo": "cupon",
        "titulo": "Cupón 10% de descuento",
        "cliente": obj.nombre,
        "redimido": obj.coupon_redeemed,
        "fecha_redencion": obj.coupon_redeemed_at,
    }


def canjear(db: Session, token: str, admin_email: str) -> dict:
    """Marca el QR como usado (un solo uso). Solo admin."""
    tipo, obj = buscar(db, token, lock=True)
    if not obj:
        return {"valido": False, "ya_redimido": False, "tipo": None,
                "mensaje": "QR inválido o no encontrado.", "premio": None,
                "cliente": None, "fecha_giro": None}

    if tipo == "premio":
        lead = db.query(Lead).filter(Lead.id == obj.lead_id).first()
        prize = db.query(Prize).filter(Prize.id == obj.prize_id).first()
        titulo = prize.nombre if prize else "Premio"
        if obj.redeemed:
            return {"valido": True, "ya_redimido": True, "tipo": "premio",
                    "mensaje": "⚠️ Este PREMIO ya fue entregado.", "premio": titulo,
                    "cliente": lead.nombre if lead else None, "fecha_giro": obj.created_at}
        obj.redeemed = True
        obj.redeemed_at = datetime.utcnow()
        obj.redeemed_by = admin_email
        db.commit()
        return {"valido": True, "ya_redimido": False, "tipo": "premio",
                "mensaje": "✅ Premio válido. Entrégalo al cliente.", "premio": titulo,
                "cliente": lead.nombre if lead else None, "fecha_giro": obj.created_at}

    # cupón
    if obj.coupon_redeemed:
        return {"valido": True, "ya_redimido": True, "tipo": "cupon",
                "mensaje": "⚠️ Este CUPÓN 10% ya fue usado.",
                "premio": "Cupón 10% de descuento", "cliente": obj.nombre,
                "fecha_giro": obj.created_at}
    obj.coupon_redeemed = True
    obj.coupon_redeemed_at = datetime.utcnow()
    obj.coupon_redeemed_by = admin_email
    db.commit()
    return {"valido": True, "ya_redimido": False, "tipo": "cupon",
            "mensaje": "✅ Cupón 10% válido. Aplica el descuento.",
            "premio": "Cupón 10% de descuento", "cliente": obj.nombre,
            "fecha_giro": obj.created_at}
