# -*- coding: utf-8 -*-
# =========================================================================================
# FORMULARIO PROFESIONAL DE ACTUALIZACIÓN DE DATOS Y HABEAS DATA
# Creado para ser desplegado en Streamlit Community Cloud
# =========================================================================================

# --- 1. IMPORTACIÓN DE LIBRERÍAS ---
import streamlit as st
from streamlit_drawable_canvas import st_canvas
import io
from PyPDF2 import PdfWriter, PdfReader
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from PIL import Image
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

# --- 2. CONFIGURACIÓN DE LA PÁGINA ---
# Esto debe ser lo primero que se ejecute en tu script.
st.set_page_config(
    page_title="Consentimiento Informado | Actualización de Datos",
    page_icon="✍️",
    layout="centered", # 'centered' o 'wide'
    initial_sidebar_state="collapsed",
)

# --- 3. ESTILO CSS PERSONALIZADO (LA PARTE "BONITA") ---
# Inyectamos CSS para personalizar la apariencia, colores y fuentes.
st.markdown("""
<style>
    /* Fuente principal de la aplicación */
    html, body, [class*="st-"] {
        font-family: 'Georgia', 'serif';
    }
    /* Estilo del contenedor principal */
    .main {
        background-color: #f5f5f5; /* Un fondo gris muy claro */
    }
    /* Estilo para los títulos */
    h1 {
        font-family: 'Georgia', 'serif';
        color: #1a237e; /* Un azul oscuro y profesional */
        text-align: center;
    }
    /* Estilo para los botones */
    .stButton>button {
        border-radius: 20px;
        border: 1px solid #1a237e;
        background-color: #3f51b5; /* Un azul más vibrante */
        color: white;
        transition: all 0.2s;
    }
    .stButton>button:hover {
        background-color: #1a237e;
        color: white;
        border: 1px solid #3f51b5;
    }
    /* Estilo para el canvas de la firma */
    canvas {
        border-radius: 8px;
        border: 2px solid #e0e0e0;
    }
</style>
""", unsafe_allow_html=True)


# --- 4. CONFIGURACIÓN DE GOOGLE DRIVE Y VARIABLES GLOBALES ---
# Intenta cargar las credenciales de Google desde los secretos de Streamlit.
try:
    # Este es el nombre que le dimos a nuestros secretos en el archivo secrets.toml
    creds_info = st.secrets["google_creds"]
    creds = service_account.Credentials.from_service_account_info(
        creds_info,
        scopes=['https://www.googleapis.com/auth/drive']
    )
    drive_service = build('drive', 'v3', credentials=creds)

    # ========================== ¡MUY IMPORTANTE! ==============================
    # REEMPLAZA ESTOS VALORES CON LOS TUYOS
    DRIVE_FOLDER_ID = "0AK7Y6MdgYyoHUk9PVA"
    TEMPLATE_PDF_PATH = 'plantilla.pdf' # Asegúrate que el nombre coincida con tu archivo
    # =========================================================================

except (FileNotFoundError, KeyError):
    st.error("🚨 ¡Error de Configuración! No se encontraron las credenciales de Google Drive.")
    st.info("Asegúrate de haber configurado el archivo 'secrets.toml' en la carpeta '.streamlit' y haberlo añadido a los secretos de tu aplicación en Streamlit Community Cloud.")
    st.stop() # Detiene la ejecución si no hay credenciales


# --- 5. TÍTULO Y DESCRIPCIÓN ---
st.title("✍️ Consentimiento Informado")
st.markdown("---")
st.markdown(
    "Para cumplir con la Ley de Protección de Datos (Habeas Data), te solicitamos "
    "amablemente que actualices tus datos y nos brindes tu consentimiento explícito. "
    "El proceso es rápido, seguro y totalmente digital."
)

# --- 6. FORMULARIO PRINCIPAL ---
# Usamos st.form para agrupar todos los campos. El formulario no se envía hasta que se presiona el botón.
with st.form(key="formulario_habeas_data"):
    
    st.subheader("1. Información Personal")
    
    # Usamos columnas para un diseño más compacto y profesional
    col1, col2 = st.columns(2)
    with col1:
        nombre = st.text_input("Nombre(s) y Apellido(s)", placeholder="Ej: Ana María Pérez")
    with col2:
        cedula = st.text_input("Documento de Identidad (C.C.)", placeholder="Ej: 1020304050")

    direccion = st.text_input("Dirección de Residencia", placeholder="Ej: Carrera 5 # 10-20, Apto 301")

    col3, col4 = st.columns(2)
    with col3:
        correo = st.text_input("Correo Electrónico", placeholder="ejemplo@correo.com")
    with col4:
        telefono = st.text_input("Teléfono Celular", placeholder="Ej: 3001234567")

    st.markdown("---")
    st.subheader("2. Tu Firma Digital")
    st.caption("Dibuja tu firma en el siguiente recuadro. Si te equivocas, puedes limpiar el área.")
    
    # Canvas para la firma
    canvas_result = st_canvas(
        fill_color="rgba(255, 255, 255, 0)",  # Fondo transparente
        stroke_width=3,
        stroke_color="#000000",
        background_color="#FFFFFF",
        height=150,
        width=600,
        drawing_mode="freedraw",
        key="canvas_firma",
    )

    st.markdown("---")
    st.subheader("3. Autorización")

    # Checkbox de autorización
    autoriza = st.checkbox(
        "**He leído y acepto la política de tratamiento de datos.** Manifiesto que autorizo de manera "
        "expresa, voluntaria e informada el tratamiento de mis datos personales de acuerdo con la "
        "legislación vigente en Colombia."
    )

    # Botón de envío del formulario
    st.markdown("---")
    submit_button = st.form_submit_button(
        label="✅ Finalizar y Enviar Documento Firmado",
        use_container_width=True
    )

