"""Helpers de generación de códigos legibles."""
import secrets
import string

_ALFA = string.ascii_uppercase + string.digits
_SIN_AMBIGUOS = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"  # sin 0/O/1/I


def codigo_cupon() -> str:
    cuerpo = "".join(secrets.choice(_SIN_AMBIGUOS) for _ in range(4))
    return f"CERRITOS-10-{cuerpo}"


def codigo_referido() -> str:
    return "".join(secrets.choice(_SIN_AMBIGUOS) for _ in range(6))


def token_url() -> str:
    return secrets.token_urlsafe(32)


def token_corto() -> str:
    """Token corto para QR de canje (URL corta => escanea fácil)."""
    return secrets.token_urlsafe(9)  # ~12 caracteres
