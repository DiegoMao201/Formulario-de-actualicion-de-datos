# -*- coding: utf-8 -*-
# =================================================================================================
# APLICACIÓN INSTITUCIONAL DE VINCULACIÓN DE CLIENTES - FERREINOX S.A.S. BIC
# Versión 19.1 (Corrección de Parser de ReportLab y Construcción Robusta de PDF)
# Fecha: 10 de Octubre de 2025
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

from reportlab.platypus import BaseDocTemplate, PageTemplate, Frame, Paragraph, Spacer, Table, TableStyle, Image as PlatypusImage, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_LEFT, TA_RIGHT
from reportlab.lib import colors
from reportlab.lib.units import inch, cm
from reportlab.lib.pagesizes import letter

from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication

st.set_page_config(page_title="Portal de Vinculación | Ferreinox", page_icon="✍️", layout="wide")

# --- Institutional Colors ---
FERREINOX_DARK_BLUE = "#0D47A1"
FERREINOX_ACCENT_BLUE = "#1565C0"
FERREINOX_LIGHT_BG = "#F0F2F6"
FERREINOX_YELLOW_ACCENT = "#FBC02D"
FERREINOX_GREY = "#424242"

st.markdown(f"""
<style>
    .main {{ background-color: {FERREINOX_LIGHT_BG}; }}
    .block-container {{ padding-top: 2rem; padding-bottom: 2rem; }}
    h1, h2, h3, h4 {{ color: {FERREINOX_DARK_BLUE}; }}
    .stButton>button {{
        border-radius: 8px; border: 2px solid {FERREINOX_DARK_BLUE}; background-color: {FERREINOX_ACCENT_BLUE};
        color: white; font-weight: bold; transition: all 0.3s;
    }}
    .stButton>button:hover {{ background-color: {FERREINOX_DARK_BLUE}; }}
    /* Ocultar la barra de navegación de Streamlit para esta página pública */
    div[data-testid="stSidebarNav"] {{
        display: none;
    }}
</style>
""", unsafe_allow_html=True)


# =================================================================================================
# --- SECCIÓN DE GENERACIÓN DE PDF MEJORADA ---
# =================================================================================================

