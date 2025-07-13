# -*- coding: utf-8 -*-
# =========================================================================================
# APLICACIÓN INSTITUCIONAL DE VINCULACIÓN DE CLIENTES - FERREINOX S.A.S. BIC
# Versión 9.0 (Mejora de Validez Legal con Notificación por Correo y Corrección de PDF)
# Fecha: 12 de Julio de 2025
# =========================================================================================

# --- 1. IMPORTACIÓN DE LIBRERÍAS ---
import streamlit as st
from streamlit_drawable_canvas import st_canvas
import io
import json
from PIL import Image
from datetime import datetime
import gspread
from reportlab.pdfgen import canvas as pdf_canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import Paragraph, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_JUSTIFY
from reportlab.lib.units import inch
from reportlab.lib.utils import ImageReader # <-- IMPORTANTE: Librería para manejar imágenes en memoria
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication

# --- 2. TEXTOS LEGALES (CONSTANTES) ---
TEXTO_TRATAMIENTO_DATOS = """
De conformidad con la Política de Tratamiento de Datos Personales de FERREINOX S.A.S. BIC (NIT. 800224617-8),
la cual está disponible en sus instalaciones y en el sitio web www.ferreinox.co, autorizo a la empresa para:
<ul>
    <li>Utilizar mis datos personales para fines relacionados con nuestra relación comercial.</li>
    <li><b>Recibir Comunicaciones:</b> Acepto recibir información sobre ventas, compras, facturas, documentos de cobro, ofertas, promociones y publicidad.</li>
    <li><b>Mantenerme Informado:</b> Acepto recibir notificaciones sobre novedades, cambios y actualizaciones de la compañía.</li>
    <li><b>Fines Administrativos:</b> Autorizo el uso de mis datos para fines estadísticos o administrativos necesarios para la operación de FERREINOX S.A.S. BIC.</li>
</ul>
La empresa se compromete a almacenar mis datos en entornos seguros, protegiéndolos del acceso no autorizado y manteniendo la confidencialidad.
"""
TEXTO_HABEAS_DATA = """
En ejercicio de mi derecho a la autodeterminación informática, autorizo de manera voluntaria, expresa e irrevocable a
FERREINOX S.A.S. BIC (o a quien represente sus derechos en el futuro) para:
<ul>
    <li><b>Consultar y Administrar mi Información:</b> Capturar, tratar, procesar, verificar y usar mi información comercial, crediticia, financiera y de servicios.</li>
    <li><b>Evaluar Riesgo Crediticio:</b> Utilizar mi información personal para el estudio, análisis y eventual otorgamiento de un crédito o para la celebración de cualquier otro contrato comercial.</li>
    <li><b>Reportar a Centrales de Riesgo:</b> Reportar, procesar y divulgar mi comportamiento e historial crediticio (tanto los hábitos positivos como los negativos de pago) a las centrales de información y/o riesgo autorizadas por la Ley 1266 de 2008, tales como Datacrédito, Cifin y Procrédito.</li>
</ul>
Asimismo, autorizo que la comunicación previa al reporte negativo, exigida por la ley, pueda ser enviada a través de un mensaje de datos al correo electrónico que suministraré en este formulario.
"""
TEXTO_DERECHOS = """
Usted tiene derecho a:
<ul>
    <li>Conocer, actualizar, rectificar o solicitar la eliminación de sus datos personales.</li>
    <li>Solicitar prueba de esta autorización.</li>
    <li>Ser informado sobre el uso que se le ha dado a su información.</li>
    <li>Presentar quejas ante la Superintendencia de Industria y Comercio si considera que sus derechos han sido vulnerados.</li>
    <li>Revocar esta autorización en cualquier momento.</li>
    <li>Acceder de forma gratuita a sus datos personales.</li>
</ul>
Puede ejercer sus derechos a través de los siguientes canales:
<ul>
    <li><b>Correo electrónico:</b> tiendapintucopereira@ferreinox.co</li>
    <li><b>Teléfono:</b> (6) 333 0101 opción 1</li>
    <li><b>Dirección:</b> CR 13 19-26 Pereira, Risaralda</li>
    <li><b>Página web:</b> www.ferreinox.co</li>
</ul>
"""
TEXTO_VERACIDAD = """
Certifico que toda la información que proporciono en este formulario es veraz, completa, exacta y actualizada.
Entiendo que cualquier error en la información suministrada será de mi exclusiva responsabilidad.
<br><br>
Declaro que he leído, comprendido y aceptado en su totalidad el contenido de estas autorizaciones y las finalidades descritas.
En consecuencia, procedo a diligenciar mi información.
"""

