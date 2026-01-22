# -*- coding: utf-8 -*-
# =================================================================================================
# PLATAFORMA CORPORATIVA DE ACTUALIZACIÓN DE DATOS - FERREINOX S.A.S. BIC
# Versión: 21.0 (Corrección de Renderizado HTML + Política Legal Ampliada)
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

# --- ReportLab Imports (Para generar el PDF) ---
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
COLOR_BG = "#F0F2F6"            # Gris Muy Claro (Fondo)
COLOR_TEXT = "#212121"          # Texto Oscuro

# --- Inyección de CSS Avanzado ---
st.markdown(f"""
<style>
    /* Importar fuente profesional */
    @import url('https://fonts.googleapis.com/css2?family=Roboto:wght@300;400;500;700&display=swap');
    
    html, body, [class*="css"] {{
        font-family: 'Roboto', sans-serif;
        background-color: {COLOR_BG};
        color: {COLOR_TEXT};
    }}
    
    /* Ocultar elementos nativos de Streamlit */
    #MainMenu {{visibility: hidden;}}
    footer {{visibility: hidden;}}
    header {{visibility: hidden;}}
    div[data-testid="stSidebarNav"] {{display: none;}}

    /* Encabezado Personalizado */
    .header-container {{
        background: linear-gradient(135deg, {COLOR_PRIMARY} 0%, {COLOR_SECONDARY} 100%);
        padding: 2.5rem 1rem;
        border-radius: 0 0 15px 15px;
        margin-bottom: 2rem;
        text-align: center;
        color: white;
        box-shadow: 0 4px 10px rgba(0,0,0,0.15);
    }}
    .header-title {{
        font-size: 2.5rem;
        font-weight: 700;
        margin-bottom: 0.5rem;
        text-transform: uppercase;
        letter-spacing: 1.5px;
    }}
    .header-subtitle {{
        font-size: 1.1rem;
        font-weight: 300;
        opacity: 0.95;
    }}

    /* Contenedores tipo Tarjeta */
    .stForm, div[data-testid="stVerticalBlock"] > div.element-container {{
        background-color: transparent;
    }}
    
    .card-box {{
        background-color: white;
        padding: 2.5rem;
        border-radius: 12px;
        box-shadow: 0 2px 15px rgba(0,0,0,0.08);
        margin-bottom: 1.5rem;
        border-top: 6px solid {COLOR_PRIMARY};
    }}

    /* Barra de Progreso (Fixed) */
    .progress-wrapper {{
        display: flex;
        justify-content: space-between;
        margin-bottom: 2rem;
        position: relative;
        padding: 0 20px;
    }}
    .progress-step {{
        text-align: center;
        position: relative;
        z-index: 2;
        flex: 1;
    }}
    .step-circle {{
        width: 45px;
        height: 45px;
        border-radius: 50%;
        background-color: #E0E0E0;
        color: #757575;
        display: flex;
        align-items: center;
        justify-content: center;
        margin: 0 auto 8px auto;
        font-weight: bold;
        transition: all 0.3s ease;
        border: 3px solid #fff;
        box-shadow: 0 2px 5px rgba(0,0,0,0.1);
    }}
    .step-label {{
        font-size: 0.85rem;
        font-weight: 500;
        color: #757575;
    }}
    
    /* Estado Activo */
    .active .step-circle {{
        background-color: {COLOR_PRIMARY};
        color: white;
        transform: scale(1.1);
        box-shadow: 0 4px 8px rgba(13, 71, 161, 0.4);
    }}
    .active .step-label {{
        color: {COLOR_PRIMARY};
        font-weight: 700;
    }}

    /* Estilo para Inputs */
    div[data-baseweb="input"] > div {{
        border-radius: 6px;
        background-color: #FAFAFA;
        border: 1px solid #E0E0E0;
    }}
    div[data-baseweb="input"] > div:focus-within {{
        border-color: {COLOR_PRIMARY};
        background-color: #FFFFFF;
        box-shadow: 0 0 0 1px {COLOR_PRIMARY};
    }}
    
    /* Botones */
    .stButton>button {{
        width: 100%;
        border-radius: 6px;
        border: none;
        background-color: {COLOR_PRIMARY};
        color: white;
        font-weight: 600;
        padding: 0.75rem 1rem;
        font-size: 1rem;
        transition: all 0.2s;
        text-transform: uppercase;
    }}
    .stButton>button:hover {{
        background-color: {COLOR_SECONDARY};
        box-shadow: 0 4px 12px rgba(0,0,0,0.2);
        transform: translateY(-1px);
        color: white;
    }}

    /* Caja Legal con Scroll */
    .legal-scroll-box {{
        height: 350px;
        overflow-y: auto;
        background-color: #f8f9fa;
        border: 1px solid #e9ecef;
        padding: 20px;
        border-radius: 8px;
        font-size: 0.9rem;
        line-height: 1.6;
        text-align: justify;
        color: #495057;
        margin-bottom: 20px;
    }}
    .legal-scroll-box h4 {{
        color: {COLOR_PRIMARY};
        margin-top: 15px;
        margin-bottom: 10px;
        font-size: 1rem;
    }}
    .legal-scroll-box ul {{
        padding-left: 20px;
    }}
    
    /* Títulos de Sección dentro de Cards */
    .section-title {{
        color: {COLOR_PRIMARY};
        font-size: 1.4rem;
        font-weight: 700;
        margin-bottom: 20px;
        padding-bottom: 10px;
        border-bottom: 2px solid #f0f0f0;
    }}

</style>
""", unsafe_allow_html=True)

