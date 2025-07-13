# -*- coding: utf-8 -*-
# =========================================================================================
# APLICACIÓN INSTITUCIONAL DE VINCULACIÓN DE CLIENTES - FERREINOX S.A.S. BIC
# Versión 7.0: Compatible con Unidades Compartidas (Shared Drives) y corrección de Formulario
# =========================================================================================

# --- 1. IMPORTACIÓN DE LIBRERÍAS ---
import streamlit as st
from streamlit_drawable_canvas import st_canvas
import io
from PIL import Image
from datetime import datetime
import gspread
from reportlab.pdfgen import canvas
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
# (Los textos legales se mantienen sin cambios)
TEXTO_TRATAMIENTO_DATOS = """..."""
TEXTO_HABEAS_DATA = """..."""
TEXTO_DERECHOS = """..."""
TEXTO_VERACIDAD = """..."""

# --- 3. CONFIGURACIÓN DE LA PÁGINA ---
st.set_page_config(page_title="Portal de Vinculación | Ferreinox", page_icon="✍️", layout="wide")

# --- 4. ESTILO CSS ---
st.markdown("""
<style>
    .main { background-color: #F0F2F6; }
    .block-container { padding-top: 2rem; padding-bottom: 2rem; }
    h1, h2, h3 { color: #0D47A1; }
    .stButton>button { border-radius: 8px; border: 2px solid #0D47A1; background-color: #1565C0; color: white; font-weight: bold; }
    .stButton>button:hover { background-color: #0D47A1; }
</style>
""", unsafe_allow_html=True)

# --- 5. CLASE GENERADORA DE PDF ---
# (La clase PDFGenerator se mantiene sin cambios)
class PDFGenerator:
    pass

# --- 6. CONFIGURACIÓN DE CONEXIONES Y VARIABLES ---
try:
    creds_info = st.secrets["gcp_service_account"]
    scopes = ['https://www.googleapis.com/auth/drive', 'https://www.googleapis.com/auth/spreadsheets']
    creds = service_account.Credentials.from_service_account_info(creds_info, scopes=scopes)
    
    drive_service = build('drive', 'v3', credentials=creds)
    DRIVE_FOLDER_ID = st.secrets.get("drive_folder_id")

    gc = gspread.authorize(creds)
    GOOGLE_SHEET_ID = st.secrets.get("google_sheet_id")
    worksheet = gc.open_by_key(GOOGLE_SHEET_ID).sheet1

except Exception as e:
    st.error(f"🚨 Error de Configuración en las APIs de Google. Verifica los permisos y secretos. Detalle: {e}")
    st.stop()

# --- 7. INTERFAZ DE USUARIO CON STREAMLIT ---
if 'terms_viewed' not in st.session_state:
    st.session_state.terms_viewed = False

def enable_authorization():
    st.session_state.terms_viewed = True

st.image('LOGO FERREINOX SAS BIC 2024.png', width=250)
st.title("Portal de Vinculación y Autorización de Datos")
st.markdown("---")

# Estructura correcta: El botón con on_click está FUERA del formulario.
st.header("📜 Términos, Condiciones y Autorización")
with st.expander("Haga clic aquí para leer los Términos, Condiciones y Autorizaciones"):
    st.subheader("1. Autorización para Tratamiento de Datos Personales")
    st.markdown(TEXTO_TRATAMIENTO_DATOS, unsafe_allow_html=True)
    # ... (resto de los textos legales) ...

st.button("He leído los términos y deseo continuar", on_click=enable_authorization, use_container_width=True)
st.markdown("---")

# El formulario solo contiene campos de entrada y el botón de envío final.
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
    canvas_result = st.canvas(height=200, drawing_mode="freedraw", key="canvas_firma")
    
    # Este es el único botón permitido con acción dentro del formulario.
    submit_button = st.form_submit_button(label="✅ Aceptar y Enviar Documento Firmado", use_container_width=True)

# --- 8. LÓGICA DE PROCESAMIENTO AL ENVIAR ---
if submit_button:
    if not st.session_state.auth_checkbox:
        st.warning("⚠️ Para continuar, debe aceptar las autorizaciones marcando la casilla correspondiente.")
    elif canvas_result.image_data is None:
        st.warning("🖋️ La firma es indispensable para validar el documento.")
    else:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        doc_id = f"FER-{datetime.now().strftime('%Y%m%d%H%M%S')}-{nit}"
        
        with st.spinner("Procesando y registrando trazabilidad... ⏳"):
            try:
                # ... (Lógica para guardar en Google Sheets sin cambios) ...
                
                # ... (Lógica para generar el PDF sin cambios) ...
                form_data = {
                    'rep_legal': rep_legal, 'cedula_rep_legal': cedula_rep_legal,
                    'razon_social': razon_social, 'nit': nit, 'correo': correo,
                    'doc_id': doc_id, 'timestamp': timestamp
                }
                form_data['firma_img_pil'] = Image.fromarray(canvas_result.image_data.astype('uint8'), 'RGBA')

                pdf_buffer = io.BytesIO()
                # pdf_gen = PDFGenerator(pdf_buffer, form_data) # Asumiendo que la clase PDFGenerator está completa
                # pdf_gen.generate()
                pdf_buffer.seek(0)
                
                st.write("Archivando PDF en Google Drive...")
                file_name = f"Consentimiento_{razon_social.replace(' ', '_')}_{nit}.pdf"
                file_metadata = {'name': file_name, 'parents': [DRIVE_FOLDER_ID]}
                media = MediaFileUpload(pdf_buffer, mimetype='application/pdf', resumable=True)
                
                # =========================================================================
                # AJUSTE CLAVE PARA UNIDADES COMPARTIDAS (SHARED DRIVES)
                # =========================================================================
                file = drive_service.files().create(
                    body=file_metadata,
                    media_body=media,
                    fields='id, webViewLink',
                    supportsAllDrives=True  # <-- Esta es la instrucción especial
                ).execute()

                st.balloons()
                st.success(f"**¡Proceso Finalizado Exitosamente!**")
                st.markdown(f"El documento para **{razon_social}** ha sido generado y archivado de forma segura.")
                st.markdown(f"Puede previsualizar el documento final aquí: [**Ver PDF Generado**]({file.get('webViewLink')})")

            except Exception as e:
                st.error(f"❌ ¡Ha ocurrido un error inesperado! Detalle técnico: {e}")
