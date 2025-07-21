# -*- coding: utf-8 -*-
# =================================================================================================
# APLICACIÓN INSTITUCIONAL DE VINCULACIÓN DE CLIENTES - FERREINOX S.A.S. BIC
# Versión 18.1 (Corrección de Acceso a Secretos)
# Fecha: 21 de Julio de 2025
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

from reportlab.platypus import BaseDocTemplate, PageTemplate, Frame, Paragraph, Spacer, Table, TableStyle, Image as PlatypusImage
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_LEFT, TA_RIGHT
from reportlab.lib import colors
from reportlab.lib.units import inch
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

def get_texto_tratamiento_datos(nombre_rep, razon_social, nit):
    return f"""
        Yo, <b>{nombre_rep}</b>, mayor de edad, identificado(a) como aparece al pie de mi firma, actuando en nombre
        propio y/o en Representación Legal de <b>{razon_social}</b>, identificado con NIT <b>{nit}</b>, manifiesto que de
        conformidad con la Política de Tratamiento de Datos Personales para Clientes, Proveedores, Colaboradores y Ex colaboradores" implementada
        por FERREINOX S.A.S. BIC., sociedad identificada con NIT. 800224617-8, la cuál puede ser encontrada en sus instalaciones o página Web
        www.ferreinox.co; y de acuerdo a la relación comercial existente entre las partes, autorizo a FERREINOX S.A.S. BIC para tratar mis datos
        personales y usarlos con el fin de enviar información de ventas, compras, comercial, publicitaria, facturas y documentos de cobro, pago, ofertas,
        promociones, para ofrecer novedades, comunicar cambios y actualizaciones de información de la compañía, actividades de mercadeo, para
        fines estadísticos o administrativos que resulten de la ejecución del objeto social de FERREINOX S.A.S. BIC.
    """