class PDFGeneratorPlatypus:
    def __init__(self, data, doc_id):
        self.data = data
        self.doc_id = doc_id
        self.story = []
        
        # --- ESTILOS PROFESIONALES ---
        styles = getSampleStyleSheet()
        self.style_body = ParagraphStyle(name='Body', parent=styles['Normal'], fontName='Helvetica', fontSize=9, alignment=TA_JUSTIFY, leading=14)
        self.style_body_bold = ParagraphStyle(name='BodyBold', parent=self.style_body, fontName='Helvetica-Bold')
        self.style_bullet = ParagraphStyle(name='Bullet', parent=self.style_body, leftIndent=20, firstLineIndent=0)
        self.style_header_title = ParagraphStyle(name='HeaderTitle', parent=styles['h1'], fontName='Helvetica-Bold', fontSize=14, alignment=TA_RIGHT, textColor=colors.HexColor(FERREINOX_DARK_BLUE))
        self.style_header_info = ParagraphStyle(name='HeaderInfo', parent=styles['Normal'], fontName='Helvetica', fontSize=8, alignment=TA_RIGHT, textColor=colors.HexColor(FERREINOX_GREY))
        self.style_footer = ParagraphStyle(name='Footer', parent=styles['Normal'], fontName='Helvetica', fontSize=8, alignment=TA_CENTER, textColor=colors.HexColor(FERREINOX_GREY))
        self.style_section_title = ParagraphStyle(name='SectionTitle', parent=styles['h2'], fontName='Helvetica-Bold', fontSize=12, alignment=TA_LEFT, textColor=colors.white, spaceBefore=12, spaceAfter=6, leftIndent=10)
        self.style_table_header = ParagraphStyle(name='TableHeader', parent=styles['Normal'], fontName='Helvetica-Bold', fontSize=9, textColor=colors.HexColor(FERREINOX_GREY), alignment=TA_LEFT)
        self.style_signature_info = ParagraphStyle(name='SignatureInfo', parent=styles['Normal'], fontName='Helvetica', fontSize=9, alignment=TA_LEFT, leading=14)

    def _on_page(self, canvas, doc):
        canvas.saveState()
        # --- ENCABEZADO MEJORADO ---
        try:
            logo = PlatypusImage('LOGO FERREINOX SAS BIC 2024.png', width=2.5*inch, height=0.8*inch, hAlign='LEFT')
        except Exception:
            logo = Paragraph("Ferreinox S.A.S. BIC", self.style_body_bold)
        
        header_title_text = "<b>AUTORIZACIÓN PARA EL TRATAMIENTO DE DATOS</b>"
        header_info_text = f"ID Documento: {self.doc_id}<br/>Fecha Generación: {self.data.get('timestamp', '')}"
        
        header_content = [
            [logo, [Paragraph(header_title_text, self.style_header_title), Spacer(1, 4), Paragraph(header_info_text, self.style_header_info)]]
        ]
        
        header_table = Table(header_content, colWidths=[3.0*inch, 4.2*inch], hAlign='LEFT')
        header_table.setStyle(TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('ALIGN', (1, 0), (1, 0), 'RIGHT'),
            ('LEFTPADDING', (0,0), (-1,-1), 0),
            ('RIGHTPADDING', (0,0), (-1,-1), 0)
        ]))
        
        w, h = header_table.wrap(doc.width, doc.topMargin)
        header_table.drawOn(canvas, doc.leftMargin, doc.height + doc.topMargin - h + 15)
        
        canvas.setStrokeColor(colors.HexColor(FERREINOX_DARK_BLUE))
        canvas.setLineWidth(2)
        canvas.line(doc.leftMargin, doc.height + doc.topMargin - h, doc.leftMargin + doc.width, doc.height + doc.topMargin - h)
        
        # --- PIE DE PÁGINA PROFESIONAL ---
        footer_text = "Ferreinox S.A.S. BIC | NIT. 800.224.617-8 | www.ferreinox.co | Pereira, Colombia"
        footer_page_num = f"Página {doc.page}"
        
        footer_content = [[Paragraph(footer_text, self.style_footer), Paragraph(footer_page_num, self.style_footer)]]
        footer_table = Table(footer_content, colWidths=[doc.width/2, doc.width/2])
        footer_table.setStyle(TableStyle([
            ('ALIGN', (0,0), (0,0), 'LEFT'),
            ('ALIGN', (1,0), (1,0), 'RIGHT'),
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE')
        ]))
        
        w, h = footer_table.wrap(doc.width, doc.bottomMargin)
        footer_table.drawOn(canvas, doc.leftMargin, h - 10)
        
        canvas.restoreState()

    # --- CORRECCIÓN ---
    # Se agrega el parámetro 'doc' para que el método tenga acceso a sus propiedades.
    def _create_section_header(self, title, doc):
        header_table = Table([[Paragraph(title, self.style_section_title)]], colWidths=[doc.width], hAlign='LEFT')
        header_table.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,-1), colors.HexColor(FERREINOX_DARK_BLUE)),
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
            ('TOPPADDING', (0,0), (-1,-1), 4),
            ('BOTTOMPADDING', (0,0), (-1,-1), 4)
        ]))
        return header_table

    # =============================================================================================
    # --- CORRECCIÓN CRÍTICA: Construcción Robusta de Textos Legales ---
    # En lugar de un gran bloque HTML, se construyen párrafos individuales.
    # =============================================================================================
    def _add_legal_authorizations(self, nombre_firmante, razon_social, nit_o_cc, email_facturacion):
        self.story.append(Paragraph(
            f"Yo, <b>{nombre_firmante}</b>, mayor de edad, identificado(a) como aparece al pie de mi firma, actuando en nombre propio y/o en calidad de Representante Legal de la entidad <b>{razon_social}</b>, identificada con NIT/C.C. No. <b>{nit_o_cc}</b> (en adelante \"EL TITULAR\"), mediante la suscripción del presente documento identificado con el ID Único <b>{self.doc_id}</b>, declaro de manera libre, expresa, inequívoca e informada, que otorgo mi consentimiento previo y autorizo a <b>FERREINOX S.A.S. BIC</b>, sociedad identificada con NIT. 800.224.617-8 (en adelante \"LA EMPRESA\"), para el tratamiento de mis datos personales y los de la entidad que represento, en conformidad con la Ley Estatutaria 1581 de 2012, la Ley 1266 de 2008 y demás normas concordantes.",
            self.style_body
        ))
        self.story.append(Spacer(1, 0.2*inch))
        
        self.story.append(Paragraph("<b>PRIMERO: AUTORIZACIÓN PARA EL TRATAMIENTO DE DATOS PERSONALES (LEY 1581 DE 2012).</b>", self.style_body))
        self.story.append(Paragraph("Manifiesto que he sido informado(a) de manera clara y comprensible sobre lo siguiente:", self.style_body))
        self.story.append(Spacer(1, 0.1*inch))
        
        self.story.append(Paragraph("<b>1. Finalidades del Tratamiento:</b> LA EMPRESA tratará mis datos personales para las siguientes finalidades:", self.style_body))
        self.story.append(Paragraph("• <b>a. Gestión Comercial y de Relacionamiento:</b> Ejecutar la relación comercial existente, incluyendo la gestión de cotizaciones, pedidos, despachos, y servicio postventa.", self.style_bullet))
        self.story.append(Paragraph("• <b>b. Gestión de Facturación y Cartera:</b> Generar, enviar, y gestionar facturas electrónicas y documentos equivalentes; realizar actividades de gestión de cobro y recuperación de cartera.", self.style_bullet))
        self.story.append(Paragraph("• <b>c. Fines de Mercadeo y Publicidad:</b> Enviar información sobre productos, servicios, ofertas, promociones, eventos, campañas de fidelización y novedades de LA EMPRESA a través de medios físicos y digitales (correo electrónico, SMS, WhatsApp, etc.).", self.style_bullet))
        self.story.append(Paragraph("• <b>d. Fines Administrativos y Estadísticos:</b> Realizar análisis estadísticos internos, reportes, encuestas de satisfacción, y cumplir con las obligaciones legales y regulatorias a las que LA EMPRESA está sujeta.", self.style_bullet))
        self.story.append(Paragraph("• <b>e. Seguridad y Control:</b> Garantizar la seguridad de las transacciones y prevenir el fraude.", self.style_bullet))
        self.story.append(Spacer(1, 0.1*inch))

        self.story.append(Paragraph("<b>2. Derechos del Titular:</b> Conozco que como titular de la información, me asisten los derechos consagrados en el artículo 8 de la Ley 1581 de 2012, en especial:", self.style_body))
        self.story.append(Paragraph("• <b>a.</b> Conocer, actualizar y rectificar mis datos personales.", self.style_bullet))
        self.story.append(Paragraph("• <b>b.</b> Solicitar prueba de la autorización otorgada.", self.style_bullet))
        self.story.append(Paragraph("• <b>c.</b> Ser informado sobre el uso que se le ha dado a mis datos.", self.style_bullet))
        self.story.append(Paragraph("• <b>d.</b> Presentar quejas ante la Superintendencia de Industria y Comercio por infracciones a la ley.", self.style_bullet))
        self.story.append(Paragraph("• <b>e.</b> Revocar la autorización y/o solicitar la supresión del dato cuando no se respeten los principios, derechos y garantías constitucionales y legales.", self.style_bullet))
        self.story.append(Paragraph("• <b>f.</b> Acceder en forma gratuita a mis datos personales objeto de tratamiento.", self.style_bullet))
        self.story.append(Spacer(1, 0.1*inch))
        
        self.story.append(Paragraph("<b>3. Política de Tratamiento:</b> Declaro conocer que la Política de Tratamiento de Datos Personales de LA EMPRESA está disponible para mi consulta en sus instalaciones y en el sitio web www.ferreinox.co.", self.style_body))
        self.story.append(Spacer(1, 0.2*inch))
        
        self.story.append(Paragraph("<b>SEGUNDO: AUTORIZACIÓN PARA CONSULTA, REPORTE Y ADMINISTRACIÓN DE INFORMACIÓN FINANCIERA Y CREDITICIA (HÁBEAS DATA - LEY 1266 DE 2008).</b>", self.style_body))
        self.story.append(Paragraph("Autorizo de manera expresa e irrevocable a LA EMPRESA, o a quien en el futuro ostente la calidad de acreedor, para:", self.style_body))
        self.story.append(Paragraph("• <b>a.</b> Consultar, en cualquier tiempo, en las centrales de riesgo (como CIFIN, DATACRÉDITO, u otras) y cualquier otra base de datos de contenido comercial o de servicios, toda la información relevante para conocer mi desempeño como deudor, mi capacidad de pago, o para valorar el riesgo futuro de concederme crédito.", self.style_bullet))
        self.story.append(Paragraph("• <b>b.</b> Reportar a las centrales de riesgo y a cualquier otra base de datos autorizada, datos sobre el cumplimiento o incumplimiento de mis obligaciones crediticias y comerciales, así como mis datos de contacto e información personal relevante.", self.style_bullet))
        self.story.append(Paragraph("• <b>c.</b> Suministrar a las centrales de riesgo datos relativos a mis solicitudes de crédito, así como otros atinentes a mis relaciones comerciales, financieras y de servicios.", self.style_bullet))
        self.story.append(Spacer(1, 0.1*inch))
        
        self.story.append(Paragraph(f"<b>Notificación Previa al Reporte Negativo:</b> De conformidad con el artículo 12 de la Ley 1266 de 2008 y el Decreto 2952 de 2010, autorizo expresamente que la comunicación previa al reporte negativo por mora en mis obligaciones se realice a través de un mensaje de datos enviado al correo electrónico de facturación suministrado en este formulario, es decir: <b>{email_facturacion}</b>.", self.style_body))
        self.story.append(Spacer(1, 0.2*inch))
        
        self.story.append(Paragraph("<b>TERCERO: DECLARACIÓN DE VERACIDAD Y VIGENCIA.</b>", self.style_body))
        self.story.append(Paragraph("Certifico que toda la información y datos personales suministrados en el presente formulario son veraces, completos, exactos, actualizados y comprobables. Me comprometo a mantener esta información actualizada, informando oportunamente a LA EMPRESA sobre cualquier cambio. La presente autorización se mantendrá vigente durante la totalidad del tiempo que dure la relación comercial con LA EMPRESA y con posterioridad a la finalización de la misma, para los fines legales y contractuales que correspondan.", self.style_body))

    # --- CORRECCIÓN ---
    # Se agrega el parámetro 'doc' para que este método pueda pasárselo a `_create_section_header`.
    def _add_signature_section(self, doc):
        # --- CORRECCIÓN ---
        # Se pasa el objeto 'doc' a la llamada a `_create_section_header`.
        self.story.append(self._create_section_header("IV. EVIDENCIA DE CONSENTIMIENTO ELECTRÓNICO", doc))
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
                id_firmante = f"{self.data.get('tipo_id', '')} No. {self.data.get('cedula_rep_legal', '')} de {self.data.get('lugar_exp_id', '')}"
            else:
                nombre_firmante = self.data.get('nombre_natural', '')
                id_firmante = f"{self.data.get('tipo_id', '')} No. {self.data.get('cedula_natural', '')} de {self.data.get('lugar_exp_id', '')}"
            
            fecha_firma = self.data.get('timestamp', 'No disponible')
            
            firma_texto = f"""<b>Firmado Digitalmente Por:</b><br/>
                                <b>Nombre:</b> {nombre_firmante}<br/>
                                <b>Identificación:</b> {id_firmante}<br/>
                                <b>Fecha y Hora de Firma:</b> {fecha_firma} (America/Bogota)<br/>
                                <b>Medio de Consentimiento:</b> Portal Web Ferreinox v19.1 (Verificado con código OTP)"""
            
            table_firma_content = [
                [firma_image, Paragraph(firma_texto, self.style_signature_info)],
                [Paragraph("<i>Firma Electrónica</i>", self.style_footer), '']
            ]
            
            table_firma = Table(table_firma_content, colWidths=[2.8*inch, 4.4*inch], rowHeights=[1.2*inch, 0.2*inch], hAlign='LEFT')
            table_firma.setStyle(TableStyle([
                ('VALIGN', (0,0), (0,0), 'TOP'),
                ('LEFTPADDING', (1,0), (1,0), 10),
                ('TOPPADDING', (0,0), (-1,-1), 5),
                ('ALIGN', (0,1), (0,1), 'CENTER')
            ]))
            self.story.append(table_firma)
            
            self.story.append(Spacer(1, 0.2*inch))
            self.story.append(Paragraph(
                "<i>Este documento y su firma electrónica han sido generados y custodiados por Ferreinox S.A.S. BIC, constituyendo plena prueba del consentimiento otorgado por el titular, de acuerdo con la Ley 527 de 1999 sobre comercio y firma electrónica.</i>",
                self.style_footer
            ))

            return firma_path
        except Exception as e:
            self.story.append(Paragraph(f"<b>Error crítico al procesar la firma digital:</b> {str(e)}", self.style_body))
            return None

    def generate(self):
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as temp_pdf:
            pdf_path = temp_pdf.name
        
        # Aquí se crea la variable 'doc'
        doc = BaseDocTemplate(pdf_path, pagesize=letter, leftMargin=0.8*inch, rightMargin=0.8*inch, topMargin=1.5*inch, bottomMargin=1.0*inch)
        
        frame = Frame(doc.leftMargin, doc.bottomMargin, doc.width, doc.height, id='main_frame', topPadding=0)
        template = PageTemplate(id='main_template', frames=[frame], onPage=self._on_page)
        doc.addPageTemplates([template])
        
        # --- SECCIÓN I: INFORMACIÓN DEL TITULAR ---
        # --- CORRECCIÓN ---
        # Se pasa el objeto 'doc' a la llamada a `_create_section_header`.
        self.story.append(self._create_section_header("I. INFORMACIÓN DEL TITULAR DE LOS DATOS", doc))
        self.story.append(Spacer(1, 0.2*inch))
        
        if self.data.get('client_type') == 'juridica':
            datos = [
                [Paragraph('Razón Social:', self.style_table_header), Paragraph(self.data.get('razon_social', ''), self.style_body), Paragraph('NIT:', self.style_table_header), Paragraph(self.data.get('nit', ''), self.style_body)],
                [Paragraph('Nombre Comercial:', self.style_table_header), Paragraph(self.data.get('nombre_comercial', ''), self.style_body), Paragraph('Teléfono:', self.style_table_header), Paragraph(f"{self.data.get('telefono', '')} / {self.data.get('celular', '')}", self.style_body)],
                [Paragraph('Dirección:', self.style_table_header), Paragraph(self.data.get('direccion', ''), self.style_body), Paragraph('Ciudad:', self.style_table_header), Paragraph(self.data.get('ciudad', ''), self.style_body)],
                [Paragraph('Email Facturación:', self.style_table_header), Paragraph(f"<b>{self.data.get('correo', '')}</b>", self.style_body), Paragraph('Email Notificaciones:', self.style_table_header), Paragraph(f"<b>{self.data.get('correo_promo', '')}</b>", self.style_body)],
                [Paragraph('Representante Legal:', self.style_table_header), Paragraph(self.data.get('rep_legal', ''), self.style_body), Paragraph('C.C. Rep. Legal:', self.style_table_header), Paragraph(self.data.get('cedula_rep_legal', ''), self.style_body)]
            ]
            table_basicos = Table(datos, colWidths=[1.5*inch, 2.1*inch, 1.5*inch, 2.1*inch], hAlign='LEFT')
            rep_legal_name, entity_name, entity_id, entity_email_facturacion = self.data['rep_legal'], self.data['razon_social'], self.data['nit'], self.data['correo']
        else: # Persona Natural
            datos = [
                [Paragraph('Nombre Completo:', self.style_table_header), Paragraph(self.data.get('nombre_natural', ''), self.style_body), Paragraph('Identificación:', self.style_table_header), Paragraph(self.data.get('cedula_natural', ''), self.style_body)],
                [Paragraph('Dirección:', self.style_table_header), Paragraph(self.data.get('direccion', ''), self.style_body), Paragraph('Ciudad:', self.style_table_header), Paragraph(self.data.get('ciudad', ''), self.style_body)],
                [Paragraph('Teléfono / Celular:', self.style_table_header), Paragraph(self.data.get('telefono', ''), self.style_body), Paragraph('Fecha Nacimiento:', self.style_table_header), Paragraph(self.data.get('fecha_nacimiento').strftime('%d-%b-%Y') if self.data.get('fecha_nacimiento') else "", self.style_body)],
                [Paragraph('Email Facturación:', self.style_table_header), Paragraph(f"<b>{self.data.get('correo', '')}</b>", self.style_body), Paragraph('Email Notificaciones:', self.style_table_header), Paragraph(f"<b>{self.data.get('correo_promo', '')}</b>", self.style_body)]
            ]
            table_basicos = Table(datos, colWidths=[1.5*inch, 2.1*inch, 1.5*inch, 2.1*inch], hAlign='LEFT')
            rep_legal_name, entity_name, entity_id, entity_email_facturacion = self.data['nombre_natural'], self.data['nombre_natural'], self.data['cedula_natural'], self.data['correo']
        
        table_basicos.setStyle(TableStyle([
            ('GRID', (0,0), (-1,-1), 0.5, colors.lightgrey),
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
            ('LEFTPADDING', (0,0), (-1,-1), 6),
            ('RIGHTPADDING', (0,0), (-1,-1), 6),
            ('TOPPADDING', (0,0), (-1,-1), 4),
            ('BOTTOMPADDING', (0,0), (-1,-1), 4),
            ('BACKGROUND', (0,0), (0,-1), colors.whitesmoke),
            ('BACKGROUND', (2,0), (2,-1), colors.whitesmoke),
        ]))
        self.story.append(table_basicos)
        self.story.append(PageBreak())

        # --- SECCIÓN II y III: AUTORIZACIONES LEGALES ---
        # --- CORRECCIÓN ---
        # Se pasa el objeto 'doc' a la llamada a `_create_section_header`.
        self.story.append(self._create_section_header("II & III. AUTORIZACIONES Y DECLARACIONES LEGALES", doc))
        self.story.append(Spacer(1, 0.2*inch))
        
        self._add_legal_authorizations(rep_legal_name, entity_name, entity_id, entity_email_facturacion)
        
        self.story.append(PageBreak())
        
        # --- SECCIÓN IV: FIRMA Y CONSTANCIA ---
        # --- CORRECCIÓN ---
        # Se pasa el objeto 'doc' a la llamada a `_add_signature_section`.
        firma_path = self._add_signature_section(doc)
        
        try:
            doc.build(self.story)
        finally:
            if firma_path and os.path.exists(firma_path):
                os.unlink(firma_path)
        
        return pdf_path


