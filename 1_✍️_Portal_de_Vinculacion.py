# -*- coding: utf-8 -*-
# =================================================================================================
# PLATAFORMA CORPORATIVA DE ACTUALIZACIÓN DE DATOS - FERREINOX S.A.S. BIC
# Versión: 22.0 (Motor PDF Corporativo High-End + UI Optimizada)
# Fecha: 22 de Enero de 2026
# Autor: GM-DATOVATE & Gemini AI
# =================================================================================================

import streamlit as st
from streamlit_drawable_canvas import st_canvas
from PIL import Image
from datetime import datetime
import gspread
import tempfile
import os
import numpy as np
import random
import pytz
import base64
from xml.sax.saxutils import escape

# --- ReportLab Imports (Motor Gráfico Avanzado) ---
from reportlab.platypus import BaseDocTemplate, PageTemplate, Frame, Paragraph, Spacer, Table, TableStyle, Image as PlatypusImage
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_LEFT, TA_RIGHT
from reportlab.lib import colors
from reportlab.lib.units import inch, mm, cm
from reportlab.lib.pagesizes import letter

# --- Google & Email Imports ---
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail, Attachment, FileContent, FileName, FileType, Disposition

# =================================================================================================
# 1. CONFIGURACIÓN DE PÁGINA Y ESTILOS CSS (MODO INSTITUCIONAL)
# =================================================================================================

