# -*- coding: utf-8 -*-
# =================================================================================================
# PLATAFORMA CORPORATIVA DE ACTUALIZACIÓN DE DATOS - FERREINOX S.A.S. BIC
# Versión: 20.0 (Enterprise UX/UI Overhaul)
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

# --- ReportLab Imports ---
from reportlab.platypus import BaseDocTemplate, PageTemplate, Frame, Paragraph, Spacer, Table, TableStyle, Image as PlatypusImage
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_LEFT, TA_RIGHT
from reportlab.lib import colors
from reportlab.lib.units import inch, cm
from reportlab.lib.pagesizes import letter

# --- Google & Email Imports ---
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication

# =================================================================================================
# 1. CONFIGURACIÓN DE PÁGINA Y ESTILOS CSS PROFESIONALES
# =================================================================================================

st.set_page_config(
    page_title="Portal de Actualización de Datos | Ferreinox S.A.S. BIC",
    page_icon="🛡️",
    layout="centered", # Centered layout for a more document-focused feel
    initial_sidebar_state="collapsed"
)

# --- Corporate Color Palette (Derived from Ferreinox Identity) ---
COLOR_PRIMARY = "#003399"       # Deep Blue
COLOR_SECONDARY = "#0056b3"     # Brighter Blue for accents
COLOR_ACCENT = "#FFC107"        # Gold/Yellow for highlights
COLOR_BG = "#F4F6F9"            # Very light grey/blue background
COLOR_TEXT = "#333333"          # Dark Grey text
COLOR_WHITE = "#FFFFFF"

# --- Advanced CSS Injection ---
st.markdown(f"""
<style>
    /* Global Settings */
    @import url('https://fonts.googleapis.com/css2?family=Roboto:wght@300;400;700&display=swap');
    
    html, body, [class*="css"] {{
        font-family: 'Roboto', sans-serif;
        background-color: {COLOR_BG};
        color: {COLOR_TEXT};
    }}
    
    /* Hide Streamlit Branding */
    #MainMenu {{visibility: hidden;}}
    footer {{visibility: hidden;}}
    header {{visibility: hidden;}}
    div[data-testid="stSidebarNav"] {{display: none;}}

    /* Custom Header container */
    .header-container {{
        background: linear-gradient(90deg, {COLOR_PRIMARY} 0%, {COLOR_SECONDARY} 100%);
        padding: 2rem 1rem;
        border-radius: 0 0 20px 20px;
        margin-bottom: 2rem;
        text-align: center;
        color: white;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }}
    
    .header-title {{
        font-size: 2.2rem;
        font-weight: 700;
        margin-bottom: 0.5rem;
        text-transform: uppercase;
        letter-spacing: 1px;
    }}
    
    .header-subtitle {{
        font-size: 1rem;
        font-weight: 300;
        opacity: 0.9;
    }}

    /* Card Containers */
    .stForm, div[data-testid="stVerticalBlock"] > div.element-container {{
        background-color: white;
        padding: 0;
        border-radius: 12px;
    }}
    
    .card-box {{
        background-color: white;
        padding: 2rem;
        border-radius: 15px;
        box-shadow: 0 2px 10px rgba(0,0,0,0.05);
        margin-bottom: 1.5rem;
        border-top: 5px solid {COLOR_PRIMARY};
    }}

    /* Progress Steps */
    .step-container {{
        display: flex;
        justify-content: space-between;
        margin-bottom: 2rem;
        padding: 0 1rem;
    }}
    .step {{
        text-align: center;
        font-size: 0.8rem;
        font-weight: bold;
        color: #aaa;
        position: relative;
        flex: 1;
    }}
    .step.active {{
        color: {COLOR_PRIMARY};
    }}
    .step-icon {{
        background-color: #eee;
        color: #aaa;
        width: 40px;
        height: 40px;
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        margin: 0 auto 5px;
        font-size: 1.2rem;
        transition: all 0.3s;
    }}
    .step.active .step-icon {{
        background-color: {COLOR_PRIMARY};
        color: white;
        box-shadow: 0 4px 10px rgba(0,51,153,0.3);
    }}

    /* Input Fields Styling */
    div[data-baseweb="input"] > div {{
        border-radius: 8px;
        border: 1px solid #e0e0e0;
        background-color: #fcfcfc;
    }}
    div[data-baseweb="input"] > div:focus-within {{
        border-color: {COLOR_PRIMARY};
        background-color: white;
    }}
    
    /* Buttons */
    .stButton>button {{
        width: 100%;
        border-radius: 8px;
        border: none;
        background: linear-gradient(45deg, {COLOR_PRIMARY}, {COLOR_SECONDARY});
        color: white;
        font-weight: bold;
        padding: 0.6rem 1rem;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        box-shadow: 0 4px 6px rgba(0,51,153,0.2);
        transition: transform 0.2s, box-shadow 0.2s;
    }}
    .stButton>button:hover {{
        transform: translateY(-2px);
        box-shadow: 0 6px 12px rgba(0,51,153,0.3);
        color: white;
    }}
    .secondary-btn>button {{
        background: transparent;
        border: 2px solid {COLOR_PRIMARY};
        color: {COLOR_PRIMARY};
    }}

    /* Legal Text Box */
    .legal-box {{
        height: 300px;
        overflow-y: scroll;
        background-color: #f9f9f9;
        border: 1px solid #ddd;
        padding: 1.5rem;
        border-radius: 8px;
        font-size: 0.9rem;
        line-height: 1.6;
        text-align: justify;
        margin-bottom: 1rem;
    }}
    
    /* Section Headers */
    .section-header {{
        color: {COLOR_PRIMARY};
        font-size: 1.3rem;
        font-weight: 700;
        border-bottom: 2px solid #eee;
        padding-bottom: 0.5rem;
        margin-bottom: 1.5rem;
        margin-top: 1rem;
    }}

</style>
""", unsafe_allow_html=True)