# =================================================================================================
# --- LÓGICA DE LA APLICACIÓN (SIN CAMBIOS) ---
# =================================================================================================

try:
    required_secrets = ["google_sheet_id", "google_credentials", "drive_folder_id", "email_credentials"]
    if not all(secret in st.secrets for secret in required_secrets):
        st.error("🚨 Error Crítico: Faltan una o más configuraciones en tus secretos de Streamlit.")
        st.stop()
        
    creds_dict = st.secrets["google_credentials"].to_dict()
    scopes = ['https://www.googleapis.com/auth/drive', 'https://www.googleapis.com/auth/spreadsheets']
    creds = Credentials.from_service_account_info(creds_dict, scopes=scopes)
    
    gc = gspread.authorize(creds)
    worksheet = gc.open_by_key(st.secrets["google_sheet_id"]).sheet1
    drive_service = build('drive', 'v3', credentials=creds)

except Exception as e:
    st.error(f"🚨 Ha ocurrido un error inesperado durante la configuración inicial de Google Services.")
    st.error(f"Detalle técnico del error: {e}")
    st.stop()

def send_email(recipient_email, subject, body, pdf_path=None, filename=None):
    try:
        creds = st.secrets["email_credentials"]
        sender_email = creds.get("smtp_user")
        sender_password = creds.get("smtp_password")
        smtp_server = creds.get("smtp_server")
        smtp_port = int(creds.get("smtp_port"))

        if not all([sender_email, sender_password, smtp_server, smtp_port]):
            st.error("🚨 Error de Configuración de Correo: Faltan credenciales completas.")
            return False

        msg = MIMEMultipart()
        msg['From'] = f"Ferreinox S.A.S. BIC <{sender_email}>"
        msg['To'] = recipient_email
        msg['Subject'] = subject
        msg.attach(MIMEText(body, 'html'))

        if pdf_path and filename:
            with open(pdf_path, "rb") as f:
                part = MIMEApplication(f.read(), Name=filename)
            part['Content-Disposition'] = f'attachment; filename="{filename}"'
            msg.attach(part)
        
        context = smtplib.ssl.create_default_context()
        with smtplib.SMTP_SSL(smtp_server, smtp_port, context=context) as server:
            server.login(sender_email, sender_password)
            server.send_message(msg)
        return True
    except smtplib.SMTPAuthenticationError:
        st.error("❌ Error de Autenticación SMTP: Las credenciales de correo son incorrectas.")
        return False
    except smtplib.SMTPException as e:
        st.error(f"❌ Error al conectar o enviar correo SMTP: {e}")
        return False
    except Exception as e:
        st.error(f"❌ Un error inesperado ocurrió al intentar enviar el correo: {e}")
        return False