def get_texto_habeas_data(nombre_rep, razon_social, nit, email):
    return f"""
        Yo, <b>{nombre_rep}</b>, mayor de edad, identificado (a) como aparece al pie de mi firma, actuando en nombre
        propio y/o en Representación Legal de <b>{razon_social}</b>, identificado con NIT <b>{nit}</b>. En ejercicio de mi Derecho a
        la Libertad y Autodeterminación Informática, autorizo a Ferreinox S.A.S. BIC o a la entidad que mi acreedor para representarlo o a su cesionario,
        endosatario o a quien ostente en el futuro la calidad de acreedor, para que la información comercial, crediticia, financiera y de servicios sea
        administrada y consultada por terceras personas autorizadas expresamente por la Ley 1266 de 2008.
        Autorizo también para que “la notificación” a que hace referencia el Decreto 2952 del 6 de agosto de 2010 en su artículo 2º, se pueda surtir a
        través de mensaje de datos y para ello suministro y declaro el siguiente correo electrónico: <b>{email}</b>.
        Certifico que los datos personales suministrados por mí, son veraces, completos, exactos, actualizados, reales y comprobables.
    """

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
        header_content = [[logo, Paragraph("<b>ACTUALIZACIÓN Y AUTORIZACIÓN<br/>DE DATOS</b>", self.style_header_title)]]
        header_table = Table(header_content, colWidths=[3.0*inch, 4.2*inch], hAlign='LEFT')
        header_table.setStyle(TableStyle([('VALIGN', (0, 0), (-1, -1), 'BOTTOM'), ('ALIGN', (1, 0), (1, 0), 'RIGHT'), ('LEFTPADDING', (0,0), (-1,-1), 0), ('RIGHTPADDING', (0,0), (-1,-1), 0), ('BOTTOMPADDING', (0,0), (-1,-1), 0), ('TOPPADDING', (0,0), (-1,-1), 0)]))
        w, h = header_table.wrap(doc.width, doc.topMargin)
        header_table.drawOn(canvas, doc.leftMargin, doc.height + doc.topMargin - h + 15)
        canvas.restoreState()
        canvas.saveState()
        footer_content = [[Paragraph(f"<b>EVOLUCIONANDO <font color='{FERREINOX_YELLOW_ACCENT}'>JUNTOS</font></b>", self.style_footer), Paragraph(f"Página {doc.page}", self.style_footer)]]
        footer_table = Table(footer_content, colWidths=[doc.width/2, doc.width/2])
        footer_table.setStyle(TableStyle([('ALIGN', (0,0), (0,0), 'LEFT'), ('ALIGN', (1,0), (1,0), 'RIGHT'), ('VALIGN', (0,0), (-1,-1), 'MIDDLE')]))
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
                nombre_firmante, id_firmante = self.data.get('rep_legal', ''), f"{self.data.get('tipo_id', '')} No. {self.data.get('cedula_rep_legal', '')} de {self.data.get('lugar_exp_id', '')}"
            else:
                nombre_firmante, id_firmante = self.data.get('nombre_natural', ''), f"{self.data.get('tipo_id', '')} No. {self.data.get('cedula_natural', '')} de {self.data.get('lugar_exp_id', '')}"
            
            fecha_firma = self.data.get('timestamp', 'No disponible')
            
            firma_texto = f"""<b>Nombre:</b> {nombre_firmante}<br/>
                <b>Identificación:</b> {id_firmante}<br/>
                <b>Fecha de Firma:</b> {fecha_firma}<br/>
                <b>Consentimiento Vía:</b> Portal Web v18.1 (Verificado)"""
            table_firma = Table([[firma_image, Paragraph(firma_texto, self.style_signature_info)]], colWidths=[2.8*inch, 4.4*inch], hAlign='LEFT')
            table_firma.setStyle(TableStyle([('VALIGN', (0,0), (-1,-1), 'TOP'), ('LEFTPADDING', (1,0), (1,0), 10)]))
            self.story.append(table_firma)
            return firma_path
        except Exception as e:
            self.story.append(Paragraph("Error al generar la imagen de la firma: " + str(e), self.style_body))
            return None

    def generate(self):
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as temp_pdf:
            pdf_path = temp_pdf.name
        doc = BaseDocTemplate(pdf_path, pagesize=letter, leftMargin=0.6*inch, rightMargin=0.6*inch, topMargin=1.1*inch, bottomMargin=0.6*inch)
        frame = Frame(doc.leftMargin, doc.bottomMargin, doc.width, doc.height, id='main_frame', topPadding=0.5*inch)
        template = PageTemplate(id='main_template', frames=[frame], onPage=self._on_page)
        doc.addPageTemplates([template])
        self.story.append(Paragraph("1. DATOS BÁSICOS", self.style_section_title))
        if self.data.get('client_type') == 'juridica':
            datos = [[Paragraph('Razón Social:', self.style_table_header), Paragraph(self.data.get('razon_social', ''), self.style_body), Paragraph('Dirección:', self.style_table_header), Paragraph(self.data.get('direccion', ''), self.style_body)], [Paragraph('Nombre Comercial:', self.style_table_header), Paragraph(self.data.get('nombre_comercial', ''), self.style_body), Paragraph('Ciudad:', self.style_table_header), Paragraph(self.data.get('ciudad', ''), self.style_body)], [Paragraph('NIT:', self.style_table_header), Paragraph(self.data.get('nit', ''), self.style_body), Paragraph('Teléfono:', self.style_table_header), Paragraph(self.data.get('telefono', ''), self.style_body)], [Paragraph('Representante Legal:', self.style_table_header), Paragraph(self.data.get('rep_legal', ''), self.style_body), Paragraph('Celular:', self.style_table_header), Paragraph(self.data.get('celular', ''), self.style_body)], [Paragraph('Correo para Notificaciones:', self.style_table_header), Paragraph(self.data.get('correo', ''), self.style_body), '', '']]
            table_basicos = Table(datos, colWidths=[1.5*inch, 2.1*inch, 1.5*inch, 2.1*inch], hAlign='LEFT', rowHeights=0.3*inch)
            table_basicos.setStyle(TableStyle([('GRID', (0,0), (-1,-1), 0.5, colors.lightgrey), ('VALIGN', (0,0), (-1,-1), 'MIDDLE'), ('BACKGROUND', (0,0), (0,-1), colors.HexColor(FERREINOX_DARK_BLUE)), ('BACKGROUND', (2,0), (2,-1), colors.HexColor(FERREINOX_DARK_BLUE)), ('SPAN', (1,-1), (3,-1)), ('LEFTPADDING', (0,0), (-1,-1), 6), ('RIGHTPADDING', (0,0), (-1,-1), 6)]))
            self.story.append(table_basicos)
            rep_legal_name, entity_name, entity_id, entity_email = self.data['rep_legal'], self.data['razon_social'], self.data['nit'], self.data['correo']
        else:
            datos = [[Paragraph('Nombre Completo:', self.style_table_header), Paragraph(self.data.get('nombre_natural', ''), self.style_body)], [Paragraph('No. Identificación:', self.style_table_header), Paragraph(self.data.get('cedula_natural', ''), self.style_body)], [Paragraph('Dirección:', self.style_table_header), Paragraph(self.data.get('direccion', ''), self.style_body)], [Paragraph('Teléfono / Celular:', self.style_table_header), Paragraph(self.data.get('telefono', ''), self.style_body)], [Paragraph('Correo Electrónico:', self.style_table_header), Paragraph(self.data.get('correo', ''), self.style_body)]]
            table_basicos = Table(datos, colWidths=[2.2*inch, 5.0*inch], hAlign='LEFT')
            table_basicos.setStyle(TableStyle([('GRID', (0,0), (-1,-1), 0.5, colors.lightgrey), ('BACKGROUND', (0,0), (0,-1), colors.HexColor(FERREINOX_DARK_BLUE)), ('VALIGN', (0,0), (-1,-1), 'MIDDLE'), ('LEFTPADDING', (0,0), (-1,-1), 6), ('RIGHTPADDING', (0,0), (-1,-1), 6), ('TOPPADDING', (0,0), (-1,-1), 5), ('BOTTOMPADDING', (0,0), (-1,-1), 5)]))
            self.story.append(table_basicos)
            rep_legal_name, entity_name, entity_id, entity_email = self.data['nombre_natural'], self.data['nombre_natural'], self.data['cedula_natural'], self.data['correo']
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