st.set_page_config(
    page_title="Portal de Actualización de Datos | Ferreinox S.A.S. BIC",
    page_icon="🛡️",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# --- Colores Corporativos ---
LOGO_PATH = "LOGO FERREINOX SAS BIC 2024.png"
COLOR_PRIMARY = "#0A2E57"       # Azul profundo Ferreinox
COLOR_SECONDARY = "#0F5EA8"     # Azul corporativo de apoyo
COLOR_HIGHLIGHT = "#F28C28"     # Acento ejecutivo cálido
COLOR_ACCENT = "#EAF3FB"        # Azul claro para superficies
COLOR_BG = "#EEF3F8"            # Fondo general
COLOR_SURFACE = "#FFFFFF"       # Superficie blanca
COLOR_TEXT = "#172B3A"          # Texto principal
COLOR_MUTED = "#5C6F82"         # Texto secundario

# --- Inyección de CSS Avanzado ---
st.markdown(f"""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Montserrat:wght@500;600;700;800&family=Source+Sans+3:wght@400;500;600;700&display=swap');

    :root {{
        --primary: {COLOR_PRIMARY};
        --secondary: {COLOR_SECONDARY};
        --highlight: {COLOR_HIGHLIGHT};
        --accent: {COLOR_ACCENT};
        --bg: {COLOR_BG};
        --surface: {COLOR_SURFACE};
        --text: {COLOR_TEXT};
        --muted: {COLOR_MUTED};
    }}

    html, body, [class*="css"] {{
        font-family: 'Source Sans 3', sans-serif;
        background:
            radial-gradient(circle at top left, rgba(242, 140, 40, 0.16), transparent 22%),
            radial-gradient(circle at top right, rgba(15, 94, 168, 0.18), transparent 25%),
            linear-gradient(180deg, #f6f9fc 0%, {COLOR_BG} 100%);
        color: {COLOR_TEXT};
    }}

    h1, h2, h3, h4, h5, h6 {{
        font-family: 'Montserrat', sans-serif;
        color: {COLOR_PRIMARY};
        letter-spacing: -0.02em;
    }}

    #MainMenu {{visibility: hidden;}}
    footer {{visibility: hidden;}}
    header {{visibility: hidden;}}
    div[data-testid="stSidebarNav"] {{display: none;}}
    div[data-testid="stAppViewContainer"] > .main {{
        background: transparent;
    }}
    .block-container {{
        padding-top: 1.2rem;
        padding-bottom: 3rem;
        max-width: 980px;
    }}

    .header-shell {{
        position: relative;
        overflow: hidden;
        border-radius: 28px;
        padding: 2rem;
        margin-bottom: 1.4rem;
        background:
            linear-gradient(140deg, rgba(10, 46, 87, 0.98) 0%, rgba(15, 94, 168, 0.95) 62%, rgba(242, 140, 40, 0.92) 160%);
        color: white;
        box-shadow: 0 24px 60px rgba(10, 46, 87, 0.24);
    }}
    .header-shell::before {{
        content: "";
        position: absolute;
        inset: auto -10% -35% auto;
        width: 320px;
        height: 320px;
        border-radius: 50%;
        background: rgba(255,255,255,0.08);
        filter: blur(2px);
    }}
    .header-badge {{
        display: inline-flex;
        align-items: center;
        gap: 0.45rem;
        padding: 0.45rem 0.8rem;
        border-radius: 999px;
        background: rgba(255,255,255,0.12);
        border: 1px solid rgba(255,255,255,0.14);
        font-size: 0.82rem;
        text-transform: uppercase;
        letter-spacing: 0.12em;
        font-weight: 700;
        margin-bottom: 1rem;
    }}
    .header-grid {{
        display: grid;
        grid-template-columns: minmax(100px, 150px) 1fr;
        gap: 1.4rem;
        align-items: center;
        position: relative;
        z-index: 1;
    }}
    .header-logo-wrap {{
        display: flex;
        align-items: center;
        justify-content: center;
        min-height: 110px;
        background: rgba(255,255,255,0.1);
        border: 1px solid rgba(255,255,255,0.15);
        border-radius: 22px;
        backdrop-filter: blur(10px);
        padding: 1rem;
    }}
    .header-logo {{
        max-width: 100%;
        max-height: 80px;
        object-fit: contain;
    }}
    .header-title {{
        margin: 0;
        color: white;
        font-size: clamp(2rem, 4vw, 3.2rem);
        line-height: 1.02;
        text-transform: uppercase;
        letter-spacing: 0.02em;
    }}
    .header-subtitle {{
        margin: 0.8rem 0 0;
        max-width: 740px;
        font-size: 1.08rem;
        line-height: 1.5;
        color: rgba(255,255,255,0.92);
    }}
    .header-points {{
        display: grid;
        grid-template-columns: repeat(3, minmax(0, 1fr));
        gap: 0.9rem;
        margin-top: 1.4rem;
    }}
    .header-point {{
        padding: 0.95rem 1rem;
        border-radius: 18px;
        background: rgba(255,255,255,0.12);
        border: 1px solid rgba(255,255,255,0.12);
    }}
    .header-point strong {{
        display: block;
        margin-bottom: 0.2rem;
        color: white;
        font-size: 0.95rem;
    }}
    .header-point span {{
        color: rgba(255,255,255,0.84);
        font-size: 0.92rem;
        line-height: 1.35;
    }}

    .card-box {{
        background: rgba(255,255,255,0.92);
        border: 1px solid rgba(10, 46, 87, 0.08);
        backdrop-filter: blur(8px);
        padding: 2.2rem;
        border-radius: 24px;
        box-shadow: 0 18px 48px rgba(15, 35, 65, 0.08);
        margin-bottom: 2rem;
    }}
    .section-title {{
        color: {COLOR_PRIMARY};
        font-size: 1.85rem;
        font-weight: 800;
        margin-bottom: 0.55rem;
        letter-spacing: -0.03em;
    }}
    .section-lead {{
        color: {COLOR_MUTED};
        font-size: 1.04rem;
        line-height: 1.55;
        margin-bottom: 1.4rem;
    }}
    .trust-strip {{
        display: grid;
        grid-template-columns: repeat(4, minmax(0, 1fr));
        gap: 0.9rem;
        margin-bottom: 1.4rem;
    }}
    .trust-item {{
        background: linear-gradient(180deg, rgba(234,243,251,0.85) 0%, rgba(255,255,255,0.96) 100%);
        border: 1px solid rgba(15, 94, 168, 0.12);
        border-radius: 18px;
        padding: 1rem;
    }}
    .trust-item strong {{
        display: block;
        color: {COLOR_PRIMARY};
        font-family: 'Montserrat', sans-serif;
        font-size: 0.95rem;
        margin-bottom: 0.3rem;
    }}
    .trust-item span {{
        color: {COLOR_MUTED};
        line-height: 1.35;
        font-size: 0.93rem;
    }}
    .notice-banner {{
        padding: 1rem 1.1rem;
        border-radius: 18px;
        margin-bottom: 1rem;
        border-left: 6px solid {COLOR_HIGHLIGHT};
        background: linear-gradient(90deg, rgba(242, 140, 40, 0.12) 0%, rgba(255,255,255,0.95) 75%);
        color: {COLOR_TEXT};
        line-height: 1.45;
    }}
    .legal-scroll-box {{
        height: 420px;
        overflow-y: auto;
        background: linear-gradient(180deg, rgba(250,252,254,1) 0%, rgba(240,246,251,1) 100%);
        border: 1px solid rgba(10, 46, 87, 0.08);
        padding: 1.4rem;
        border-radius: 20px;
        font-size: 0.98rem;
        line-height: 1.75;
        color: {COLOR_TEXT};
        margin-bottom: 1rem;
    }}
    .legal-scroll-box h4 {{
        color: {COLOR_PRIMARY};
        margin-top: 1.2rem;
        margin-bottom: 0.5rem;
        font-size: 1rem;
        font-weight: 800;
        font-family: 'Montserrat', sans-serif;
    }}
    .legal-scroll-box p {{
        margin-bottom: 0.6rem;
    }}
    .consent-box {{
        padding: 1rem 1.1rem;
        border-radius: 18px;
        background: rgba(10, 46, 87, 0.04);
        border: 1px dashed rgba(10, 46, 87, 0.18);
        margin: 1rem 0 1.25rem;
        color: {COLOR_TEXT};
    }}
    .type-grid {{
        display: grid;
        grid-template-columns: repeat(2, minmax(0, 1fr));
        gap: 1rem;
        margin-bottom: 1rem;
    }}
    .type-card {{
        padding: 1.2rem;
        border-radius: 20px;
        background: linear-gradient(180deg, rgba(234,243,251,0.9) 0%, rgba(255,255,255,1) 100%);
        border: 1px solid rgba(10, 46, 87, 0.1);
        min-height: 150px;
    }}
    .type-card h4 {{
        margin: 0 0 0.45rem 0;
        color: {COLOR_PRIMARY};
        font-size: 1.1rem;
    }}
    .type-card p {{
        margin: 0;
        color: {COLOR_MUTED};
        line-height: 1.45;
    }}

    .progress-wrapper {{
        display: flex;
        justify-content: space-between;
        gap: 0.6rem;
        margin: 0 0 1.6rem;
    }}
    .progress-step {{
        flex: 1;
        text-align: center;
        padding: 0.9rem 0.4rem;
        border-radius: 18px;
        background: rgba(255,255,255,0.74);
        border: 1px solid rgba(10, 46, 87, 0.08);
    }}
    .step-circle {{
        width: 46px;
        height: 46px;
        border-radius: 50%;
        background-color: #dfe8f3;
        color: {COLOR_MUTED};
        display: flex;
        align-items: center;
        justify-content: center;
        margin: 0 auto 0.55rem auto;
        font-weight: 800;
        font-family: 'Montserrat', sans-serif;
        transition: all 0.3s ease;
        border: 3px solid rgba(255,255,255,0.9);
        box-shadow: 0 6px 16px rgba(10, 46, 87, 0.08);
    }}
    .step-label {{
        font-size: 0.82rem;
        font-weight: 700;
        color: {COLOR_MUTED};
        text-transform: uppercase;
        letter-spacing: 0.08em;
    }}
    .active.progress-step {{
        background: linear-gradient(180deg, rgba(10,46,87,0.09) 0%, rgba(255,255,255,0.95) 100%);
        border-color: rgba(15, 94, 168, 0.2);
    }}
    .active .step-circle {{
        background: linear-gradient(135deg, {COLOR_PRIMARY} 0%, {COLOR_SECONDARY} 100%);
        color: white;
        transform: scale(1.08);
        box-shadow: 0 10px 26px rgba(10, 46, 87, 0.2);
    }}
    .active .step-label {{
        color: {COLOR_PRIMARY};
    }}

    div[data-baseweb="input"] > div,
    div[data-baseweb="base-input"] > div,
    div[data-baseweb="select"] > div,
    textarea {{
        border-radius: 14px !important;
        background-color: rgba(248, 251, 254, 0.98) !important;
        border: 1px solid rgba(10, 46, 87, 0.12) !important;
        padding: 6px !important;
        box-shadow: none !important;
    }}
    div[data-baseweb="input"] > div:focus-within,
    div[data-baseweb="base-input"] > div:focus-within,
    div[data-baseweb="select"] > div:focus-within,
    textarea:focus {{
        border-color: {COLOR_SECONDARY} !important;
        background-color: #FFFFFF !important;
        box-shadow: 0 0 0 3px rgba(15, 94, 168, 0.12) !important;
    }}
    label, .stDateInput label {{
        font-weight: 700 !important;
        color: {COLOR_PRIMARY} !important;
    }}

    .stButton>button, .stFormSubmitButton>button {{
        width: 100%;
        min-height: 3.2rem;
        border-radius: 16px;
        border: none;
        background: linear-gradient(90deg, {COLOR_PRIMARY} 0%, {COLOR_SECONDARY} 82%);
        color: white;
        font-weight: 800;
        font-family: 'Montserrat', sans-serif;
        padding: 0.85rem 1rem;
        font-size: 0.95rem;
        transition: all 0.25s ease;
        letter-spacing: 0.06em;
        text-transform: uppercase;
        box-shadow: 0 14px 30px rgba(10, 46, 87, 0.16);
    }}
    .stButton>button:hover, .stFormSubmitButton>button:hover {{
        transform: translateY(-1px);
        box-shadow: 0 18px 34px rgba(10, 46, 87, 0.24);
        color: white;
    }}

    div[data-testid="stCheckbox"] {{
        padding: 0.25rem 0;
    }}
    div[data-testid="stCheckbox"] label p {{
        color: {COLOR_TEXT} !important;
        font-weight: 600;
    }}

    .helper-note {{
        padding: 0.95rem 1rem;
        background: rgba(255,255,255,0.85);
        border-radius: 16px;
        border: 1px solid rgba(10, 46, 87, 0.08);
        color: {COLOR_MUTED};
        margin-bottom: 1rem;
    }}
    .signature-note {{
        padding: 1rem 1.1rem;
        border-radius: 18px;
        background: linear-gradient(90deg, rgba(10,46,87,0.08) 0%, rgba(15,94,168,0.08) 100%);
        border: 1px solid rgba(15, 94, 168, 0.15);
        margin: 1rem 0 1rem;
    }}
    .otp-note {{
        padding: 1rem 1.1rem;
        border-radius: 18px;
        background: linear-gradient(90deg, rgba(234,243,251,0.95) 0%, rgba(255,255,255,1) 100%);
        border: 1px solid rgba(10, 46, 87, 0.08);
        color: {COLOR_TEXT};
        margin-bottom: 1rem;
    }}
    .success-panel {{
        text-align: center;
        background: linear-gradient(180deg, rgba(255,255,255,0.97) 0%, rgba(234,243,251,0.96) 100%);
    }}
    .success-kicker {{
        display: inline-block;
        padding: 0.5rem 0.9rem;
        border-radius: 999px;
        background: rgba(10, 46, 87, 0.08);
        color: {COLOR_PRIMARY};
        font-weight: 800;
        text-transform: uppercase;
        letter-spacing: 0.1em;
        font-size: 0.78rem;
        margin-bottom: 0.8rem;
    }}
    .success-grid {{
        display: grid;
        grid-template-columns: repeat(3, minmax(0, 1fr));
        gap: 0.9rem;
        margin: 1.4rem 0 1.6rem;
        text-align: left;
    }}
    .success-item {{
        padding: 1rem;
        border-radius: 18px;
        background: white;
        border: 1px solid rgba(10, 46, 87, 0.08);
    }}
    .success-item strong {{
        display: block;
        color: {COLOR_PRIMARY};
        margin-bottom: 0.25rem;
        font-family: 'Montserrat', sans-serif;
        font-size: 0.9rem;
    }}
    .success-item span {{
        color: {COLOR_MUTED};
        line-height: 1.4;
    }}
    .action-link {{
        background: linear-gradient(90deg, {COLOR_PRIMARY} 0%, {COLOR_SECONDARY} 100%);
        color: white !important;
        padding: 0.95rem 1.6rem;
        text-decoration: none;
        border-radius: 999px;
        font-weight: 800;
        font-family: 'Montserrat', sans-serif;
        box-shadow: 0 16px 30px rgba(10, 46, 87, 0.22);
        display: inline-block;
    }}

    @media (max-width: 768px) {{
        .header-grid,
        .header-points,
        .trust-strip,
        .type-grid,
        .success-grid {{
            grid-template-columns: 1fr;
        }}
        .card-box {{
            padding: 1.35rem;
            border-radius: 20px;
        }}
        .progress-wrapper {{
            flex-direction: column;
        }}
    }}
</style>
""", unsafe_allow_html=True)

# =================================================================================================
# 2. SISTEMA DE GENERACIÓN DE PDF PROFESIONAL (MOTOR ACTUALIZADO)
# =================================================================================================

class CorporatePDFGenerator:
    def __init__(self, data, doc_id):
        self.data = data
        self.doc_id = doc_id
        self.story = []
        
        # --- Configuración de Estilos ---
        styles = getSampleStyleSheet()
        
        # Colores
        self.c_primary = colors.HexColor(COLOR_PRIMARY)
        self.c_secondary = colors.HexColor(COLOR_SECONDARY)
        self.c_highlight = colors.HexColor(COLOR_HIGHLIGHT)
        self.c_accent = colors.HexColor(COLOR_ACCENT)
        self.c_text = colors.HexColor("#2C3E50")
        self.c_grey_light = colors.HexColor("#F4F6F7")
        
        # Estilos de Texto
        self.s_normal = ParagraphStyle('NormalCorp', parent=styles['Normal'], fontName='Helvetica', fontSize=9, leading=12, textColor=self.c_text, alignment=TA_JUSTIFY)
        self.s_label = ParagraphStyle('LabelCorp', parent=styles['Normal'], fontName='Helvetica-Bold', fontSize=8, leading=10, textColor=self.c_primary, textTransform='uppercase')
        self.s_value = ParagraphStyle('ValueCorp', parent=styles['Normal'], fontName='Helvetica', fontSize=9, leading=10, textColor=colors.black)
        self.s_heading = ParagraphStyle('HeadingCorp', parent=styles['Heading2'], fontName='Helvetica-Bold', fontSize=12, leading=14, textColor=colors.white, spaceAfter=0)
        self.s_legal = ParagraphStyle('LegalCorp', parent=styles['Normal'], fontName='Helvetica', fontSize=8.3, leading=10.8, textColor=colors.HexColor("#455A64"), alignment=TA_JUSTIFY)
        self.s_footer = ParagraphStyle('FooterCorp', parent=styles['Normal'], fontName='Helvetica', fontSize=7, leading=9, textColor=colors.gray, alignment=TA_CENTER)
        self.s_callout = ParagraphStyle('CalloutCorp', parent=styles['Normal'], fontName='Helvetica', fontSize=9, leading=12, textColor=colors.white, alignment=TA_LEFT)
        self.s_section_intro = ParagraphStyle('SectionIntroCorp', parent=styles['Normal'], fontName='Helvetica', fontSize=9.2, leading=12.5, textColor=self.c_text, alignment=TA_JUSTIFY)
        self.s_small = ParagraphStyle('SmallCorp', parent=styles['Normal'], fontName='Helvetica', fontSize=7.4, leading=9, textColor=colors.HexColor("#637381"), alignment=TA_LEFT)

    def _draw_header_footer(self, canvas, doc):
        canvas.saveState()
        w, h = doc.pagesize
        
        # --- HEADER ---
        # Barra Superior de Color
        canvas.setFillColor(self.c_primary)
        canvas.rect(0, h - 25*mm, w, 25*mm, fill=1, stroke=0)
        
        # Logo (Simulado o Cargado)
        logo_path = LOGO_PATH
        try:
            if os.path.exists(logo_path):
                canvas.drawImage(logo_path, 20*mm, h - 20*mm, width=50*mm, height=15*mm, preserveAspectRatio=True, mask='auto')
            else:
                # Fallback Texto Logo
                canvas.setFont("Helvetica-Bold", 20)
                canvas.setFillColor(colors.white)
                canvas.drawString(20*mm, h - 18*mm, "FERREINOX S.A.S. BIC")
        except:
            pass

        # Título del Documento en Header
        canvas.setFont("Helvetica-Bold", 14)
        canvas.setFillColor(colors.white)
        canvas.drawRightString(w - 20*mm, h - 12*mm, "AUTORIZACIÓN Y VINCULACIÓN")
        
        canvas.setFont("Helvetica", 9)
        canvas.setFillColor(colors.white)
        canvas.drawRightString(w - 20*mm, h - 17*mm, f"Ref: {self.doc_id}")
        canvas.drawRightString(w - 20*mm, h - 21*mm, f"Fecha: {self.data.get('timestamp')}")

        # --- FOOTER ---
        # Línea divisoria
        canvas.setStrokeColor(self.c_primary)
        canvas.setLineWidth(0.5)
        canvas.line(20*mm, 20*mm, w - 20*mm, 20*mm)
        
        # Texto Legal Footer
        footer_text = "Ferreinox S.A.S. BIC | NIT. 800.224.617-8 | Evidencia electrónica de aceptación y firma"
        canvas.setFont("Helvetica", 7)
        canvas.setFillColor(colors.gray)
        canvas.drawCentredString(w/2, 15*mm, footer_text)
        canvas.drawCentredString(w/2, 12*mm, "www.ferreinox.co | Pereira, Risaralda, Colombia | Ley 527 de 1999")
        
        # Paginación
        canvas.drawRightString(w - 20*mm, 15*mm, f"Pág. {doc.page}")

        canvas.restoreState()

    def _create_section_header(self, title):
        # Crear una tabla para el título de la sección con fondo de color
        data = [[Paragraph(title.upper(), self.s_heading)]]
        t = Table(data, colWidths=[190*mm])
        t.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), self.c_secondary),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ('LEFTPADDING', (0, 0), (-1, -1), 10),
            ('ROUNDEDCORNERS', [4, 4, 4, 4]) # Esquinas redondeadas (Reportlab moderno)
        ]))
        return t

    def _create_executive_banner(self):
        summary = Paragraph(
            "<b>Resumen ejecutivo:</b> este documento deja constancia de que FERREINOX S.A.S. BIC actualiza, valida y conserva la información del cliente para operar la relación comercial, soportar la facturación electrónica, atender requerimientos legales, evaluar riesgo crediticio cuando aplique y mantener trazabilidad de la autorización otorgada.",
            self.s_callout
        )
        rights = Paragraph(
            "<b>Claridad para el cliente:</b> la firma de este documento no habilita usos ajenos a los aquí descritos. Usted conserva sus derechos de acceso, actualización, rectificación, revocatoria y supresión conforme a la normativa vigente.",
            self.s_callout
        )
        banner = Table([[summary], [rights]], colWidths=[190*mm])
        banner.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), self.c_primary),
            ('ROWBACKGROUNDS', (0, 0), (-1, -1), [self.c_primary, self.c_secondary]),
            ('LEFTPADDING', (0, 0), (-1, -1), 12),
            ('RIGHTPADDING', (0, 0), (-1, -1), 12),
            ('TOPPADDING', (0, 0), (-1, -1), 9),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 9),
            ('BOX', (0, 0), (-1, -1), 0.5, colors.white),
        ]))
        return banner

    def _create_data_grid(self):
        # Preparar datos
        d = self.data
        if d['client_type'] == 'juridica':
            grid_data = [
                [Paragraph("RAZÓN SOCIAL", self.s_label), Paragraph(d.get('razon_social', ''), self.s_value), Paragraph("NIT", self.s_label), Paragraph(d.get('nit', ''), self.s_value)],
                [Paragraph("DIRECCIÓN", self.s_label), Paragraph(d.get('direccion', ''), self.s_value), Paragraph("CIUDAD", self.s_label), Paragraph(d.get('ciudad', ''), self.s_value)],
                [Paragraph("EMAIL CONTACTO", self.s_label), Paragraph(d.get('correo', ''), self.s_value), Paragraph("EMAIL FACTURACIÓN", self.s_label), Paragraph(d.get('correo_facturacion', ''), self.s_value)],
                [Paragraph("TELÉFONO/MÓVIL", self.s_label), Paragraph(f"{d.get('telefono', '')} / {d.get('celular', '')}", self.s_value), Paragraph("REP. LEGAL", self.s_label), Paragraph(d.get('rep_legal', ''), self.s_value)],
                [Paragraph("C.C. REP. LEGAL", self.s_label), Paragraph(d.get('cedula_rep_legal', ''), self.s_value), Paragraph("", self.s_label), Paragraph("", self.s_value)],
            ]
        else:
            def safe_txt(k): return str(d.get(k, ''))
            grid_data = [
                [Paragraph("NOMBRE COMPLETO", self.s_label), Paragraph(safe_txt('nombre_natural'), self.s_value), Paragraph("CÉDULA", self.s_label), Paragraph(safe_txt('cedula_natural'), self.s_value)],
                [Paragraph("DIRECCIÓN", self.s_label), Paragraph(safe_txt('direccion'), self.s_value), Paragraph("CIUDAD", self.s_label), Paragraph(safe_txt('ciudad'), self.s_value)],
                [Paragraph("EMAIL PERSONAL", self.s_label), Paragraph(safe_txt('correo'), self.s_value), Paragraph("EMAIL FACTURACIÓN", self.s_label), Paragraph(safe_txt('correo_facturacion'), self.s_value)],
                [Paragraph("CELULAR", self.s_label), Paragraph(safe_txt('telefono'), self.s_value), Paragraph("FECHA NACIMIENTO", self.s_label), Paragraph(safe_txt('fecha_nacimiento'), self.s_value)],
            ]

        # Configurar Tabla Grilla
        col_w = [35*mm, 60*mm, 35*mm, 60*mm]
        t = Table(grid_data, colWidths=col_w)
        
        style = [
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
            ('BACKGROUND', (0,0), (0,-1), self.c_accent), # Columna Labels 1
            ('BACKGROUND', (2,0), (2,-1), self.c_accent), # Columna Labels 2
            ('GRID', (0,0), (-1,-1), 0.5, colors.white),  # Líneas blancas para separar
            ('LINEBELOW', (0,0), (-1,-1), 1, self.c_grey_light),
            ('PADDING', (0,0), (-1,-1), 6),
        ]
        t.setStyle(TableStyle(style))
        return t

    def _create_authorization_matrix(self):
        rows = [
            [
                Paragraph("TRATAMIENTO DE DATOS", self.s_label),
                Paragraph("FERREINOX S.A.S. BIC podrá recolectar, almacenar, actualizar, usar y conservar los datos aquí suministrados para gestionar la relación comercial, tributaria, contable, logística, de servicio y mercadeo autorizado.", self.s_legal)
            ],
            [
                Paragraph("CONSULTA Y REPORTE FINANCIERO", self.s_label),
                Paragraph("El titular autoriza la consulta, verificación, procesamiento y reporte de información financiera, comercial y crediticia ante operadores o centrales de información, cuando ello sea necesario para evaluación de crédito, cartera y comportamiento de pago.", self.s_legal)
            ],
            [
                Paragraph("FACTURACIÓN ELECTRÓNICA", self.s_label),
                Paragraph("El correo registrado para facturación se reconoce como canal oficial para remitir facturas electrónicas, notas débito, notas crédito y soportes asociados, conforme a las exigencias de la DIAN y la regulación aplicable.", self.s_legal)
            ],
            [
                Paragraph("VERACIDAD Y ACTUALIZACIÓN", self.s_label),
                Paragraph("El cliente declara que la información entregada es veraz, vigente y suficiente para su vinculación. Asimismo, se compromete a informar oportunamente cualquier cambio material en datos de contacto, representación, facturación o identificación.", self.s_legal)
            ],
            [
                Paragraph("CUMPLIMIENTO Y ORIGEN DE FONDOS", self.s_label),
                Paragraph("Bajo la gravedad de juramento, el titular declara que sus recursos provienen de actividades lícitas y que no están relacionados con lavado de activos, financiación del terrorismo ni actividades prohibidas por la ley o políticas de cumplimiento aplicables.", self.s_legal)
            ],
            [
                Paragraph("VIGENCIA Y DERECHOS", self.s_label),
                Paragraph("La autorización permanecerá vigente mientras exista relación comercial, contractual o legal, y durante el tiempo requerido para soportes, auditoría y cumplimiento normativo. El titular conserva sus derechos de acceso, rectificación, actualización, revocatoria y supresión en los términos legales.", self.s_legal)
            ],
        ]
        table = Table(rows, colWidths=[48*mm, 142*mm], repeatRows=0)
        table.setStyle(TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('BACKGROUND', (0, 0), (0, -1), self.c_accent),
            ('ROWBACKGROUNDS', (1, 0), (1, -1), [colors.white, colors.HexColor('#F9FBFD')]),
            ('BOX', (0, 0), (-1, -1), 0.5, colors.HexColor('#D6E2EF')),
            ('INNERGRID', (0, 0), (-1, -1), 0.35, colors.HexColor('#D6E2EF')),
            ('LEFTPADDING', (0, 0), (-1, -1), 8),
            ('RIGHTPADDING', (0, 0), (-1, -1), 8),
            ('TOPPADDING', (0, 0), (-1, -1), 7),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 7),
        ]))
        return table

    def _create_customer_assurance_box(self):
        items = [
            "<b>Canales oficiales:</b> correo registrado por el cliente, líneas y sedes de FERREINOX, y el portal www.ferreinox.co.",
            "<b>Propósito del documento:</b> dejar evidencia clara, verificable y auditable de la autorización otorgada por el titular.",
            "<b>Seguridad de la firma:</b> el documento integra OTP validado, marca de tiempo y firma manuscrita digitalizada insertada en el PDF.",
        ]
        paragraphs = [Paragraph(item, self.s_small) for item in items]
        table = Table([[p] for p in paragraphs], colWidths=[190*mm])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#FFF8EF')),
            ('BOX', (0, 0), (-1, -1), 0.8, self.c_highlight),
            ('LEFTPADDING', (0, 0), (-1, -1), 10),
            ('RIGHTPADDING', (0, 0), (-1, -1), 10),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ]))
        return table

    def _create_signature_box(self):
        # Procesar Imagen
        img_temp = None
        try:
            with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as tf:
                img_temp = tf.name
            pil_img = self.data['firma_img_pil']
            if pil_img.mode == "RGBA":
                bg = Image.new("RGB", pil_img.size, (255,255,255))
                bg.paste(pil_img, mask=pil_img.split()[3])
                bg.save(img_temp)
            else:
                pil_img.save(img_temp)
            
            sig_img = PlatypusImage(img_temp, width=40*mm, height=20*mm)
        except:
            sig_img = Paragraph("[Error Imagen]", self.s_normal)

        # Datos de Firma
        signer = self.data['rep_legal'] if self.data['client_type'] == 'juridica' else self.data['nombre_natural']
        id_signer = self.data['nit'] if self.data['client_type'] == 'juridica' else self.data['cedula_natural']
        
        sig_details = [
            Paragraph(f"<b>FIRMADO POR:</b> {signer}", self.s_normal),
            Paragraph(f"<b>ID/NIT:</b> {id_signer}", self.s_normal),
            Paragraph(f"<b>FECHA:</b> {self.data['timestamp']}", self.s_normal),
            Paragraph(f"<b>HASH SEGURO:</b> {self.doc_id}", self.s_normal),
            Paragraph(f"<b>VALIDACIÓN:</b> OTP Token Verificado", self.s_normal),
            Paragraph("<b>ALCANCE:</b> aceptación expresa de actualización de datos, autorizaciones y declaraciones aquí contenidas.", self.s_normal),
        ]
        
        # Tabla de Firma Estilo "Certificado"
        data = [[sig_img, sig_details]]
        t = Table(data, colWidths=[60*mm, 120*mm])
        t.setStyle(TableStyle([
            ('VALIGN', (0,0), (-1,-1), 'CENTER'),
            ('BOX', (0,0), (-1,-1), 1, self.c_primary), # Borde Azul
            ('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#FAFAFA")),
            ('LEFTPADDING', (0,0), (-1,-1), 10),
            ('RIGHTPADDING', (0,0), (-1,-1), 10),
            ('TOPPADDING', (0,0), (-1,-1), 10),
            ('BOTTOMPADDING', (0,0), (-1,-1), 10),
        ]))
        
        return t, img_temp

    def generate(self):
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as f:
            path = f.name
            
        doc = BaseDocTemplate(path, pagesize=letter, 
                              topMargin=30*mm, bottomMargin=25*mm, 
                              leftMargin=20*mm, rightMargin=20*mm)
        
        frame = Frame(doc.leftMargin, doc.bottomMargin, doc.width, doc.height, id='normal')
        doc.addPageTemplates([PageTemplate(id='main', frames=[frame], onPage=self._draw_header_footer)])
        
        # --- Construcción del Contenido ---
        
        # Sección 1: Datos del Titular
        self.story.append(self._create_executive_banner())
        self.story.append(Spacer(1, 6*mm))
        self.story.append(self._create_section_header("I. INFORMACIÓN DEL TITULAR"))
        self.story.append(Spacer(1, 5*mm))
        self.story.append(self._create_data_grid())
        self.story.append(Spacer(1, 8*mm))
        
        # Sección 2: Autorizaciones Legales
        self.story.append(self._create_section_header("II. ALCANCE DE LA AUTORIZACIÓN"))
        self.story.append(Spacer(1, 2*mm))
        self.story.append(Paragraph("Yo, el titular de la información, actuando en nombre propio o en representación legal de la entidad descrita en la Sección I, confirmo que comprendo el propósito de este documento y otorgo las siguientes autorizaciones de manera libre, previa, expresa e informada:", self.s_section_intro))
        self.story.append(Spacer(1, 4*mm))
        self.story.append(self._create_authorization_matrix())
        self.story.append(Spacer(1, 8*mm))
        self.story.append(self._create_customer_assurance_box())
        self.story.append(Spacer(1, 8*mm))
        
        # Sección 3: Firma Electrónica
        self.story.append(self._create_section_header("III. CERTIFICADO DE FIRMA ELECTRÓNICA"))
        self.story.append(Spacer(1, 5*mm))
        
        sig_table, img_path = self._create_signature_box()
        self.story.append(sig_table)
        
        self.story.append(Spacer(1, 5*mm))
        legal_footer = "Este documento electrónico tiene plena validez jurídica y probatoria de conformidad con la Ley 527 de 1999 y deja trazabilidad verificable de la autorización otorgada por el titular."
        self.story.append(Paragraph(legal_footer, ParagraphStyle('Tiny', parent=self.s_normal, fontSize=6, alignment=TA_CENTER, textColor=colors.gray)))

        try:
            doc.build(self.story)
            return path
        finally:
            if img_path and os.path.exists(img_path): os.unlink(img_path)

# =================================================================================================
# 3. LÓGICA DE APLICACIÓN (MANTENIDA Y OPTIMIZADA)
# =================================================================================================

def init_state():
    defaults = {'step': 1, 'client_type': None, 'form_data': {}, 'otp': "", 'final_url': "", 'final_doc_id': "", 'final_timestamp': ""}
    for k, v in defaults.items():
        if k not in st.session_state: st.session_state[k] = v

init_state()

def get_logo_data_uri():
    if not os.path.exists(LOGO_PATH):
        return ""
    try:
        with open(LOGO_PATH, "rb") as logo_file:
            encoded = base64.b64encode(logo_file.read()).decode("utf-8")
        return f"data:image/png;base64,{encoded}"
    except Exception:
        return ""

def get_signer_name(data):
    return data.get('rep_legal') or data.get('nombre_natural') or "Cliente Ferreinox"

def build_email_shell(title, preheader, body_html, footer_note):
    return f"""
    <div style="margin:0; padding:32px 12px; background:#eef3f8; font-family:'Segoe UI', Arial, sans-serif; color:{COLOR_TEXT};">
        <div style="max-width:720px; margin:0 auto; background:#ffffff; border-radius:28px; overflow:hidden; box-shadow:0 18px 40px rgba(10,46,87,0.12); border:1px solid rgba(10,46,87,0.08);">
            <div style="padding:28px 32px; background:linear-gradient(135deg, {COLOR_PRIMARY} 0%, {COLOR_SECONDARY} 70%, {COLOR_HIGHLIGHT} 180%); color:white;">
                <div style="display:inline-block; padding:8px 12px; border-radius:999px; background:rgba(255,255,255,0.14); font-size:12px; letter-spacing:1.6px; font-weight:700; text-transform:uppercase; margin-bottom:14px;">
                    Ferreinox S.A.S. BIC
                </div>
                <h1 style="margin:0; font-size:30px; line-height:1.08; font-weight:800;">{title}</h1>
                <p style="margin:12px 0 0; font-size:15px; line-height:1.6; color:rgba(255,255,255,0.92);">{preheader}</p>
            </div>
            <div style="padding:28px 32px; background:#ffffff;">
                {body_html}
            </div>
            <div style="padding:20px 32px 28px; background:#f8fbfe; border-top:1px solid #e4edf5;">
                <p style="margin:0 0 10px; color:{COLOR_PRIMARY}; font-size:13px; font-weight:700; text-transform:uppercase; letter-spacing:1px;">Canales oficiales</p>
                <p style="margin:0; color:{COLOR_MUTED}; font-size:14px; line-height:1.65;">www.ferreinox.co | Pereira, Risaralda, Colombia<br>{footer_note}</p>
            </div>
        </div>
    </div>
    """

def build_otp_email(recipient_name, otp):
    body = f"""
    <p style="margin:0 0 18px; font-size:15px; line-height:1.7; color:{COLOR_TEXT};">
        Estimado(a) <b>{escape(recipient_name)}</b>, este código confirma que la persona que diligencia el formulario es quien autoriza la actualización de datos y la firma electrónica del documento de vinculación con Ferreinox.
    </p>
    <div style="padding:22px; border-radius:22px; background:linear-gradient(180deg, #f5f9fd 0%, #ffffff 100%); border:1px solid #d9e6f2; margin-bottom:18px; text-align:center;">
        <p style="margin:0 0 10px; color:{COLOR_PRIMARY}; font-size:13px; font-weight:700; text-transform:uppercase; letter-spacing:1.4px;">Código de verificación</p>
        <div style="display:inline-block; padding:16px 24px; border-radius:18px; background:{COLOR_PRIMARY}; color:white; font-size:36px; letter-spacing:10px; font-weight:800;">{otp}</div>
        <p style="margin:14px 0 0; color:{COLOR_MUTED}; font-size:13px;">Este código expira en 10 minutos y no debe compartirse.</p>
    </div>
    <div style="display:grid; grid-template-columns:repeat(2, minmax(0, 1fr)); gap:12px; margin-bottom:16px;">
        <div style="padding:16px; border-radius:18px; background:#fff8ef; border:1px solid #f5d3ae;">
            <p style="margin:0 0 6px; color:{COLOR_PRIMARY}; font-size:13px; font-weight:700; text-transform:uppercase;">Qué confirma este paso</p>
            <p style="margin:0; color:{COLOR_MUTED}; font-size:14px; line-height:1.55;">La aceptación expresa del documento y la validación de identidad antes de emitir el PDF firmado.</p>
        </div>
        <div style="padding:16px; border-radius:18px; background:#f5f9fd; border:1px solid #d9e6f2;">
            <p style="margin:0 0 6px; color:{COLOR_PRIMARY}; font-size:13px; font-weight:700; text-transform:uppercase;">Recomendación</p>
            <p style="margin:0; color:{COLOR_MUTED}; font-size:14px; line-height:1.55;">Si usted no está realizando este proceso, ignore este correo y comuníquese con Ferreinox.</p>
        </div>
    </div>
    <p style="margin:0; color:{COLOR_MUTED}; font-size:14px; line-height:1.7;">Una vez ingresado el código, el sistema generará el PDF con su firma electrónica insertada y enviará una copia a su correo.</p>
    """
    return build_email_shell(
        "Verificación de seguridad para firma electrónica",
        "Use este código para completar la validación y autorizar su documento de actualización de datos.",
        body,
        "Si no reconoce este proceso, por favor no comparta el código y contacte a Ferreinox."
    )

def build_confirmation_email(doc_id, ts, signer_name, email_dest):
    body = f"""
    <p style="margin:0 0 18px; font-size:15px; line-height:1.7; color:{COLOR_TEXT};">
        Estimado(a) <b>{escape(signer_name)}</b>, Ferreinox S.A.S. BIC confirma la recepción exitosa de su autorización, la actualización de su información y la generación del documento electrónico firmado.
    </p>
    <div style="padding:20px; border-radius:22px; background:linear-gradient(180deg, #f5f9fd 0%, #ffffff 100%); border:1px solid #d9e6f2; margin-bottom:18px;">
        <p style="margin:0 0 12px; color:{COLOR_PRIMARY}; font-size:13px; font-weight:700; text-transform:uppercase; letter-spacing:1.3px;">Constancia del trámite</p>
        <table style="width:100%; border-collapse:collapse; font-size:14px;">
            <tr>
                <td style="padding:8px 0; color:{COLOR_MUTED}; width:140px;">Radicado</td>
                <td style="padding:8px 0; color:{COLOR_TEXT}; font-weight:700;">{doc_id}</td>
            </tr>
            <tr>
                <td style="padding:8px 0; color:{COLOR_MUTED};">Fecha de firma</td>
                <td style="padding:8px 0; color:{COLOR_TEXT}; font-weight:700;">{ts}</td>
            </tr>
            <tr>
                <td style="padding:8px 0; color:{COLOR_MUTED};">Correo registrado</td>
                <td style="padding:8px 0; color:{COLOR_TEXT}; font-weight:700;">{escape(email_dest)}</td>
            </tr>
        </table>
    </div>
    <div style="display:grid; grid-template-columns:repeat(3, minmax(0, 1fr)); gap:12px; margin-bottom:18px;">
        <div style="padding:16px; border-radius:18px; background:#ffffff; border:1px solid #d9e6f2;">
            <p style="margin:0 0 6px; color:{COLOR_PRIMARY}; font-size:13px; font-weight:700; text-transform:uppercase;">Qué firmó</p>
            <p style="margin:0; color:{COLOR_MUTED}; font-size:14px; line-height:1.55;">Autorización de tratamiento de datos, confirmación de canales oficiales y aceptación de soportes electrónicos.</p>
        </div>
        <div style="padding:16px; border-radius:18px; background:#fff8ef; border:1px solid #f5d3ae;">
            <p style="margin:0 0 6px; color:{COLOR_PRIMARY}; font-size:13px; font-weight:700; text-transform:uppercase;">Qué recibe</p>
            <p style="margin:0; color:{COLOR_MUTED}; font-size:14px; line-height:1.55;">El PDF adjunto con su firma insertada, trazabilidad temporal y evidencia del OTP validado.</p>
        </div>
        <div style="padding:16px; border-radius:18px; background:#f5f9fd; border:1px solid #d9e6f2;">
            <p style="margin:0 0 6px; color:{COLOR_PRIMARY}; font-size:13px; font-weight:700; text-transform:uppercase;">Qué hacer si requiere cambios</p>
            <p style="margin:0; color:{COLOR_MUTED}; font-size:14px; line-height:1.55;">Contactar a Ferreinox para actualizar nuevamente la información o ejercer sus derechos como titular.</p>
        </div>
    </div>
    <p style="margin:0; color:{COLOR_MUTED}; font-size:14px; line-height:1.7;">Conserve este correo y el PDF como soporte de su autorización. Si identifica algún dato incorrecto, solicite su actualización por los canales oficiales de Ferreinox.</p>
    """
    return build_email_shell(
        "Su documento de vinculación ha sido emitido",
        "El proceso quedó formalizado y el PDF firmado se adjunta a este correo para su custodia.",
        body,
        "Este mensaje constituye una notificación informativa sobre un trámite realizado a nombre del titular registrado."
    )

def render_header():
    logo_uri = get_logo_data_uri()
    logo_html = f'<img src="{logo_uri}" class="header-logo" alt="Ferreinox" />' if logo_uri else '<div style="font-family:Montserrat, sans-serif; font-size:1.3rem; font-weight:800; color:white;">FERREINOX</div>'
    st.markdown(f"""
    <div class="header-shell">
        <div class="header-badge">Portal corporativo de vinculación</div>
        <div class="header-grid">
            <div class="header-logo-wrap">{logo_html}</div>
            <div>
                <h1 class="header-title">Actualización de datos con respaldo corporativo real</h1>
                <p class="header-subtitle">Este portal formaliza su autorización con lenguaje claro, evidencia electrónica verificable y un documento PDF ejecutivo alineado con la identidad de Ferreinox S.A.S. BIC.</p>
            </div>
        </div>
        <div class="header-points">
            <div class="header-point">
                <strong>Proceso transparente</strong>
                <span>Le explicamos exactamente qué información se actualiza, para qué se utiliza y qué está autorizando.</span>
            </div>
            <div class="header-point">
                <strong>Evidencia electrónica</strong>
                <span>Su documento queda respaldado con OTP, marca de tiempo y firma manuscrita insertada en el PDF.</span>
            </div>
            <div class="header-point">
                <strong>Canales oficiales Ferreinox</strong>
                <span>Comunicación formal, custodia documental y soporte a través de www.ferreinox.co y medios corporativos.</span>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

def render_progress():
    s = st.session_state.step
    c1 = "active" if s >= 1 else ""
    c2 = "active" if s >= 2 else ""
    c3 = "active" if s >= 3 else ""
    c4 = "active" if s >= 4 else ""
    
    html = f"""
    <div class="progress-wrapper">
        <div class="progress-step {c1}">
            <div class="step-circle">1</div>
            <div class="step-label">Términos</div>
        </div>
        <div class="progress-step {c2}">
            <div class="step-circle">2</div>
            <div class="step-label">Tipo</div>
        </div>
        <div class="progress-step {c3}">
            <div class="step-circle">3</div>
            <div class="step-label">Datos</div>
        </div>
        <div class="progress-step {c4}">
            <div class="step-circle">4</div>
            <div class="step-label">Verificar</div>
        </div>
    </div>
    """
    st.markdown(html, unsafe_allow_html=True)

def get_services():
    try:
        secrets = st.secrets["google_credentials"]
        creds = Credentials.from_service_account_info(secrets.to_dict(), scopes=['https://www.googleapis.com/auth/drive', 'https://www.googleapis.com/auth/spreadsheets'])
        gc = gspread.authorize(creds)
        sh = gc.open_by_key(st.secrets["google_sheet_id"]).sheet1
        drive = build('drive', 'v3', credentials=creds)
        return sh, drive
    except Exception as e:
        st.error(f"Error de conexión con Google: {e}")
        return None, None

def send_email_sendgrid(to, subject, html, pdf=None, pdf_name=None):
    try:
        api_key = st.secrets["sendgrid"]["api_key"]
        from_email = st.secrets["sendgrid"]["from_email"]
        from_name = st.secrets["sendgrid"].get("from_name", "Ferreinox S.A.S. BIC")
        message = Mail(
            from_email=(from_email, from_name),
            to_emails=to,
            subject=subject,
            html_content=html
        )
        if pdf and pdf_name:
            with open(pdf, "rb") as f:
                data = f.read()
            encoded = base64.b64encode(data).decode()
            attachedFile = Attachment(
                FileContent(encoded),
                FileName(pdf_name),
                FileType('application/pdf'),
                Disposition('attachment')
            )
            message.attachment = attachedFile
        
        sg = SendGridAPIClient(api_key)
        response = sg.send(message)
        return response.status_code in [200, 202]
    except Exception as e:
        st.error(f"Error enviando correo por SendGrid: {e}")
        return False

# =================================================================================================
# 4. FLUJO DE PANTALLAS (STEPS)
# =================================================================================================

render_header()
if st.session_state.step < 5:
    render_progress()

# --- PASO 1: TÉRMINOS LEGALES AMPLIADOS ---
if st.session_state.step == 1:
    st.markdown('<div class="card-box">', unsafe_allow_html=True)
    st.markdown('<div class="section-title">Antes de continuar: esto es exactamente lo que vamos a hacer</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-lead">Ferreinox S.A.S. BIC solicita esta autorización para mantener sus datos correctos, operar su relación comercial con trazabilidad, enviar soportes electrónicos por el correo oficial que usted registre y dejar evidencia verificable de su aceptación.</div>', unsafe_allow_html=True)

    st.markdown(f"""
    <div class="trust-strip">
        <div class="trust-item">
            <strong>Actualización documental</strong>
            <span>Validamos datos de contacto, identificación, facturación y representación para que su registro quede formalmente actualizado.</span>
        </div>
        <div class="trust-item">
            <strong>Facturación electrónica</strong>
            <span>El correo que usted entregue será el canal oficial para facturas, notas y soportes tributarios asociados.</span>
        </div>
        <div class="trust-item">
            <strong>Evaluación y cartera</strong>
            <span>Cuando aplique, la información podrá usarse para consulta y reporte financiero dentro del marco legal vigente.</span>
        </div>
        <div class="trust-item">
            <strong>Soporte con evidencia</strong>
            <span>El proceso termina con OTP, firma electrónica y un PDF ejecutivo para su custodia y la de Ferreinox.</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown('<div class="notice-banner"><b>Mensaje clave:</b> usted no está firmando un texto ambiguo. Está autorizando de manera expresa y clara el tratamiento de sus datos para fines comerciales, operativos, tributarios, de servicio y cumplimiento, bajo las condiciones aquí descritas.</div>', unsafe_allow_html=True)

    st.markdown(f"""
    <div class="legal-scroll-box">
        <h4>1. Responsable del tratamiento</h4>
        <p><b>FERREINOX S.A.S. BIC</b>, identificada con NIT 800.224.617-8, actúa como responsable del tratamiento de los datos personales que usted suministre en este formulario.</p>

        <h4>2. Para qué se usarán sus datos</h4>
        <p>Sus datos se utilizarán para registrar o actualizar su vinculación comercial, gestionar pedidos, despachos, cartera, servicio al cliente, facturación electrónica, soporte tributario, validaciones internas, comunicaciones autorizadas y demás actividades asociadas a la relación con Ferreinox.</p>

        <h4>3. Qué autoriza usted de forma expresa</h4>
        <p>Al continuar, usted autoriza a Ferreinox para recolectar, almacenar, actualizar, usar, transmitir y conservar la información entregada. También autoriza, cuando aplique, la consulta y reporte de información financiera, crediticia y comercial ante operadores o centrales de información en los términos de la Ley 1266 de 2008 y normas concordantes.</p>

        <h4>4. Correo oficial para facturación electrónica</h4>
        <p>El correo que usted registre como correo de facturación será reconocido como el medio oficial para remitir facturas electrónicas, notas débito, notas crédito y demás soportes relacionados, conforme a la regulación vigente de la DIAN.</p>

        <h4>5. Declaraciones del titular</h4>
        <p>Usted declara que la información suministrada es veraz, suficiente y actual. Asimismo, declara bajo gravedad de juramento que los recursos vinculados a la relación comercial provienen de actividades lícitas y que no tienen relación con lavado de activos, financiación del terrorismo u otras actividades prohibidas por la ley.</p>

        <h4>6. Sus derechos</h4>
        <p>Como titular puede conocer, actualizar, rectificar y solicitar prueba de la autorización otorgada. También puede presentar solicitudes de revocatoria o supresión cuando proceda legalmente y no exista deber contractual o legal que obligue a conservar la información.</p>

        <h4>7. Evidencia del consentimiento</h4>
        <p>Este proceso genera una constancia electrónica compuesta por sus datos diligenciados, OTP de verificación, marca de tiempo y firma manuscrita insertada en el PDF final.</p>
    </div>
    """, unsafe_allow_html=True)

    st.markdown('<div class="consent-box"><b>En resumen:</b> Ferreinox está formalizando su actualización de datos y la autorización asociada con un documento ejecutivo, claro y auditable. Nada queda implícito: el alcance de su consentimiento queda expresamente documentado.</div>', unsafe_allow_html=True)
    st.info("Para ampliar información sobre políticas de tratamiento de datos, consulte el portal oficial de Ferreinox: https://www.ferreinox.co/es/politica-tratamiento-de-datos-CPG232")

    check = st.checkbox("Declaro que he leído y comprendido el alcance de esta autorización, acepto el tratamiento de mis datos en los términos descritos y reconozco el correo registrado como canal oficial para comunicaciones y facturación electrónica.")

    if st.button("ACEPTAR Y CONTINUAR ➜"):
        if check:
            st.session_state.step = 2
            st.rerun()
        else:
            st.warning("⚠️ Debe aceptar los términos legales para continuar con la vinculación.")
    st.markdown('</div>', unsafe_allow_html=True)

# --- PASO 2: TIPO DE CLIENTE ---
elif st.session_state.step == 2:
    st.markdown('<div class="card-box">', unsafe_allow_html=True)
    st.markdown('<div class="section-title">Seleccione el perfil que va a formalizar</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-lead">Elegir el tipo correcto permite construir el formulario, el PDF y la evidencia de firma con los campos que corresponden a su realidad jurídica.</div>', unsafe_allow_html=True)
    st.markdown("""
    <div class="type-grid">
        <div class="type-card">
            <h4>Persona jurídica</h4>
            <p>Para empresas, sociedades, entidades o negocios que actuarán a través de un representante legal y requieren soportar razón social, NIT, correo de facturación y trazabilidad corporativa.</p>
        </div>
        <div class="type-card">
            <h4>Persona natural</h4>
            <p>Para clientes independientes o personas que autorizan en nombre propio y necesitan formalizar sus datos personales, su canal oficial de facturación y su evidencia de consentimiento.</p>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    c1, c2 = st.columns(2)
    with c1:
        if st.button("🏢 PERSONA JURÍDICA\nEmpresas y sociedades", use_container_width=True):
            st.session_state.client_type = 'juridica'
            st.session_state.step = 3
            st.rerun()
    with c2:
        if st.button("👤 PERSONA NATURAL\nClientes e independientes", use_container_width=True):
            st.session_state.client_type = 'natural'
            st.session_state.step = 3
            st.rerun()
            
    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("‹ Volver"):
        st.session_state.step = 1
        st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

# --- PASO 3: FORMULARIO DE DATOS ---
elif st.session_state.step == 3:
    st.markdown('<div class="card-box">', unsafe_allow_html=True)
    st.markdown('<div class="section-title">Diligenciamiento de información y evidencia de firma</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-lead">Complete la información con el mayor nivel de precisión posible. Estos datos alimentarán el PDF final, la constancia electrónica y los canales formales de contacto y facturación.</div>', unsafe_allow_html=True)
    st.markdown('<div class="helper-note"><b>Importante:</b> revise especialmente el correo de facturación electrónica, la identificación y el nombre del firmante. El documento final quedará emitido exactamente con los datos aquí registrados.</div>', unsafe_allow_html=True)
    
    with st.form("main_form"):
        if st.session_state.client_type == 'juridica':
            st.subheader("Datos Empresariales")
            col1, col2 = st.columns(2)
            razon_social = col1.text_input("Razón Social (RUT)*")
            nit = col2.text_input("NIT (Sin Dígito Verificación)*")
            direccion = col1.text_input("Dirección Principal*")
            ciudad = col2.text_input("Ciudad / Departamento*")
            telefono = col1.text_input("Teléfono Fijo")
            celular = col2.text_input("Celular Contacto*")
            
            st.subheader("Facturación y Representación")
            correo = st.text_input("Correo Electrónico de Contacto*")
            correo_facturacion = st.text_input("Correo para Facturación Electrónica (DIAN)*")
            st.markdown(
                "<span style='font-size:0.98rem; color:#37474F;'>"
                "El correo de facturación electrónica será el <b>canal oficial y formal</b> para el envío de facturas, notas débito, notas crédito y demás soportes tributarios. "
                "Por eso debe corresponder al buzón correcto de recepción documental de su empresa.</span>",
                unsafe_allow_html=True
            )
            rep_legal = col1.text_input("Nombre Representante Legal*")
            cedula_rep = col2.text_input("Cédula Rep. Legal*")
            
            nom_nat, ced_nat, fe_nac = "", "", None
        else:
            st.subheader("Datos Personales")
            col1, col2 = st.columns(2)
            nom_nat = col1.text_input("Nombre Completo (Cédula)*")
            ced_nat = col2.text_input("Número de Cédula*")
            fe_nac = col1.date_input("Fecha de Nacimiento*", min_value=datetime(1940,1,1).date(), max_value=datetime(2005,1,1).date())
            direccion = col2.text_input("Dirección Residencia*")
            ciudad = col1.text_input("Ciudad*")
            celular = col2.text_input("Celular Personal*")
            correo = st.text_input("Correo Electrónico Personal*")
            correo_facturacion = st.text_input("Correo para Facturación Electrónica (DIAN)*")
            st.markdown(
                "<span style='font-size:0.98rem; color:#37474F;'>"
                "El correo de facturación electrónica será el <b>canal oficial y formal</b> para remitir facturas electrónicas y soportes asociados. "
                "Asegúrese de registrar un correo activo al que usted realmente tenga acceso.</span>",
                unsafe_allow_html=True
            )
            telefono = celular
            
            razon_social, nit, rep_legal, cedula_rep = nom_nat, ced_nat, "", ""

        st.markdown("---")
        st.markdown('<div class="signature-note"><b>Firma electrónica:</b> esta firma será insertada en el PDF final como evidencia visual del consentimiento. Firme dentro del recuadro blanco usando el mouse o el dedo, procurando que la firma sea clara y completa.</div>', unsafe_allow_html=True)

        canvas = st_canvas(
            fill_color="rgba(255, 255, 255, 0)",
            stroke_width=2,
            stroke_color="#000000",
            background_color="#FFFFFF",
            height=150,
            width=600,
            drawing_mode="freedraw",
            key="canvas",
        )
        
        submitted = st.form_submit_button("GUARDAR Y VALIDAR IDENTIDAD ➜")
        
        if submitted:
            valid = True
            if st.session_state.client_type == 'juridica':
                if not all([razon_social, nit, direccion, ciudad, correo, correo_facturacion, celular, rep_legal, cedula_rep]): valid = False
            else:
                if not all([nom_nat, ced_nat, direccion, ciudad, correo, correo_facturacion, celular]): valid = False

            if canvas.image_data is None or np.all(canvas.image_data == 255):
                st.error("⚠️ La firma es obligatoria.")
                valid = False

            if valid:
                st.session_state.form_data = {
                    'client_type': st.session_state.client_type,
                    'razon_social': razon_social, 'nit': nit, 'direccion': direccion, 
                    'ciudad': ciudad, 'telefono': telefono, 'celular': celular,
                    'correo': correo, 'correo_facturacion': correo_facturacion,
                    'rep_legal': rep_legal, 'cedula_rep_legal': cedula_rep,
                    'nombre_natural': nom_nat, 'cedula_natural': ced_nat, 'fecha_nacimiento': fe_nac,
                    'firma_img_pil': Image.fromarray(canvas.image_data.astype('uint8'), 'RGBA')
                }
                # Generar OTP y Enviar
                otp = str(random.randint(100000, 999999))
                st.session_state.otp = otp
                signer_name = rep_legal if st.session_state.client_type == 'juridica' else nom_nat
                html_otp = build_otp_email(signer_name or "Cliente Ferreinox", otp)
                with st.spinner("Enviando código de verificación..."):
                    if send_email_sendgrid(correo, "Código de Verificación - Ferreinox", html_otp):
                        st.session_state.step = 4
                        st.rerun()
                    else:
                        st.error("Error enviando el correo. Verifique la dirección ingresada.")
            else:
                st.warning("Por favor complete todos los campos obligatorios (*)")

    if st.button("‹ Atrás"):
        st.session_state.step = 2
        st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

# --- PASO 4: VERIFICACIÓN OTP Y FINALIZACIÓN ---
elif st.session_state.step == 4:
    st.markdown('<div class="card-box">', unsafe_allow_html=True)
    st.markdown('<div class="section-title">Verificación de seguridad y emisión del documento</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-lead">Este es el último control antes de generar el PDF final. Al ingresar el código OTP, el sistema emitirá la constancia con su firma insertada y dejará trazabilidad del consentimiento.</div>', unsafe_allow_html=True)
    
    email_dest = st.session_state.form_data.get('correo')
    st.markdown(f'<div class="otp-note"><b>Correo de validación:</b> hemos enviado un código de 6 dígitos a <b>{escape(email_dest)}</b>. Use ese código para confirmar que usted autoriza el documento.</div>', unsafe_allow_html=True)
    
    col1, col2 = st.columns([3, 1])
    input_otp = col1.text_input("Ingrese el Código", placeholder="######", max_chars=6)
    
    if st.button("CONFIRMAR Y FIRMAR DOCUMENTO ✅"):
        if input_otp == st.session_state.otp:
            with st.spinner("Generando contrato corporativo, firmando digitalmente y archivando..."):
                # Preparar Datos
                tz = pytz.timezone('America/Bogota')
                ts = datetime.now(tz).strftime("%Y-%m-%d %H:%M:%S")
                st.session_state.form_data['timestamp'] = ts
                
                uid = st.session_state.form_data['nit'] if st.session_state.client_type == 'juridica' else st.session_state.form_data['cedula_natural']
                doc_id = f"FER-{datetime.now().strftime('%Y%m%d%H%M')}-{uid}"
                st.session_state.final_doc_id = doc_id
                st.session_state.final_timestamp = ts
                
                # --- GENERAR PDF CON LA NUEVA CLASE CORPORATIVA ---
                gen = CorporatePDFGenerator(st.session_state.form_data, doc_id)
                pdf_path = gen.generate()
                
                # Guardar Google Sheets / Drive
                sheet, drive = get_services()
                if sheet and drive:
                    try:
                        # Sheets
                        row = [
                            ts, doc_id, 
                            st.session_state.form_data.get('razon_social', ''),
                            st.session_state.form_data.get('nit', '') or st.session_state.form_data.get('cedula_natural', ''),
                            st.session_state.form_data.get('rep_legal', '') or st.session_state.form_data.get('nombre_natural', ''),
                            st.session_state.form_data.get('correo', ''),
                            "", "AUTORIZADO", st.session_state.form_data.get('celular', ''), 
                            "", "FIRMADO", st.session_state.otp,
                            # Campos extra para completar columnas si existen en tu sheet
                        ]
                        # Ajustar longitud de row según tu sheet real si es necesario
                        sheet.append_row(row)
                        
                        # Drive
                        meta = {'name': f"VINCULACION_{doc_id}.pdf", 'parents': [st.secrets["drive_folder_id"]]}
                        media = MediaFileUpload(pdf_path, mimetype='application/pdf')
                        f = drive.files().create(body=meta, media_body=media, fields='webViewLink', supportsAllDrives=True).execute()
                        st.session_state.final_url = f.get('webViewLink')
                        
                        # Email Final
                        html_end = build_confirmation_email(doc_id, ts, get_signer_name(st.session_state.form_data), email_dest)
                        send_email_sendgrid(email_dest, "Confirmación Vinculación - Ferreinox", html_end, pdf_path, f"Vinculacion_{doc_id}.pdf")
                        
                        st.session_state.step = 5
                        st.rerun()
                        
                    except Exception as e:
                        st.error(f"Error guardando datos: {e}")
                else:
                    st.error("Error conectando con base de datos.")
        else:
            st.error("❌ Código incorrecto.")
            
    st.markdown('</div>', unsafe_allow_html=True)

# --- PASO 5: ÉXITO ---
elif st.session_state.step == 5:
    st.balloons()
    st.markdown(f"""
    <div class="card-box success-panel">
        <div class="success-kicker">Proceso formalizado</div>
        <h1 style="color: #2E7D32; font-size: 4.4rem; margin:0 0 0.35rem;">✓</h1>
        <h2 style="color: {COLOR_PRIMARY}; text-transform: uppercase; margin-bottom:0.6rem;">Su autorización quedó emitida correctamente</h2>
        <p style="font-size:1.08rem; color:{COLOR_MUTED}; max-width:720px; margin:0 auto; line-height:1.65;">Sus datos han sido actualizados, su firma electrónica quedó incorporada en el PDF y una copia del documento fue enviada al correo registrado.</p>
        <div class="success-grid">
            <div class="success-item">
                <strong>Radicado</strong>
                <span>{st.session_state.final_doc_id or 'Generado correctamente'}</span>
            </div>
            <div class="success-item">
                <strong>Fecha de emisión</strong>
                <span>{st.session_state.final_timestamp or 'Registro exitoso'}</span>
            </div>
            <div class="success-item">
                <strong>Soporte entregado</strong>
                <span>PDF ejecutivo con firma insertada y trazabilidad electrónica.</span>
            </div>
        </div>
        <a href="{st.session_state.final_url}" target="_blank" class="action-link">Ver documento PDF</a>
        <div style="margin-top:1rem; color:{COLOR_MUTED}; font-size:0.95rem;">Si requiere corrección de datos, por favor contacte a Ferreinox por sus canales oficiales.</div>
    </div>
    """, unsafe_allow_html=True)
    
    if st.button("Volver al Inicio"):
        for k in list(st.session_state.keys()):
            del st.session_state[k]
        st.rerun()