try:
    st.image('LOGO FERREINOX SAS BIC 2024.png', width=300)
except Exception:
    st.image("https://placehold.co/300x100/0D47A1/FFFFFF?text=Ferreinox+S.A.S.+BIC", width=300)
st.title("Portal de Vinculación y Autorización de Datos")
st.markdown("---")

def init_session_state():
    if 'terms_accepted' not in st.session_state: st.session_state.terms_accepted = False
    if 'client_type' not in st.session_state: st.session_state.client_type = None
    if 'verification_code_sent' not in st.session_state: st.session_state.verification_code_sent = False
    if 'process_complete' not in st.session_state: st.session_state.process_complete = False
    if 'form_data_cache' not in st.session_state: st.session_state.form_data_cache = {}
    if 'generated_code' not in st.session_state: st.session_state.generated_code = ""
    if 'final_link' not in st.session_state: st.session_state.final_link = ""
    if 'final_razon_social' not in st.session_state: st.session_state.final_razon_social = ""
init_session_state()

def reset_to_terms(): st.session_state.update(terms_accepted=False, client_type=None, verification_code_sent=False)
def reset_to_selection(): st.session_state.update(client_type=None, verification_code_sent=False)
def full_reset():
    keys_to_delete = list(st.session_state.keys())
    for key in keys_to_delete:
        del st.session_state[key]
    init_session_state()
    st.rerun()

