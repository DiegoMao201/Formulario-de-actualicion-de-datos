# -*- coding: utf-8 -*-
# =========================================================================================
# APLICACIÓN INSTITUCIONAL DE VINCULACIÓN DE CLIENTES - FERREINOX S.A.S. BIC
# Versión 5.0: Trazabilidad en Google Sheets y Corrección de Error de Formulario
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
TEXTO_TRATAMIENTO_DATOS = "..." # (Mismo texto de la versión anterior)
TEXTO_HABEAS_DATA = "..." # (Mismo texto de la versión anterior)
TEXTO_DERECHOS = "..." # (Mismo texto de la versión anterior)
TEXTO_VERACIDAD = "..." # (Mismo texto de la versión anterior)

# --- 3. CONFIGURACIÓN DE LA PÁGINA ---
st.set_page_config(page_title="Portal de Vinculación | Ferreinox", page_icon="✍️", layout="wide")

# --- 4. ESTILO CSS ---
st.markdown("""<style>...</style>""", unsafe_allow_html=True) # (Mismo CSS de la versión anterior)

# --- 5. CLASE GENERADORA DE PDF ---
class PDFGenerator:
    # ... (Clase PDFGenerator sin cambios respecto a la versión anterior) ...
    pass

# --- 6. CONFIGURACIÓN DE CONEXIONES Y VARIABLES ---
try:
    creds_info = st.secrets["gcp_service_account"]
    creds = service_account.Credentials.from_service_account_info(creds_info, scopes=[
        'https://www.googleapis.com/auth/drive',
        'https://www.googleapis.com/auth/spreadsheets'
    ])
    
    # Conexión a Google Drive
    drive_service = build('drive', 'v3', credentials=creds)
    DRIVE_FOLDER_ID = st.secrets.get("drive_folder_id", "REEMPLAZA_ID_CARPETA_DRIVE")

    # Conexión a Google Sheets
    gc = gspread.service_account(credentials=creds)
    GOOGLE_SHEET_ID = st.secrets.get("google_sheet_id", "REEMPLAZA_ID_HOJA_CALCULO")
    worksheet = gc.open_by_key(GOOGLE_SHEET_ID).sheet1

except Exception as e:
    st.error(f"🚨 Error de Configuración en las APIs de Google. Verifica los permisos y secretos. Detalle: {e}")
    st.stop()


# --- 7. INTERFAZ DE USUARIO CON STREAMLIT ---
# Inicializar estado de sesión
if 'terms_viewed' not in st.session_state:
    st.session_state.terms_viewed = False

def enable_authorization():
    st.session_state.terms_viewed = True

# Encabezado
st.image('LOGO FERREINOX SAS BIC 2024.png', width=250)
st.title("Portal de Vinculación y Autorización de Datos")
st.markdown("---")

# ========================== SOLUCIÓN AL ERROR ==========================
# El botón para habilitar la autorización AHORA ESTÁ FUERA del formulario.
# Esto evita el error `StreamlitInvalidFormCallbackError`.
# =====================================================================
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

# Formulario principal
with st.form(key="formulario_principal"):
    st.header("👤 Datos del Representante Legal")
    # ... (campos de texto sin cambios: rep_legal, cedula_rep_legal) ...
    rep_legal = st.text_input("Nombre Completo*", placeholder="Ej: Ana María Pérez")
    cedula_rep_legal = st.text_input("Cédula de Ciudadanía*", placeholder="Ej: 1020304050")

    st.header("🏢 Datos de la Empresa")
    # ... (campos de texto sin cambios: razon_social, correo, nit) ...
    razon_social = st.text_input("Razón Social*", placeholder="Mi Empresa S.A.S.")
    correo = st.text_input("Correo Electrónico para Notificaciones*", placeholder="ejemplo@correo.com")
    nit = st.text_input("NIT*", placeholder="900.123.456-7")
    
    # Checkbox de autorización, se habilita con el botón anterior
    autoriza = st.checkbox(
        "**Acepto las autorizaciones.** Declaro que he leído, comprendido y aceptado en su totalidad el contenido de las autorizaciones.",
        disabled=not st.session_state.terms_viewed,
        key="auth_checkbox"
    )
    
    st.header("✍️ Firma Digital")
    st.caption("Por favor, firme en el recuadro para sellar su consentimiento.")
    canvas_result = st.canvas(height=200, drawing_mode="freedraw", key="canvas_firma")
    
    # Botón de envío final
    submit_button = st.form_submit_button(label="✅ Aceptar y Enviar Documento Firmado", use_container_width=True)

# --- 8. LÓGICA DE PROCESAMIENTO AL ENVIAR ---
if submit_button:
    # Validaciones
    if not st.session_state.auth_checkbox:
        st.warning("⚠️ Para continuar, debe aceptar las autorizaciones marcando la casilla correspondiente.")
    elif canvas_result.image_data is None:
        st.warning("🖋️ La firma es indispensable para validar el documento.")
    else:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        doc_id = f"FER-{datetime.now().strftime('%Y%m%d%H%M%S')}-{nit}"
        
        # Inicia el proceso con un spinner
        with st.spinner("Procesando y registrando trazabilidad... ⏳"):
            try:
                # --- NUEVO PASO: GUARDAR REGISTRO EN GOOGLE SHEETS ---
                st.write("Guardando registro en Log de Trazabilidad...")
                log_row = [
                    timestamp,
                    doc_id,
                    razon_social,
                    nit,
                    rep_legal,
                    correo,
                    "Enviado" # Estado inicial
                ]
                worksheet.append_row(log_row, value_input_option='USER_ENTERED')
                st.write("Registro guardado con éxito en Google Sheets.")
                
                # --- PASO 2: GENERAR EL PDF (código existente) ---
                st.write("Generando documento PDF institucional...")
                form_data = {
                    'rep_legal': rep_legal, 'cedula_rep_legal': cedula_rep_legal,
                    'razon_social': razon_social, 'nit': nit, 'correo': correo,
                    'doc_id': doc_id, 'timestamp': timestamp
                }
                form_data['firma_img_pil'] = Image.fromarray(canvas_result.image_data.astype('uint8'), 'RGBA')

                pdf_buffer = io.BytesIO()
                pdf_gen = PDFGenerator(pdf_buffer, form_data)
                pdf_gen.generate()
                pdf_buffer.seek(0)
                
                # --- PASO 3: SUBIR PDF A GOOGLE DRIVE (código existente) ---
                st.write("Archivando PDF en Google Drive...")
                file_name = f"Consentimiento_{razon_social.replace(' ', '_')}_{nit}.pdf"
                file_metadata = {'name': file_name, 'parents': [DRIVE_FOLDER_ID]}
                media = MediaFileUpload(pdf_buffer, mimetype='application/pdf', resumable=True)
                file = drive_service.files().create(body=file_metadata, media_body=media, fields='id, webViewLink').execute()

                st.balloons()
                st.success(f"**¡Proceso Finalizado Exitosamente!**")
                st.markdown(f"El documento de consentimiento para **{razon_social}** ha sido generado y archivado de forma segura.")
                st.markdown(f"Puedes previsualizar el documento final en el siguiente enlace: [**Ver PDF Generado**]({file.get('webViewLink')})")

            except Exception as e:
                st.error(f"❌ ¡Ha ocurrido un error inesperado! Detalle técnico: {e}")
                # Opcional: Actualizar el estado en Google Sheets a "Error"
                worksheet.update_acell(f'G{worksheet.row_count}', 'Error')