# --- CONEXIONES Y SECRETOS (BLOQUE CORREGIDO) ---
try:
    if "google_sheet_id" not in st.secrets or "google_credentials" not in st.secrets or "drive_folder_id" not in st.secrets:
        st.error("🚨 Error Crítico: Faltan 'google_sheet_id', 'drive_folder_id' o la sección '[google_credentials]' en tus secretos de Streamlit Cloud.")
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

# --- FUNCIONES DE CORREO ---
def send_email(recipient_email, subject, body, pdf_path=None, filename=None):
    try:
        if "email_credentials" not in st.secrets:
            st.error("🚨 Error de Configuración de Correo: La sección '[email_credentials]' no se encuentra en tus secretos de Streamlit.")
            return False

        creds = st.secrets["email_credentials"]
        sender_email = creds.get("smtp_user")
        sender_password = creds.get("smtp_password")
        smtp_server = creds.get("smtp_server")
        smtp_port = int(creds.get("smtp_port"))

        if not all([sender_email, sender_password, smtp_server, smtp_port]):
            st.error("🚨 Error de Configuración de Correo: Faltan credenciales completas en la sección '[email_credentials]'.")
            return False

        msg = MIMEMultipart()
        msg['From'] = sender_email
        msg['To'] = recipient_email
        msg['Subject'] = subject
        msg.attach(MIMEText(body, 'html'))

        if pdf_path and filename:
            with open(pdf_path, "rb") as f:
                part = MIMEApplication(f.read(), Name=filename)
            part['Content-Disposition'] = f'attachment; filename="{filename}"'
            msg.attach(part)
        
        # Use SSL context for secure connection
        context = smtplib.ssl.create_default_context()
        with smtplib.SMTP_SSL(smtp_server, smtp_port, context=context) as server:
            server.login(sender_email, sender_password)
            server.send_message(msg)
        return True
    except smtplib.SMTPAuthenticationError:
        st.error("❌ Error de Autenticación SMTP: Las credenciales de correo (usuario/contraseña de aplicación) son incorrectas.")
        st.error("Por favor, verifica tu 'smtp_user' y 'smtp_password' en los secretos de Streamlit. Si usas Gmail/Outlook, asegúrate de usar una 'contraseña de aplicación'.")
        return False
    except smtplib.SMTPException as e:
        st.error(f"❌ Error al conectar o enviar correo SMTP: {e}")
        st.error("Verifica el 'smtp_server' y 'smtp_port' en tus secretos. Podría ser un problema de red o configuración del servidor de correo.")
        return False
    except Exception as e:
        st.error(f"❌ Un error inesperado ocurrió al intentar enviar el correo: {e}")
        return False


# --- LÓGICA DE LA APLICACIÓN Y NAVEGACIÓN ---
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
    for key in list(st.session_state.keys()):
        del st.session_state[key]
    init_session_state()
    st.rerun() # Ensure rerun after full reset

# --- Flujo de la aplicación ---