if st.session_state.process_complete:
    st.success(f"**¡Proceso Finalizado Exitosamente!**")
    st.markdown(f"El formulario para **{st.session_state.final_razon_social}** ha sido generado, archivado y enviado a su correo electrónico.")
    if st.session_state.final_link:
        st.markdown(f"Puede previsualizar el documento final aquí: [**Ver PDF Generado**]({st.session_state.final_link})")
    st.button("Realizar otra vinculación", on_click=full_reset, use_container_width=True)

elif st.session_state.verification_code_sent:
    st.header("🔐 Verificación de Firma")
    correo_notificaciones = st.session_state.form_data_cache.get('correo_promo')
    st.info(f"Hemos enviado un código de 6 dígitos a su correo: **{correo_notificaciones}**. Por favor, ingréselo para completar el proceso.")
    user_code = st.text_input("Código de Verificación", max_chars=6)
    
    if st.button("Verificar y Completar Proceso", use_container_width=True):
        if user_code == st.session_state.generated_code:
            with st.spinner("Código correcto. Finalizando proceso... ⏳"):
                form_data = st.session_state.form_data_cache
                
                colombia_tz = pytz.timezone('America/Bogota')
                now_colombia = datetime.now(colombia_tz)
                timestamp = now_colombia.strftime("%Y-%m-%d %H:%M:%S")
                form_data['timestamp'] = timestamp

                entity_id_for_doc = form_data.get('nit', form_data.get('cedula_natural'))
                doc_id = f"FER-{now_colombia.strftime('%Y%m%d%H%M%S')}-{entity_id_for_doc}"
                pdf_file_path = None
                try:
                    pdf_gen = PDFGeneratorPlatypus(form_data, doc_id)
                    pdf_file_path = pdf_gen.generate()
                    
                    try:
                        if form_data['client_type'] == 'juridica':
                            log_row = [
                                timestamp, doc_id, form_data.get('razon_social', ''), form_data.get('nit', ''),
                                form_data.get('rep_legal', ''), form_data.get('correo', ''), form_data.get('correo_promo', ''),
                                form_data.get('ciudad', ''), f"{form_data.get('telefono', '')} / {form_data.get('celular', '')}",
                                "Persona Jurídica", "Verificado y Enviado", st.session_state.generated_code,
                                form_data.get('nombre_compras', ''), form_data.get('email_compras', ''), form_data.get('celular_compras', ''),
                                form_data.get('nombre_cartera', ''), form_data.get('email_cartera', ''), form_data.get('celular_cartera', ''),
                                ""
                            ]
                        else:
                            log_row = [
                                timestamp, doc_id, form_data.get('nombre_natural', ''), form_data.get('cedula_natural', ''),
                                form_data.get('nombre_natural', ''), form_data.get('correo', ''), form_data.get('correo_promo', ''),
                                form_data.get('ciudad', ''), form_data.get('telefono', ''),
                                "Persona Natural", "Verificado y Enviado", st.session_state.generated_code,
                                "", "", "", "", "", "",
                                form_data.get('fecha_nacimiento').strftime('%Y-%m-%d') if form_data.get('fecha_nacimiento') else ""
                            ]
                        
                        worksheet.append_row(log_row, value_input_option='USER_ENTERED')
                        st.success("✅ Datos guardados exitosamente en Google Sheets.")
                    except Exception as sheet_error:
                        st.error("❌ ¡ERROR CRÍTICO AL GUARDAR EN GOOGLE SHEETS!")
                        st.error(f"Detalle técnico: {sheet_error}")

                    file_name = f"Autorizacion_{st.session_state.final_razon_social.replace(' ', '_')}_{entity_id_for_doc}.pdf"
                    email_body = f"""<h3>Confirmación de Autorización - Ferreinox S.A.S. BIC</h3><p>Estimado(a) <b>{form_data.get('rep_legal', form_data.get('nombre_natural'))}</b>,</p><p>Este correo confirma que hemos recibido y procesado exitosamente su formulario de autorización de datos.</p><p>Adjunto encontrará el documento PDF con la información y la constancia de su consentimiento.</p><p><b>ID del Documento:</b> {doc_id}<br><b>Fecha y Hora (Colombia):</b> {timestamp}</p><p>Gracias por confiar en Ferreinox S.A.S. BIC.</p>"""
                    
                    correo_notificaciones_final = form_data.get('correo_promo')
                    email_sent_successfully = send_email(correo_notificaciones_final, f"Confirmación Vinculación - {st.session_state.final_razon_social}", email_body, pdf_file_path, file_name)
                    
                    if email_sent_successfully:
                        media = MediaFileUpload(pdf_file_path, mimetype='application/pdf', resumable=True)
                        file = drive_service.files().create(body={'name': file_name, 'parents': [st.secrets["drive_folder_id"]]}, media_body=media, fields='id, webViewLink', supportsAllDrives=True).execute()
                        st.session_state.final_link = file.get('webViewLink')
                        st.session_state.process_complete = True
                        st.rerun()
                    else:
                        st.warning("El PDF fue generado, pero el correo de confirmación final no pudo ser enviado.")
                except Exception as e:
                    st.error(f"❌ ¡Ha ocurrido un error inesperado durante el procesamiento final del documento o subida a Drive!")
                    st.error(f"Detalle técnico: {e}")
                finally:
                    if pdf_file_path and os.path.exists(pdf_file_path):
                        os.unlink(pdf_file_path)
        else:
            st.error("El código ingresado es incorrecto. Por favor, intente de nuevo.")
    if st.button("‹ Llenar el formulario nuevamente"):
        st.session_state.update(verification_code_sent=False, form_data_cache={}, generated_code="")
        st.rerun()