# =================================================================================================
# 2. CLASES Y FUNCIONES DE BACKEND (PDF, EMAIL, SHEETS)
# =================================================================================================

class PDFGeneratorPlatypus:
    def __init__(self, data, doc_id):
        self.data = data
        self.doc_id = doc_id
        self.story = []
        
        # Estilos mejorados para ReportLab
        styles = getSampleStyleSheet()
        self.style_body = ParagraphStyle(name='Body', parent=styles['Normal'], fontName='Helvetica', fontSize=10, alignment=TA_JUSTIFY, leading=15)
        self.style_body_bold = ParagraphStyle(name='BodyBold', parent=self.style_body, fontName='Helvetica-Bold')
        self.style_bullet = ParagraphStyle(name='Bullet', parent=self.style_body, leftIndent=25, firstLineIndent=0, spaceBefore=3)
        self.style_header_title = ParagraphStyle(name='HeaderTitle', parent=styles['h1'], fontName='Helvetica-Bold', fontSize=14, alignment=TA_RIGHT, textColor=colors.HexColor(COLOR_PRIMARY))
        self.style_header_info = ParagraphStyle(name='HeaderInfo', parent=styles['Normal'], fontName='Helvetica', fontSize=8, alignment=TA_RIGHT, textColor=colors.HexColor("#666666"))
        self.style_footer = ParagraphStyle(name='Footer', parent=styles['Normal'], fontName='Helvetica', fontSize=8, alignment=TA_CENTER, textColor=colors.HexColor("#666666"))
        self.style_section_title = ParagraphStyle(name='SectionTitle', parent=styles['h2'], fontName='Helvetica-Bold', fontSize=12, alignment=TA_LEFT, textColor=colors.white, spaceBefore=12, spaceAfter=6, leftIndent=10)
        self.style_table_header = ParagraphStyle(name='TableHeader', parent=styles['Normal'], fontName='Helvetica-Bold', fontSize=9, textColor=colors.HexColor("#444444"), alignment=TA_LEFT)
        self.style_signature_info = ParagraphStyle(name='SignatureInfo', parent=styles['Normal'], fontName='Helvetica', fontSize=8, alignment=TA_LEFT, leading=12)

    def _on_page(self, canvas, doc):
        canvas.saveState()
        # Encabezado Institucional
        try:
            # Intento de cargar logo si existe, sino texto
            logo = PlatypusImage('LOGO FERREINOX SAS BIC 2024.png', width=2.2*inch, height=0.7*inch, hAlign='LEFT')
        except:
            logo = Paragraph("<b>FERREINOX S.A.S. BIC</b>", self.style_body_bold)
        
        header_title_text = "<b>AUTORIZACIÓN DE TRATAMIENTO DE DATOS</b>"
        header_info_text = f"ID Control: {self.doc_id}<br/>Fecha: {self.data.get('timestamp', '')}"
        
        header_content = [[logo, [Paragraph(header_title_text, self.style_header_title), Spacer(1, 4), Paragraph(header_info_text, self.style_header_info)]]]
        header_table = Table(header_content, colWidths=[3.0*inch, 4.2*inch])
        header_table.setStyle(TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('ALIGN', (1, 0), (1, 0), 'RIGHT'),
        ]))
        w, h = header_table.wrap(doc.width, doc.topMargin)
        header_table.drawOn(canvas, doc.leftMargin, doc.height + doc.topMargin - h + 10)
        
        # Línea divisoria corporativa
        canvas.setStrokeColor(colors.HexColor(COLOR_PRIMARY))
        canvas.setLineWidth(2)
        canvas.line(doc.leftMargin, doc.height + doc.topMargin - h - 5, doc.leftMargin + doc.width, doc.height + doc.topMargin - h - 5)
        
        # Pie de página
        footer_text = "Ferreinox S.A.S. BIC | NIT. 800.224.617-8 | Actualización de Datos | www.ferreinox.co"
        footer_page = f"Pág. {doc.page}"
        canvas.setFont("Helvetica", 8)
        canvas.setFillColor(colors.HexColor("#666666"))
        canvas.drawCentredString(doc.width/2.0 + doc.leftMargin, 0.5*inch, footer_text)
        canvas.drawRightString(doc.width + doc.leftMargin, 0.5*inch, footer_page)
        
        canvas.restoreState()

    def _create_section_header(self, title, doc):
        header_table = Table([[Paragraph(title.upper(), self.style_section_title)]], colWidths=[doc.width], hAlign='LEFT')
        header_table.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,-1), colors.HexColor(COLOR_PRIMARY)),
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
            ('TOPPADDING', (0,0), (-1,-1), 5),
            ('BOTTOMPADDING', (0,0), (-1,-1), 5)
        ]))
        return header_table

    def _add_legal_authorizations(self, nombre_firmante, razon_social, nit_o_cc, email_facturacion):
        # Texto legal robusto (resumido en código pero completo en PDF)
        self.story.append(Paragraph(f"Yo, <b>{nombre_firmante}</b>, identificado como aparece al pie de mi firma, obrando en nombre propio y/o como Representante Legal de <b>{razon_social}</b>, identificado con NIT/C.C. <b>{nit_o_cc}</b>, autorizo de manera expresa a <b>FERREINOX S.A.S. BIC</b> para el tratamiento de mis datos personales y crediticios.", self.style_body))
        self.story.append(Spacer(1, 0.15*inch))
        
        self.story.append(Paragraph("<b>1. POLÍTICA DE DATOS PERSONALES (LEY 1581 DE 2012):</b>", self.style_body_bold))
        self.story.append(Paragraph("Autorizo a FERREINOX S.A.S. BIC a recolectar, almacenar, usar, circular y suprimir mis datos para fines comerciales, gestión contable, fiscal, administrativa, campañas de fidelización, marketing y seguridad.", self.style_body))
        self.story.append(Spacer(1, 0.1*inch))

        self.story.append(Paragraph("<b>2. REPORTE EN CENTRALES DE RIESGO (LEY 1266 DE 2008):</b>", self.style_body_bold))
        self.story.append(Paragraph("Autorizo irrevocablemente a consultar, solicitar, reportar, procesar y divulgar ante las centrales de riesgo (Datacrédito, Cifin, etc.) toda la información referente a mi comportamiento crediticio, comercial y de servicios.", self.style_body))
        self.story.append(Spacer(1, 0.1*inch))
        
        self.story.append(Paragraph(f"<b>3. NOTIFICACIONES:</b> Acepto que cualquier reporte negativo será notificado previamente al correo suministrado en este formulario: <b>{email_facturacion}</b>.", self.style_body))

    def _add_signature_section(self, doc):
        self.story.append(Spacer(1, 0.4*inch))
        self.story.append(self._create_section_header("IV. EVIDENCIA DE CONSENTIMIENTO DIGITAL", doc))
        self.story.append(Spacer(1, 0.2*inch))
        
        firma_path = None
        try:
            with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as temp_img:
                firma_path = temp_img.name
            
            firma_img_pil = self.data['firma_img_pil']
            if firma_img_pil.mode == "RGBA":
                background = Image.new("RGB", firma_img_pil.size, (255, 255, 255))
                background.paste(firma_img_pil, mask=firma_img_pil.split()[3])
                background.save(firma_path, format="PNG")
            else:
                firma_img_pil.save(firma_path, format="PNG")
            
            firma_image = PlatypusImage(firma_path, width=2.5*inch, height=1.0*inch)
            
            if self.data.get('client_type') == 'juridica':
                nombre_firmante = self.data.get('rep_legal', '')
                id_firmante = f"C.C. {self.data.get('cedula_rep_legal', '')}"
            else:
                nombre_firmante = self.data.get('nombre_natural', '')
                id_firmante = f"C.C. {self.data.get('cedula_natural', '')}"
            
            fecha_firma = self.data.get('timestamp', 'No disponible')
            
            firma_texto = f"""<b>Firmado Electrónicamente por:</b><br/>
                            {nombre_firmante}<br/>
                            {id_firmante}<br/>
                            <b>Fecha:</b> {fecha_firma} (GMT-5)<br/>
                            <b>Hash de Seguridad:</b> {self.doc_id}<br/>
                            <i>Verificado vía OTP (Email)</i>"""
            
            table_firma_content = [[firma_image, Paragraph(firma_texto, self.style_signature_info)]]
            table_firma = Table(table_firma_content, colWidths=[2.8*inch, 4.4*inch], hAlign='LEFT')
            table_firma.setStyle(TableStyle([
                ('VALIGN', (0,0), (-1,-1), 'CENTER'),
                ('LEFTPADDING', (1,0), (1,0), 10),
                ('BOX', (0,0), (0,0), 0.5, colors.grey) # Recuadro solo a la imagen para formalidad
            ]))
            self.story.append(table_firma)
            
            self.story.append(Spacer(1, 0.2*inch))
            self.story.append(Paragraph("La presente firma goza de plena validez jurídica conforme a la Ley 527 de 1999 de Comercio Electrónico.", self.style_footer))

            return firma_path
        except Exception as e:
            return None

    def generate(self):
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as temp_pdf:
            pdf_path = temp_pdf.name
        
        doc = BaseDocTemplate(pdf_path, pagesize=letter, leftMargin=0.8*inch, rightMargin=0.8*inch, topMargin=1.5*inch, bottomMargin=1.0*inch)
        frame = Frame(doc.leftMargin, doc.bottomMargin, doc.width, doc.height, id='main_frame')
        template = PageTemplate(id='main_template', frames=[frame], onPage=self._on_page)
        doc.addPageTemplates([template])
        
        # --- SECCIÓN I: INFORMACIÓN ---
        self.story.append(self._create_section_header("I. INFORMACIÓN DEL TITULAR", doc))
        self.story.append(Spacer(1, 0.2*inch))
        
        # Lógica para construir tabla de datos
        if self.data.get('client_type') == 'juridica':
            datos = [
                [Paragraph('Razón Social:', self.style_table_header), Paragraph(self.data.get('razon_social', ''), self.style_body), Paragraph('NIT:', self.style_table_header), Paragraph(self.data.get('nit', ''), self.style_body)],
                [Paragraph('Dirección:', self.style_table_header), Paragraph(self.data.get('direccion', ''), self.style_body), Paragraph('Ciudad:', self.style_table_header), Paragraph(self.data.get('ciudad', ''), self.style_body)],
                [Paragraph('Teléfonos:', self.style_table_header), Paragraph(f"{self.data.get('telefono', '')} / {self.data.get('celular', '')}", self.style_body), Paragraph('Email Facturación:', self.style_table_header), Paragraph(self.data.get('correo', ''), self.style_body)],
                [Paragraph('Rep. Legal:', self.style_table_header), Paragraph(self.data.get('rep_legal', ''), self.style_body), Paragraph('ID Rep. Legal:', self.style_table_header), Paragraph(f"{self.data.get('cedula_rep_legal', '')} ({self.data.get('lugar_exp_id', '')})", self.style_body)]
            ]
            rep_legal_name, entity_name, entity_id, entity_email = self.data['rep_legal'], self.data['razon_social'], self.data['nit'], self.data['correo']
        else:
            datos = [
                [Paragraph('Nombre:', self.style_table_header), Paragraph(self.data.get('nombre_natural', ''), self.style_body), Paragraph('Identificación:', self.style_table_header), Paragraph(f"{self.data.get('cedula_natural', '')} ({self.data.get('lugar_exp_id', '')})", self.style_body)],
                [Paragraph('Dirección:', self.style_table_header), Paragraph(self.data.get('direccion', ''), self.style_body), Paragraph('Ciudad:', self.style_table_header), Paragraph(self.data.get('ciudad', ''), self.style_body)],
                [Paragraph('Celular:', self.style_table_header), Paragraph(self.data.get('telefono', ''), self.style_body), Paragraph('Email:', self.style_table_header), Paragraph(self.data.get('correo', ''), self.style_body)],
                [Paragraph('Fecha Nac.:', self.style_table_header), Paragraph(str(self.data.get('fecha_nacimiento', '')), self.style_body), '', '']
            ]
            rep_legal_name, entity_name, entity_id, entity_email = self.data['nombre_natural'], self.data['nombre_natural'], self.data['cedula_natural'], self.data['correo']

        table_basicos = Table(datos, colWidths=[1.4*inch, 2.2*inch, 1.4*inch, 2.2*inch])
        table_basicos.setStyle(TableStyle([
            ('GRID', (0,0), (-1,-1), 0.25, colors.lightgrey),
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
            ('BACKGROUND', (0,0), (0,-1), colors.whitesmoke),
            ('BACKGROUND', (2,0), (2,-1), colors.whitesmoke),
            ('PADDING', (0,0), (-1,-1), 6),
        ]))
        self.story.append(table_basicos)
        self.story.append(Spacer(1, 0.3*inch))

        # --- SECCIONES LEGALES ---
        self.story.append(self._create_section_header("II & III. DECLARACIONES Y AUTORIZACIONES", doc))
        self.story.append(Spacer(1, 0.1*inch))
        self._add_legal_authorizations(rep_legal_name, entity_name, entity_id, entity_email)

        # --- SECCIÓN FIRMA ---
        firma_path = self._add_signature_section(doc)
        
        try:
            doc.build(self.story)
        finally:
            if firma_path and os.path.exists(firma_path):
                os.unlink(firma_path)
        
        return pdf_path