# --- 3. CONFIGURACIÓN DE LA PÁGINA ---
st.set_page_config(page_title="Portal de Vinculación | Ferreinox", page_icon="✍️", layout="wide")

# --- 4. ESTILO CSS ---
st.markdown("""
<style>
    .main { background-color: #F0F2F6; }
    .block-container { padding-top: 2rem; padding-bottom: 2rem; }
    h1, h2, h3 { color: #0D47A1; }
    .stButton>button {
        border-radius: 8px; border: 2px solid #0D47A1; background-color: #1565C0;
        color: white; font-weight: bold; transition: all 0.3s;
    }
    .stButton>button:hover { background-color: #0D47A1; }
</style>
""", unsafe_allow_html=True)

# --- 5. CLASE GENERADORA DE PDF ---
class PDFGenerator:
    def __init__(self, buffer, data):
        self.buffer = buffer
        self.data = data
        self.c = pdf_canvas.Canvas(self.buffer, pagesize=letter)
        self.width, self.height = letter
        self.color_primary = colors.HexColor('#0D47A1')
        self.color_secondary = colors.HexColor('#1565C0')
        self.styles = getSampleStyleSheet()
        self.paragraph_style = ParagraphStyle('normal', parent=self.styles['Normal'], fontName='Helvetica', fontSize=9, leading=14, alignment=TA_JUSTIFY)

    def _draw_header(self, page_title):
        self.c.saveState()
        try:
            # Asegúrate de que el logo esté en la misma carpeta o proporciona la ruta completa
            self.c.drawImage('LOGO FERREINOX SAS BIC 2024.png', 50, self.height - 70, width=150, height=50, mask='auto')
        except:
            self.c.drawString(50, self.height - 60, "Ferreinox S.A.S. BIC")
        self.c.setFont("Helvetica-Bold", 14)
        self.c.setFillColor(self.color_primary)
        self.c.drawCentredString(self.width / 2, self.height - 100, page_title)
        self.c.restoreState()

    def _draw_paragraph(self, x, y, width, text):
        text_for_pdf = text.replace('<ul>','').replace('</ul>','')
        text_for_pdf = text_for_pdf.replace('<li>','<br/>  •   ')
        text_for_pdf = text_for_pdf.replace('</li>','')
        text_for_pdf = text_for_pdf.replace('\n', ' ')
        text_for_pdf = ' '.join(text_for_pdf.split())
        p = Paragraph(text_for_pdf, self.paragraph_style)
        p.wrapOn(self.c, width, self.height)
        p_height = p.height
        p.drawOn(self.c, x, y - p_height)
        return p_height

    def generate(self):
        self._draw_header("CONSENTIMIENTO Y AUTORIZACIÓN DE DATOS")
        y_pos = self.height - 150

        self.c.setFont("Helvetica-Bold", 12)
        self.c.setFillColor(self.color_primary)
        self.c.drawString(50, y_pos, "1. Autorización para Tratamiento de Datos Personales")
        y_pos -= 20
        h = self._draw_paragraph(50, y_pos, 500, self.data['texto_tratamiento'])
        y_pos -= (h + 30)

        self.c.setFont("Helvetica-Bold", 12)
        self.c.setFillColor(self.color_primary)
        self.c.drawString(50, y_pos, "2. Autorización para Consulta y Reporte en Centrales de Riesgo")
        y_pos -= 20
        h = self._draw_paragraph(50, y_pos, 500, self.data['texto_habeas'])
        y_pos -= (h + 40)

        self.c.setFont("Helvetica-Bold", 11)
        self.c.setFillColor(self.color_secondary)
        self.c.drawString(50, y_pos, "CONSTANCIA DE ACEPTACIÓN Y FIRMA")
        self.c.line(50, y_pos - 5, self.width - 50, y_pos - 5)
        y_pos -= 30

        self.c.setFont("Helvetica-Bold", 10)
        self.c.drawString(50, y_pos, "Firma del Representante Legal:")
        
        # --- CORRECCIÓN CLAVE PARA EL MANEJO DE LA IMAGEN DE LA FIRMA ---
        # Se convierte la imagen a un stream de bytes y se usa ImageReader de ReportLab.
        firma_buffer = io.BytesIO()
        self.data['firma_img_pil'].save(firma_buffer, format='PNG')
        firma_buffer.seek(0)
        
        # Se envuelve el buffer en ImageReader para que ReportLab lo procese correctamente.
        self.c.drawImage(ImageReader(firma_buffer), 50, y_pos - 70, width=180, height=60, mask='auto')
        self.c.line(50, y_pos - 80, 230, y_pos - 80)
        self.c.setFont("Helvetica", 9)
        self.c.drawString(50, y_pos - 90, self.data['rep_legal'])

        data_trazabilidad = [
            ['Concepto de Trazabilidad', 'Registro'],
            ['ID Único del Documento:', self.data.get('doc_id', '')],
            ['Fecha y Hora de Firma:', self.data.get('timestamp', '')],
            ['Correo Electrónico Asociado:', self.data.get('correo', '')],
            ['Consentimiento Registrado Vía:', 'Portal Web Institucional v9.0'],
            ['IP de Origen:', 'No registrada (Estándar Streamlit Cloud)']
        ]
        tabla = Table(data_trazabilidad, colWidths=[2*inch, 2.5*inch], rowHeights=0.3*inch)
        tabla.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (1, 0), self.color_primary),('TEXTCOLOR',(0,0),(-1,0),colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'), ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'), ('FONTNAME', (0, 1), (0, -1), 'Helvetica-Bold'),
            ('GRID', (0,0), (-1,-1), 1, self.color_secondary)
        ]))
        tabla.wrapOn(self.c, self.width, self.height)
        tabla.drawOn(self.c, 280, y_pos - 90)

        self.c.save()