elif not st.session_state.terms_accepted:
    st.header("📜 Términos, Condiciones y Autorizaciones")
    st.markdown("Bienvenido al portal de vinculación de Ferreinox S.A.S. BIC. A continuación, encontrará los términos y condiciones para el tratamiento de sus datos.")
    with st.expander("Haga clic aquí para leer los Términos Completos"):
        st.subheader("Autorización para Tratamiento de Datos y Consulta en Centrales (Habeas Data)")
        st.markdown("""
        Yo, <b>[Su Nombre / Rep. Legal]</b>, en calidad de representante de <b>[Su Empresa / Su Nombre]</b> con NIT/C.C. <b>[Su NIT / Cédula]</b>, autorizo a <b>FERREINOX S.A.S. BIC</b> para el tratamiento de mis datos personales conforme a la Ley 1581 de 2012 y la Ley 1266 de 2008. Esto incluye finalidades comerciales, de facturación, mercadeo, y administrativas. Así mismo, autorizo la consulta y reporte de mi información financiera y crediticia en centrales de riesgo. Manifiesto que la notificación previa al reporte negativo por mora se podrá realizar al correo electrónico de facturación: <b>[Su Correo de Facturación]</b>. Declaro que la información suministrada es veraz y conozco la política de tratamiento de datos de la empresa.
        """, unsafe_allow_html=True)
    if st.button("He leído y acepto los términos para continuar", on_click=lambda: st.session_state.update(terms_accepted=True), use_container_width=True):
        st.rerun()