# =================================================================================================
# 3. LÓGICA DE APLICACIÓN Y UI
# =================================================================================================

# --- Initialization & State Management ---
def init_session_state():
    if 'step' not in st.session_state: st.session_state.step = 1 # 1:Terms, 2:Type, 3:Form, 4:Verify, 5:Done
    if 'client_type' not in st.session_state: st.session_state.client_type = None
    if 'form_data_cache' not in st.session_state: st.session_state.form_data_cache = {}
    if 'generated_code' not in st.session_state: st.session_state.generated_code = ""
    if 'final_link' not in st.session_state: st.session_state.final_link = ""

init_session_state()

# --- Utility: Navigation Header ---
def render_header():
    st.markdown(f"""
    <div class="header-container">
        <div class="header-title">FERREINOX S.A.S. BIC</div>
        <div class="header-subtitle">Portal Seguro de Actualización y Vinculación de Clientes</div>
    </div>
    """, unsafe_allow_html=True)

# --- Utility: Progress Steps ---
def render_progress_bar():
    steps = [
        {"num": 1, "label": "Términos", "icon": "📜"},
        {"num": 2, "label": "Tipo Cliente", "icon": "👤"},
        {"num": 3, "label": "Datos", "icon": "📝"},
        {"num": 4, "label": "Verificar", "icon": "🔐"},
    ]
    
    html = '<div class="step-container">'
    for s in steps:
        active_class = "active" if st.session_state.step >= s['num'] else ""
        html += f"""
        <div class="step {active_class}">
            <div class="step-icon">{s['icon']}</div>
            {s['label']}
        </div>
        """
    html += '</div>'
    st.markdown(html, unsafe_allow_html=True)

