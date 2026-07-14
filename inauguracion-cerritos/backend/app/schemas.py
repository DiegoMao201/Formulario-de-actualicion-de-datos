"""Esquemas Pydantic para validación de entrada/salida."""
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr, Field, field_validator


# ---------- Público: registro ----------
class LeadCreate(BaseModel):
    nombre: str = Field(min_length=2, max_length=160)
    telefono: str = Field(min_length=7, max_length=40)
    correo: EmailStr
    cedula: str = Field(min_length=4, max_length=40)
    direccion: Optional[str] = Field(default=None, max_length=255)
    consentimiento_datos: bool
    referral_code: Optional[str] = None  # código de quien lo invitó

    @field_validator("consentimiento_datos")
    @classmethod
    def debe_consentir(cls, v: bool) -> bool:
        if not v:
            raise ValueError("Debes aceptar el tratamiento de datos personales.")
        return v

    @field_validator("telefono", "cedula")
    @classmethod
    def solo_digitos_razonable(cls, v: str) -> str:
        limpio = v.strip()
        if not limpio:
            raise ValueError("Valor requerido.")
        return limpio


class LeadResponse(BaseModel):
    id: str
    nombre: str
    coupon_code: str
    referral_code: str
    magic_token: str
    whatsapp_url: str


# ---------- Ruleta ----------
class WheelSegment(BaseModel):
    id: str
    nombre: str
    color: str
    es_perdedor: bool


class SpinResult(BaseModel):
    gano: bool
    prize_id: Optional[str]
    prize_nombre: Optional[str]
    segment_index: int  # índice del segmento a resaltar en la animación
    mensaje: str


# ---------- Admin ----------
class AdminLogin(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class PrizeBase(BaseModel):
    nombre: str = Field(min_length=1, max_length=120)
    descripcion: Optional[str] = None
    stock_total: int = Field(ge=0)
    probabilidad: float = Field(ge=0)
    color: str = "#0A2E57"
    es_perdedor: bool = False
    activo: bool = True
    orden: int = 0


class PrizeCreate(PrizeBase):
    pass


class PrizeUpdate(BaseModel):
    nombre: Optional[str] = None
    descripcion: Optional[str] = None
    stock_total: Optional[int] = Field(default=None, ge=0)
    probabilidad: Optional[float] = Field(default=None, ge=0)
    color: Optional[str] = None
    es_perdedor: Optional[bool] = None
    activo: Optional[bool] = None
    orden: Optional[int] = None


class PrizeResponse(PrizeBase):
    id: str
    stock_restante: int

    class Config:
        from_attributes = True


class Metrics(BaseModel):
    total_participantes: int
    total_giros: int
    premios_ganados: int
    premios_entregados: int
    premios_disponibles: int
    tasa_conversion: float


class RedeemRequest(BaseModel):
    token: str  # JWT contenido en el QR escaneado


class RedeemResponse(BaseModel):
    valido: bool
    ya_redimido: bool
    mensaje: str
    tipo: Optional[str] = None  # "premio" | "cupon"
    premio: Optional[str] = None
    cliente: Optional[str] = None
    fecha_giro: Optional[datetime] = None
