"""Genera un reporte ejecutivo en Excel (.xlsx) con formato premium."""
from datetime import datetime
from io import BytesIO

from openpyxl import Workbook
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter
from sqlalchemy import func
from sqlalchemy.orm import Session

from ..models import Lead, Prize, Spin

NAVY = "FF0A2E57"
NAVY_LIGHT = "FF12386B"
YELLOW = "FFFFD200"
GREEN = "FF1F9E5A"
RED = "FFE63329"
WHITE = "FFFFFFFF"
LIGHT = "FFEEF3F8"

thin = Side(style="thin", color="FFD5DEE8")
BORDER = Border(left=thin, right=thin, top=thin, bottom=thin)


def _title(ws, text, ncols):
    ws.merge_cells(start_row=1, start_column=1, end_row=1, end_column=ncols)
    c = ws.cell(row=1, column=1, value=text)
    c.font = Font(bold=True, size=16, color=WHITE)
    c.fill = PatternFill("solid", fgColor=NAVY)
    c.alignment = Alignment(horizontal="left", vertical="center", indent=1)
    ws.row_dimensions[1].height = 34
    ws.merge_cells(start_row=2, start_column=1, end_row=2, end_column=ncols)
    s = ws.cell(row=2, column=1,
                value=f"Tienda Pintuco Cerritos · Generado {datetime.utcnow():%Y-%m-%d %H:%M} UTC")
    s.font = Font(size=9, italic=True, color=NAVY_LIGHT)
    s.fill = PatternFill("solid", fgColor=LIGHT)
    ws.row_dimensions[2].height = 18


def _header(ws, row, headers):
    for j, h in enumerate(headers, start=1):
        c = ws.cell(row=row, column=j, value=h)
        c.font = Font(bold=True, color=WHITE, size=11)
        c.fill = PatternFill("solid", fgColor=NAVY_LIGHT)
        c.alignment = Alignment(horizontal="center", vertical="center")
        c.border = BORDER
    ws.row_dimensions[row].height = 22


def _autosize(ws, widths):
    for j, w in enumerate(widths, start=1):
        ws.column_dimensions[get_column_letter(j)].width = w


def _kpi(ws, row, col, label, value, color):
    lc = ws.cell(row=row, column=col, value=label)
    lc.font = Font(size=10, color=NAVY_LIGHT, bold=True)
    lc.alignment = Alignment(horizontal="center")
    vc = ws.cell(row=row + 1, column=col, value=value)
    vc.font = Font(size=22, bold=True, color=WHITE)
    vc.fill = PatternFill("solid", fgColor=color)
    vc.alignment = Alignment(horizontal="center", vertical="center")
    vc.border = BORDER
    ws.row_dimensions[row + 1].height = 40


