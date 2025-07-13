# -*- coding: utf-8 -*-
# =================================================================================================
# APLICACIÓN INSTITUCIONAL DE VINCULACIÓN DE CLIENTES - FERREINOX S.A.S. BIC
# Versión 10.3 (Solución Definitiva de TypeError y Corrección de Layout de PDF)
# Fecha: 12 de Julio de 2025
# =================================================================================================

# --- 1. IMPORTACIÓN DE LIBRERÍAS ---
import streamlit as st
from streamlit_drawable_canvas import st_canvas
import io
from PIL import Image
from datetime import datetime
import gspread
import tempfile # <--- LIBRERÍA NUEVA para manejo de archivos temporales
import os       # <--- LIBRERÍA NUEVA para operaciones del sistema (eliminar archivo)

# --- Librerías de ReportLab para PDF Profesional (Platypus) ---
from reportlab.platypus import BaseDocTemplate, PageTemplate, Frame, Paragraph, Spacer, Table, TableStyle, Image as PlatypusImage
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_LEFT, TA_RIGHT
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.lib.pagesizes import letter

# --- Librerías para Conexiones de Google y Correo ---
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication

# --- 2. CONFIGURACIÓN DE LA PÁGINA DE STREAMLIT ---
st.set_page_config(page_title="Portal de Vinculación | Ferreinox", page_icon="✍️", layout="wide")

# --- 3. ESTILO CSS PERSONALIZADO ---
st.markdown("""
<style>
    .main { background-color: #F0F2F6; }
    .block-container { padding-top: 2rem; padding-bottom: 2rem; }
    h1, h2, h3, h4 { color: #0D47A1; }
    .stButton>button {
        border-radius: 8px; border: 2px solid #0D47A1; background-color: #1565C0;
        color: white; font-weight: bold; transition: all 0.3s;
    }
    .stButton>button:hover { background-color: #0D47A1; }
</style>
""", unsafe_allow_html=True)

# --- 4. TEXTOS LEGALES DINÁMICOS ---
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