# --- 7. LÓGICA DE PROCESAMIENTO AL ENVIAR EL FORMULARIO ---
if submit_button:
    # Primero, validamos que todos los campos estén completos
    if not all([nombre, cedula, direccion, correo, telefono]):
        st.warning("⚠️ Por favor, completa todos los campos de información personal.")
    elif not autoriza:
        st.warning("⚠️ Debes aceptar la política de tratamiento de datos para continuar.")
    elif canvas_result.image_data is None:
        st.warning("🖋️ ¡Tu firma es indispensable! Por favor, firma en el recuadro.")
    else:
        # Si todo está correcto, mostramos un mensaje de espera
        with st.spinner("Estamos procesando tu firma y generando el documento... ✨"):
            try:
                # --- A. CREAR LA CAPA DE DATOS CON REPORTLAB ---
                packet = io.BytesIO()
                c = canvas.Canvas(packet, pagesize=letter)
                
                # ========================== ¡MUY IMPORTANTE! ==============================
                # Ajusta estas coordenadas (X, Y) para que coincidan con tu plantilla PDF.
                # El punto (0, 0) es la esquina INFERIOR IZQUIERDA.
                c.drawString(180, 650, nombre)
                c.drawString(180, 625, cedula)
                c.drawString(180, 600, direccion)
                c.drawString(180, 575, correo)
                c.drawString(400, 575, telefono)

                # Marcar la casilla de autorización en el PDF
                c.drawString(85, 300, "X") # Coordenadas de la "X" de autorización

                # Fecha actual de firma
                from datetime import datetime
                fecha_actual = datetime.now().strftime("%d / %m / %Y")
                c.drawString(150, 200, fecha_actual)

                # Incrustar la imagen de la firma
                firma_img = Image.fromarray(canvas_result.image_data.astype('uint8'), 'RGBA')
                # Guardamos la imagen en un buffer para que reportlab la pueda leer
                img_buffer = io.BytesIO()
                firma_img.save(img_buffer, format='PNG')
                img_buffer.seek(0)
                
                # Coordenadas y tamaño de la firma en el PDF
                c.drawImage(img_buffer, x=250, y=250, width=180, height=90, mask='auto')
                # =========================================================================

                c.save()
                packet.seek(0)

                # --- B. FUSIONAR LA PLANTILLA CON LA CAPA DE DATOS ---
                new_pdf = PdfReader(packet)
                existing_pdf = PdfReader(open(TEMPLATE_PDF_PATH, "rb"))
                output = PdfWriter()
                page = existing_pdf.pages[0]
                page.merge_page(new_pdf.pages[0])
                output.add_page(page)

                final_pdf_stream = io.BytesIO()
                output.write(final_pdf_stream)
                final_pdf_stream.seek(0)

                # --- C. SUBIR EL PDF FINAL A GOOGLE DRIVE ---
                file_name = f"Consentimiento_{nombre.replace(' ', '_')}_{cedula}.pdf"
                file_metadata = {'name': file_name, 'parents': [DRIVE_FOLDER_ID]}
                media = MediaFileUpload(
                    final_pdf_stream,
                    mimetype='application/pdf',
                    resumable=True
                )
                
                file = drive_service.files().create(
                    body=file_metadata,
                    media_body=media,
                    fields='id, webViewLink'
                ).execute()
                
                st.balloons() # ¡Una pequeña celebración!
                st.success(f"¡Documento generado y guardado con éxito! 🎉")
                st.markdown(f"**Gracias, {nombre.split()[0]}.** Tu consentimiento ha sido registrado.")
                st.markdown(f"Puedes ver tu documento firmado [**haciendo clic aquí**]({file.get('webViewLink')}).", unsafe_allow_html=True)

            except Exception as e:
                st.error(f"❌ Ocurrió un error inesperado al generar el documento.")
                st.error(f"Detalle del error: {e}")
                st.info("Por favor, inténtalo de nuevo o contacta al administrador.")
