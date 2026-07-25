"""Panel de administración: auth, métricas, CRUD de premios, redención de QR y export."""
import csv
import io
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy import func
from sqlalchemy.orm import Session

from ..config import settings
from ..database import get_db
from ..models import AdminUser, Channel, Lead, Prize, Spin
from ..schemas import (
    AdminLogin,
    ChannelCreate,
    ChannelResponse,
    ChannelUpdate,
    Metrics,
    PrizeCreate,
    PrizeResponse,
    PrizeUpdate,
    RedeemRequest,
    RedeemResponse,
    TokenResponse,
)
from ..security import create_session_token, get_current_admin, verify_password
from ..services import redeem as redeem_svc
from ..services import report as report_svc
from ..utils import slugify


def _channel_out(ch: Channel) -> ChannelResponse:
    return ChannelResponse(
        id=ch.id, tipo=ch.tipo, nombre=ch.nombre, slug=ch.slug, modo=ch.modo,
        activo=ch.activo, orden=ch.orden,
        qr_url=f"{settings.public_base_url}/girar/{ch.slug}",
    )

router = APIRouter(prefix="/admin", tags=["admin"])


# ---------------- Auth ----------------
@router.post("/login", response_model=TokenResponse)
def login(data: AdminLogin, db: Session = Depends(get_db)):
    admin = db.query(AdminUser).filter(AdminUser.email == str(data.email).lower()).first()
    if not admin or not verify_password(data.password, admin.hashed_password):
        raise HTTPException(status_code=401, detail="Credenciales inválidas.")
    return TokenResponse(access_token=create_session_token(admin.id, admin.email))


# ---------------- Métricas ----------------
@router.get("/metrics", response_model=Metrics)
def metrics(db: Session = Depends(get_db), _=Depends(get_current_admin)):
    total_part = db.query(func.count(Lead.id)).scalar() or 0
    total_giros = db.query(func.count(Spin.id)).scalar() or 0
    ganados = db.query(func.count(Spin.id)).filter(Spin.gano.is_(True)).scalar() or 0
    entregados = db.query(func.count(Spin.id)).filter(Spin.redeemed.is_(True)).scalar() or 0
    disponibles = db.query(func.coalesce(func.sum(Prize.stock_restante), 0)).filter(
        Prize.activo.is_(True), Prize.es_perdedor.is_(False)
    ).scalar() or 0
    conv = round((total_giros / total_part * 100), 1) if total_part else 0.0
    return Metrics(
        total_participantes=total_part,
        total_giros=total_giros,
        premios_ganados=ganados,
        premios_entregados=entregados,
        premios_disponibles=int(disponibles),
        tasa_conversion=conv,
    )


# ---------------- CRUD canales (sedes / vendedores) ----------------
@router.get("/channels", response_model=list[ChannelResponse])
def listar_canales(db: Session = Depends(get_db), _=Depends(get_current_admin)):
    chs = db.query(Channel).order_by(Channel.tipo.asc(), Channel.orden.asc(), Channel.nombre.asc()).all()
    return [_channel_out(c) for c in chs]


@router.post("/channels", response_model=ChannelResponse, status_code=201)
def crear_canal(data: ChannelCreate, db: Session = Depends(get_db), _=Depends(get_current_admin)):
    base = slugify(data.slug or data.nombre)
    slug = base
    i = 2
    while db.query(Channel).filter(Channel.slug == slug).first():
        slug = f"{base}-{i}"
        i += 1
    ch = Channel(tipo=data.tipo, nombre=data.nombre, slug=slug, modo=data.modo,
                 activo=data.activo, orden=data.orden)
    db.add(ch)
    db.commit()
    db.refresh(ch)
    return _channel_out(ch)


@router.put("/channels/{channel_id}", response_model=ChannelResponse)
def actualizar_canal(
    channel_id: str, data: ChannelUpdate, db: Session = Depends(get_db), _=Depends(get_current_admin)
):
    ch = db.query(Channel).filter(Channel.id == channel_id).first()
    if not ch:
        raise HTTPException(status_code=404, detail="Canal no encontrado.")
    for k, v in data.model_dump(exclude_unset=True).items():
        setattr(ch, k, v)
    db.commit()
    db.refresh(ch)
    return _channel_out(ch)