# =================================================================================================
# 2. SISTEMA DE GENERACIÓN DE PDF Y EMAILS
# =================================================================================================

class PDFGeneratorPlatypus:
    def __init__(self, data, doc_id):
        self.data = data
        self.doc_id = doc_id
        self.story = []
        
        styles = getSampleStyleSheet()
        self.style_body = ParagraphStyle(name='Body', parent=styles['Normal'], fontName='Helvetica', fontSize=9, alignment=TA_JUSTIFY, leading=13)
        self.style_body_bold = ParagraphStyle(name='BodyBold', parent=self.style_body, fontName='Helvetica-Bold')
        self.style_header_title = ParagraphStyle(name='HeaderTitle', parent=styles['h1'], fontName='Helvetica-Bold', fontSize=14, alignment=TA_RIGHT, textColor=colors.HexColor(COLOR_PRIMARY))
        self.style_header_info = ParagraphStyle(name='HeaderInfo', parent=styles['Normal'], fontName='Helvetica', fontSize=8, alignment=TA_RIGHT, textColor=colors.gray)
        self.style_section_title = ParagraphStyle(name='SectionTitle', parent=styles['h2'], fontName='Helvetica-Bold', fontSize=11, alignment=TA_LEFT, textColor=colors.white, spaceBefore=10, spaceAfter=6, leftIndent=5)
        self.style_table_header = ParagraphStyle(name='TableHeader', parent=styles['Normal'], fontName='Helvetica-Bold', fontSize=8, textColor=colors.HexColor("#333333"))
        
    def _on_page(self, canvas, doc):
        canvas.saveState()
        # Header
        try:
            logo = PlatypusImage('LOGO FERREINOX SAS BIC 2024.png', width=2.2*inch, height=0.7*inch, hAlign='LEFT')
        except:
            logo = Paragraph("<b>FERREINOX S.A.S. BIC</b>", self.style_body_bold)
            
        header_data = [[logo, [Paragraph("AUTORIZACIÓN TRATAMIENTO DE DATOS", self.style_header_title), Paragraph(f"Ref: {self.doc_id}<br/>Fecha: {self.data.get('timestamp')}", self.style_header_info)]]]
        t = Table(header_data, colWidths=[3.5*inch, 3.5*inch])
        t.setStyle(TableStyle([('VALIGN', (0,0), (-1,-1), 'TOP'), ('ALIGN', (1,0), (1,0), 'RIGHT')]))
        w, h = t.wrap(doc.width, doc.topMargin)
        t.drawOn(canvas, doc.leftMargin, doc.height + doc.topMargin - h)
        
        # Linea
        canvas.setStrokeColor(colors.HexColor(COLOR_PRIMARY))
        canvas.setLineWidth(2)
        canvas.line(doc.leftMargin, doc.height + doc.topMargin - h - 10, doc.leftMargin + doc.width, doc.height + doc.topMargin - h - 10)
        
        # Footer
        canvas.setFont("Helvetica", 7)
        canvas.setFillColor(colors.gray)
        canvas.drawCentredString(doc.width/2 + doc.leftMargin, 0.5*inch, "Ferreinox S.A.S. BIC | NIT. 800.224.617-8 | Pereira, Colombia | www.ferreinox.co")
        canvas.drawRightString(doc.width + doc.leftMargin, 0.5*inch, f"Página {doc.page}")
        canvas.restoreState()

    def _create_section(self, title, doc):
        t = Table([[Paragraph(title.upper(), self.style_section_title)]], colWidths=[doc.width])
        t.setStyle(TableStyle([('BACKGROUND', (0,0), (-1,-1), colors.HexColor(COLOR_PRIMARY)), ('TOPPADDING', (0,0), (-1,-1), 3), ('BOTTOMPADDING', (0,0), (-1,-1), 3)]))
        return t

    def _add_legal_text(self, nombre, id_num, tipo_cli):
        self.story.append(Paragraph(f"Yo, <b>{nombre}</b>, identificado(a) con C.C./NIT <b>{id_num}</b>, actuando en nombre propio o en representación legal de la entidad citada en este documento (en adelante 'EL TITULAR'), autorizo de manera previa, expresa e informada a <b>FERREINOX S.A.S. BIC</b>:", self.style_body))
        self.story.append(Spacer(1, 0.1*inch))
        
        clauses = [
            "<b>1. TRATAMIENTO DE DATOS (LEY 1581 DE 2012):</b> Recolectar, almacenar, usar y circular mis datos personales para fines comerciales, contables, logísticos y de mercadeo. Conozco que tengo derecho a conocer, actualizar, rectificar y suprimir mis datos, así como a revocar esta autorización.",
            "<b>2. CONSULTA EN CENTRALES DE RIESGO (LEY 1266 DE 2008):</b> Consultar, reportar y procesar mi comportamiento crediticio, financiero y comercial ante centrales de riesgo (Datacrédito, Cifin, Procrédito, etc.) con fines de análisis de riesgo crediticio.",
            "<b>3. FACTURACIÓN ELECTRÓNICA:</b> Autorizo el envío de facturas electrónicas y notas crédito/débito al correo electrónico suministrado en este formulario, dándolo por notificado conforme al Decreto 2242 de 2015.",
            "<b>4. DECLARACIÓN DE ORIGEN DE FONDOS:</b> Declaro que los recursos de mi actividad provienen de actividades lícitas y no tienen relación con lavado de activos o financiación del terrorismo."
        ]
        
        for c in clauses:
            self.story.append(Paragraph(c, self.style_body))
            self.story.append(Spacer(1, 0.08*inch))

    def generate(self):
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as f:
            path = f.name
            
        doc = BaseDocTemplate(path, pagesize=letter, leftMargin=0.8*inch, rightMargin=0.8*inch, topMargin=1.5*inch, bottomMargin=1*inch)
        frame = Frame(doc.leftMargin, doc.bottomMargin, doc.width, doc.height, id='normal')
        doc.addPageTemplates([PageTemplate(id='main', frames=[frame], onPage=self._on_page)])
        
        # Section 1: Data
        self.story.append(self._create_section("I. Información del Titular", doc))
        self.story.append(Spacer(1, 0.15*inch))
        
        if self.data['client_type'] == 'juridica':
            d = [
                [Paragraph("Razón Social:", self.style_table_header), Paragraph(self.data.get('razon_social'), self.style_body), Paragraph("NIT:", self.style_table_header), Paragraph(self.data.get('nit'), self.style_body)],
                [Paragraph("Dirección:", self.style_table_header), Paragraph(self.data.get('direccion'), self.style_body), Paragraph("Ciudad:", self.style_table_header), Paragraph(self.data.get('ciudad'), self.style_body)],
                [Paragraph("Email Facturación:", self.style_table_header), Paragraph(self.data.get('correo'), self.style_body), Paragraph("Teléfono:", self.style_table_header), Paragraph(f"{self.data.get('telefono')} / {self.data.get('celular')}", self.style_body)],
                [Paragraph("Rep. Legal:", self.style_table_header), Paragraph(self.data.get('rep_legal'), self.style_body), Paragraph("C.C. Rep. Legal:", self.style_table_header), Paragraph(self.data.get('cedula_rep_legal'), self.style_body)],
            ]
            signer, id_signer = self.data['rep_legal'], self.data['nit']
        else:
            d = [
                [Paragraph("Nombre Completo:", self.style_table_header), Paragraph(self.data.get('nombre_natural'), self.style_body), Paragraph("Cédula:", self.style_table_header), Paragraph(self.data.get('cedula_natural'), self.style_body)],
                [Paragraph("Dirección:", self.style_table_header), Paragraph(self.data.get('direccion'), self.style_body), Paragraph("Ciudad:", self.style_table_header), Paragraph(self.data.get('ciudad'), self.style_body)],
                [Paragraph("Email Personal:", self.style_table_header), Paragraph(self.data.get('correo'), self.style_body), Paragraph("Celular:", self.style_table_header), Paragraph(self.data.get('telefono'), self.style_body)],
                [Paragraph("Fecha Nacimiento:", self.style_table_header), Paragraph(str(self.data.get('fecha_nacimiento')), self.style_body), "", ""]
            ]
            signer, id_signer = self.data['nombre_natural'], self.data['cedula_natural']
            
        t_data = Table(d, colWidths=[1.2*inch, 2.3*inch, 1.2*inch, 2.2*inch])
        t_data.setStyle(TableStyle([('GRID', (0,0), (-1,-1), 0.5, colors.lightgrey), ('BACKGROUND', (0,0), (0,-1), colors.whitesmoke), ('BACKGROUND', (2,0), (2,-1), colors.whitesmoke), ('VALIGN', (0,0), (-1,-1), 'MIDDLE'), ('PADDING', (0,0), (-1,-1), 5)]))
        self.story.append(t_data)
        
        self.story.append(Spacer(1, 0.3*inch))
        
        # Section 2: Legal
        self.story.append(self._create_section("II. Autorizaciones Legales", doc))
        self.story.append(Spacer(1, 0.15*inch))
        self._add_legal_text(signer, id_signer, self.data['client_type'])
        
        # Section 3: Signature
        self.story.append(Spacer(1, 0.3*inch))
        self.story.append(self._create_section("III. Firma Electrónica", doc))
        self.story.append(Spacer(1, 0.2*inch))
        
        # Process Image
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
            
            sig_img = PlatypusImage(img_temp, width=2.5*inch, height=1*inch)
            sig_text = f"<b>Firmado Digitalmente por:</b><br/>{signer}<br/>ID: {id_signer}<br/>Fecha: {self.data['timestamp']}<br/>Hash: {self.doc_id}<br/><i>Validado vía Token OTP</i>"
            
            t_sig = Table([[sig_img, Paragraph(sig_text, self.style_body)]], colWidths=[2.6*inch, 4*inch])
            t_sig.setStyle(TableStyle([('VALIGN', (0,0), (-1,-1), 'CENTER'), ('BOX', (0,0), (0,0), 0.5, colors.black)]))
            self.story.append(t_sig)
            
        except Exception:
            self.story.append(Paragraph("Error procesando imagen de firma.", self.style_body))
        
        self.story.append(Spacer(1, 0.2*inch))
        self.story.append(Paragraph("Este documento cumple con los requisitos de validez de la Ley 527 de 1999 de Comercio Electrónico.", ParagraphStyle('Tiny', parent=self.style_body, fontSize=7, alignment=TA_CENTER)))
        
        try:
            doc.build(self.story)
            return path
        finally:
            if img_temp and os.path.exists(img_temp): os.unlink(img_temp)

