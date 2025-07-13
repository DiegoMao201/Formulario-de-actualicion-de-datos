# -*- coding: utf-8 -*-
# =========================================================================================
# APLICACIÓN INSTITUCIONAL DE VINCULACIÓN DE CLIENTES - FERREINOX S.A.S. BIC
# Versión 2.0: Generación Dinámica de PDF con ReportLab
# =========================================================================================

# --- IMPORTACIÓN DE LIBRERÍAS ---
import streamlit as st
from streamlit_drawable_canvas import st_canvas
import io
from PIL import Image
from datetime import datetime

# Librerías para la magia del PDF
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import Paragraph
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_JUSTIFY, TA_CENTER
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

# Librerías para la conexión con Google Drive
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

# --- CONFIGURACIÓN INICIAL DE LA PÁGINA DE STREAMLIT ---
st.set_page_config(
    page_title="Portal de Vinculación | Ferreinox S.A.S. BIC",
    page_icon="🔗",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# --- ESTILO CSS PERSONALIZADO ---
st.markdown("""
<style>
    /* Fuente y fondo */
    html, body, [class*="st-"] { font-family: 'Helvetica', 'sans-serif'; }
    .main { background-color: #F0F2F6; }
    /* Contenedor principal de la app */
    .block-container { padding-top: 2rem; padding-bottom: 2rem; }
    /* Títulos */
    h1, h2, h3 { color: #0D47A1; } /* Azul oscuro corporativo */
    /* Botones */
    .stButton>button {
        border-radius: 8px; border: 2px solid #0D47A1; background-color: #1565C0;
        color: white; font-weight: bold; transition: all 0.3s;
    }
    .stButton>button:hover {
        background-color: #0D47A1; border: 2px solid #1565C0;
    }
</style>
""", unsafe_allow_html=True)


# =========================================================================================
# CLASE PARA GENERAR EL DOCUMENTO PDF INSTITUCIONAL
# Esta clase contiene toda la lógica para dibujar el PDF, haciéndolo modular y profesional.
# =========================================================================================
class PDFGenerator:
    def __init__(self, buffer, data):
        self.buffer = buffer
        self.data = data
        self.c = canvas.Canvas(self.buffer, pagesize=letter)
        self.width, self.height = letter

        # Colores corporativos
        self.color_primary = colors.HexColor('#0D47A1') # Azul oscuro
        self.color_secondary = colors.HexColor('#1565C0') # Azul medio
        self.color_text = colors.black
        self.color_gray = colors.HexColor('#424242')

    def _draw_header(self, page_title):
        """Dibuja el encabezado estándar en cada página."""
        # Logo de la empresa
        try:
            self.c.drawImage('LOGO FERREINOX SAS BIC 2024.png', 50, self.height - 70, width=150, height=50, mask='auto')
        except:
            self.c.drawString(50, self.height - 60, "Ferreinox S.A.S. BIC")

        # Título de la página
        self.c.setFont("Helvetica-Bold", 14)
        self.c.setFillColor(self.color_primary)
        self.c.drawCentredString(self.width / 2, self.height - 100, page_title)
        
        # Slogan
        self.c.setFont("Helvetica-Oblique", 9)
        self.c.setFillColor(self.color_gray)
        self.c.drawRightString(self.width - 50, self.height - 60, "EVOLUCIONANDO JUNTOS")
        
        # Línea divisoria
        self.c.setStrokeColor(self.color_secondary)
        self.c.line(50, self.height - 115, self.width - 50, self.height - 115)


    def _draw_footer(self, page_number):
        """Dibuja el pie de página."""
        self.c.setFont("Helvetica", 8)
        self.c.setFillColor(self.color_gray)
        self.c.drawCentredString(self.width / 2, 30, f"Página {page_number} | Documento generado digitalmente por el Portal de Vinculación Ferreinox")

    def _draw_field(self, x, y, label, value, label_width=150):
        """Dibuja un campo con etiqueta y valor."""
        self.c.setFont("Helvetica-Bold", 9)
        self.c.setFillColor(self.color_primary)
        self.c.drawString(x, y, f"{label}:")
        self.c.setFont("Helvetica", 9)
        self.c.setFillColor(self.color_text)
        self.c.drawString(x + label_width, y, str(value))


    def _draw_paragraph(self, x, y, width, text):
        """Dibuja un párrafo con justificación de texto."""
        styles = getSampleStyleSheet()
        style = ParagraphStyle(
            'normal',
            parent=styles['Normal'],
            fontName='Helvetica',
            fontSize=9,
            leading=14,
            alignment=TA_JUSTIFY,
        )
        p = Paragraph(text, style)
        p.wrapOn(self.c, width, self.height)
        p.drawOn(self.c, x, y)

    def generate(self):
        """Método principal que construye todo el PDF."""
        # --- PÁGINA 1: DATOS BÁSICOS DEL CLIENTE ---
        self._draw_header("FORMULARIO DE ACTUALIZACIÓN DE DATOS - CLIENTES")
        
        y_pos = self.height - 150
        self.c.setFont("Helvetica-Bold", 11)
        self.c.setFillColor(self.color_secondary)
        self.c.drawString(50, y_pos, "1. Información General de la Empresa")
        y_pos -= 30
        
        self._draw_field(60, y_pos, "Fecha de Diligenciamiento", self.data['fecha_diligencia'])
        y_pos -= 25
        self._draw_field(60, y_pos, "Razón Social", self.data['razon_social'])
        self._draw_field(350, y_pos, "NIT", self.data['nit'])
        y_pos -= 25
        self._draw_field(60, y_pos, "Nombre Comercial", self.data['nombre_comercial'])
        y_pos -= 25
        self._draw_field(60, y_pos, "Representante Legal", self.data['rep_legal'])
        
        y_pos -= 40
        self.c.setFont("Helvetica-Bold", 11)
        self.c.setFillColor(self.color_secondary)
        self.c.drawString(50, y_pos, "2. Datos de Contacto y Ubicación")
        y_pos -= 30

        self._draw_field(60, y_pos, "Dirección Principal", self.data['direccion'])
        self._draw_field(350, y_pos, "Ciudad", self.data['ciudad'])
        y_pos -= 25
        self._draw_field(60, y_pos, "Teléfono Fijo", self.data['telefono'])
        self._draw_field(350, y_pos, "Celular Principal", self.data['celular'])
        y_pos -= 25
        self._draw_field(60, y_pos, "Correo Electrónico (Facturación)", self.data['correo'])
        
        y_pos -= 40
        self.c.setFont("Helvetica-Bold", 11)
        self.c.setFillColor(self.color_secondary)
        self.c.drawString(50, y_pos, "3. Contactos Clave")
        y_pos -= 30

        self._draw_field(60, y_pos, "Contacto de Compras", self.data['contacto_compras'])
        self._draw_field(350, y_pos, "Celular Compras", self.data['celular_compras'])
        y_pos -= 25
        self._draw_field(60, y_pos, "Contacto de Pagos (Tesorería)", self.data['contacto_pagos'])
        self._draw_field(350, y_pos, "Celular Pagos", self.data['celular_pagos'])
        
        y_pos -= 40
        self.c.setFont("Helvetica-Bold", 11)
        self.c.setFillColor(self.color_secondary)
        self.c.drawString(50, y_pos, "4. Información Logística")
        y_pos -= 30
        self._draw_field(60, y_pos, "Lugares de Entrega Autorizados", self.data['lugares_entrega'])
        y_pos -= 25
        self._draw_field(60, y_pos, "Requisitos para la Entrega", self.data['requisitos_entrega'])

        self._draw_footer(1)
        self.c.showPage() # Finaliza la página 1

        # --- PÁGINA 2: AUTORIZACIONES LEGALES ---
        self._draw_header("AUTORIZACIONES DE TRATAMIENTO DE DATOS")
        y_pos = self.height - 150

        # Sección Habeas Data
        self.c.setFont("Helvetica-Bold", 12)
        self.c.setFillColor(self.color_primary)
        self.c.drawString(50, y_pos, "AUTORIZACIÓN HABEAS DATA")
        y_pos -= 20
        
        texto_habeas = f"""
        Yo, <b>{self.data['rep_legal']}</b>, mayor de edad, identificado(a) como aparece al pie de mi firma, actuando en nombre
        propio y/o en Representación Legal de <b>{self.data['razon_social']}</b>, identificado con NIT <b>{self.data['nit']}</b>, en ejercicio de mi Derecho a
        la Libertad y Autodeterminación Informática, autorizo a Ferreinox S.A.S. BIC o a la entidad que mi acreedor para representarlo o a su cesionario,
        endosatario o a quien ostente en el futuro la calidad de acreedor, de manera irrevocable, escrita, expresa, voluntaria e informada, para que la información comercial, crediticia y financiera de la cual soy
        titular, sea administrada, capturada, tratada, procesada, verificada, transmitida, usada y consultada por terceras personas autorizadas por la Ley 1266 de 2008.
        Con estos mismos alcances, autorizo expresamente para que tal información sea concernida y reportada en las Centrales de Información y/o Riesgo (Datacrédito, Cifin y Procrédito).
        """
        self._draw_paragraph(50, y_pos - 120, 500, texto_habeas)

        y_pos -= 150

        # Sección Tratamiento de Datos Personales
        self.c.setFont("Helvetica-Bold", 12)
        self.c.setFillColor(self.color_primary)
        self.c.drawString(50, y_pos, "AUTORIZACIÓN PARA EL TRATAMIENTO DE DATOS PERSONALES")
        y_pos -= 20

        texto_tratamiento = f"""
        De conformidad con la Política de Tratamiento de Datos Personales de FERREINOX S.A.S. BIC (NIT. 800224617-8), la cuál puede ser encontrada en sus instalaciones o página Web www.ferreinox.co,
        autorizo a FERREINOX S.A.S. BIC para tratar mis datos personales con el fin de enviar información de ventas, compras, comercial, publicitaria, facturas, documentos de cobro, ofertas, promociones,
        y para fines estadísticos o administrativos que resulten de la ejecución de nuestro objeto social.
        """
        self._draw_paragraph(50, y_pos - 60, 500, texto_tratamiento)
        y_pos -= 100

        # Sección de la Firma
        self.c.setFont("Helvetica-Bold", 11)
        self.c.setFillColor(self.color_secondary)
        self.c.drawString(50, y_pos, "CONSTANCIA DE ACEPTACIÓN")
        y_pos -= 20

        self.c.setFont("Helvetica", 9)
        self.c.drawString(50, y_pos, "En virtud de lo anterior, SÍ AUTORIZO a FERREINOX S.A.S. BIC para que realice el tratamiento de mis datos.")
        y_pos -= 15
        self.c.drawString(50, y_pos, "Certifico que los datos suministrados son veraces, completos y actualizados.")

        y_pos -= 40
        self.c.setFont("Helvetica-Bold", 10)
        self.c.drawString(50, y_pos, "Firma del Representante Legal:")
        self.c.drawImage(self.data['firma_img'], 50, y_pos - 70, width=180, height=60, mask='auto')

        self.c.line(50, y_pos - 80, 230, y_pos - 80)
        y_pos -= 90
        self.c.setFont("Helvetica", 9)
        self.c.drawString(50, y_pos, self.data['rep_legal'])
        y_pos -= 12
        self.c.drawString(50, y_pos, f"C.C. {self.data['cedula_rep_legal']}")
        y_pos -= 12
        self.c.drawString(50, y_pos, f"Cargo: {self.data['cargo_rep_legal']}")
        
        self._draw_footer(2)
        self.c.save() # Guarda el PDF

# --- CONFIGURACIÓN DE GOOGLE DRIVE ---
try:
    creds_info = st.secrets["google_creds"]
    creds = service_account.Credentials.from_service_account_info(creds_info, scopes=['https://www.googleapis.com/auth/drive'])
    drive_service = build('drive', 'v3', credentials=creds)
    DRIVE_FOLDER_ID = "0AK7Y6MdgYyoHUk9PVA" # REEMPLAZA ESTO
except (FileNotFoundError, KeyError):
    st.error("🚨 ¡Error de Configuración de Drive! Revisa los secretos de la aplicación.")
    st.stop()

# --- INTERFAZ DE USUARIO CON STREAMLIT ---
# Título y Logo en la App
col_logo1, col_logo2 = st.columns([1, 4])
with col_logo1:
    st.image('LOGO FERREINOX SAS BIC 2024.png', width=200)
with col_logo2:
    st.title("Portal de Vinculación de Clientes")
    st.markdown("### _EVOLUCIONANDO JUNTOS_")

st.markdown("---")
st.info("**Bienvenido.** Este portal te guiará para actualizar la información de tu empresa y autorizar el tratamiento de datos de forma 100% digital.")

# Formulario principal
with st.form(key="formulario_principal"):
    st.header("1. Datos de la Empresa")
    col1, col2 = st.columns(2)
    with col1:
        razon_social = st.text_input("Razón Social*", placeholder="Ferreinox S.A.S. BIC")
        nombre_comercial = st.text_input("Nombre Comercial", placeholder="Ferreinox")
        rep_legal = st.text_input("Nombre del Representante Legal*", placeholder="Juan Pérez")
        cargo_rep_legal = st.text_input("Cargo del Representante Legal*", placeholder="Gerente General")
    with col2:
        nit = st.text_input("NIT*", placeholder="800.224.617-8")
        ciudad = st.text_input("Ciudad Principal*", placeholder="Pereira")
        cedula_rep_legal = st.text_input("C.C. del Representante Legal*", placeholder="123456789")

    st.header("2. Datos de Contacto")
    col3, col4 = st.columns(2)
    with col3:
        direccion = st.text_input("Dirección de Facturación*", placeholder="Cr. 10 #17-56")
        telefono = st.text_input("Teléfono Fijo", placeholder="6063223868")
        contacto_compras = st.text_input("Nombre Contacto de Compras")
        contacto_pagos = st.text_input("Nombre Contacto de Pagos/Tesorería")
    with col4:
        correo = st.text_input("Correo para Factura Electrónica*", placeholder="facturacion@empresa.com")
        celular = st.text_input("Celular Principal*", placeholder="3142087169")
        celular_compras = st.text_input("Celular de Compras")
        celular_pagos = st.text_input("Celular de Pagos")

    st.header("3. Información de Entrega")
    lugares_entrega = st.text_area("Lugares de entrega autorizados (Separar con comas)", placeholder="Bodega principal, Sucursal centro...")
    requisitos_entrega = st.text_area("Requisitos para la entrega (Opcional)", placeholder="Presentar orden de compra, Sello de recibido...")
    
    st.header("4. Firma y Autorización")
    st.caption("El Representante Legal debe firmar en el siguiente recuadro.")
    
    canvas_result = st_canvas(
        fill_color="rgba(255, 255, 255, 0)", stroke_width=3, stroke_color="#000000",
        background_color="#FFFFFF", height=200, width=700, drawing_mode="freedraw", key="canvas_firma"
    )

    autoriza = st.checkbox("**SI, AUTORIZO.** Como Representante Legal, he leído y acepto las condiciones de tratamiento de datos y Habeas Data.", value=True)
    
    st.markdown("---")
    submit_button = st.form_submit_button(label="🚀 Finalizar y Enviar Vinculación", use_container_width=True)

# --- LÓGICA DE PROCESAMIENTO ---
if submit_button:
    # Validaciones
    required_fields = [razon_social, nit, rep_legal, cargo_rep_legal, ciudad, cedula_rep_legal, direccion, correo, celular]
    if not all(required_fields):
        st.warning("⚠️ Revisa el formulario. Los campos marcados con (*) son obligatorios.")
    elif canvas_result.image_data is None:
        st.warning("🖋️ ¡La firma del Representante Legal es indispensable!")
    else:
        with st.spinner("Construyendo documento institucional... Un momento por favor. ☕"):
            try:
                # Recopilar todos los datos del formulario en un diccionario
                form_data = {
                    'fecha_diligencia': datetime.now().strftime("%d / %m / %Y"),
                    'razon_social': razon_social, 'nit': nit, 'nombre_comercial': nombre_comercial,
                    'rep_legal': rep_legal, 'cargo_rep_legal': cargo_rep_legal, 'cedula_rep_legal': cedula_rep_legal,
                    'direccion': direccion, 'ciudad': ciudad, 'telefono': telefono, 'celular': celular, 'correo': correo,
                    'contacto_compras': contacto_compras, 'celular_compras': celular_compras,
                    'contacto_pagos': contacto_pagos, 'celular_pagos': celular_pagos,
                    'lugares_entrega': lugares_entrega, 'requisitos_entrega': requisitos_entrega
                }

                # Procesar la imagen de la firma
                firma_img_pil = Image.fromarray(canvas_result.image_data.astype('uint8'), 'RGBA')
                img_buffer = io.BytesIO()
                firma_img_pil.save(img_buffer, format='PNG')
                img_buffer.seek(0)
                form_data['firma_img'] = img_buffer

                # Generar el PDF
                pdf_buffer = io.BytesIO()
                pdf_gen = PDFGenerator(pdf_buffer, form_data)
                pdf_gen.generate()
                pdf_buffer.seek(0)

                # Subir a Google Drive
                file_name = f"Vinculacion_{razon_social.replace(' ', '_')}_{nit}.pdf"
                file_metadata = {'name': file_name, 'parents': [DRIVE_FOLDER_ID]}
                media = MediaFileUpload(pdf_buffer, mimetype='application/pdf', resumable=True)
                
                file = drive_service.files().create(
                    body=file_metadata, media_body=media, fields='id, webViewLink').execute()
                
                st.balloons()
                st.success(f"**¡Proceso Finalizado Exitosamente!**")
                st.markdown(f"El documento de vinculación para **{razon_social}** ha sido generado y archivado de forma segura.")
                st.markdown(f"Puedes previsualizar el documento final en el siguiente enlace: [**Ver PDF Generado**]({file.get('webViewLink')})")

            except Exception as e:
                st.error("❌ **¡Ha ocurrido un error!**")
                st.error(f"No pudimos procesar tu solicitud. Por favor, contacta a soporte. Detalle técnico: {e}")
