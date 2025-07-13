# -*- coding: utf-8 -*-
# =================================================================================================
# APLICACIÓN INSTITUCIONAL DE VINCULACIÓN DE CLIENTES - FERREINOX S.A.S. BIC
# Versión 14.0 (Optimización de PDF a dos páginas)
# Fecha: 13 de Julio de 2025
# =================================================================================================

import streamlit as st
from streamlit_drawable_canvas import st_canvas
from PIL import Image
from datetime import datetime
import gspread
import tempfile
import os
import numpy as np

from reportlab.platypus import BaseDocTemplate, PageTemplate, Frame, Paragraph, Spacer, Table, TableStyle, Image as PlatypusImage
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_LEFT, TA_RIGHT
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.lib.pagesizes import letter

from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication

st.set_page_config(page_title="Portal de Vinculación | Ferreinox", page_icon="✍️", layout="wide")

# --- Institutional Colors (inspired by ferreinox.co - dark blue, light blue/yellow accents) ---
FERREINOX_DARK_BLUE = "#0D47A1" # Deeper blue, similar to the one used for titles in the original code
FERREINOX_ACCENT_BLUE = "#1565C0" # Slightly lighter blue, used for buttons/highlights
FERREINOX_LIGHT_BG = "#F0F2F6" # Light background from original CSS
FERREINOX_YELLOW_ACCENT = "#FBC02D" # Found in "EVOLUCIONANDO JUNTOS"

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
</style>
""", unsafe_allow_html=True)

def get_texto_tratamiento_datos(nombre_rep, razon_social, nit):
    return f"""
        Yo, <b>{nombre_rep}</b>, mayor de edad, identificado(a) como aparece al pie de mi firma, actuando en nombre
        propio y/o en Representación Legal de <b>{razon_social}</b>, identificado con NIT <b>{nit}</b>, manifiesto que de
        conformidad con la Política de Tratamiento de Datos Personales para Clientes, Proveedores, Colaboradores y Ex colaboradores" implementada
        por FERREINOX S.A.S. BIC., sociedad identificada con NIT. 800224617-8, la cuál puede ser encontrada en sus instalaciones o página Web
        www.ferreinox.co; y de acuerdo a la relación comercial existente entre las partes, autorizo a FERREINOX S.A.S. BIC para tratar mis datos
        personales y usarlos con el fin de enviar información de ventas, compras, comercial, publicitaria, facturas y documentos de cobro, pago, ofertas,
        promociones, para ofrecer novedades, comunicar cambios y actualizaciones de información de la compañía, actividades de mercadeo, para
        fines estadísticos o administrativos que resulten de la ejecución del objeto social de FERREINOX S.A.S. BIC. Los datos personales de nuestros
        Clientes, Proveedores, Colaboradores y Ex colaboradores, los conservaremos y almacenaremos en contornos seguros, para protegerlos de
        acceso de terceros no autorizados, en cumplimiento de nuestro deber de confidencialidad; y acorde a los preceptos legales, usted como titular
        de la información objeto de tratamiento, puede ejercer los derechos consagrados en la norma, los cuales permiten: A) Solicitar, conocer,
        actualizar, rectificar o suprimir sus datos personales de nuestras bases de datos B) Ser informados con previa solicitud, respecto al uso de sus
        datos personales, D) Previo requerimiento o consulta ante la Empresa, presentar ante la Superintendencia de industria y Comercio quejas por
        infracciones a la normatividad legal vigente, E) Deshacer la autorización y/o solicitar el no entregar el dato cuando se estén vulnerando el
        principio, derechos y garantías constitucionales legales, F) Acceder en una forma gratuita a sus datos personales. Los canales habilitados para
        cualquier tipo de información frente a éste tema son: correo electrónico: tiendapintucopereira@ferreinox.co, tel. (6) 333 0101 opción 1,
        dirección: CR 13 19-26 Pereira, Risaralda, y la página web: www.ferreinox.co.
    """

def get_texto_habeas_data(nombre_rep, razon_social, nit, email):
    return f"""
        Yo, <b>{nombre_rep}</b>, mayor de edad, identificado (a) como aparece al pie de mi firma, actuando en nombre
        propio y/o en Representación Legal de <b>{razon_social}</b>, identificado con NIT <b>{nit}</b>. En ejercicio de mi Derecho a
        la Libertad y Autodeterminación Informática, autorizo a Ferreinox S.A.S. BIC o a la entidad que mi acreedor para representarlo o a su cesionario,
        endosatario o a quien ostente en el futuro la calidad de acreedor, previo a la relación contractual y de manera irrevocable, escrita, expresa,
        concreta, suficiente, voluntaria e informada, con la finalidad que la información comercial, crediticia, financiera y de servicios de la cual soy
        titular, referida al nacimiento, ejecución y extinción de obligaciones dinerarias (independientemente de la naturaleza del contrato que les dé
        origen), a mi comportamiento e historial crediticio, incluida la información positiva y negativa de mis hábitos de pago, y aquella que se refiera
        a la información personal necesaria para el estudio, análisis y eventual otorgamiento de un crédito o celebración de un contrato, sea en general
        administrada y en especial: capturada, tratada, procesada, operada, verificada, transmitida, transferida, usada o puesta en circulación y
        consultada por terceras personas autorizadas expresamente por la Ley 1266 de 2008, incluidos los Usuarios de la Información.
        Con estos mismos alcances, atributos y finalidad autorizo expresamente para que tal información sea concernida y reportada en las Centrales de
        Información y/o Riesgo (Datacrédito, Cifin y Procrédito).<br/><br/>
        Autorizo también para que “la notificación” a que hace referencia el Decreto 2952 del 6 de agosto de 2010 en su artículo 2º, se pueda surtir a
        través de mensaje de datos y para ello suministro y declaro el siguiente correo electrónico: <b>{email}</b>.<br/><br/>
        Certifico que los datos personales suministrados por mí, son veraces, completos, exactos, actualizados, reales y comprobables. Por tanto,
        cualquier error en la información suministrada será de mi única y exclusiva responsabilidad, lo que exonera a Ferreinox S.A.S. BIC, de su
        responsabilidad ante las autoridades judiciales y/o administrativas. Declaro que he leído y comprendido a cabalidad el contenido de la presente
        Autorización, y acepto la finalidad en ella descrita y las consecuencias que se derivan de ella.
    """

# --- PDF GENERATOR: REDISEÑO GERENCIAL, INSTITUCIONAL, PROFESIONAL ---
class PDFGeneratorPlatypus:
    def __init__(self, data):
        self.data = data
        self.story = []

        styles = getSampleStyleSheet()
        self.style_body = ParagraphStyle(name='Body', parent=styles['Normal'], fontName='Helvetica', fontSize=9, alignment=TA_JUSTIFY, leading=14)
        self.style_header_title = ParagraphStyle(name='HeaderTitle', parent=styles['h1'], fontName='Helvetica-Bold', fontSize=16, alignment=TA_RIGHT, textColor=colors.HexColor(FERREINOX_DARK_BLUE), spaceAfter=2)
        self.style_footer = ParagraphStyle(name='Footer', parent=styles['Normal'], fontName='Helvetica', fontSize=9, alignment=TA_CENTER, textColor=colors.HexColor(FERREINOX_DARK_BLUE))
        self.style_section_title = ParagraphStyle(name='SectionTitle', parent=styles['h2'], fontName='Helvetica-Bold', fontSize=14, alignment=TA_LEFT, textColor=colors.HexColor(FERREINOX_DARK_BLUE), spaceBefore=18, spaceAfter=8)
        self.style_table_header = ParagraphStyle(name='TableHeader', parent=styles['Normal'], fontName='Helvetica-Bold', fontSize=9, textColor=colors.white, alignment=TA_LEFT)
        self.style_signature_info = ParagraphStyle(name='SignatureInfo', parent=styles['Normal'], fontName='Helvetica', fontSize=9, alignment=TA_LEFT, leading=14)

    def _on_page(self, canvas, doc):
        canvas.saveState()
        try:
            logo = PlatypusImage('LOGO FERREINOX SAS BIC 2024.png', width=2.5*inch, height=0.8*inch, hAlign='LEFT')
        except Exception:
            logo = Paragraph("Ferreinox S.A.S. BIC", self.style_body)

        header_content = [
            [
                logo,
                Paragraph(
                    "<b>ACTUALIZACIÓN Y AUTORIZACIÓN<br/>DE DATOS DE CLIENTE</b>",
                    self.style_header_title
                )
            ]
        ]
        header_table = Table(header_content, colWidths=[3.0*inch, 4.2*inch], hAlign='LEFT')
        header_table.setStyle(
            TableStyle([
                ('VALIGN', (0, 0), (-1, -1), 'BOTTOM'),
                ('ALIGN', (1, 0), (1, 0), 'RIGHT'),
                ('LEFTPADDING', (0,0), (-1,-1), 0),
                ('RIGHTPADDING', (0,0), (-1,-1), 0),
                ('BOTTOMPADDING', (0,0), (-1,-1), 0),
                ('TOPPADDING', (0,0), (-1,-1), 0)
            ])
        )
        w, h = header_table.wrap(doc.width, doc.topMargin)
        header_table.drawOn(canvas, doc.leftMargin, doc.height + doc.topMargin - h + 15)
        canvas.restoreState()

        canvas.saveState()
        footer_content = [
            [Paragraph(f"<b>EVOLUCIONANDO <font color='{FERREINOX_YELLOW_ACCENT}'>JUNTOS</font></b>", self.style_footer), Paragraph(f"Página {doc.page}", self.style_footer)]
        ]
        footer_table = Table(footer_content, colWidths=[doc.width/2, doc.width/2])
        footer_table.setStyle(TableStyle([
            ('ALIGN', (0,0), (0,0), 'LEFT'),
            ('ALIGN', (1,0), (1,0), 'RIGHT'),
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE')
        ]))
        w, h = footer_table.wrap(doc.width, doc.bottomMargin)
        footer_table.drawOn(canvas, doc.leftMargin, h - 10)
        canvas.restoreState()

    def _add_signature_section(self):
        self.story.append(Paragraph("4. CONSTANCIA DE ACEPTACIÓN Y FIRMA DIGITAL", self.style_section_title))
        firma_path = None
        try:
            with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as temp_img:
                firma_path = temp_img.name
            
            firma_img = self.data['firma_img_pil']
            if firma_img.mode == "RGBA":
                background = Image.new("RGB", firma_img.size, (255, 255, 255))
                background.paste(firma_img, mask=firma_img.split()[3])
                background.save(firma_path, format="PNG")
            else:
                firma_img.save(firma_path, format="PNG")

            firma_image = PlatypusImage(firma_path, width=2.5*inch, height=1.0*inch)
            
            if self.data.get('client_type') == 'juridica':
                 nombre_firmante = self.data.get('rep_legal', '')
                 id_firmante = f"{self.data.get('tipo_id', '')} No. {self.data.get('cedula_rep_legal', '')} de {self.data.get('lugar_exp_id', '')}"
            else:
                 nombre_firmante = self.data.get('nombre_natural', '')
                 id_firmante = f"{self.data.get('tipo_id', '')} No. {self.data.get('cedula_natural', '')} de {self.data.get('lugar_exp_id', '')}"

            firma_texto = f"""<b>Nombre:</b> {nombre_firmante}<br/>
                <b>Identificación:</b> {id_firmante}<br/>
                <b>Fecha de Firma:</b> {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}<br/>
                <b>Consentimiento Vía:</b> Portal Web v14.0"""
            
            table_firma = Table([[firma_image, Paragraph(firma_texto, self.style_signature_info)]], colWidths=[2.8*inch, 4.4*inch], hAlign='LEFT')
            table_firma.setStyle(TableStyle([
                ('VALIGN', (0,0), (-1,-1), 'TOP'),
                ('LEFTPADDING', (1,0), (1,0), 10),
            ]))
            self.story.append(table_firma)
            return firma_path
        except Exception as e:
            self.story.append(Paragraph("Error al generar la imagen de la firma: " + str(e), self.style_body))
            return None

    def generate(self):
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as temp_pdf:
            pdf_path = temp_pdf.name

        doc = BaseDocTemplate(
            pdf_path, pagesize=letter,
            leftMargin=0.6*inch, rightMargin=0.6*inch, topMargin=1.1*inch, bottomMargin=0.6*inch
        )
        main_frame = Frame(doc.leftMargin, doc.bottomMargin, doc.width, doc.height, id='main_frame')
        template = PageTemplate(id='main_template', frames=[main_frame], onPage=self._on_page)
        doc.addPageTemplates([template])

        self.story.append(Spacer(1, 0.2*inch))
        self.story.append(Paragraph("1. DATOS BÁSICOS", self.style_section_title))
        
        if self.data.get('client_type') == 'juridica':
            datos = [
                [Paragraph('Razón Social:', self.style_table_header), Paragraph(self.data.get('razon_social', ''), self.style_body),
                 Paragraph('Dirección:', self.style_table_header), Paragraph(self.data.get('direccion', ''), self.style_body)],
                [Paragraph('Nombre Comercial:', self.style_table_header), Paragraph(self.data.get('nombre_comercial', ''), self.style_body),
                 Paragraph('Ciudad:', self.style_table_header), Paragraph(self.data.get('ciudad', ''), self.style_body)],
                [Paragraph('NIT:', self.style_table_header), Paragraph(self.data.get('nit', ''), self.style_body),
                 Paragraph('Teléfono:', self.style_table_header), Paragraph(self.data.get('telefono', ''), self.style_body)],
                [Paragraph('Representante Legal:', self.style_table_header), Paragraph(self.data.get('rep_legal', ''), self.style_body),
                 Paragraph('Celular:', self.style_table_header), Paragraph(self.data.get('celular', ''), self.style_body)],
                [Paragraph('Correo para Notificaciones:', self.style_table_header), Paragraph(self.data.get('correo', ''), self.style_body), '', '']
            ]
            table_basicos = Table(datos, colWidths=[1.5*inch, 2.1*inch, 1.5*inch, 2.1*inch], hAlign='LEFT', rowHeights=0.3*inch)
            table_basicos.setStyle(TableStyle([
                ('GRID', (0,0), (-1,-1), 0.5, colors.lightgrey),
                ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
                ('BACKGROUND', (0,0), (0,-1), colors.HexColor(FERREINOX_DARK_BLUE)),
                ('BACKGROUND', (2,0), (2,-1), colors.HexColor(FERREINOX_DARK_BLUE)),
                ('SPAN', (1,-1), (3,-1)),
                ('LEFTPADDING', (0,0), (-1,-1), 6),
                ('RIGHTPADDING', (0,0), (-1,-1), 6),
            ]))
            self.story.append(table_basicos)
            rep_legal_name = self.data['rep_legal']
            entity_name = self.data['razon_social']
            entity_id = self.data['nit']
            entity_email = self.data['correo']

        else: # Persona Natural
            datos = [
                [Paragraph('Nombre Completo:', self.style_table_header), Paragraph(self.data.get('nombre_natural', ''), self.style_body)],
                [Paragraph('No. Identificación:', self.style_table_header), Paragraph(self.data.get('cedula_natural', ''), self.style_body)],
                [Paragraph('Dirección:', self.style_table_header), Paragraph(self.data.get('direccion', ''), self.style_body)],
                [Paragraph('Teléfono / Celular:', self.style_table_header), Paragraph(self.data.get('telefono', ''), self.style_body)],
                [Paragraph('Correo Electrónico:', self.style_table_header), Paragraph(self.data.get('correo', ''), self.style_body)],
            ]
            table_basicos = Table(datos, colWidths=[2.2*inch, 5.0*inch], hAlign='LEFT')
            table_basicos.setStyle(TableStyle([
                ('GRID', (0,0), (-1,-1), 0.5, colors.lightgrey),
                ('BACKGROUND', (0,0), (0,-1), colors.HexColor(FERREINOX_DARK_BLUE)),
                ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
                ('LEFTPADDING', (0,0), (-1,-1), 6), ('RIGHTPADDING', (0,0), (-1,-1), 6),
                ('TOPPADDING', (0,0), (-1,-1), 5), ('BOTTOMPADDING', (0,0), (-1,-1), 5),
            ]))
            self.story.append(table_basicos)
            rep_legal_name = self.data['nombre_natural']
            entity_name = self.data['nombre_natural'] 
            entity_id = self.data['cedula_natural']
            entity_email = self.data['correo']

        # ** CORRECCIÓN CLAVE: Se elimina el salto de página forzado **
        # self.story.append(FrameBreak()) -> ESTA LÍNEA FUE ELIMINADA

        self.story.append(Paragraph("2. AUTORIZACIÓN HABEAS DATA", self.style_section_title))
        self.story.append(Paragraph(get_texto_habeas_data(rep_legal_name, entity_name, entity_id, entity_email), self.style_body))
        
        self.story.append(Paragraph("3. AUTORIZACIÓN PARA EL TRATAMIENTO DE DATOS PERSONALES", self.style_section_title))
        self.story.append(Paragraph(get_texto_tratamiento_datos(rep_legal_name, entity_name, entity_id), self.style_body))
        
        firma_path = self._add_signature_section()
        
        try:
            doc.build(self.story)
        finally:
            if firma_path and os.path.exists(firma_path):
                os.unlink(firma_path)
        return pdf_path

# --- CONEXIONES Y SECRETOS ---
try:
    if "google_sheet_id" not in st.secrets:
        st.error("🚨 Error Crítico: Faltan secretos de configuración. Revisa tu archivo secrets.toml")
        st.stop()
    private_key = st.secrets["private_key"].replace('\\n', '\n')
    creds_info = {
        "type": st.secrets["type"], "project_id": st.secrets["project_id"],
        "private_key_id": st.secrets["private_key_id"], "private_key": private_key,
        "client_email": st.secrets["client_email"], "client_id": st.secrets["client_id"],
        "auth_uri": st.secrets["auth_uri"], "token_uri": st.secrets["token_uri"],
        "auth_provider_x509_cert_url": st.secrets["auth_provider_x509_cert_url"],
        "client_x509_cert_url": st.secrets["client_x509_cert_url"]
    }
    GOOGLE_SHEET_ID = st.secrets["google_sheet_id"]
    DRIVE_FOLDER_ID = st.secrets["drive_folder_id"]
    scopes = ['https://www.googleapis.com/auth/drive', 'https://www.googleapis.com/auth/spreadsheets']
    creds = service_account.Credentials.from_service_account_info(creds_info, scopes=scopes)
    gc = gspread.authorize(creds)
    worksheet = gc.open_by_key(GOOGLE_SHEET_ID).sheet1
    drive_service = build('drive', 'v3', credentials=creds)
except Exception as e:
    st.error(f"🚨 Ha ocurrido un error inesperado durante la configuración inicial.")
    st.error(f"Detalle técnico del error: {e}")
    st.stop()

def send_email_with_attachment(recipient_email, subject, body, pdf_path, filename):
    sender_email = st.secrets.email_credentials.smtp_user
    sender_password = st.secrets.email_credentials.smtp_password
    smtp_server = st.secrets.email_credentials.smtp_server
    smtp_port = int(st.secrets.email_credentials.smtp_port)
    msg = MIMEMultipart()
    msg['From'] = sender_email
    msg['To'] = recipient_email
    msg['Subject'] = subject
    msg.attach(MIMEText(body, 'html'))
    with open(pdf_path, "rb") as f:
        part = MIMEApplication(f.read(), Name=filename)
    part['Content-Disposition'] = f'attachment; filename="{filename}"'
    msg.attach(part)
    context = smtplib.ssl.create_default_context()
    with smtplib.SMTP_SSL(smtp_server, smtp_port, context=context) as server:
        server.login(sender_email, sender_password)
        server.send_message(msg)

# --- UI STREAMLIT ---
try:
    st.image('LOGO FERREINOX SAS BIC 2024.png', width=300)
except Exception:
    st.image("https://placehold.co/300x100/0D47A1/FFFFFF?text=Ferreinox+S.A.S.+BIC", width=300)

st.title("Portal de Vinculación y Autorización de Datos")
st.markdown("---")

if 'terms_accepted' not in st.session_state:
    st.session_state.terms_accepted = False
if 'client_type' not in st.session_state:
    st.session_state.client_type = None

def accept_terms():
    st.session_state.terms_accepted = True

def set_client_type(type):
    st.session_state.client_type = type

if not st.session_state.terms_accepted:
    st.header("📜 Términos, Condiciones y Autorizaciones")
    with st.expander("Haga clic aquí para leer los Términos Completos"):
        st.subheader("Autorización para Tratamiento de Datos Personales")
        st.markdown(get_texto_tratamiento_datos("[Su Nombre / Nombre Rep. Legal]", "[Su Empresa / Su Nombre]", "[Su NIT / Cédula]"), unsafe_allow_html=True)
        st.subheader("Autorización para Consulta en Centrales de Riesgo (Habeas Data)")
        st.markdown(get_texto_habeas_data("[Su Nombre / Nombre Rep. Legal]", "[Su Empresa / Su Nombre]", "[Su NIT / Cédula]", "[Su Correo]"), unsafe_allow_html=True)
    st.button("He leído y acepto los términos para continuar", on_click=accept_terms, use_container_width=True)

elif st.session_state.client_type is None:
    st.header("👤 Selección de Tipo de Cliente")
    st.markdown("Por favor, seleccione el tipo de vinculación que desea realizar.")
    col1, col2 = st.columns(2)
    with col1:
        st.button("Soy Persona Jurídica (Empresa)", on_click=set_client_type, args=('juridica',), use_container_width=True)
    with col2:
        st.button("Soy Persona Natural", on_click=set_client_type, args=('natural',), use_container_width=True)

elif st.session_state.client_type == 'juridica':
    with st.form(key="form_juridica"):
        st.header("📝 Formulario de Vinculación: Persona Jurídica")
        st.markdown("Por favor, complete todos los campos a continuación.")
        
        st.subheader("Datos de la Empresa")
        col1, col2 = st.columns(2)
        with col1:
            razon_social = st.text_input("Razón Social*", placeholder="Mi Empresa S.A.S.")
            nit = st.text_input("NIT*", placeholder="900.123.456-7")
            direccion = st.text_input("Dirección de la Sede Principal*", placeholder="Cr 13 #19-26")
            telefono = st.text_input("Teléfono Fijo", placeholder="6063330101")
        with col2:
            nombre_comercial = st.text_input("Nombre Comercial*", placeholder="Ferreinox")
            ciudad = st.text_input("Ciudad*", placeholder="Pereira")
            correo = st.text_input("Correo para Notificaciones y Facturas*", placeholder="facturacion@empresa.com")
            celular = st.text_input("Celular de Contacto General", placeholder="3101234567")
        
        st.subheader("Datos del Representante Legal")
        col3, col4, col5 = st.columns(3)
        with col3:
            rep_legal = st.text_input("Nombre Completo del Representante Legal*", placeholder="Ana María Pérez")
        with col4:
            cedula_rep_legal = st.text_input("Número de Identificación*", placeholder="1020304050")
        with col5:
            tipo_id_rep = st.selectbox("Tipo de ID*", ["C.C.", "C.E.", "Pasaporte", "Otro"], key="tipo_id_rep")
            lugar_exp_id_rep = st.text_input("Ciudad de Expedición del ID*", placeholder="Pereira", key="lugar_exp_rep")

        st.subheader("✍️ Firma Digital de Aceptación")
        st.caption("El Representante Legal debe firmar en el siguiente recuadro para validar la información y las autorizaciones.")
        canvas_result = st_canvas(
            fill_color="rgba(255, 255, 255, 0)", stroke_width=3, stroke_color="#000000",
            background_color="#FFFFFF", height=200, drawing_mode="freedraw", key="canvas_firma_juridica"
        )
        submit_button = st.form_submit_button(label="✅ Finalizar y Enviar Formulario Firmado", use_container_width=True)

    if submit_button:
        campos_obligatorios = [razon_social, nit, direccion, ciudad, correo, rep_legal, cedula_rep_legal, lugar_exp_id_rep, nombre_comercial]
        if not all(campos_obligatorios):
            st.warning("⚠️ Por favor, complete todos los campos marcados con *.")
        elif canvas_result.image_data is None:
            st.warning("🖋️ La firma del Representante Legal es indispensable para validar el documento.")
        else:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            doc_id = f"FER-{datetime.now().strftime('%Y%m%d%H%M%S')}-{nit}"
            with st.spinner("Procesando su solicitud... Este proceso puede tardar un momento. ⏳"):
                pdf_file_path = None
                try:
                    firma_img_pil = Image.fromarray(canvas_result.image_data.astype('uint8'), 'RGBA')
                    form_data = {
                        'client_type': 'juridica',
                        'razon_social': razon_social, 'nombre_comercial': nombre_comercial, 'nit': nit,
                        'direccion': direccion, 'ciudad': ciudad, 'telefono': telefono, 'celular': celular,
                        'correo': correo, 'rep_legal': rep_legal, 'cedula_rep_legal': cedula_rep_legal,
                        'tipo_id': tipo_id_rep, 'lugar_exp_id': lugar_exp_id_rep,
                        'firma_img_pil': firma_img_pil
                    }
                    
                    st.write("Paso 1/4: Generando documento PDF institucional...")
                    pdf_gen = PDFGeneratorPlatypus(form_data)
                    pdf_file_path = pdf_gen.generate()
                    
                    st.write("Paso 2/4: Guardando registro en Log de Trazabilidad...")
                    log_row = [timestamp, doc_id, razon_social, nit, rep_legal, correo, ciudad, f"{telefono} / {celular}", "Persona Jurídica", "Enviado y Notificado"]
                    worksheet.append_row(log_row, value_input_option='USER_ENTERED')
                    
                    st.write("Paso 3/4: Enviando correo de confirmación al cliente...")
                    file_name = f"Actualizacion_Datos_{razon_social.replace(' ', '_')}_{nit}.pdf"
                    email_body = f"""
                    <h3>Confirmación de Actualización de Datos - Ferreinox S.A.S. BIC</h3>
                    <p>Estimado(a) <b>{rep_legal}</b>,</p>
                    <p>Reciba un cordial saludo.</p>
                    <p>Este correo confirma que hemos recibido y procesado exitosamente el formulario de actualización y autorización de tratamiento de datos para la empresa <b>{razon_social}</b> (NIT: {nit}).</p>
                    <p>Adjunto a este mensaje encontrará el documento PDF con toda la información registrada y la constancia de su consentimiento.</p>
                    <p><b>ID del Documento:</b> {doc_id}<br><b>Fecha de registro:</b> {timestamp}</p>
                    <p>Agradecemos su confianza en Ferreinox S.A.S. BIC.</p><br>
                    <p><i>Este es un mensaje automático, por favor no responda a este correo.</i></p>
                    """
                    send_email_with_attachment(correo, f"Confirmación de Vinculación - {razon_social}", email_body, pdf_file_path, file_name)
                    
                    st.write("Paso 4/4: Archivando PDF en el repositorio digital...")
                    file_metadata = {'name': file_name, 'parents': [DRIVE_FOLDER_ID]}
                    media = MediaFileUpload(pdf_file_path, mimetype='application/pdf', resumable=True)
                    file = drive_service.files().create(body=file_metadata, media_body=media, fields='id, webViewLink', supportsAllDrives=True).execute()
                    
                    st.balloons()
                    st.success(f"**¡Proceso Finalizado Exitosamente!**")
                    st.markdown(f"El formulario para **{razon_social}** ha sido generado, archivado y enviado a su correo electrónico.")
                    st.markdown(f"Puede previsualizar el documento final aquí: [**Ver PDF Generado**]({file.get('webViewLink')})")

                except Exception as e:
                    st.error(f"❌ ¡Ha ocurrido un error inesperado durante el envío! Por favor, intente de nuevo.")
                    st.error(f"Detalle técnico: {e}")
                    try:
                        worksheet.append_row([timestamp, doc_id, razon_social, nit, rep_legal, correo, f"Error: {e}"], value_input_option='USER_ENTERED')
                    except Exception as log_e:
                        st.error(f"No se pudo registrar el error en Google Sheets. Detalle: {log_e}")
                finally:
                    if pdf_file_path and os.path.exists(pdf_file_path):
                        os.unlink(pdf_file_path)

elif st.session_state.client_type == 'natural':
    with st.form(key="form_natural"):
        st.header("📝 Formulario de Vinculación: Persona Natural")
        st.markdown("Por favor, complete todos los campos a continuación.")

        col1, col2 = st.columns(2)
        with col1:
            nombre_natural = st.text_input("Nombre Completo*", placeholder="Ana María Pérez")
            cedula_natural = st.text_input("Número de Identificación*", placeholder="1020304050")
            direccion_natural = st.text_input("Dirección de Residencia*", placeholder="Cr 13 #19-26")
        with col2:
            correo_natural = st.text_input("Correo Electrónico*", placeholder="ana.perez@email.com")
            telefono_natural = st.text_input("Teléfono / Celular*", placeholder="3101234567")
            tipo_id_nat = st.selectbox("Tipo de ID*", ["C.C.", "C.E.", "Pasaporte", "Otro"], key="tipo_id_nat")
            lugar_exp_id_nat = st.text_input("Ciudad de Expedición del ID*", placeholder="Pereira", key="lugar_exp_nat")

        st.subheader("✍️ Firma Digital de Aceptación")
        st.caption("Firme en el siguiente recuadro para validar su información y autorizaciones.")
        canvas_result = st_canvas(
            fill_color="rgba(255, 255, 255, 0)", stroke_width=3, stroke_color="#000000",
            background_color="#FFFFFF", height=200, drawing_mode="freedraw", key="canvas_firma_natural"
        )
        submit_button = st.form_submit_button(label="✅ Finalizar y Enviar Formulario Firmado", use_container_width=True)

    if submit_button:
        campos_obligatorios = [nombre_natural, cedula_natural, direccion_natural, correo_natural, telefono_natural, lugar_exp_id_nat]
        if not all(campos_obligatorios):
            st.warning("⚠️ Por favor, complete todos los campos marcados con *.")
        elif canvas_result.image_data is None:
            st.warning("🖋️ Su firma es indispensable para validar el documento.")
        else:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            doc_id = f"FER-{datetime.now().strftime('%Y%m%d%H%M%S')}-{cedula_natural}"
            with st.spinner("Procesando su solicitud... Este proceso puede tardar un momento. ⏳"):
                pdf_file_path = None
                try:
                    firma_img_pil = Image.fromarray(canvas_result.image_data.astype('uint8'), 'RGBA')
                    form_data = {
                        'client_type': 'natural',
                        'nombre_natural': nombre_natural, 'cedula_natural': cedula_natural, 'tipo_id': tipo_id_nat,
                        'lugar_exp_id': lugar_exp_id_nat, 'direccion': direccion_natural,
                        'correo': correo_natural, 'telefono': telefono_natural,
                        'firma_img_pil': firma_img_pil
                    }

                    st.write("Paso 1/4: Generando documento PDF institucional...")
                    pdf_gen = PDFGeneratorPlatypus(form_data)
                    pdf_file_path = pdf_gen.generate()

                    st.write("Paso 2/4: Guardando registro en Log de Trazabilidad...")
                    log_row = [timestamp, doc_id, nombre_natural, cedula_natural, nombre_natural, correo_natural, "", telefono_natural, "Persona Natural", "Enviado y Notificado"]
                    worksheet.append_row(log_row, value_input_option='USER_ENTERED')

                    st.write("Paso 3/4: Enviando correo de confirmación...")
                    file_name = f"Autorizacion_Datos_{nombre_natural.replace(' ', '_')}_{cedula_natural}.pdf"
                    email_body = f"""
                    <h3>Confirmación de Autorización de Datos - Ferreinox S.A.S. BIC</h3>
                    <p>Estimado(a) <b>{nombre_natural}</b>,</p>
                    <p>Reciba un cordial saludo.</p>
                    <p>Este correo confirma que hemos recibido y procesado exitosamente su formulario de autorización de tratamiento de datos.</p>
                    <p>Adjunto a este mensaje encontrará el documento PDF con toda la información registrada y la constancia de su consentimiento.</p>
                    <p><b>ID del Documento:</b> {doc_id}<br><b>Fecha de registro:</b> {timestamp}</p>
                    <p>Agradecemos su confianza en Ferreinox S.A.S. BIC.</p><br>
                    <p><i>Este es un mensaje automático, por favor no responda a este correo.</i></p>
                    """
                    send_email_with_attachment(correo_natural, f"Confirmación de Vinculación - {nombre_natural}", email_body, pdf_file_path, file_name)

                    st.write("Paso 4/4: Archivando PDF en el repositorio digital...")
                    file_metadata = {'name': file_name, 'parents': [DRIVE_FOLDER_ID]}
                    media = MediaFileUpload(pdf_file_path, mimetype='application/pdf', resumable=True)
                    file = drive_service.files().create(body=file_metadata, media_body=media, fields='id, webViewLink', supportsAllDrives=True).execute()

                    st.balloons()
                    st.success(f"**¡Proceso Finalizado Exitosamente!**")
                    st.markdown(f"El formulario para **{nombre_natural}** ha sido generado, archivado y enviado a su correo electrónico.")
                    st.markdown(f"Puede previsualizar el documento final aquí: [**Ver PDF Generado**]({file.get('webViewLink')})")
                
                except Exception as e:
                    st.error(f"❌ ¡Ha ocurrido un error inesperado durante el envío! Por favor, intente de nuevo.")
                    st.error(f"Detalle técnico: {e}")
                    try:
                        worksheet.append_row([timestamp, doc_id, nombre_natural, cedula_natural, nombre_natural, correo_natural, f"Error: {e}"], value_input_option='USER_ENTERED')
                    except Exception as log_e:
                        st.error(f"No se pudo registrar el error en Google Sheets. Detalle: {log_e}")
                finally:
                    if pdf_file_path and os.path.exists(pdf_file_path):
                        os.unlink(pdf_file_path)