# --- 6. CONFIGURACIÓN DE CONEXIONES Y SECRETOS ---
# --- 6.A. INSTRUCCIONES PARA NUEVOS SECRETOS DE CORREO ---
# Para activar la notificación por correo, debes añadir los siguientes secretos a tu cuenta de Streamlit:
# 1. sender_email: El correo desde el cual se enviarán las notificaciones (ej: "notificaciones.ferreinox@gmail.com").
# 2. sender_password: La contraseña de aplicación de ese correo. IMPORTANTE: No uses tu contraseña principal.
#                    Busca "Crear contraseñas de aplicación" para tu proveedor de correo (Gmail, Outlook, etc.).
# 3. smtp_server: El servidor de correo (ej: "smtp.gmail.com").
# 4. smtp_port: El puerto del servidor (ej: 587 para TLS).
try:
    required_secrets = [
        "type", "project_id", "private_key_id", "private_key", "client_email",
        "client_id", "auth_uri", "token_uri", "auth_provider_x509_cert_url",
        "client_x509_cert_url", "google_sheet_id", "drive_folder_id",
        # Nuevos secretos para el envío de correo
        "sender_email", "sender_password", "smtp_server", "smtp_port"
    ]
    missing_secrets = [secret for secret in required_secrets if secret not in st.secrets]
    if missing_secrets:
        st.error(f"🚨 Error Crítico: Faltan secretos en la configuración: {', '.join(missing_secrets)}")
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
    st.warning("Verifica que las credenciales y los secretos de Google y del correo electrónico sean correctos.")
    st.stop()

# --- 7. INTERFAZ DE USUARIO ---
if 'terms_viewed' not in st.session_state:
    st.session_state.terms_viewed = False

def enable_authorization():
    st.session_state.terms_viewed = True

try:
    st.image('LOGO FERREINOX SAS BIC 2024.png', width=250)