# --- Services Configuration (Hidden Logic) ---
def get_google_services():
    try:
        required_secrets = ["google_sheet_id", "google_credentials", "drive_folder_id", "email_credentials"]
        if not all(secret in st.secrets for secret in required_secrets):
            st.error("Error de configuración del servidor.")
            return None, None, None
        
        creds_dict = st.secrets["google_credentials"].to_dict()
        scopes = ['https://www.googleapis.com/auth/drive', 'https://www.googleapis.com/auth/spreadsheets']
        creds = Credentials.from_service_account_info(creds_dict, scopes=scopes)
        
        gc = gspread.authorize(creds)
        worksheet = gc.open_by_key(st.secrets["google_sheet_id"]).sheet1
        drive_service = build('drive', 'v3', credentials=creds)
        return worksheet, drive_service, creds
    except Exception as e:
        st.error(f"Error de conexión: {e}")
        return None, None, None

def send_email_func(recipient, subject, html_body, pdf_path=None, filename=None):
    try:
        creds = st.secrets["email_credentials"]
        msg = MIMEMultipart()
        msg['From'] = f"Ferreinox S.A.S. BIC <{creds.get('smtp_user')}>"
        msg['To'] = recipient
        msg['Subject'] = subject
        msg.attach(MIMEText(html_body, 'html'))

        if pdf_path and filename:
            with open(pdf_path, "rb") as f:
                part = MIMEApplication(f.read(), Name=filename)
            part['Content-Disposition'] = f'attachment; filename="{filename}"'
            msg.attach(part)
        
        context = smtplib.ssl.create_default_context()
        with smtplib.SMTP_SSL(creds.get("smtp_server"), int(creds.get("smtp_port")), context=context) as server:
            server.login(creds.get("smtp_user"), creds.get("smtp_password"))
            server.send_message(msg)
        return True
    except Exception as e:
        print(f"Error email: {e}")
        return False