@router.delete("/channels/{channel_id}", status_code=204)
def eliminar_canal(channel_id: str, db: Session = Depends(get_db), _=Depends(get_current_admin)):
    ch = db.query(Channel).filter(Channel.id == channel_id).first()
    if not ch:
        raise HTTPException(status_code=404, detail="Canal no encontrado.")
    db.query(Prize).filter(Prize.channel_id == channel_id).delete()
    db.delete(ch)
    db.commit()


# ---------------- CRUD premios ----------------
@router.get("/prizes", response_model=list[PrizeResponse])
def listar_premios(
    channel_id: str | None = None, db: Session = Depends(get_db), _=Depends(get_current_admin)
):
    """Premios de un canal. Sin channel_id => premios de la inauguración (channel_id NULL)."""
    q = db.query(Prize)
    if channel_id:
        q = q.filter(Prize.channel_id == channel_id)
    else:
        q = q.filter(Prize.channel_id.is_(None))
    return q.order_by(Prize.orden.asc(), Prize.created_at.asc()).all()


@router.post("/prizes", response_model=PrizeResponse, status_code=201)
def crear_premio(data: PrizeCreate, db: Session = Depends(get_db), _=Depends(get_current_admin)):
    premio = Prize(**data.model_dump(), stock_restante=data.stock_total)
    db.add(premio)
    db.commit()
    db.refresh(premio)
    return premio


@router.put("/prizes/{prize_id}", response_model=PrizeResponse)
def actualizar_premio(
    prize_id: str, data: PrizeUpdate, db: Session = Depends(get_db), _=Depends(get_current_admin)
):
    premio = db.query(Prize).filter(Prize.id == prize_id).first()
    if not premio:
        raise HTTPException(status_code=404, detail="Premio no encontrado.")
    payload = data.model_dump(exclude_unset=True)
    # Si sube el stock_total, ajusta el restante proporcionalmente al alta
    if "stock_total" in payload:
        delta = payload["stock_total"] - premio.stock_total
        premio.stock_restante = max(0, premio.stock_restante + delta)
    for k, v in payload.items():
        setattr(premio, k, v)
    db.commit()
    db.refresh(premio)
    return premio


@router.delete("/prizes/{prize_id}", status_code=204)
def eliminar_premio(prize_id: str, db: Session = Depends(get_db), _=Depends(get_current_admin)):
    premio = db.query(Prize).filter(Prize.id == prize_id).first()
    if not premio:
        raise HTTPException(status_code=404, detail="Premio no encontrado.")
    db.delete(premio)
    db.commit()


# ---------------- Redención de QR (escáner) ----------------
@router.post("/redeem", response_model=RedeemResponse)
def redimir(data: RedeemRequest, db: Session = Depends(get_db), admin=Depends(get_current_admin)):
    """Canjea (marca como usado) un QR de cupón o premio. Un solo uso."""
    token = redeem_svc.extraer_token(data.token)
    r = redeem_svc.canjear(db, token, admin.get("email"))
    return RedeemResponse(
        valido=r["valido"], ya_redimido=r["ya_redimido"], tipo=r["tipo"],
        mensaje=r["mensaje"], premio=r["premio"], cliente=r["cliente"],
        fecha_giro=r["fecha_giro"],
    )


# ---------------- Export leads CSV ----------------
@router.get("/leads.csv")
def export_leads(db: Session = Depends(get_db), _=Depends(get_current_admin)):
    leads = db.query(Lead).order_by(Lead.created_at.desc()).all()
    buf = io.StringIO()
    w = csv.writer(buf)
    w.writerow(["Nombre", "Telefono", "Correo", "Cedula", "Direccion",
                "Cupon", "Referido_por", "Fecha"])
    for l in leads:
        w.writerow([l.nombre, l.telefono, l.correo, l.cedula, l.direccion or "",
                    l.coupon_code, l.referred_by or "", l.created_at.isoformat()])
    buf.seek(0)
    return StreamingResponse(
        iter([buf.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=leads_cerritos.csv"},
    )


# ---------------- Reporte ejecutivo Excel ----------------
@router.get("/reporte.xlsx")
def export_reporte(db: Session = Depends(get_db), _=Depends(get_current_admin)):
    data = report_svc.generar_reporte(db)
    return StreamingResponse(
        iter([data]),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": "attachment; filename=Reporte_Cerritos.xlsx"},
    )