except Exception:
    st.image("https://placehold.co/250x80/0D47A1/FFFFFF?text=Ferreinox+S.A.S.+BIC", width=250)

st.title("Portal de Vinculación y Autorización de Datos")
st.markdown("---")

st.header("📜 Términos, Condiciones y Autorización")
with st.expander("Haga clic aquí para leer los Términos, Condiciones y Autorizaciones"):
    st.subheader("1. Autorización para Tratamiento de Datos Personales")
    st.markdown(TEXTO_TRATAMIENTO_DATOS, unsafe_allow_html=True)
    st.subheader("2. Autorización para Consulta y Reporte en Centrales de Riesgo")
    st.markdown(TEXTO_HABEAS_DATA, unsafe_allow_html=True)
    st.subheader("3. Sus Derechos como Titular de la Información")
    st.markdown(TEXTO_DERECHOS, unsafe_allow_html=True)
    st.subheader("4. Declaración de Veracidad y Aceptación")
    st.markdown(TEXTO_VERACIDAD, unsafe_allow_html=True)

st.button("He leído los términos y deseo continuar", on_click=enable_authorization, use_container_width=True)
st.markdown("---")

with st.form(key="formulario_principal"):
    st.header("👤 Datos del Representante Legal")
    col1, col2 = st.columns(2)
    with col1:
        rep_legal = st.text_input("Nombre Completo*", placeholder="Ej: Ana María Pérez")
    with col2:
        cedula_rep_legal = st.text_input("Cédula de Ciudadanía*", placeholder="Ej: 1020304050")
    
    st.header("🏢 Datos de la Empresa")
    col3, col4 = st.columns(2)
    with col3:
        razon_social = st.text_input("Razón Social*", placeholder="Mi Empresa S.A.S.")
        correo = st.text_input("Correo Electrónico para Notificaciones*", placeholder="ejemplo@correo.com")
    with col4:
        nit = st.text_input("NIT*", placeholder="900.123.456-7")

    autoriza = st.checkbox(
        "**Acepto las autorizaciones.** Declaro que he leído, comprendido y aceptado en su totalidad el contenido de las autorizaciones.",
        disabled=not st.session_state.terms_viewed,
        key="auth_checkbox"
    )
    
    st.header("✍️ Firma Digital")
    st.caption("Por favor, firme en el recuadro para sellar su consentimiento.")
    canvas_result = st_canvas(
        fill_color="rgba(255, 255, 255, 0)", stroke_width=3, stroke_color="#000000",
        background_color="#FFFFFF", height=200, drawing_mode="freedraw", key="canvas_firma"
    )
    
    submit_button = st.form_submit_button(label="✅ Aceptar y Enviar Documento Firmado", use_container_width=True)

# --- 8. LÓGICA DE PROCESAMIENTO ---
# --- 8.A. FUNCIÓN PARA ENVIAR CORREO DE CONFIRMACIÓN ---
def send_email_with_attachment(recipient_email, subject, body, pdf_buffer, filename):
    msg = MIMEMultipart()
    msg['From'] = st.secrets["sender_email"]
    msg['To'] = recipient_email
    msg['Subject'] = subject
    
    msg.attach(MIMEText(body, 'html'))
    
    pdf_buffer.seek(0)
    part = MIMEApplication(pdf_buffer.read(), Name=filename)
    part['Content-Disposition'] = f'attachment; filename="{filename}"'
    msg.attach(part)
    
    server = smtplib.SMTP(st.secrets["smtp_server"], st.secrets["smtp_port"])
    server.starttls()
    server.login(st.secrets["sender_email"], st.secrets["sender_password"])
    server.send_message(msg)
    server.quit()