# --- 5. CLASE GENERADORA DE PDF (CORREGIDA) ---
class PDFGeneratorPlatypus:
    def __init__(self, buffer, data):
        self.buffer = buffer
        self.data = data
        self.story = []
        
        self.styles = getSampleStyleSheet()
        
        self.style_title = ParagraphStyle(name='Title', parent=self.styles['h1'], fontName='Helvetica-Bold', fontSize=14, alignment=TA_CENTER, textColor=colors.HexColor('#0D47A1'))
        self.style_subtitle = ParagraphStyle(name='SubTitle', parent=self.styles['h2'], fontName='Helvetica-Bold', fontSize=11, alignment=TA_LEFT, textColor=colors.HexColor('#0D47A1'), spaceAfter=8)
        self.style_body = ParagraphStyle(name='Body', parent=self.styles['Normal'], fontName='Helvetica', fontSize=9, alignment=TA_JUSTIFY, leading=14)
        self.style_footer = ParagraphStyle(name='Footer', parent=self.styles['Normal'], fontName='Helvetica', fontSize=8, alignment=TA_CENTER, textColor=colors.grey)

    def _header(self, canvas, doc):
        canvas.saveState()
        try:
            logo = PlatypusImage('LOGO FERREINOX SAS BIC 2024.png', width=2.5*inch, height=0.8*inch)
            logo.drawOn(canvas, doc.leftMargin, doc.height + doc.topMargin - 0.9*inch)
        except:
            canvas.setFont('Helvetica-Bold', 12)
            canvas.drawString(doc.leftMargin, doc.height + doc.topMargin - 0.7*inch, "Ferreinox S.A.S. BIC")
        canvas.restoreState()

    def _footer(self, canvas, doc):
        canvas.saveState()
        # --- PIE DE PÁGINA CORREGIDO CON UNA TABLA PARA EVITAR SUPERPOSICIÓN ---
        footer_table = Table(
            [[
                Paragraph("EVOLUCIONANDO JUNTOS", self.style_footer),
                Paragraph(f"Página {doc.page}", self.style_footer)
            ]],
            colWidths=[doc.width/2, doc.width/2]
        )
        footer_table.setStyle(TableStyle([
            ('ALIGN', (0,0), (0,0), 'LEFT'),
            ('ALIGN', (1,0), (1,0), 'RIGHT')
        ]))
        
        w, h = footer_table.wrap(doc.width, doc.bottomMargin)
        footer_table.drawOn(canvas, doc.leftMargin, h)
        canvas.restoreState()

    def generate(self):
        doc = BaseDocTemplate(self.buffer, pagesize=letter, leftMargin=1*inch, rightMargin=1*inch, topMargin=1.2*inch, bottomMargin=1*inch)
        frame = Frame(doc.leftMargin, doc.bottomMargin, doc.width, doc.height, id='normal')
        template = PageTemplate(id='main_template', frames=[frame], onPage=self._header, onPageEnd=self._footer)
        doc.addPageTemplates([template])

        self.story.append(Paragraph("ACTUALIZACIÓN Y AUTORIZACIÓN DE DATOS DE CLIENTE", self.style_title))
        self.story.append(Spacer(1, 0.4*inch))
        
        self.story.append(Paragraph("1. DATOS BÁSICOS", self.style_subtitle))
        
        datos_basicos = [
            [Paragraph('<b>Razón Social:</b>', self.style_body), Paragraph(self.data.get('razon_social', ''), self.style_body)],
            [Paragraph('<b>Nombre Comercial:</b>', self.style_body), Paragraph(self.data.get('nombre_comercial', ''), self.style_body)],
            [Paragraph('<b>NIT:</b>', self.style_body), Paragraph(self.data.get('nit', ''), self.style_body)],
            [Paragraph('<b>Representante Legal:</b>', self.style_body), Paragraph(self.data.get('rep_legal', ''), self.style_body)],
            [Paragraph('<b>Dirección:</b>', self.style_body), Paragraph(self.data.get('direccion', ''), self.style_body)],
            [Paragraph('<b>Ciudad:</b>', self.style_body), Paragraph(self.data.get('ciudad', ''), self.style_body)],
            [Paragraph('<b>Teléfono:</b>', self.style_body), Paragraph(self.data.get('telefono', ''), self.style_body)],
            [Paragraph('<b>Celular:</b>', self.style_body), Paragraph(self.data.get('celular', ''), self.style_body)],
            [Paragraph('<b>Correo para Notificaciones:</b>', self.style_body), Paragraph(self.data.get('correo', ''), self.style_body)],
        ]
        table_basicos = Table(datos_basicos, colWidths=[2.2*inch, 4.3*inch])
        table_basicos.setStyle(TableStyle([('GRID', (0,0), (-1,-1), 0.5, colors.lightgrey), ('VALIGN', (0,0), (-1,-1), 'MIDDLE'), ('LEFTPADDING', (0,0), (-1,-1), 6), ('RIGHTPADDING', (0,0), (-1,-1), 6)]))
        self.story.append(table_basicos)
        self.story.append(Spacer(1, 0.4*inch))

        datos_contactos = [
            [Paragraph('<b>CONTACTO DE COMPRAS</b>', self.style_body), Paragraph('<b>CONTACTO DE PAGOS</b>', self.style_body)],
            [Paragraph(f"""<b>Nombre:</b> {self.data.get('compras_nombre', '')}<br/><b>Correo:</b> {self.data.get('compras_correo', '')}<br/><b>Tel/Cel:</b> {self.data.get('compras_celular', '')}""", self.style_body),
             Paragraph(f"""<b>Nombre:</b> {self.data.get('pagos_nombre', '')}<br/><b>Correo:</b> {self.data.get('pagos_correo', '')}<br/><b>Tel/Cel:</b> {self.data.get('pagos_celular', '')}""", self.style_body)]
        ]
        table_contactos = Table(datos_contactos, colWidths=[3.25*inch, 3.25*inch])
        table_contactos.setStyle(TableStyle([('GRID', (0,0), (-1,-1), 0.5, colors.lightgrey), ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#E0E0E0')), ('ALIGN', (0,0), (-1,0), 'CENTER'), ('VALIGN', (0,0), (-1,-1), 'TOP'), ('LEFTPADDING', (0,0), (-1,-1), 6), ('TOPPADDING', (0,0), (-1,-1), 6), ('BOTTOMPADDING', (0,0), (-1,-1), 6)]))
        self.story.append(table_contactos)
        self.story.append(Spacer(1, 0.4*inch))
        
        self.story.append(Paragraph("2. AUTORIZACIÓN HABEAS DATA", self.style_subtitle))
        self.story.append(Paragraph(get_texto_habeas_data(self.data['rep_legal'], self.data['razon_social'], self.data['nit'], self.data['correo']), self.style_body))
        self.story.append(Spacer(1, 0.4*inch))

        self.story.append(Paragraph("3. AUTORIZACIÓN PARA EL TRATAMIENTO DE DATOS PERSONALES", self.style_subtitle))
        self.story.append(Paragraph(get_texto_tratamiento_datos(self.data['rep_legal'], self.data['razon_social'], self.data['nit']), self.style_body))
        self.story.append(Spacer(1, 0.4*inch))

        self.story.append(Paragraph("4. CONSTANCIA DE ACEPTACIÓN Y FIRMA DIGITAL", self.style_subtitle))
        
        # --- SOLUCIÓN DEFINITIVA PARA EL ERROR DE IMAGEN ---
        # 1. Guardar la imagen de la firma en un archivo temporal.
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".png")
        try:
            self.data['firma_img_pil'].save(temp_file.name)
            temp_file.close()

            # 2. Usar la ruta del archivo temporal en PlatypusImage.
            firma_image = PlatypusImage(temp_file.name, width=2.5*inch, height=0.8*inch)

            firma_texto = f"""<b>Nombre:</b> {self.data.get('rep_legal', '')}<br/>
                              <b>Identificación:</b> {self.data.get('tipo_id', '')} No. {self.data.get('cedula_rep_legal', '')} de {self.data.get('lugar_exp_id', '')}<br/>
                              <b>Fecha de Firma:</b> {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}<br/>
                              <b>Consentimiento Vía:</b> Portal Web v10.3"""

            table_firma = Table([[firma_image, Paragraph(firma_texto, self.style_body)]], colWidths=[2.8*inch, 3.7*inch])
            table_firma.setStyle(TableStyle([('VALIGN', (0,0), (-1,-1), 'MIDDLE')]))
            self.story.append(table_firma)
            
            doc.build(self.story)
        
        finally:
            # 3. Asegurarse de eliminar el archivo temporal después de usarlo.
            if os.path.exists(temp_file.name):
                os.unlink(temp_file.name)


# --- 6. CONFIGURACIÓN DE CONEXIONES Y SECRETOS ---
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

# --- 7. FUNCIÓN PARA ENVIAR CORREO ---
def send_email_with_attachment(recipient_email, subject, body, pdf_buffer, filename):
    sender_email = st.secrets.email_credentials.smtp_user
    sender_password = st.secrets.email_credentials.smtp_password
    smtp_server = st.secrets.email_credentials.smtp_server
    smtp_port = int(st.secrets.email_credentials.smtp_port)

    msg = MIMEMultipart()
    msg['From'] = sender_email
    msg['To'] = recipient_email
    msg['Subject'] = subject
    msg.attach(MIMEText(body, 'html'))
    
    pdf_buffer.seek(0)
    part = MIMEApplication(pdf_buffer.read(), Name=filename)
    part['Content-Disposition'] = f'attachment; filename="{filename}"'
    msg.attach(part)
    
    context = smtplib.ssl.create_default_context()
    with smtplib.SMTP_SSL(smtp_server, smtp_port, context=context) as server:
        server.login(sender_email, sender_password)
        server.send_message(msg)

# --- 8. INTERFAZ DE USUARIO ---
try:
    st.image('LOGO FERREINOX SAS BIC 2024.png', width=300)
except Exception:
    st.image("https://placehold.co/300x100/0D47A1/FFFFFF?text=Ferreinox+S.A.S.+BIC", width=300)

st.title("Portal de Vinculación y Autorización de Datos")
st.markdown("---")

if 'terms_accepted' not in st.session_state:
    st.session_state.terms_accepted = False

def accept_terms():
    st.session_state.terms_accepted = True

if not st.session_state.terms_accepted:
    st.header("📜 Términos, Condiciones y Autorizaciones")
    with st.expander("Haga clic aquí para leer los Términos Completos"):
        st.subheader("Autorización para Tratamiento de Datos Personales")
        st.markdown(get_texto_tratamiento_datos("[Su Nombre]", "[Su Empresa]", "[Su NIT]"), unsafe_allow_html=True)
        st.subheader("Autorización para Consulta en Centrales de Riesgo (Habeas Data)")
        st.markdown(get_texto_habeas_data("[Su Nombre]", "[Su Empresa]", "[Su NIT]", "[Su Correo]"), unsafe_allow_html=True)

    st.button("He leído y acepto los términos para continuar", on_click=accept_terms, use_container_width=True)

else:
    with st.form(key="formulario_principal"):
        st.header("👤 Formulario de Vinculación")
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
            tipo_id = st.selectbox("Tipo de ID*", ["C.C.", "C.E.", "Pasaporte", "Otro"])
            lugar_exp_id = st.text_input("Ciudad de Expedición del ID*", placeholder="Pereira")

        st.subheader("Información de Contactos")
        col6, col7 = st.columns(2)
        with col6:
            st.markdown("#### Contacto de Compras")
            compras_nombre = st.text_input("Nombre (Compras)", key="compras_nombre")
            compras_correo = st.text_input("Correo (Compras)", key="compras_correo")
            compras_celular = st.text_input("Celular (Compras)", key="compras_celular")
        with col7:
            st.markdown("#### Contacto de Pagos / Cartera")
            pagos_nombre = st.text_input("Nombre (Pagos)", key="pagos_nombre")
            pagos_correo = st.text_input("Correo (Pagos)", key="pagos_correo")
            pagos_celular = st.text_input("Celular (Pagos)", key="pagos_celular")
        
        st.subheader("Información Logística")
        lugares_entrega = st.text_area("Lugares de entrega autorizados (direcciones)", placeholder="Sede Principal: Cr 13 #19-26, Pereira\nBodega: Km 5 Vía Cerritos, Bodega 4")
        requisitos_entrega = st.text_area("Requisitos para la entrega de mercancía", placeholder="Dejar en portería a nombre de Juan Valdés. Requiere sello de recibido.")
        
        st.subheader("✍️ Firma Digital de Aceptación")
        st.caption("El Representante Legal debe firmar en el siguiente recuadro para validar toda la información y autorizaciones.")
        canvas_result = st_canvas(
            fill_color="rgba(255, 255, 255, 0)", stroke_width=3, stroke_color="#000000",
            background_color="#FFFFFF", height=200, drawing_mode="freedraw", key="canvas_firma"
        )
        
        submit_button = st.form_submit_button(label="✅ Finalizar y Enviar Formulario Firmado", use_container_width=True)

    # --- 9. LÓGICA DE PROCESAMIENTO ---
    if submit_button:
        campos_obligatorios = [razon_social, nit, direccion, ciudad, correo, rep_legal, cedula_rep_legal, lugar_exp_id, nombre_comercial]
        if not all(campos_obligatorios):
            st.warning("⚠️ Por favor, complete todos los campos marcados con *.")
        elif canvas_result.image_data is None:
            st.warning("🖋️ La firma del Representante Legal es indispensable para validar el documento.")
        else:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            doc_id = f"FER-{datetime.now().strftime('%Y%m%d%H%M%S')}-{nit}"
            
            with st.spinner("Procesando su solicitud... Este proceso puede tardar un momento. ⏳"):
                try:
                    form_data = {
                        'razon_social': razon_social, 'nombre_comercial': nombre_comercial, 'nit': nit, 
                        'direccion': direccion, 'ciudad': ciudad, 'telefono': telefono, 'celular': celular,
                        'correo': correo, 'rep_legal': rep_legal, 'cedula_rep_legal': cedula_rep_legal,
                        'tipo_id': tipo_id, 'lugar_exp_id': lugar_exp_id, 'compras_nombre': compras_nombre,
                        'compras_correo': compras_correo, 'compras_celular': compras_celular,
                        'pagos_nombre': pagos_nombre, 'pagos_correo': pagos_correo, 'pagos_celular': pagos_celular,
                        'lugares_entrega': lugares_entrega, 'requisitos_entrega': requisitos_entrega,
                        'firma_img_pil': Image.fromarray(canvas_result.image_data.astype('uint8'), 'RGBA')
                    }
                    
                    st.write("Paso 1/4: Generando documento PDF institucional...")
                    pdf_buffer = io.BytesIO()
                    pdf_gen = PDFGeneratorPlatypus(pdf_buffer, form_data)
                    pdf_gen.generate()
                    
                    st.write("Paso 2/4: Guardando registro en Log de Trazabilidad...")
                    log_row = [
                        timestamp, doc_id, razon_social, nit, rep_legal, correo,
                        ciudad, telefono, celular, compras_nombre, compras_correo,
                        pagos_nombre, pagos_correo, "Enviado y Notificado"
                    ]
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
                    send_email_with_attachment(correo, f"Confirmación de Vinculación - {razon_social}", email_body, pdf_buffer, file_name)

                    st.write("Paso 4/4: Archivando PDF en el repositorio digital...")
                    pdf_buffer.seek(0)
                    file_metadata = {'name': file_name, 'parents': [DRIVE_FOLDER_ID]}
                    media = MediaFileUpload(pdf_buffer, mimetype='application/pdf', resumable=True)
                    file = drive_service.files().create(
                        body=file_metadata, media_body=media, fields='id, webViewLink', supportsAllDrives=True
                    ).execute()

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