# =================================================================================================
# 4. FLUJO PRINCIPAL DE PANTALLAS
# =================================================================================================

render_header()

if st.session_state.step < 5:
    render_progress_bar()

# --- PANTALLA 1: TÉRMINOS Y CONDICIONES ---
if st.session_state.step == 1:
    st.markdown('<div class="card-box">', unsafe_allow_html=True)
    st.markdown(f"<div class='section-header'>DECLARACIÓN DE TRATAMIENTO DE DATOS</div>", unsafe_allow_html=True)
    
    st.markdown("""
    <div class="legal-box">
        <p><b>AUTORIZACIÓN PARA EL TRATAMIENTO DE DATOS PERSONALES Y CONSULTA EN CENTRALES DE RIESGO</b></p>
        <p>En cumplimiento de la <b>Ley 1581 de 2012</b> (Protección de Datos Personales) y la <b>Ley 1266 de 2008</b> (Habeas Data Financiero), FERREINOX S.A.S. BIC solicita su autorización expresa para continuar con el proceso de vinculación o actualización de datos.</p>
        <p><b>Al aceptar, usted declara y autoriza lo siguiente:</b></p>
        <ol>
            <li><b>Tratamiento de Datos:</b> Autoriza a FERREINOX S.A.S. BIC a recolectar, almacenar, usar y circular sus datos personales para fines de gestión comercial, facturación electrónica, contacto logístico, y envío de información promocional.</li>
            <li><b>Centrales de Riesgo:</b> Autoriza de manera irrevocable a FERREINOX S.A.S. BIC a consultar, reportar y procesar su comportamiento crediticio, financiero y comercial ante centrales de riesgo (como Datacrédito, Cifin, entre otras).</li>
            <li><b>Veracidad:</b> Declara que la información que suministrará a continuación es veraz, completa y exacta.</li>
            <li><b>Notificación Electrónica:</b> Acepta recibir notificaciones previas a reportes negativos y facturación electrónica al correo que suministrará en este formulario.</li>
        </ol>
        <p>La política completa de tratamiento de datos está disponible en <i>www.ferreinox.co</i>.</p>
    </div>
    """, unsafe_allow_html=True)
    
    check_terms = st.checkbox("He leído, comprendo y ACEPTO los términos y condiciones descritos anteriormente.")
    
    if st.button("Continuar al Paso 2 ➜"):
        if check_terms:
            st.session_state.step = 2
            st.rerun()
        else:
            st.warning("⚠️ Debe aceptar los términos para poder continuar.")
    
    st.markdown('</div>', unsafe_allow_html=True)

