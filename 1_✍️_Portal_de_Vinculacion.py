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
from reportlab.platypus import BaseDocTemplate, PageTemplate, Frame, Paragraph, Spacer, Table, TableStyle, Image as PlatypusImage, NextPageTemplate
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
COLOR_PRIMARY = "#0D47A1"       # Azul Institucional Oscuro
COLOR_SECONDARY = "#1565C0"     # Azul Medio
COLOR_ACCENT = "#E3F2FD"        # Azul Muy Claro (Fondos PDF)
COLOR_BG = "#F0F2F6"            # Gris Muy Claro (Fondo Web)
COLOR_TEXT = "#212121"          # Texto Oscuro

# --- Inyección de CSS Avanzado ---
st.markdown(f"""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Roboto:wght@300;400;500;700&display=swap');
    
    html, body, [class*="css"] {{
        font-family: 'Roboto', sans-serif;
        background-color: {COLOR_BG};
        color: {COLOR_TEXT};
    }}
    
    #MainMenu {{visibility: hidden;}}
    footer {{visibility: hidden;}}
    header {{visibility: hidden;}}
    div[data-testid="stSidebarNav"] {{display: none;}}

    .header-container {{
        background: linear-gradient(135deg, {COLOR_PRIMARY} 0%, {COLOR_SECONDARY} 100%);
        padding: 3rem 1rem;
        border-radius: 0 0 20px 20px;
        margin-bottom: 2.5rem;
        text-align: center;
        color: white;
        box-shadow: 0 10px 20px rgba(13, 71, 161, 0.2);
    }}
    .header-title {{
        font-size: 2.8rem;
        font-weight: 800;
        margin-bottom: 0.5rem;
        text-transform: uppercase;
        letter-spacing: 2px;
    }}
    .header-subtitle {{
        font-size: 1.2rem;
        font-weight: 300;
        opacity: 0.9;
    }}

    /* Tarjetas y Formularios */
    .stForm, div[data-testid="stVerticalBlock"] > div.element-container {{
        background-color: transparent;
    }}
    
    .card-box {{
        background-color: white;
        padding: 3rem;
        border-radius: 16px;
        box-shadow: 0 5px 20px rgba(0,0,0,0.05);
        margin-bottom: 2rem;
        border-top: 6px solid {COLOR_PRIMARY};
    }}

    /* Pasos de Progreso */
    .progress-wrapper {{
        display: flex;
        justify-content: space-between;
        margin-bottom: 2.5rem;
        position: relative;
        padding: 0 30px;
    }}
    .progress-step {{
        text-align: center;
        position: relative;
        z-index: 2;
        flex: 1;
    }}
    .step-circle {{
        width: 50px;
        height: 50px;
        border-radius: 50%;
        background-color: #ECEFF1;
        color: #90A4AE;
        display: flex;
        align-items: center;
        justify-content: center;
        margin: 0 auto 10px auto;
        font-weight: bold;
        transition: all 0.3s cubic-bezier(0.25, 0.8, 0.25, 1);
        border: 4px solid #fff;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        font-size: 1.2rem;
    }}
    .step-label {{
        font-size: 0.8rem;
        font-weight: 600;
        color: #90A4AE;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }}
    
    .active .step-circle {{
        background-color: {COLOR_PRIMARY};
        color: white;
        transform: scale(1.15);
        box-shadow: 0 8px 15px rgba(13, 71, 161, 0.3);
    }}
    .active .step-label {{
        color: {COLOR_PRIMARY};
        font-weight: 800;
    }}

    /* Inputs y Botones */
    div[data-baseweb="input"] > div {{
        border-radius: 8px;
        background-color: #F8F9FA;
        border: 1px solid #CFD8DC;
        padding: 4px;
    }}
    div[data-baseweb="input"] > div:focus-within {{
        border-color: {COLOR_PRIMARY};
        background-color: #FFFFFF;
        box-shadow: 0 0 0 2px rgba(13, 71, 161, 0.2);
    }}
    
    .stButton>button {{
        width: 100%;
        border-radius: 8px;
        border: none;
        background: linear-gradient(90deg, {COLOR_PRIMARY} 0%, {COLOR_SECONDARY} 100%);
        color: white;
        font-weight: 700;
        padding: 0.8rem 1rem;
        font-size: 1rem;
        transition: all 0.3s;
        text-transform: uppercase;
        letter-spacing: 1px;
    }}
    .stButton>button:hover {{
        box-shadow: 0 8px 20px rgba(13, 71, 161, 0.3);
        transform: translateY(-2px);
        color: white;
    }}

    /* Scroll Legal */
    .legal-scroll-box {{
        height: 400px;
        overflow-y: auto;
        background-color: #F8F9FA;
        border: 1px solid #E0E0E0;
        padding: 25px;
        border-radius: 10px;
        font-size: 0.95rem;
        line-height: 1.8;
        text-align: justify;
        color: #37474F;
        margin-bottom: 25px;
    }}
    .legal-scroll-box h4 {{
        color: {COLOR_PRIMARY};
        margin-top: 20px;
        margin-bottom: 12px;
        font-size: 1.1rem;
        font-weight: 700;
    }}
    
    .section-title {{
        color: {COLOR_PRIMARY};
        font-size: 1.6rem;
        font-weight: 800;
        margin-bottom: 25px;
        padding-bottom: 15px;
        border-bottom: 3px solid #ECEFF1;
        letter-spacing: -0.5px;
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
        self.c_accent = colors.HexColor(COLOR_ACCENT)
        self.c_text = colors.HexColor("#2C3E50")
        self.c_grey_light = colors.HexColor("#F4F6F7")
        
        # Estilos de Texto
        self.s_normal = ParagraphStyle('NormalCorp', parent=styles['Normal'], fontName='Helvetica', fontSize=9, leading=12, textColor=self.c_text, alignment=TA_JUSTIFY)
        self.s_label = ParagraphStyle('LabelCorp', parent=styles['Normal'], fontName='Helvetica-Bold', fontSize=8, leading=10, textColor=self.c_primary, textTransform='uppercase')
        self.s_value = ParagraphStyle('ValueCorp', parent=styles['Normal'], fontName='Helvetica', fontSize=9, leading=10, textColor=colors.black)
        self.s_heading = ParagraphStyle('HeadingCorp', parent=styles['Heading2'], fontName='Helvetica-Bold', fontSize=12, leading=14, textColor=colors.white, spaceAfter=0)
        self.s_legal = ParagraphStyle('LegalCorp', parent=styles['Normal'], fontName='Helvetica', fontSize=8, leading=10, textColor=colors.HexColor("#555555"), alignment=TA_JUSTIFY)
        self.s_footer = ParagraphStyle('FooterCorp', parent=styles['Normal'], fontName='Helvetica', fontSize=7, leading=9, textColor=colors.gray, alignment=TA_CENTER)

    def _draw_header_footer(self, canvas, doc):
        canvas.saveState()
        w, h = doc.pagesize
        
        # --- HEADER ---
        # Barra Superior de Color
        canvas.setFillColor(self.c_primary)
        canvas.rect(0, h - 25*mm, w, 25*mm, fill=1, stroke=0)
        
        # Logo (Simulado o Cargado)
        logo_path = 'LOGO FERREINOX SAS BIC 2024.png'
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
        footer_text = "Ferreinox S.A.S. BIC | NIT. 800.224.617-8 | Documento Firmado Digitalmente bajo Ley 527 de 1999"
        canvas.setFont("Helvetica", 7)
        canvas.setFillColor(colors.gray)
        canvas.drawCentredString(w/2, 15*mm, footer_text)
        canvas.drawCentredString(w/2, 12*mm, "www.ferreinox.co | Pereira, Risaralda, Colombia")
        
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

    def _create_data_grid(self):
        # Preparar datos
        d = self.data
        if d['client_type'] == 'juridica':
            grid_data = [
                [Paragraph("RAZÓN SOCIAL", self.s_label), Paragraph(d.get('razon_social', ''), self.s_value), Paragraph("NIT", self.s_label), Paragraph(d.get('nit', ''), self.s_value)],
                [Paragraph("DIRECCIÓN", self.s_label), Paragraph(d.get('direccion', ''), self.s_value), Paragraph("CIUDAD", self.s_label), Paragraph(d.get('ciudad', ''), self.s_value)],
                [Paragraph("EMAIL FACTURACIÓN", self.s_label), Paragraph(d.get('correo', ''), self.s_value), Paragraph("TELÉFONO/MÓVIL", self.s_label), Paragraph(f"{d.get('telefono', '')} / {d.get('celular', '')}", self.s_value)],
                [Paragraph("REP. LEGAL", self.s_label), Paragraph(d.get('rep_legal', ''), self.s_value), Paragraph("C.C. REP. LEGAL", self.s_label), Paragraph(d.get('cedula_rep_legal', ''), self.s_value)],
            ]
        else:
            def safe_txt(k): return str(d.get(k, ''))
            grid_data = [
                [Paragraph("NOMBRE COMPLETO", self.s_label), Paragraph(safe_txt('nombre_natural'), self.s_value), Paragraph("CÉDULA", self.s_label), Paragraph(safe_txt('cedula_natural'), self.s_value)],
                [Paragraph("DIRECCIÓN", self.s_label), Paragraph(safe_txt('direccion'), self.s_value), Paragraph("CIUDAD", self.s_label), Paragraph(safe_txt('ciudad'), self.s_value)],
                [Paragraph("EMAIL PERSONAL", self.s_label), Paragraph(safe_txt('correo'), self.s_value), Paragraph("CELULAR", self.s_label), Paragraph(safe_txt('telefono'), self.s_value)],
                [Paragraph("FECHA NACIMIENTO", self.s_label), Paragraph(safe_txt('fecha_nacimiento'), self.s_value), Paragraph("", self.s_label), Paragraph("", self.s_value)],
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

    def _create_legal_columns(self):
        # Texto legal en dos columnas para mayor profesionalismo
        
        clauses = [
            "<b>1. TRATAMIENTO DE DATOS PERSONALES (LEY 1581 DE 2012):</b> Autorizo a FERREINOX S.A.S. BIC para recolectar, almacenar, usar, circular y suprimir mis datos personales. Estos serán usados para fines de la relación comercial, contable, tributaria y de mercadeo. Conozco que tengo derecho a conocer, actualizar y rectificar mis datos.",
            "<b>2. REPORTE EN CENTRALES DE RIESGO:</b> Autorizo de manera irrevocable, expresa e informada a FERREINOX S.A.S. BIC para consultar, reportar, procesar y divulgar a las Centrales de Información Financiera (como Datacrédito, Cifin, etc.) todo lo referente a mi comportamiento crediticio, comercial y financiero, positivo o negativo.",
            "<b>3. FACTURACIÓN ELECTRÓNICA:</b> Acepto recibir facturas electrónicas, notas débito y crédito al correo electrónico registrado en este formulario, conforme a la normatividad vigente de la DIAN (Decreto 2242 de 2015 y normas que lo modifiquen).",
            "<b>4. ORIGEN DE FONDOS (SAGRILAFT):</b> Declaro bajo la gravedad de juramento que los recursos que poseo y los que utilizo en mis operaciones comerciales provienen de actividades lícitas y no tienen relación alguna con lavado de activos, financiación del terrorismo ni ninguna otra actividad delictiva.",
            "<b>5. VIGENCIA:</b> La presente autorización permanecerá vigente mientras subsista alguna relación comercial o legal con FERREINOX S.A.S. BIC y por el término necesario para fines legales y de auditoría."
        ]
        
        story_left = []
        story_right = []
        
        for i, clause in enumerate(clauses):
            p = Paragraph(clause, self.s_legal)
            if i < 3:
                story_left.append(p)
                story_left.append(Spacer(1, 4))
            else:
                story_right.append(p)
                story_right.append(Spacer(1, 4))
                
        data = [[story_left, story_right]]
        t = Table(data, colWidths=[92*mm, 92*mm])
        t.setStyle(TableStyle([
            ('VALIGN', (0,0), (-1,-1), 'TOP'),
            ('LEFTPADDING', (0,0), (0,0), 0),
            ('RIGHTPADDING', (1,0), (1,0), 0),
        ]))
        return t

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
        self.story.append(self._create_section_header("I. INFORMACIÓN DEL TITULAR"))
        self.story.append(Spacer(1, 5*mm))
        self.story.append(self._create_data_grid())
        self.story.append(Spacer(1, 8*mm))
        
        # Sección 2: Autorizaciones Legales
        self.story.append(self._create_section_header("II. AUTORIZACIONES Y DECLARACIONES"))
        self.story.append(Spacer(1, 2*mm))
        self.story.append(Paragraph("Yo, el titular de la información, actuando en nombre propio o en representación legal de la entidad descrita en la Sección I, otorgo las siguientes autorizaciones:", self.s_normal))
        self.story.append(Spacer(1, 4*mm))
        self.story.append(self._create_legal_columns()) # Texto en 2 columnas
        self.story.append(Spacer(1, 8*mm))
        
        # Sección 3: Firma Electrónica
        self.story.append(self._create_section_header("III. CERTIFICADO DE FIRMA ELECTRÓNICA"))
        self.story.append(Spacer(1, 5*mm))
        
        sig_table, img_path = self._create_signature_box()
        self.story.append(sig_table)
        
        self.story.append(Spacer(1, 5*mm))
        legal_footer = "Este documento electrónico tiene plena validez jurídica y probatoria de conformidad con la Ley 527 de 1999."
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
    defaults = {'step': 1, 'client_type': None, 'form_data': {}, 'otp': "", 'final_url': ""}
    for k, v in defaults.items():
        if k not in st.session_state: st.session_state[k] = v

init_state()

def render_header():
    st.markdown(f"""
    <div class="header-container">
        <div class="header-title">Ferreinox S.A.S. BIC</div>
        <div class="header-subtitle">Portal Institucional de Actualización de Datos y Vinculación</div>
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
    st.markdown('<div class="section-title">POLÍTICA DE TRATAMIENTO DE DATOS</div>', unsafe_allow_html=True)
    
    st.markdown(f"""
    <div class="legal-scroll-box">
        <p><b>FERREINOX S.A.S. BIC</b>, identificada con NIT 800.224.617-8, informa que es responsable del tratamiento de sus datos personales. De conformidad con lo dispuesto en la <b>Ley Estatutaria 1581 de 2012</b>, el <b>Decreto Reglamentario 1377 de 2013</b> y demás normas concordantes, solicitamos su autorización libre, previa, expresa e informada para continuar con el tratamiento de sus datos.</p>
        
        <h4>1. FINALIDADES DEL TRATAMIENTO</h4>
        <p>Los datos suministrados serán utilizados para:</p>
        <ul>
            <li>El desarrollo de la relación comercial, contractual y contable (facturación, cobranza, despachos).</li>
            <li>La consulta y reporte ante centrales de riesgo financiero (Datacrédito, CIFIN) para el estudio de crédito y comportamiento de pago (Ley 1266 de 2008).</li>
            <li>El envío de información sobre novedades, productos, promociones y eventos de FERREINOX S.A.S. BIC.</li>
            <li>La implementación de procesos de facturación electrónica conforme a las exigencias de la DIAN.</li>
        </ul>

        <h4>2. DERECHOS DEL TITULAR (Habeas Data)</h4>
        <p>Como titular de la información, usted tiene derecho a:</p>
        <ul>
            <li>Acceder de forma gratuita a sus datos personales.</li>
            <li>Solicitar la actualización y rectificación de sus datos frente a información parcial, inexacta o incompleta.</li>
            <li>Solicitar prueba de la autorización otorgada.</li>
            <li>Revocar la autorización y/o solicitar la supresión del dato cuando no se respeten los principios constitucionales.</li>
        </ul>

        <h4>3. DECLARACIONES Y AUTORIZACIONES</h4>
        <p>El titular manifiesta que la información suministrada es veraz y autoriza la consulta en listas restrictivas y centrales de riesgo.</p>
    </div>
    """, unsafe_allow_html=True)
    
    check = st.checkbox("Declaro que he leído, comprendo y ACEPTO la Política de Tratamiento de Datos Personales y autorizo las consultas en Centrales de Riesgo.")
    
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
    st.markdown('<div class="section-title">SELECCIONE EL TIPO DE VINCULACIÓN</div>', unsafe_allow_html=True)
    
    c1, c2 = st.columns(2)
    with c1:
        if st.button("🏢 PERSONA JURÍDICA\n(Empresas, S.A.S, Ltda)", use_container_width=True):
            st.session_state.client_type = 'juridica'
            st.session_state.step = 3
            st.rerun()
    with c2:
        if st.button("👤 PERSONA NATURAL\n(Independientes, Personas)", use_container_width=True):
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
    st.markdown('<div class="section-title">DILIGENCIAMIENTO DE INFORMACIÓN</div>', unsafe_allow_html=True)
    
    with st.form("main_form"):
        # Lógica Condicional de Campos
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
            correo = st.text_input("Correo para Facturación Electrónica (DIAN)*")
            rep_legal = col1.text_input("Nombre Representante Legal*")
            cedula_rep = col2.text_input("Cédula Rep. Legal*")
            
            # Variables vacías para el otro tipo
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
            telefono = celular
            
            # Variables vacías para el otro tipo
            razon_social, nit, rep_legal, cedula_rep = nom_nat, ced_nat, "", ""

        st.markdown("---")
        st.markdown("<b>FIRMA DIGITAL:</b> Por favor firme en el recuadro blanco usando el mouse o dedo.")
        
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
            # Validacion
            valid = True
            if st.session_state.client_type == 'juridica':
                if not all([razon_social, nit, direccion, ciudad, correo, celular, rep_legal, cedula_rep]): valid = False
            else:
                if not all([nom_nat, ced_nat, direccion, ciudad, correo, celular]): valid = False
            
            if canvas.image_data is None or np.all(canvas.image_data == 255):
                st.error("⚠️ La firma es obligatoria.")
                valid = False
                
            if valid:
                # Guardar en Session State
                st.session_state.form_data = {
                    'client_type': st.session_state.client_type,
                    'razon_social': razon_social, 'nit': nit, 'direccion': direccion, 
                    'ciudad': ciudad, 'telefono': telefono, 'celular': celular,
                    'correo': correo, 'rep_legal': rep_legal, 'cedula_rep_legal': cedula_rep,
                    'nombre_natural': nom_nat, 'cedula_natural': ced_nat, 'fecha_nacimiento': fe_nac,
                    'firma_img_pil': Image.fromarray(canvas.image_data.astype('uint8'), 'RGBA')
                }
                
                # Generar OTP y Enviar
                otp = str(random.randint(100000, 999999))
                st.session_state.otp = otp
                
                html_otp = f"""
                <div style='background:#f4f4f4; padding:20px; font-family:Arial, sans-serif;'>
                    <div style='background:#fff; padding:30px; border-radius:10px; border-top:6px solid {COLOR_PRIMARY}; max-width:600px; margin:auto;'>
                        <h2 style='color:{COLOR_PRIMARY}; margin-top:0;'>Código de Seguridad</h2>
                        <p style='color:#555;'>Para firmar digitalmente su vinculación con <b>Ferreinox S.A.S. BIC</b>, utilice el siguiente código de verificación:</p>
                        <div style='background:{COLOR_BG}; padding:15px; text-align:center; border-radius:8px; margin:20px 0;'>
                            <h1 style='letter-spacing:8px; margin:0; color:{COLOR_TEXT};'>{otp}</h1>
                        </div>
                        <p style='font-size:12px; color:gray; text-align:center;'>Este código expira en 10 minutos. No lo comparta.</p>
                    </div>
                </div>
                """
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
    st.markdown('<div class="section-title">VERIFICACIÓN DE SEGURIDAD</div>', unsafe_allow_html=True)
    
    email_dest = st.session_state.form_data.get('correo')
    st.info(f"Hemos enviado un código de 6 dígitos a: **{email_dest}**")
    
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
                        html_end = f"""
                        <div style='font-family:Arial, sans-serif; color:#333;'>
                            <h2 style='color:{COLOR_PRIMARY};'>Vinculación Exitosa</h2>
                            <p>Estimado usuario,</p>
                            <p>Ferreinox S.A.S. BIC confirma la recepción y firma exitosa de su autorización de datos.</p>
                            <ul>
                                <li><b>Radicado:</b> {doc_id}</li>
                                <li><b>Fecha:</b> {ts}</li>
                            </ul>
                            <p>Adjunto encontrará el documento PDF firmado y legalizado para sus archivos.</p>
                            <hr style='border:0; border-top:1px solid #eee;'>
                            <p style='font-size:11px; color:#999;'>Ferreinox S.A.S. BIC - Pereira, Colombia</p>
                        </div>
                        """
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
    <div class="card-box" style="text-align: center;">
        <h1 style="color: #4CAF50; font-size: 5rem; margin-bottom:10px;">✅</h1>
        <h2 style="color: {COLOR_PRIMARY}; text-transform: uppercase;">¡Proceso Completado!</h2>
        <p style="font-size:1.1rem; color:#555;">Sus datos han sido actualizados y el contrato ha sido firmado digitalmente.</p>
        <p>Hemos enviado una copia del documento a su correo electrónico.</p>
        <br>
        <a href="{st.session_state.final_url}" target="_blank" style="
            background-color:{COLOR_PRIMARY}; 
            color:white; 
            padding:15px 30px; 
            text-decoration:none; 
            border-radius:50px; 
            font-weight:bold;
            box-shadow: 0 5px 15px rgba(13, 71, 161, 0.4);
            display: inline-block;
            transition: all 0.3s;
        ">VER DOCUMENTO PDF</a>
        <br><br><br>
    </div>
    """, unsafe_allow_html=True)
    
    if st.button("Volver al Inicio"):
        for k in st.session_state.keys():
            del st.session_state[k]
        st.rerun()