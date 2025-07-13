# -*- coding: utf-8 -*-
# =========================================================================================
# APLICACIÓN INSTITUCIONAL DE VINCULACIÓN DE CLIENTES - FERREINOX S.A.S. BIC
# Versión 8.1 (Diagnóstico Mejorado)
# Fecha: 12 de Julio de 2025
# =========================================================================================

# --- 1. IMPORTACIÓN DE LIBRERÍAS ---
import streamlit as st
from streamlit_drawable_canvas import st_canvas
import io
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
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

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
        text_for_pdf = text.replace('<ul>','').replace('</ul>','').replace('<li>','<para>• ').replace('</li>','</para>').replace('<b>','<b>').replace('</b>','</b>')
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
        self.c.drawImage(self.data['firma_img_pil'], 50, y_pos - 70, width=180, height=60, mask='auto')
        self.c.line(50, y_pos - 80, 230, y_pos - 80)
        self.c.setFont("Helvetica", 9)
        self.c.drawString(50, y_pos - 90, self.data['rep_legal'])

        data_trazabilidad = [
            ['Concepto', 'Registro'],
            ['ID Único del Documento:', self.data.get('doc_id', '')],
            ['Fecha y Hora de Firma:', self.data.get('timestamp', '')],
            ['Método de Consentimiento:', 'Aceptación en portal web tras visualización de términos.'],
            ['Correo Electrónico Asociado:', self.data.get('correo', '')]
        ]
        tabla = Table(data_trazabilidad, colWidths=[1.8*inch, 2.5*inch], rowHeights=0.3*inch)
        tabla.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (1, 0), self.color_primary),('TEXTCOLOR',(0,0),(-1,0),colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'), ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'), ('FONTNAME', (0, 1), (0, -1), 'Helvetica-Bold'),
            ('GRID', (0,0), (-1,-1), 1, self.color_secondary)
        ]))
        tabla.wrapOn(self.c, self.width, self.height)
        tabla.drawOn(self.c, 300, y_pos - 90)

        self.c.save()

# --- 6. CONFIGURACIÓN DE CONEXIONES Y VARIABLES (CON DIAGNÓSTICO MEJORADO) ---
try:
    # Paso 1: Verificar que los secretos existen
    if "gcp_service_account" not in st.secrets or "google_sheet_id" not in st.secrets or "drive_folder_id" not in st.secrets:
        st.error("🚨 Error Crítico: Faltan uno o más secretos en la configuración de Streamlit (gcp_service_account, google_sheet_id, drive_folder_id).")
        st.stop()

    creds_info = st.secrets["gcp_service_account"]
    GOOGLE_SHEET_ID = st.secrets["google_sheet_id"]
    DRIVE_FOLDER_ID = st.secrets["drive_folder_id"]
    scopes = ['https://www.googleapis.com/auth/drive', 'https://www.googleapis.com/auth/spreadsheets']
    
    # Paso 2: Crear credenciales
    creds = service_account.Credentials.from_service_account_info(creds_info, scopes=scopes)
    
    # Paso 3: Conectar a Google Sheets
    with st.spinner("Conectando con el registro de trazabilidad (Google Sheets)..."):
        gc = gspread.authorize(creds)
        worksheet = gc.open_by_key(GOOGLE_SHEET_ID).sheet1
    
    # Paso 4: Conectar a Google Drive
    with st.spinner("Conectando con el archivo digital (Google Drive)..."):
        drive_service = build('drive', 'v3', credentials=creds)

except gspread.exceptions.SpreadsheetNotFound:
    st.error(f"🚨 Error de Configuración: No se pudo encontrar la hoja de Google Sheets.")
    st.error(f"El ID de la hoja que se intentó abrir fue: '{st.secrets.get('google_sheet_id')}'")
    st.warning("Por favor, verifica los siguientes puntos:")
    st.markdown("""
    1.  **El `google_sheet_id` en tus secretos de Streamlit es correcto.** Cópialo directamente desde la URL de tu Google Sheet.
    2.  **Has compartido la hoja de cálculo con el correo de la cuenta de servicio.** El correo se encuentra dentro de tu archivo de secretos (`client_email`) y debe tener permisos de **Editor** en la hoja.
    """)
    st.stop()
