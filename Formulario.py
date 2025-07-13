# -*- coding: utf-8 -*-
# =========================================================================================
# APLICACIÓN INSTITUCIONAL DE VINCULACIÓN DE CLIENTES - FERREINOX S.A.S. BIC
# Versión 3.0: Flujo de Consentimiento Explícito y Trazabilidad Legal
# =========================================================================================

# --- 1. IMPORTACIÓN DE LIBRERÍAS ---
import streamlit as st
from streamlit_drawable_canvas import st_canvas
import io
from PIL import Image
from datetime import datetime
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_JUSTIFY, TA_CENTER
from reportlab.lib.units import inch
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

# --- 2. CONFIGURACIÓN DE LA PÁGINA ---
st.set_page_config(page_title="Portal de Vinculación | Ferreinox", page_icon="✍️", layout="wide")

# --- 3. ESTILO CSS PROFESIONAL ---
st.markdown("""
<style>
    .main { background-color: #F0F2F6; }
    .block-container { padding-top: 2rem; }
    h1, h2, h3 { color: #0D47A1; }
    .stButton>button {
        border-radius: 8px; border: 2px solid #0D47A1; background-color: #1565C0;
        color: white; font-weight: bold;
    }
    .stButton>button:hover { background-color: #0D47A1; }
</style>
""", unsafe_allow_html=True)

# --- 4. CLASE GENERADORA DE PDF ---
class PDFGenerator:
    def __init__(self, buffer, data):
        self.buffer = buffer
        self.data = data
        self.c = canvas.Canvas(self.buffer, pagesize=letter)
        self.width, self.height = letter
        self.color_primary = colors.HexColor('#0D47A1')
        self.color_secondary = colors.HexColor('#1565C0')
        self.color_text = colors.black
        self.color_gray = colors.HexColor('#424242')

    def _draw_header(self, page_title):
        self.c.saveState()
        try:
            self.c.drawImage('LOGO FERREINOX SAS BIC 2024.png', 50, self.height - 70, width=150, height=50, mask='auto')
        except:
            self.c.drawString(50, self.height - 60, "Ferreinox S.A.S. BIC")
        self.c.setFont("Helvetica-Bold", 14)
        self.c.setFillColor(self.color_primary)
        self.c.drawCentredString(self.width / 2, self.height - 100, page_title)
        self.c.setFont("Helvetica-Oblique", 9)
        self.c.setFillColor(self.color_gray)
        self.c.drawRightString(self.width - 50, self.height - 60, "EVOLUCIONANDO JUNTOS")
        self.c.setStrokeColor(self.color_secondary)
        self.c.line(50, self.height - 115, self.width - 50, self.height - 115)
        self.c.restoreState()

    def _draw_footer(self, page_number):
        self.c.saveState()
        self.c.setFont("Helvetica", 8)
        self.c.setFillColor(self.color_gray)
        self.c.drawCentredString(self.width / 2, 30, f"Página {page_number} | Documento generado digitalmente por el Portal de Vinculación Ferreinox")
        self.c.restoreState()

    def _draw_paragraph(self, x, y, width, text):
        styles = getSampleStyleSheet()
        style = ParagraphStyle('normal', parent=styles['Normal'], fontName='Helvetica', fontSize=9, leading=14, alignment=TA_JUSTIFY)
        p = Paragraph(text, style)
        p.wrapOn(self.c, width, self.height)
        p.drawOn(self.c, x, y)
        return p.height

    def generate(self):
        # PÁGINA 1
        self._draw_header("FORMULARIO DE ACTUALIZACIÓN Y VINCULACIÓN")
        # Aquí iría el código para dibujar los campos de la página 1... (omitido por brevedad, es el mismo de antes)
        self.c.drawString(100, 500, "Contenido de la Página 1 (Datos de la Empresa, etc.)")
        self._draw_footer(1)
        self.c.showPage()

        # PÁGINA 2
        self._draw_header("AUTORIZACIONES Y CONSTANCIA DE ACEPTACIÓN")
        y_pos = self.height - 150
        
        # Textos legales
        texto_habeas = f"Yo, <b>{self.data['rep_legal']}</b>, actuando en representación de <b>{self.data['razon_social']}</b> (NIT <b>{self.data['nit']}</b>), autorizo a Ferreinox S.A.S. BIC para el tratamiento de datos conforme a la Ley 1266 de 2008..."
        h = self._draw_paragraph(50, y_pos - 40, 500, texto_habeas)
        y_pos -= (h + 60)

        # Firma
        self.c.setFont("Helvetica-Bold", 10)
        self.c.drawString(50, y_pos, "Firma del Representante Legal:")
        
        # ================================== CORRECCIÓN DEL ERROR ==================================
        # Dibujamos la imagen directamente desde el objeto PIL, no desde el buffer.
        self.c.drawImage(self.data['firma_img_pil'], 50, y_pos - 70, width=180, height=60, mask='auto')
        # ========================================================================================
        
        self.c.line(50, y_pos - 80, 230, y_pos - 80)
        self.c.setFont("Helvetica", 9)
        self.c.drawString(50, y_pos - 90, self.data['rep_legal'])
        self.c.drawString(50, y_pos - 102, f"C.C. {self.data['cedula_rep_legal']}")
        y_pos -= 130
        
        # --- NUEVA SECCIÓN DE TRAZABILIDAD LEGAL ---
        self.c.setFont("Helvetica-Bold", 11)
        self.c.setFillColor(self.color_secondary)
        self.c.drawString(50, y_pos, "TRAZABILIDAD DE LA FIRMA ELECTRÓNICA")
        self.c.line(50, y_pos - 5, self.width - 50, y_pos - 5)
        y_pos -= 25

        data_trazabilidad = [
            ['Concepto', 'Registro'],
            ['ID Único del Documento:', self.data.get('doc_id', 'No disponible')],
            ['Fecha y Hora de Firma:', self.data.get('timestamp', 'No disponible')],
            ['Dirección IP de Origen:', self.data.get('ip_address', 'No registrada')],
            ['Método de Consentimiento:', 'Aceptación explícita en portal web tras visualización de términos.'],
            ['Correo Electrónico Asociado:', self.data.get('correo', '')]
        ]
        
        tabla = Table(data_trazabilidad, colWidths=[1.8*inch, 4*inch])
        tabla.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (1, 0), self.color_primary),
            ('TEXTCOLOR', (0, 0), (1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTNAME', (0, 1), (0, -1), 'Helvetica-Bold'),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#F0F2F6')),
            ('GRID', (0, 0), (-1, -1), 1, self.color_secondary)
        ]))
        tabla.wrapOn(self.c, self.width, self.height)
        tabla.drawOn(self.c, 50, y_pos - 100)

        self._draw_footer(2)
        self.c.save()