# =================================================================================================
# 3. LÓGICA DE APLICACIÓN
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

# --- FUNCIÓN CORREGIDA PARA LA BARRA DE PROGRESO ---
def render_progress():
    s = st.session_state.step
    # Definimos las clases 'active' basadas en el paso actual
    c1 = "active" if s >= 1 else ""
    c2 = "active" if s >= 2 else ""
    c3 = "active" if s >= 3 else ""
    c4 = "active" if s >= 4 else ""
    
    # HTML Sólido sin roturas
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

def send_email(to, subject, html, pdf=None, pdf_name=None):
    try:
        creds = st.secrets["email_credentials"]
        msg = MIMEMultipart()
        msg['From'] = f"Legal Ferreinox <{creds['smtp_user']}>"
        msg['To'] = to
        msg['Subject'] = subject
        msg.attach(MIMEText(html, 'html'))
        
        if pdf:
            with open(pdf, "rb") as f:
                att = MIMEApplication(f.read(), Name=pdf_name)
            att['Content-Disposition'] = f'attachment; filename="{pdf_name}"'
            msg.attach(att)
            
        ctx = smtplib.ssl.create_default_context()
        with smtplib.SMTP_SSL(creds['smtp_server'], int(creds['smtp_port']), context=ctx) as server:
            server.login(creds['smtp_user'], creds['smtp_password'])
            server.send_message(msg)
        return True
    except Exception as e:
        st.error(f"Error enviando correo: {e}")
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
    st.markdown('<div class="section-title">POLÍTICA DE TRATAMIENTO DE DATOS PERSONALES</div>', unsafe_allow_html=True)
    
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
            <li>Presentar quejas ante la Superintendencia de Industria y Comercio (SIC) por infracciones a lo dispuesto en la ley.</li>
            <li>Revocar la autorización y/o solicitar la supresión del dato cuando no se respeten los principios constitucionales.</li>
        </ul>

        <h4>3. NOTIFICACIONES Y MEDIOS ELECTRÓNICOS</h4>
        <p>El titular autoriza expresamente a FERREINOX S.A.S. BIC para que le notifique cualquier información relacionada con el estado de su crédito o mora previo al reporte negativo en centrales de riesgo al correo electrónico y celular suministrados en este formulario.</p>
        
        <p>Para conocer nuestra Política de Privacidad completa, visite <a href="https://www.ferreinox.co" target="_blank">www.ferreinox.co</a>.</p>
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
    if st.button("‹ Volver", type="secondary"):
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
                <div style='background:#f4f4f4; padding:20px; font-family:Arial;'>
                    <div style='background:#fff; padding:20px; border-radius:10px; border-top:5px solid {COLOR_PRIMARY};'>
                        <h2 style='color:{COLOR_PRIMARY};'>Código de Seguridad</h2>
                        <p>Para firmar digitalmente el documento de vinculación con Ferreinox S.A.S. BIC, utilice el siguiente código:</p>
                        <h1 style='letter-spacing:5px; text-align:center;'>{otp}</h1>
                        <p style='font-size:12px; color:gray;'>Este código expira en 10 minutos.</p>
                    </div>
                </div>
                """
                with st.spinner("Enviando código de verificación..."):
                    if send_email(correo, "Código de Verificación - Ferreinox", html_otp):
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
            with st.spinner("Generando contrato, firmando digitalmente y archivando..."):
                # Preparar Datos
                tz = pytz.timezone('America/Bogota')
                ts = datetime.now(tz).strftime("%Y-%m-%d %H:%M:%S")
                st.session_state.form_data['timestamp'] = ts
                
                uid = st.session_state.form_data['nit'] if st.session_state.client_type == 'juridica' else st.session_state.form_data['cedula_natural']
                doc_id = f"FER-{datetime.now().strftime('%Y%m%d%H%M')}-{uid}"
                
                # Generar PDF
                gen = PDFGeneratorPlatypus(st.session_state.form_data, doc_id)
                pdf_path = gen.generate()
                
                # Guardar Google Sheets / Drive
                sheet, drive = get_services()
                if sheet and drive:
                    try:
                        # Sheets
                        row = [ts, doc_id, st.session_state.client_type, 
                               st.session_state.form_data.get('razon_social'), st.session_state.form_data.get('nit'),
                               st.session_state.form_data.get('nombre_natural'), st.session_state.form_data.get('cedula_natural'),
                               st.session_state.form_data.get('correo'), st.session_state.form_data.get('celular'),
                               "AUTORIZADO Y FIRMADO"]
                        sheet.append_row(row)
                        
                        # Drive
                        meta = {'name': f"AUTORIZACION_{doc_id}.pdf", 'parents': [st.secrets["drive_folder_id"]]}
                        media = MediaFileUpload(pdf_path, mimetype='application/pdf')
                        f = drive.files().create(body=meta, media_body=media, fields='webViewLink').execute()
                        st.session_state.final_url = f.get('webViewLink')
                        
                        # Email Final
                        html_end = f"""
                        <div style='font-family:Arial; color:#333;'>
                            <h2 style='color:{COLOR_PRIMARY};'>Proceso Exitoso</h2>
                            <p>Ferreinox S.A.S. BIC confirma la recepción de su autorización de datos.</p>
                            <ul>
                                <li><b>ID Radicado:</b> {doc_id}</li>
                                <li><b>Fecha:</b> {ts}</li>
                            </ul>
                            <p>Adjunto encontrará el PDF firmado para su archivo.</p>
                        </div>
                        """
                        send_email(email_dest, "Confirmación Vinculación - Ferreinox", html_end, pdf_path, f"Autorizacion_{doc_id}.pdf")
                        
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
        <h1 style="color: green; font-size: 4rem;">✅</h1>
        <h2 style="color: {COLOR_PRIMARY};">¡Proceso Completado!</h2>
        <p>Sus datos han sido actualizados exitosamente en la base de datos de Ferreinox S.A.S. BIC.</p>
        <p>Hemos enviado una copia del documento legal a su correo electrónico.</p>
        <br>
        <a href="{st.session_state.final_url}" target="_blank" style="background:{COLOR_PRIMARY}; color:white; padding:10px 20px; text-decoration:none; border-radius:5px; font-weight:bold;">VER DOCUMENTO PDF</a>
        <br><br>
    </div>
    """, unsafe_allow_html=True)
    
    if st.button("Volver al Inicio"):
        for k in st.session_state.keys():
            del st.session_state[k]
        st.rerun()