except Exception as e:
    st.error(f"🚨 Ha ocurrido un error inesperado durante la configuración con las APIs de Google.")
    st.error(f"Detalle técnico del error: {e}")
    st.warning("Verifica que las APIs de Google Drive y Google Sheets estén activadas en tu proyecto de Google Cloud.")
    st.stop()

# --- 7. INTERFAZ DE USUARIO CON STREAMLIT ---
if 'terms_viewed' not in st.session_state:
    st.session_state.terms_viewed = False

def enable_authorization():
    st.session_state.terms_viewed = True

# Asegúrate de que el logo esté en la misma carpeta o proporciona la ruta completa
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
    # CORRECCIÓN: Se usa st_canvas en lugar de st.canvas
    canvas_result = st_canvas(
        fill_color="rgba(255, 255, 255, 0)",  # Fondo transparente
        stroke_width=3,
        stroke_color="#000000",
        background_color="#FFFFFF",
        height=200,
        drawing_mode="freedraw",
        key="canvas_firma"
    )
    
    submit_button = st.form_submit_button(label="✅ Aceptar y Enviar Documento Firmado", use_container_width=True)

# --- 8. LÓGICA DE PROCESAMIENTO AL ENVIAR ---
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
        
        with st.spinner("Procesando y registrando trazabilidad... ⏳"):
            try:
                st.write("Paso 1/3: Guardando registro en Log de Trazabilidad...")
                log_row = [timestamp, doc_id, razon_social, nit, rep_legal, correo, "Enviado"]
                worksheet.append_row(log_row, value_input_option='USER_ENTERED')
                
                st.write("Paso 2/3: Generando documento PDF institucional...")
                form_data = {
                    'rep_legal': rep_legal, 'cedula_rep_legal': cedula_rep_legal,
                    'razon_social': razon_social, 'nit': nit, 'correo': correo,
                    'doc_id': doc_id, 'timestamp': timestamp,
                    'texto_tratamiento': TEXTO_TRATAMIENTO_DATOS, 'texto_habeas': TEXTO_HABEAS_DATA,
                }
                # Convertir la imagen del canvas a un objeto de imagen PIL
                form_data['firma_img_pil'] = Image.fromarray(canvas_result.image_data.astype('uint8'), 'RGBA')

                pdf_buffer = io.BytesIO()
                pdf_gen = PDFGenerator(pdf_buffer, form_data)
                pdf_gen.generate()
                pdf_buffer.seek(0)
                
                st.write("Paso 3/3: Archivando PDF en Google Drive...")
                file_name = f"Consentimiento_{razon_social.replace(' ', '_')}_{nit}.pdf"
                file_metadata = {'name': file_name, 'parents': [DRIVE_FOLDER_ID]}
                media = MediaFileUpload(pdf_buffer, mimetype='application/pdf', resumable=True)
                
                # Sube el archivo a Drive, asegurando compatibilidad con Unidades Compartidas
                file = drive_service.files().create(
                    body=file_metadata,
                    media_body=media,
                    fields='id, webViewLink',
                    supportsAllDrives=True
                ).execute()

                st.balloons()
                st.success(f"**¡Proceso Finalizado Exitosamente!**")
                st.markdown(f"El documento para **{razon_social}** ha sido generado y archivado de forma segura.")
                st.markdown(f"Puede previsualizar el documento final aquí: [**Ver PDF Generado**]({file.get('webViewLink')})")

            except Exception as e:
                st.error(f"❌ ¡Ha ocurrido un error inesperado durante el envío! Detalle técnico: {e}")
                # Intenta registrar el error en la hoja de cálculo para tener trazabilidad
                try:
                    worksheet.append_row([timestamp, doc_id, razon_social, nit, rep_legal, correo, f"Error: {e}"], value_input_option='USER_ENTERED')
                except Exception as log_e:
                    st.error(f"No se pudo registrar el error en Google Sheets. Detalle: {log_e}")