# --- CONFIGURACIÓN DE GOOGLE DRIVE Y VARIABLES ---
try:
    creds_info = st.secrets["gcp_service_account"]
    creds = service_account.Credentials.from_service_account_info(creds_info, scopes=['https.www.googleapis.com/auth/drive'])
    drive_service = build('drive', 'v3', credentials=creds)
    DRIVE_FOLDER_ID = st.secrets.get("drive_folder_id", "TU_ID_DE_CARPETA_AQUI")
    # ============================ NUEVA VARIABLE ============================
    # REEMPLAZA ESTE ENLACE con el enlace PÚBLICO de tu PDF de Términos y Condiciones en Drive
    TERMS_URL = "https://docs.google.com/document/d/1B7A_4z5F.../edit?usp=sharing"
    # =======================================================================
except Exception as e:
    st.error("🚨 Error de Configuración de Drive. Verifica los secretos de la aplicación.")
    st.stop()


# --- INTERFAZ DE USUARIO CON STREAMLIT ---
# Inicializar estado de sesión para el flujo de autorización
if 'terms_viewed' not in st.session_state:
    st.session_state.terms_viewed = False

def view_terms():
    st.session_state.terms_viewed = True

# Título y formulario... (se mantiene la estructura anterior)
st.title("🔗 Portal de Vinculación y Autorización")
# ... resto del formulario ...
with st.form(key="formulario_principal"):
    # ... todos los campos de texto del formulario (razón social, nit, etc.) ...
    razon_social = st.text_input("Razón Social*") # Ejemplo
    nit = st.text_input("NIT*") # Ejemplo
    rep_legal = st.text_input("Representante Legal*") # Ejemplo
    cedula_rep_legal = st.text_input("C.C. Rep. Legal*") # Ejemplo
    correo = st.text_input("Correo Electrónico*") # Ejemplo

    st.header("4. Firma y Autorización Legal")
    st.info("Para garantizar la validez del proceso, por favor sigue estos dos pasos:")
    
    # --- NUEVO FLUJO DE TÉRMINOS Y CONDICIONES ---
    col1, col2 = st.columns([1,3])
    with col1:
        st.link_button("1. Ver Términos y Condiciones", TERMS_URL, on_click=view_terms)

    with col2:
        autoriza = st.checkbox(
            "**2. SÍ, AUTORIZO.** Como Representante Legal, declaro que he leído y acepto los Términos y Condiciones, y autorizo el tratamiento de datos.",
            disabled=not st.session_state.terms_viewed, # El checkbox está deshabilitado hasta que se ven los términos
            key="auth_checkbox"
        )
    
    st.caption("Nota: Debes hacer clic en 'Ver Términos y Condiciones' para poder marcar la casilla de autorización.")
    
    # Canvas para la firma
    canvas_result = st_canvas(height=200, width=700, drawing_mode="freedraw", key="canvas_firma")
    submit_button = st.form_submit_button(label="🚀 Finalizar y Sellar Documento", use_container_width=True)


# --- LÓGICA DE PROCESAMIENTO ---
if submit_button:
    if not st.session_state.auth_checkbox: # Verifica si la casilla de autorización fue marcada
        st.warning("⚠️ Debes autorizar explícitamente marcando la casilla para poder continuar.")
    else:
        with st.spinner("Sellando documento con trazabilidad... ⏳"):
            try:
                # Recopilar datos y la nueva evidencia legal
                form_data = {
                    'razon_social': razon_social, 'nit': nit, 'rep_legal': rep_legal,
                    'cedula_rep_legal': cedula_rep_legal, 'correo': correo,
                    # Datos de Trazabilidad
                    'doc_id': f"FER-{datetime.now().strftime('%Y%m%d%H%M%S')}-{nit}",
                    'timestamp': datetime.now().strftime("%d/%m/%Y, %H:%M:%S"),
                    'ip_address': "No implementado en esta versión" # Se puede agregar con servicios externos
                }

                # --- CORRECCIÓN DEL ERROR ---
                firma_img_pil = Image.fromarray(canvas_result.image_data.astype('uint8'), 'RGBA')
                form_data['firma_img_pil'] = firma_img_pil

                # Generar PDF
                pdf_buffer = io.BytesIO()
                pdf_gen = PDFGenerator(pdf_buffer, form_data)
                pdf_gen.generate()
                pdf_buffer.seek(0)
                
                # Subir a Drive
                # ... (código de subida a Drive sin cambios) ...
                
                st.success("✅ ¡Documento Firmado y Archivado con Éxito!")
                # ... (mensaje de éxito con el enlace) ...

            except Exception as e:
                st.error(f"❌ ¡Ha ocurrido un error! Detalle técnico: {e}")