if submit_button:
    # Validaciones de campos
    campos_validos = all([rep_legal, cedula_rep_legal, razon_social, nit, correo])
    if not campos_validos:
        st.warning("⚠️ Por favor, complete todos los campos marcados con *.")
    elif not st.session_state.auth_checkbox:
        st.warning("⚠️ Para continuar, debe aceptar las autorizaciones marcando la casilla correspondiente.")
    elif canvas_result.image_data is None:
        st.warning("🖋️ La firma es indispensable para validar el documento.")
    else:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        doc_id = f"FER-{datetime.now().strftime('%Y%m%d%H%M%S')}-{nit}"
        
        with st.spinner("Procesando su solicitud... ⏳"):
            try:
                # PASO 1: Guardar registro en Google Sheets
                st.write("Paso 1/4: Guardando registro en Log de Trazabilidad...")
                log_row = [timestamp, doc_id, razon_social, nit, rep_legal, correo, "Enviado y Notificado"]
                worksheet.append_row(log_row, value_input_option='USER_ENTERED')
                
                # PASO 2: Generar el documento PDF
                st.write("Paso 2/4: Generando documento PDF institucional...")
                form_data = {
                    'rep_legal': rep_legal, 'cedula_rep_legal': cedula_rep_legal,
                    'razon_social': razon_social, 'nit': nit, 'correo': correo,
                    'doc_id': doc_id, 'timestamp': timestamp,
                    'texto_tratamiento': TEXTO_TRATAMIENTO_DATOS, 'texto_habeas': TEXTO_HABEAS_DATA,
                    'firma_img_pil': Image.fromarray(canvas_result.image_data.astype('uint8'), 'RGBA')
                }
                pdf_buffer = io.BytesIO()
                pdf_gen = PDFGenerator(pdf_buffer, form_data)
                pdf_gen.generate()
                
                # PASO 3: Enviar correo de notificación con el PDF adjunto
                st.write("Paso 3/4: Enviando correo de confirmación al cliente...")
                file_name = f"Consentimiento_Ferreinox_{razon_social.replace(' ', '_')}_{nit}.pdf"
                email_body = f"""
                <h3>Confirmación de Vinculación y Autorización - Ferreinox S.A.S. BIC</h3>
                <p>Estimado(a) <b>{rep_legal}</b>,</p>
                <p>Reciba un cordial saludo.</p>
                <p>Este correo confirma que hemos recibido y procesado exitosamente el formulario de vinculación y autorización de tratamiento de datos para la empresa <b>{razon_social}</b> (NIT: {nit}).</p>
                <p>Adjunto a este mensaje encontrará el documento PDF con la constancia de su consentimiento y la firma registrada.</p>
                <p><b>ID del Documento:</b> {doc_id}<br>
                   <b>Fecha de registro:</b> {timestamp}</p>
                <p>Agradecemos su confianza en Ferreinox S.A.S. BIC.</p>
                <br>
                <p><i>Este es un mensaje automático, por favor no responda a este correo.</i></p>
                """
                send_email_with_attachment(correo, f"Confirmación de Vinculación - {razon_social}", email_body, pdf_buffer, file_name)

                # PASO 4: Archivar el PDF en Google Drive
                st.write("Paso 4/4: Archivando PDF en el repositorio digital...")
                pdf_buffer.seek(0)
                file_metadata = {'name': file_name, 'parents': [DRIVE_FOLDER_ID]}
                media = MediaFileUpload(pdf_buffer, mimetype='application/pdf', resumable=True)
                file = drive_service.files().create(
                    body=file_metadata, media_body=media, fields='id, webViewLink', supportsAllDrives=True
                ).execute()

                st.balloons()
                st.success(f"**¡Proceso Finalizado Exitosamente!**")
                st.markdown(f"El documento para **{razon_social}** ha sido generado, archivado y enviado a su correo electrónico.")
                st.markdown(f"Puede previsualizar el documento final aquí: [**Ver PDF Generado**]({file.get('webViewLink')})")

            except Exception as e:
                st.error(f"❌ ¡Ha ocurrido un error inesperado durante el envío! Por favor, intente de nuevo.")
                st.error(f"Detalle técnico: {e}")
                # Intenta registrar el error en la hoja de cálculo
                try:
                    worksheet.append_row([timestamp, doc_id, razon_social, nit, rep_legal, correo, f"Error: {e}"], value_input_option='USER_ENTERED')
                except Exception as log_e:
                    st.error(f"No se pudo registrar el error en Google Sheets. Detalle: {log_e}")