# --- PANTALLA 2: SELECCIÓN TIPO CLIENTE ---
elif st.session_state.step == 2:
    st.markdown('<div class="card-box">', unsafe_allow_html=True)
    st.markdown(f"<div class='section-header'>SELECCIONE SU TIPO DE VINCULACIÓN</div>", unsafe_allow_html=True)
    st.write("Por favor identifique si su relación comercial es a título personal o empresarial.")
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🏢\nPERSONA JURÍDICA\n(Empresas, S.A.S, Ltda)"):
            st.session_state.client_type = 'juridica'
            st.session_state.step = 3
            st.rerun()
    with col2:
        if st.button("👤\nPERSONA NATURAL\n(Independientes, Personas)"):
            st.session_state.client_type = 'natural'
            st.session_state.step = 3
            st.rerun()
            
    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("‹ Regresar"):
        st.session_state.step = 1
        st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

# --- PANTALLA 3: FORMULARIO DE DATOS ---
elif st.session_state.step == 3:
    st.markdown('<div class="card-box">', unsafe_allow_html=True)
    
    with st.form(key="main_form"):
        st.markdown(f"<div class='section-header'>INFORMACIÓN COMERCIAL Y TRIBUTARIA</div>", unsafe_allow_html=True)
        
        # --- CAMPOS DINÁMICOS ---
        if st.session_state.client_type == 'juridica':
            c1, c2 = st.columns(2)
            razon_social = c1.text_input("Razón Social (Como aparece en RUT)*")
            nit = c2.text_input("NIT (Sin dígito de verificación)*")
            c3, c4 = st.columns(2)
            nombre_comercial = c3.text_input("Nombre Comercial")
            direccion = c4.text_input("Dirección Principal*")
            c5, c6 = st.columns(2)
            ciudad = c5.text_input("Ciudad / Departamento*")
            telefono = c6.text_input("Teléfono Fijo")
            
            st.markdown(f"<div class='section-header'>CONTACTOS DIGITALES (IMPORTANTE)</div>", unsafe_allow_html=True)
            st.info("Estos correos son fundamentales para la facturación electrónica y notificaciones legales.")
            ec1, ec2 = st.columns(2)
            correo = ec1.text_input("Correo Facturación Electrónica (DIAN)*")
            correo_promo = ec2.text_input("Correo Notificaciones / Pagos*", help="Aquí llegará el código de seguridad.")
            celular = st.text_input("Celular Corporativo / Contacto*")

            st.markdown(f"<div class='section-header'>REPRESENTACIÓN LEGAL</div>", unsafe_allow_html=True)
            rl1, rl2 = st.columns(2)
            rep_legal = rl1.text_input("Nombre Representante Legal*")
            cedula_rep_legal = rl2.text_input("Cédula de Ciudadanía Rep. Legal*")
            lugar_exp_id = st.text_input("Lugar de Expedición CC*")
            
            # Datos adicionales ocultos
            nombre_natural = ""
            cedula_natural = ""
            fecha_nacimiento = None
            
        else: # Persona Natural
            c1, c2 = st.columns(2)
            nombre_natural = c1.text_input("Nombre Completo (Como aparece en Cédula)*")
            cedula_natural = c2.text_input("Número de Cédula*")
            lugar_exp_id = st.text_input("Lugar de Expedición CC*")
            c3, c4 = st.columns(2)
            direccion = c3.text_input("Dirección de Residencia/Comercial*")
            ciudad = c4.text_input("Ciudad*")
            
            st.markdown(f"<div class='section-header'>CONTACTO</div>", unsafe_allow_html=True)
            ec1, ec2 = st.columns(2)
            correo = ec1.text_input("Correo Personal / Facturación*")
            correo_promo = ec2.text_input("Correo Alterno / Notificaciones*", help="Aquí llegará el código de seguridad.")
            celular = st.text_input("Celular*")
            fecha_nacimiento = st.date_input("Fecha de Nacimiento*", min_value=datetime(1940,1,1).date())
            
            # Datos adicionales ocultos
            razon_social = nombre_natural # Mapeo para lógica
            nit = cedula_natural
            nombre_comercial = ""
            telefono = celular
            rep_legal = ""
            cedula_rep_legal = ""

        st.markdown(f"<div class='section-header'>FIRMA MANUSCRITA DIGITAL</div>", unsafe_allow_html=True)
        st.write("Por favor, firme en el recuadro blanco usando su mouse o pantalla táctil.")
        
        canvas_result = st_canvas(
            fill_color="rgba(255, 165, 0, 0.3)",
            stroke_width=2,
            stroke_color="#000000",
            background_color="#ffffff",
            height=180,
            width=600,
            drawing_mode="freedraw",
            key="canvas",
        )
        
        st.markdown("<br>", unsafe_allow_html=True)
        col_b1, col_b2 = st.columns([1, 2])
        with col_b1:
            if st.form_submit_button("‹ Atrás", type="secondary"):
                st.session_state.step = 2
                st.rerun()
        with col_b2:
            submit = st.form_submit_button("GUARDAR Y VALIDAR FIRMA ➜")
    
    if submit:
        # Validación Básica
        valid = True
        if st.session_state.client_type == 'juridica':
            if not all([razon_social, nit, direccion, ciudad, correo, correo_promo, celular, rep_legal, cedula_rep_legal, lugar_exp_id]): valid = False
        else:
            if not all([nombre_natural, cedula_natural, direccion, ciudad, correo, correo_promo, celular, lugar_exp_id]): valid = False
            
        if canvas_result.image_data is None or np.all(canvas_result.image_data == 255):
            valid = False
            st.error("⚠️ La firma es obligatoria.")

        if valid:
            # Guardar en Cache y Generar OTP
            st.session_state.form_data_cache = {
                'client_type': st.session_state.client_type,
                'razon_social': razon_social, 'nit': nit, 'nombre_comercial': nombre_comercial,
                'direccion': direccion, 'ciudad': ciudad, 'telefono': telefono, 'celular': celular,
                'correo': correo, 'correo_promo': correo_promo,
                'rep_legal': rep_legal, 'cedula_rep_legal': cedula_rep_legal, 'lugar_exp_id': lugar_exp_id,
                'nombre_natural': nombre_natural, 'cedula_natural': cedula_natural,
                'fecha_nacimiento': fecha_nacimiento,
                'firma_img_pil': Image.fromarray(canvas_result.image_data.astype('uint8'), 'RGBA')
            }
            
            # Generar OTP
            otp_code = str(random.randint(100000, 999999))
            st.session_state.generated_code = otp_code
            
            # Enviar Email
            with st.spinner("Conectando con servidor seguro... Enviando código de verificación..."):
                html_otp = f"""
                <div style="font-family: Arial, sans-serif; color: #333; padding: 20px; border: 1px solid #ddd; border-radius: 10px;">
                    <h2 style="color: #003399;">Código de Seguridad Ferreinox</h2>
                    <p>Está realizando un proceso de firma digital. Use el siguiente código para validar su identidad:</p>
                    <div style="background: #f4f6f9; padding: 15px; text-align: center; font-size: 24px; font-weight: bold; letter-spacing: 5px; border-radius: 5px; margin: 20px 0;">
                        {otp_code}
                    </div>
                    <p style="font-size: 12px; color: #777;">Si no solicitó este código, por favor ignore este correo.</p>
                </div>
                """
                if send_email_func(correo_promo, "Código de Verificación - Ferreinox S.A.S.", html_otp):
                    st.session_state.step = 4
                    st.rerun()
                else:
                    st.error("Error enviando el correo. Verifique que la dirección sea correcta.")
        else:
            st.error("⚠️ Por favor complete todos los campos obligatorios (*) y firme el documento.")

    st.markdown('</div>', unsafe_allow_html=True)