if st.session_state.process_complete:
    st.success(f"**¡Proceso Finalizado Exitosamente!**")
    st.markdown(f"El formulario para **{st.session_state.final_razon_social}** ha sido generado, archivado y enviado a su correo electrónico.")
    if st.session_state.final_link:
        st.markdown(f"Puede previsualizar el documento final aquí: [**Ver PDF Generado**]({st.session_state.final_link})")
    st.button("Realizar otra vinculación", on_click=full_reset, use_container_width=True)

elif st.session_state.verification_code_sent:
    st.header("🔐 Verificación de Firma")
    st.info(f"Hemos enviado un código de 6 dígitos a su correo: **{st.session_state.form_data_cache.get('correo')}**. Por favor, ingréselo para completar el proceso.")
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
                    pdf_gen = PDFGeneratorPlatypus(form_data)
                    pdf_file_path = pdf_gen.generate()
                    
                    try:
                        # Ensure 18 columns consistently
                        if form_data['client_type'] == 'juridica':
                            log_row = [
                                timestamp,                      # 1
                                doc_id,                         # 2
                                form_data['razon_social'],      # 3
                                form_data['nit'],               # 4
                                form_data['rep_legal'],         # 5
                                form_data['correo'],            # 6
                                form_data['ciudad'],            # 7
                                f"{form_data['telefono']} / {form_data['celular']}", # 8
                                "Persona Jurídica",             # 9
                                "Verificado y Enviado",         # 10
                                st.session_state.generated_code,# 11
                                form_data['nombre_compras'],   # 12
                                form_data['email_compras'],    # 13
                                form_data['celular_compras'],  # 14
                                form_data['nombre_cartera'],   # 15
                                form_data['email_cartera'],    # 16
                                form_data['celular_cartera'],  # 17
                                "" # 18 - Campo vacío para fecha_nacimiento de persona natural
                            ]
                        else: # Persona Natural
                            log_row = [
                                timestamp,                      # 1
                                doc_id,                         # 2
                                form_data['nombre_natural'],    # 3 (Usamos nombre_natural como Razón Social para consistencia)
                                form_data['cedula_natural'],    # 4 (Usamos cédula_natural como NIT para consistencia)
                                form_data['nombre_natural'],    # 5 (Representante legal es el mismo)
                                form_data['correo'],            # 6
                                form_data['ciudad'] if 'ciudad' in form_data else "", # 7 (Añadido para consistencia)
                                form_data['telefono'],          # 8 (Teléfono/Celular)
                                "Persona Natural",              # 9
                                "Verificado y Enviado",         # 10
                                st.session_state.generated_code,# 11
                                "", "", "",                     # 12, 13, 14 - Campos vacíos para contactos de compras
                                "", "", "",                     # 15, 16, 17 - Campos vacíos para contactos de cartera
                                form_data['fecha_nacimiento'].strftime('%Y-%m-%d') if form_data.get('fecha_nacimiento') else "" # 18
                            ]
                        
                        worksheet.append_row(log_row, value_input_option='USER_ENTERED')
                        st.success("✅ Datos guardados exitosamente en Google Sheets.")
                    except Exception as sheet_error:
                        st.error("❌ ¡ERROR CRÍTICO AL GUARDAR EN GOOGLE SHEETS!")
                        st.warning("Asegúrese de que la hoja de cálculo tiene 18 columnas en el orden correcto y que los tipos de datos coinciden.")
                        st.error(f"Detalle técnico: {sheet_error}")

                    file_name = f"Autorizacion_{st.session_state.final_razon_social.replace(' ', '_')}_{entity_id_for_doc}.pdf"
                    email_body = f"""<h3>Confirmación de Autorización - Ferreinox S.A.S. BIC</h3><p>Estimado(a) <b>{form_data.get('rep_legal', form_data.get('nombre_natural'))}</b>,</p><p>Este correo confirma que hemos recibido y procesado exitosamente su formulario de autorización de datos.</p><p>Adjunto encontrará el documento PDF con la información y la constancia de su consentimiento.</p><p><b>ID del Documento:</b> {doc_id}<br><b>Fecha y Hora (Colombia):</b> {timestamp}</p><p>Gracias por confiar en Ferreinox S.A.S. BIC.</p>"""
                    
                    email_sent_successfully = send_email(form_data['correo'], f"Confirmación Vinculación - {st.session_state.final_razon_social}", email_body, pdf_file_path, file_name)
                    
                    if email_sent_successfully:
                        # Only upload to Drive and mark process complete if email was sent
                        media = MediaFileUpload(pdf_file_path, mimetype='application/pdf', resumable=True)
                        file = drive_service.files().create(body={'name': file_name, 'parents': [st.secrets["drive_folder_id"]]}, media_body=media, fields='id, webViewLink', supportsAllDrives=True).execute()
                        st.session_state.final_link = file.get('webViewLink')
                        st.session_state.process_complete = True
                        st.rerun()
                    else:
                        st.warning("El PDF fue generado y los datos se intentaron guardar, pero el correo no pudo ser enviado. Por favor, contacte a soporte.")
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
        st.subheader("Autorización para Tratamiento de Datos Personales")
        st.markdown(get_texto_tratamiento_datos("[Su Nombre / Nombre Rep. Legal]", "[Su Empresa / Su Nombre]", "[Su NIT / Cédula]"), unsafe_allow_html=True)
        st.subheader("Autorización para Consulta en Centrales de Riesgo (Habeas Data)")
        st.markdown(get_texto_habeas_data("[Su Nombre / Nombre Rep. Legal]", "[Su Empresa / Su Nombre]", "[Su NIT / Cédula]", "[Su Correo]"), unsafe_allow_html=True)
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
            with col2:
                nombre_comercial = st.text_input("Nombre Comercial*", value=st.session_state.form_data_cache.get('nombre_comercial', ''))
                ciudad = st.text_input("Ciudad*", value=st.session_state.form_data_cache.get('ciudad', ''))
                correo = st.text_input("Correo para Notificaciones*", value=st.session_state.form_data_cache.get('correo', ''))
                celular = st.text_input("Celular", value=st.session_state.form_data_cache.get('celular', ''))
            
            st.markdown("---")
            st.subheader("Datos del Representante Legal")
            col3, col4, col5 = st.columns(3)
            with col3:
                rep_legal = st.text_input("Nombre Rep. Legal*", value=st.session_state.form_data_cache.get('rep_legal', ''))
            with col4:
                cedula_rep_legal = st.text_input("C.C. Rep. Legal*", value=st.session_state.form_data_cache.get('cedula_rep_legal', ''))
            with col5:
                # Set default value for selectbox
                default_tipo_id_rep = st.session_state.form_data_cache.get('tipo_id', "C.C.")
                tipo_id_rep = st.selectbox("Tipo ID*", ["C.C.", "C.E."], index=["C.C.", "C.E."].index(default_tipo_id_rep) if default_tipo_id_rep in ["C.C.", "C.E."] else 0, key="id_r")
                lugar_exp_id_rep = st.text_input("Lugar Exp. ID*", value=st.session_state.form_data_cache.get('lugar_exp_id', ''), key="lex_r")
            
            with st.expander("👤 Contactos Adicionales (Opcional - Para programa de fidelización)"):
                st.info("Ayúdanos a tener una comunicación más fluida y a incluirte en nuestro programa 'Más Allá del Color'.")
                col_compras, col_cartera = st.columns(2)
                with col_compras:
                    st.write("**Contacto de Compras**")
                    nombre_compras = st.text_input("Nombre Encargado Compras", value=st.session_state.form_data_cache.get('nombre_compras', ''), key="nc")
                    email_compras = st.text_input("Email Compras", value=st.session_state.form_data_cache.get('email_compras', ''), key="ec")
                    celular_compras = st.text_input("Celular Compras", value=st.session_state.form_data_cache.get('celular_compras', ''), key="cc")
                with col_cartera:
                    st.write("**Contacto de Cartera**")
                    nombre_cartera = st.text_input("Nombre Encargado Cartera", value=st.session_state.form_data_cache.get('nombre_cartera', ''), key="nca")
                    email_cartera = st.text_input("Email Cartera", value=st.session_state.form_data_cache.get('email_cartera', ''), key="eca")
                    celular_cartera = st.text_input("Celular Cartera", value=st.session_state.form_data_cache.get('celular_cartera', ''), key="cca")

            st.subheader("✍️ Firma Digital de Aceptación")
            canvas_result = st_canvas(fill_color="#FFFFFF", stroke_width=3, stroke_color="#000000", height=200, key="canvas_j")
            
            if st.form_submit_button("Enviar y Solicitar Código de Verificación", use_container_width=True):
                if not all([razon_social, nit, correo, rep_legal, cedula_rep_legal, ciudad, nombre_comercial, lugar_exp_id_rep]) or canvas_result.image_data is None or np.all(canvas_result.image_data == 255): # Added check for empty canvas
                    st.warning("⚠️ Los campos marcados con * son obligatorios y la firma no puede estar vacía.")
                else:
                    form_data_to_process = {
                        'client_type': 'juridica', 'razon_social': razon_social,
                        'nombre_comercial': nombre_comercial, 'nit': nit, 'direccion': direccion,
                        'ciudad': ciudad, 'telefono': telefono, 'celular': celular, 'correo': correo,
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
                direccion_natural = st.text_input("Dirección*", value=st.session_state.form_data_cache.get('direccion', ''))
                telefono_natural = st.text_input("Teléfono / Celular*", value=st.session_state.form_data_cache.get('telefono', ''))
            with col2:
                correo_natural = st.text_input("Correo Electrónico*", value=st.session_state.form_data_cache.get('correo', ''))
                default_tipo_id_nat = st.session_state.form_data_cache.get('tipo_id', "C.C.")
                tipo_id_nat = st.selectbox("Tipo ID*", ["C.C.", "C.E."], index=["C.C.", "C.E."].index(default_tipo_id_nat) if default_tipo_id_nat in ["C.C.", "C.E."] else 0, key="id_n")
                lugar_exp_id_nat = st.text_input("Lugar Exp. ID*", value=st.session_state.form_data_cache.get('lugar_exp_id', ''), key="lex_n")
                
                # Handling date_input's default value for persistent state
                default_date = st.session_state.form_data_cache.get('fecha_nacimiento')
                if default_date and isinstance(default_date, str):
                    try:
                        default_date = datetime.strptime(default_date, '%Y-%m-%d').date()
                    except ValueError:
                        default_date = None # Reset if invalid string
                elif not isinstance(default_date, (datetime, type(None))): # Handles case where it might be a date object from previous run
                     default_date = None
                
                fecha_nacimiento = st.date_input("Fecha de Nacimiento*", min_value=datetime(1930, 1, 1).date(), max_value=datetime.now().date(), value=default_date)


            st.subheader("✍️ Firma Digital de Aceptación")
            canvas_result = st_canvas(fill_color="#FFFFFF", stroke_width=3, stroke_color="#000000", height=200, key="canvas_n")
            
            if st.form_submit_button("Enviar y Solicitar Código de Verificación", use_container_width=True):
                if not all([nombre_natural, cedula_natural, correo_natural, telefono_natural, fecha_nacimiento, direccion_natural, lugar_exp_id_nat]) or canvas_result.image_data is None or np.all(canvas_result.image_data == 255): # Added check for empty canvas
                    st.warning("⚠️ Los campos marcados con * y la firma son obligatorios.")
                else:
                    form_data_to_process = {
                        'client_type': 'natural', 'nombre_natural': nombre_natural,
                        'cedula_natural': cedula_natural, 'tipo_id': tipo_id_nat, 'lugar_exp_id': lugar_exp_id_nat,
                        'direccion': direccion_natural, 'correo': correo_natural, 'telefono': telefono_natural,
                        'firma_img_pil': Image.fromarray(canvas_result.image_data.astype('uint8'), 'RGBA'),
                        'fecha_nacimiento': fecha_nacimiento
                    }
                    st.session_state.final_razon_social = nombre_natural

    if form_data_to_process:
        with st.spinner("Generando y enviando código de verificación..."):
            st.session_state.form_data_cache = form_data_to_process
            code = str(random.randint(100000, 999999))
            st.session_state.generated_code = code
            email_body = f"""<h3>Su Código de Verificación para Ferreinox</h3>
                                <p>Hola,</p>
                                <p>Use el siguiente código para verificar su firma y completar el proceso de vinculación:</p>
                                <h2 style='text-align:center; letter-spacing: 5px;'>{code}</h2>
                                <p>Este código es válido por un tiempo limitado.</p>
                                <p>Si usted no solicitó este código, puede ignorar este mensaje.</p>
                                <br>
                                <p>Atentamente,</p>
                                <p><b>Ferreinox S.A.S. BIC</b></p>"""
            
            email_sent = send_email(form_data_to_process['correo'], "Su Código de Verificación - Ferreinox", email_body)
            
            if email_sent:
                st.session_state.verification_code_sent = True
                st.rerun()
            else:
                # Error message already displayed by send_email function
                pass # Do not rerun here if email failed, allow user to see error and try again