def generar_reporte(db: Session) -> bytes:
    wb = Workbook()

    # ---------- Hoja 1: Resumen ----------
    ws = wb.active
    ws.title = "Resumen"
    ws.sheet_view.showGridLines = False
    _title(ws, "📊 REPORTE EJECUTIVO — INAUGURACIÓN", 6)

    total_part = db.query(func.count(Lead.id)).scalar() or 0
    total_giros = db.query(func.count(Spin.id)).scalar() or 0
    ganados = db.query(func.count(Spin.id)).filter(Spin.gano.is_(True)).scalar() or 0
    entregados = db.query(func.count(Spin.id)).filter(Spin.redeemed.is_(True)).scalar() or 0
    disponibles = db.query(func.coalesce(func.sum(Prize.stock_restante), 0)).filter(
        Prize.activo.is_(True), Prize.es_perdedor.is_(False)).scalar() or 0
    conv = round((total_giros / total_part * 100), 1) if total_part else 0.0
    referidos = db.query(func.count(Lead.id)).filter(Lead.referred_by.isnot(None)).scalar() or 0

    _kpi(ws, 4, 1, "PARTICIPANTES", total_part, NAVY)
    _kpi(ws, 4, 2, "GIROS", total_giros, NAVY_LIGHT)
    _kpi(ws, 4, 3, "CONVERSIÓN", f"{conv}%", GREEN)
    _kpi(ws, 4, 4, "PREMIOS GANADOS", ganados, RED)
    _kpi(ws, 7, 1, "ENTREGADOS", entregados, NAVY)
    _kpi(ws, 7, 2, "DISPONIBLES", int(disponibles), NAVY_LIGHT)
    _kpi(ws, 7, 3, "POR ENTREGAR", ganados - entregados, "FFB8860B")
    _kpi(ws, 7, 4, "REFERIDOS", referidos, GREEN)
    _autosize(ws, [20, 18, 16, 18, 16, 16])

    # Desglose por premio
    _header(ws, 11, ["Premio", "Stock total", "Restante", "Ganados", "Entregados"])
    prizes = db.query(Prize).order_by(Prize.orden.asc()).all()
    r = 12
    for p in prizes:
        pg = db.query(func.count(Spin.id)).filter(Spin.prize_id == p.id).scalar() or 0
        pe = db.query(func.count(Spin.id)).filter(
            Spin.prize_id == p.id, Spin.redeemed.is_(True)).scalar() or 0
        for j, v in enumerate([p.nombre, p.stock_total, p.stock_restante, pg, pe], start=1):
            c = ws.cell(row=r, column=j, value=v)
            c.border = BORDER
            c.alignment = Alignment(horizontal="center" if j > 1 else "left")
        r += 1

    # ---------- Hoja 2: Participantes ----------
    ws2 = wb.create_sheet("Participantes")
    ws2.sheet_view.showGridLines = False
    _title(ws2, "👥 PARTICIPANTES", 8)
    _header(ws2, 4, ["Nombre", "Teléfono", "Correo", "Cédula", "Dirección",
                     "Cupón", "Referido por", "Fecha"])
    leads = db.query(Lead).order_by(Lead.created_at.desc()).all()
    for i, l in enumerate(leads):
        row = 5 + i
        vals = [l.nombre, l.telefono, l.correo, l.cedula, l.direccion or "",
                l.coupon_code, l.referred_by or "", l.created_at.strftime("%Y-%m-%d %H:%M")]
        for j, v in enumerate(vals, start=1):
            c = ws2.cell(row=row, column=j, value=v)
            c.border = BORDER
            if row % 2 == 0:
                c.fill = PatternFill("solid", fgColor=LIGHT)
    ws2.freeze_panes = "A5"
    _autosize(ws2, [26, 16, 30, 16, 26, 18, 16, 18])

    # ---------- Hoja 3: Giros y premios ----------
    ws3 = wb.create_sheet("Giros y Premios")
    ws3.sheet_view.showGridLines = False
    _title(ws3, "🎡 GIROS Y PREMIOS", 8)
    _header(ws3, 4, ["Cliente", "Cédula", "Resultado", "¿Ganó?", "¿Entregado?",
                     "Entregado por", "Fecha giro", "Fecha entrega"])
    spins = db.query(Spin).order_by(Spin.created_at.desc()).all()
    for i, s in enumerate(spins):
        row = 5 + i
        lead = db.query(Lead).filter(Lead.id == s.lead_id).first()
        prize = db.query(Prize).filter(Prize.id == s.prize_id).first() if s.prize_id else None
        vals = [
            lead.nombre if lead else "", lead.cedula if lead else "",
            prize.nombre if prize else "Sin premio",
            "SÍ" if s.gano else "No", "SÍ" if s.redeemed else "No",
            s.redeemed_by or "", s.created_at.strftime("%Y-%m-%d %H:%M"),
            s.redeemed_at.strftime("%Y-%m-%d %H:%M") if s.redeemed_at else "",
        ]
        for j, v in enumerate(vals, start=1):
            c = ws3.cell(row=row, column=j, value=v)
            c.border = BORDER
            c.alignment = Alignment(horizontal="center" if j >= 4 else "left")
            if j == 4 and s.gano:
                c.font = Font(bold=True, color=GREEN)
    ws3.freeze_panes = "A5"
    _autosize(ws3, [26, 16, 22, 10, 12, 22, 18, 18])

    buf = BytesIO()
    wb.save(buf)
    return buf.getvalue()
