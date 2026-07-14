"""Modelos SQLAlchemy de la plataforma de inauguración."""
import uuid
from datetime import datetime

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from .database import Base


def _uuid() -> str:
    return str(uuid.uuid4())


class Lead(Base):
    __tablename__ = "leads"

    id = Column(UUID(as_uuid=False), primary_key=True, default=_uuid)
    nombre = Column(String(160), nullable=False)
    telefono = Column(String(40), nullable=False, index=True)
    correo = Column(String(160), nullable=False, index=True)
    cedula = Column(String(40), nullable=False, unique=True, index=True)
    direccion = Column(String(255), nullable=True)

    # Ley 1581 / Habeas Data
    consentimiento_datos = Column(Boolean, default=False, nullable=False)
    consentimiento_ts = Column(DateTime, nullable=True)

    coupon_code = Column(String(40), unique=True, nullable=False, index=True)
    coupon_jwt = Column(Text, nullable=True)

    referral_code = Column(String(20), unique=True, nullable=False, index=True)
    referred_by = Column(UUID(as_uuid=False), ForeignKey("leads.id"), nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    spins = relationship("Spin", back_populates="lead")
    magic_links = relationship("MagicLink", back_populates="lead")


class Prize(Base):
    __tablename__ = "prizes"

    id = Column(UUID(as_uuid=False), primary_key=True, default=_uuid)
    nombre = Column(String(120), nullable=False)
    descripcion = Column(String(255), nullable=True)
    stock_total = Column(Integer, default=0, nullable=False)
    stock_restante = Column(Integer, default=0, nullable=False)
    probabilidad = Column(Float, default=0.0, nullable=False)  # peso relativo
    color = Column(String(20), default="#0A2E57", nullable=False)
    es_perdedor = Column(Boolean, default=False, nullable=False)  # "sigue participando"
    activo = Column(Boolean, default=True, nullable=False)
    orden = Column(Integer, default=0, nullable=False)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)


class Spin(Base):
    __tablename__ = "spins"

    id = Column(UUID(as_uuid=False), primary_key=True, default=_uuid)
    lead_id = Column(UUID(as_uuid=False), ForeignKey("leads.id"), nullable=False)
    prize_id = Column(UUID(as_uuid=False), ForeignKey("prizes.id"), nullable=True)

    server_seed = Column(String(64), nullable=False)  # provably fair
    gano = Column(Boolean, default=False, nullable=False)
    prize_jwt = Column(Text, nullable=True)

    redeemed = Column(Boolean, default=False, nullable=False)
    redeemed_at = Column(DateTime, nullable=True)
    redeemed_by = Column(String(160), nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    lead = relationship("Lead", back_populates="spins")
    prize = relationship("Prize")


class MagicLink(Base):
    __tablename__ = "magic_links"

    id = Column(UUID(as_uuid=False), primary_key=True, default=_uuid)
    lead_id = Column(UUID(as_uuid=False), ForeignKey("leads.id"), nullable=False)
    token = Column(String(64), unique=True, nullable=False, index=True)
    used = Column(Boolean, default=False, nullable=False)
    expires_at = Column(DateTime, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    lead = relationship("Lead", back_populates="magic_links")


class AdminUser(Base):
    __tablename__ = "admin_users"

    id = Column(UUID(as_uuid=False), primary_key=True, default=_uuid)
    email = Column(String(160), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    nombre = Column(String(120), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