# --- PANTALLA 4: VERIFICACIÓN OTP ---
elif st.session_state.step == 4:
    st.markdown('<div class="card-box">', unsafe_allow_html=True)
    st.markdown(f"<div class='section-header'>VERIFICACIÓN DE SEGURIDAD (MFA)</div>", unsafe_allow_html=True)
    
    email_dest = st.session_state.form_data_cache.get('correo_promo')
    st.info(f"Hemos enviado un código de 6 dígitos al correo: **{email_dest}**")
    
    col_otp1, col_otp2 = st.columns([2, 1])
    with col_otp1:
        user_otp = st.text_input("Ingrese el Código Recibido", max_chars=6, placeholder="000000")
    
    if st.button("FINALIZAR Y FIRMAR DOCUMENTO ✅"):
        if user_otp == st.session_state.generated_code:
            with st.spinner("Generando documentos legales, archivando y notificando..."):
                # 1. Preparar Datos Finales
                colombia_tz = pytz.timezone('America/Bogota')
                now = datetime.now(colombia_tz)
                timestamp = now.strftime("%Y-%m-%d %H:%M:%S")
                st.session_state.form_data_cache['timestamp'] = timestamp
                
                # Identificador Único
                if st.session_state.client_type == 'juridica':
                    uid = st.session_state.form_data_cache['nit']
                    name_file = st.session_state.form_data_cache['razon_social']
                else:
                    uid = st.session_state.form_data_cache['cedula_natural']
                    name_file = st.session_state.form_data_cache['nombre_natural']
                
                doc_id = f"FER-{now.strftime('%y%m%d')}-{uid}"
                
                # 2. Generar PDF
                pdf_gen = PDFGeneratorPlatypus(st.session_state.form_data_cache, doc_id)
                pdf_path = pdf_gen.generate()
                
                # 3. Guardar en Google Sheets y Drive
                worksheet, drive, creds = get_google_services()
                
                if worksheet and drive:
                    try:
                        # Sheets Log
                        row = [
                            timestamp, doc_id, st.session_state.client_type,
                            st.session_state.form_data_cache.get('razon_social', ''), 
                            st.session_state.form_data_cache.get('nit', ''),
                            st.session_state.form_data_cache.get('nombre_natural', ''),
                            st.session_state.form_data_cache.get('cedula_natural', ''),
                            st.session_state.form_data_cache.get('correo', ''),
                            st.session_state.form_data_cache.get('celular', ''),
                            st.session_state.form_data_cache.get('ciudad', ''),
                            "FIRMADO Y VERIFICADO"
                        ]
                        worksheet.append_row(row, value_input_option='USER_ENTERED')
                        
                        # Drive Upload
                        file_metadata = {'name': f"AUTORIZACION_{doc_id}_{name_file}.pdf", 'parents': [st.secrets["drive_folder_id"]]}
                        media = MediaFileUpload(pdf_path, mimetype='application/pdf')
                        file = drive.files().create(body=file_metadata, media_body=media, fields='id, webViewLink').execute()
                        st.session_state.final_link = file.get('webViewLink')
                        
                        # 4. Email Final con PDF
                        html_final = f"""
                        <div style="font-family: Arial; padding: 20px; border: 1px solid #ddd;">
                            <h2 style="color: #003399;">Proceso Exitoso</h2>
                            <p>Estimado Cliente,</p>
                            <p>Ferreinox S.A.S. BIC certifica que se ha recibido correctamente su autorización de tratamiento de datos.</p>
                            <ul>
                                <li><b>ID Transacción:</b> {doc_id}</li>
                                <li><b>Fecha:</b> {timestamp}</li>
                            </ul>
                            <p>Adjunto encontrará el documento PDF firmado digitalmente para sus archivos.</p>
                            <p>Atentamente,<br><b>Equipo de Gestión Documental<br>Ferreinox S.A.S. BIC</b></p>
                        </div>
                        """
                        send_email_func(st.session_state.form_data_cache['correo_promo'], f"Confirmación Vinculación - {name_file}", html_final, pdf_path, f"Autorizacion_{doc_id}.pdf")
                        
                        st.session_state.step = 5
                        st.rerun()
                        
                    except Exception as e:
                        st.error(f"Error crítico guardando datos: {e}")
                else:
                    st.error("No se pudo conectar a la base de datos de Google.")
        else:
            st.error("❌ Código incorrecto. Verifique su correo.")
            
    st.markdown('</div>', unsafe_allow_html=True)

# --- PANTALLA 5: ÉXITO ---
elif st.session_state.step == 5:
    st.balloons()
    st.markdown("""
    <div class="card-box" style="text-align: center;">
        <div style="color: green; font-size: 60px;">✅</div>
        <h2 style="color: #003399;">¡Proceso Finalizado con Éxito!</h2>
        <p>Sus datos han sido actualizados y el documento legal ha sido generado, firmado y archivado en nuestros sistemas seguros.</p>
        <p>Hemos enviado una copia del contrato a su correo electrónico.</p>
    </div>
    """, unsafe_allow_html=True)
    
    if st.session_state.final_link:
        st.markdown(f"""
        <div style="text-align: center; margin-bottom: 20px;">
            <a href="{st.session_state.final_link}" target="_blank" style="background-color: #003399; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px; font-weight: bold;">
                👁️ Ver Documento PDF Generado
            </a>
        </div>
        """, unsafe_allow_html=True)
        
    if st.button("Realizar otra actualización"):
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.rerun()