elif st.session_state.client_type is None:
    st.header("👤 Selección de Tipo de Cliente")
    st.markdown("Por favor, seleccione el tipo de vinculación que desea realizar.")
    col1, col2 = st.columns(2)
    with col1:
        st.button("Soy Persona Jurídica (Empresa)", on_click=lambda: st.session_state.update(client_type='juridica'), use_container_width=True)
    with col2:
        st.button("Soy Persona Natural", on_click=lambda: st.session_state.update(client_type='natural'), use_container_width=True)
    st.button("‹ Volver a Términos y Condiciones", on_click=reset_to_terms)

else:
    form_data_to_process = None
    if st.session_state.client_type == 'juridica':
        st.button("‹ Volver a Selección de Tipo", on_click=reset_to_selection)
        with st.form(key="form_juridica"):
            st.header("📝 Formulario: Persona Jurídica")
            col1, col2 = st.columns(2)
            with col1:
                razon_social = st.text_input("Razón Social*", value=st.session_state.form_data_cache.get('razon_social', ''))
                nit = st.text_input("NIT*", value=st.session_state.form_data_cache.get('nit', ''))
                direccion = st.text_input("Dirección*", value=st.session_state.form_data_cache.get('direccion', ''))
                telefono = st.text_input("Teléfono Fijo", value=st.session_state.form_data_cache.get('telefono', ''))
                correo_promo = st.text_input("Correo para Promociones y Notificaciones del Portal*", help="A este correo enviaremos el código de verificación y la copia final del documento.", value=st.session_state.form_data_cache.get('correo_promo', ''))
            with col2:
                nombre_comercial = st.text_input("Nombre Comercial*", value=st.session_state.form_data_cache.get('nombre_comercial', ''))
                ciudad = st.text_input("Ciudad*", value=st.session_state.form_data_cache.get('ciudad', ''))
                correo = st.text_input("Correo para Facturación Electrónica*", help="Correo para recibir facturas y documentos contables.", value=st.session_state.form_data_cache.get('correo', ''))
                celular = st.text_input("Celular", value=st.session_state.form_data_cache.get('celular', ''))
            
            st.markdown("---")
            st.subheader("Datos del Representante Legal")
            col3, col4, col5 = st.columns(3)
            with col3:
                rep_legal = st.text_input("Nombre Rep. Legal*", value=st.session_state.form_data_cache.get('rep_legal', ''))
            with col4:
                cedula_rep_legal = st.text_input("C.C. Rep. Legal*", value=st.session_state.form_data_cache.get('cedula_rep_legal', ''))
            with col5:
                tipo_id_rep = st.selectbox("Tipo ID*", ["C.C.", "C.E."], key="id_r")
                lugar_exp_id_rep = st.text_input("Lugar Exp. ID*", value=st.session_state.form_data_cache.get('lugar_exp_id', ''), key="lex_r")
            
            with st.expander("👤 Contactos Adicionales (Opcional)"):
                col_compras, col_cartera = st.columns(2)
                with col_compras:
                    st.write("**Contacto de Compras**")
                    nombre_compras = st.text_input("Nombre", key="nc")
                    email_compras = st.text_input("Email", key="ec")
                    celular_compras = st.text_input("Celular", key="cc")
                with col_cartera:
                    st.write("**Contacto de Cartera**")
                    nombre_cartera = st.text_input("Nombre", key="nca")
                    email_cartera = st.text_input("Email", key="eca")
                    celular_cartera = st.text_input("Celular", key="cca")

            st.subheader("✍️ Firma Digital de Aceptación")
            canvas_result = st_canvas(fill_color="#FFFFFF", stroke_width=3, stroke_color="#000000", height=200, key="canvas_j")
            
            if st.form_submit_button("Enviar y Solicitar Código de Verificación", use_container_width=True):
                if not all([razon_social, nit, correo, correo_promo, rep_legal, cedula_rep_legal, ciudad, nombre_comercial, lugar_exp_id_rep]) or canvas_result.image_data is None or np.all(canvas_result.image_data == 255):
                    st.warning("⚠️ Los campos marcados con * son obligatorios y la firma no puede estar vacía.")
                else:
                    form_data_to_process = {
                        'client_type': 'juridica', 'razon_social': razon_social,
                        'nombre_comercial': nombre_comercial, 'nit': nit, 'direccion': direccion,
                        'ciudad': ciudad, 'telefono': telefono, 'celular': celular, 'correo': correo,
                        'correo_promo': correo_promo,
                        'rep_legal': rep_legal, 'cedula_rep_legal': cedula_rep_legal, 'tipo_id': tipo_id_rep,
                        'lugar_exp_id': lugar_exp_id_rep,
                        'firma_img_pil': Image.fromarray(canvas_result.image_data.astype('uint8'), 'RGBA'),
                        'nombre_compras': nombre_compras, 'email_compras': email_compras, 'celular_compras': celular_compras,
                        'nombre_cartera': nombre_cartera, 'email_cartera': email_cartera, 'celular_cartera': celular_cartera
                    }
                    st.session_state.final_razon_social = razon_social
    
    elif st.session_state.client_type == 'natural':
        st.button("‹ Volver a Selección de Tipo", on_click=reset_to_selection)
        with st.form(key="form_natural"):
            st.header("📝 Formulario: Persona Natural")
            col1, col2 = st.columns(2)
            with col1:
                nombre_natural = st.text_input("Nombre Completo*", value=st.session_state.form_data_cache.get('nombre_natural', ''))
                cedula_natural = st.text_input("C.C.*", value=st.session_state.form_data_cache.get('cedula_natural', ''))
                direccion_natural = st.text_input("Dirección de Residencia*", value=st.session_state.form_data_cache.get('direccion', ''))
                telefono_natural = st.text_input("Teléfono / Celular*", value=st.session_state.form_data_cache.get('telefono', ''))
                correo_promo_natural = st.text_input("Correo para Promociones y Notificaciones*", help="A este correo enviaremos el código de verificación y la copia final.", value=st.session_state.form_data_cache.get('correo_promo', ''))
            with col2:
                correo_natural = st.text_input("Correo para Facturación Electrónica*", help="Correo para recibir facturas y documentos contables.", value=st.session_state.form_data_cache.get('correo', ''))
                ciudad_natural = st.text_input("Ciudad de Residencia*", value=st.session_state.form_data_cache.get('ciudad', ''))
                tipo_id_nat = st.selectbox("Tipo ID*", ["C.C.", "C.E."], key="id_n")
                lugar_exp_id_nat = st.text_input("Lugar Exp. ID*", value=st.session_state.form_data_cache.get('lugar_exp_id', ''), key="lex_n")
            
            fecha_nacimiento = st.date_input("Fecha de Nacimiento*", min_value=datetime(1930, 1, 1).date(), max_value=datetime.now().date())

            st.subheader("✍️ Firma Digital de Aceptación")
            canvas_result = st_canvas(fill_color="#FFFFFF", stroke_width=3, stroke_color="#000000", height=200, key="canvas_n")
            
            if st.form_submit_button("Enviar y Solicitar Código de Verificación", use_container_width=True):
                if not all([nombre_natural, cedula_natural, correo_natural, correo_promo_natural, telefono_natural, fecha_nacimiento, direccion_natural, lugar_exp_id_nat, ciudad_natural]) or canvas_result.image_data is None or np.all(canvas_result.image_data == 255):
                    st.warning("⚠️ Los campos marcados con * y la firma son obligatorios.")
                else:
                    form_data_to_process = {
                        'client_type': 'natural', 'nombre_natural': nombre_natural,
                        'cedula_natural': cedula_natural, 'tipo_id': tipo_id_nat, 'lugar_exp_id': lugar_exp_id_nat,
                        'direccion': direccion_natural, 'correo': correo_natural, 'telefono': telefono_natural,
                        'correo_promo': correo_promo_natural,
                        'ciudad': ciudad_natural,
                        'firma_img_pil': Image.fromarray(canvas_result.image_data.astype('uint8'), 'RGBA'),
                        'fecha_nacimiento': fecha_nacimiento
                    }
                    st.session_state.final_razon_social = nombre_natural

    if form_data_to_process:
        with st.spinner("Generando y enviando código de verificación... Por favor, espere."):
            st.session_state.form_data_cache = form_data_to_process
            code = str(random.randint(100000, 999999))
            st.session_state.generated_code = code
            email_body = f"""<h3>Su Código de Verificación para Ferreinox</h3>
                                        <p>Hola,</p>
                                        <p>Use el siguiente código para verificar su firma y completar el proceso de vinculación:</p>
                                        <h2 style='text-align:center; letter-spacing: 5px;'>{code}</h2>
                                        <p>Este código es válido por un tiempo limitado.</p>
                                        <p>Si usted no solicitó este código, puede ignorar este mensaje.</p><br>
                                        <p>Atentamente,<br><b>Ferreinox S.A.S. BIC</b></p>"""
            
            correo_notificaciones = form_data_to_process['correo_promo']
            email_sent = send_email(correo_notificaciones, "Su Código de Verificación - Ferreinox", email_body)
            
            if email_sent:
                st.session_state.verification_code_sent = True
                st.rerun()
