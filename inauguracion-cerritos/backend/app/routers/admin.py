"""Panel de administración: auth, métricas, CRUD de premios, redención de QR y export."""
import csv
import io
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy import func
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import AdminUser, Lead, Prize, Spin
from ..schemas import (
    AdminLogin,
    Metrics,
    PrizeCreate,
    PrizeResponse,
    PrizeUpdate,
    RedeemRequest,
    RedeemResponse,
    TokenResponse,
)
from ..security import create_session_token, get_current_admin, verify_password
from ..services import qr as qr_svc

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


# ---------------- CRUD premios ----------------
@router.get("/prizes", response_model=list[PrizeResponse])
def listar_premios(db: Session = Depends(get_db), _=Depends(get_current_admin)):
    return db.query(Prize).order_by(Prize.orden.asc(), Prize.created_at.asc()).all()


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
    payload = qr_svc.verificar(data.token, "prize")
    if not payload:
        return RedeemResponse(valido=False, ya_redimido=False,
                              mensaje="QR inválido, alterado o expirado.")

    spin = db.query(Spin).filter(Spin.id == payload.get("spin_id")).with_for_update().first()
    if not spin or not spin.gano:
        return RedeemResponse(valido=False, ya_redimido=False,
                              mensaje="El premio no existe en el sistema.")

    lead = db.query(Lead).filter(Lead.id == spin.lead_id).first()
    premio = db.query(Prize).filter(Prize.id == spin.prize_id).first()

    if spin.redeemed:
        return RedeemResponse(
            valido=True, ya_redimido=True,
            mensaje="⚠️ Este premio YA fue entregado.",
            premio=premio.nombre if premio else payload.get("prize"),
            cliente=lead.nombre if lead else None,
            fecha_giro=spin.created_at,
        )

    spin.redeemed = True
    spin.redeemed_at = datetime.utcnow()
    spin.redeemed_by = admin.get("email")
    db.commit()

    return RedeemResponse(
        valido=True, ya_redimido=False,
        mensaje="✅ Premio válido. Entrégalo al cliente.",
        premio=premio.nombre if premio else payload.get("prize"),
        cliente=lead.nombre if lead else None,
        fecha_giro=spin.created_at,
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
