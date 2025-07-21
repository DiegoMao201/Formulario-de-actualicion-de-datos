# -*- coding: utf-8 -*-
# =================================================================================================
# PANEL DE GESTIÓN "MÁS ALLÁ DEL COLOR" - FERREINOX S.A.S. BIC
# Versión 1.4 (Columnas de Contacto Editables)
# Fecha: 21 de Julio de 2025
# =================================================================================================

import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
import dropbox
from datetime import datetime, timedelta
import pytz
from urllib.parse import quote
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import io
import unicodedata

# --- Configuración de la Página ---
st.set_page_config(page_title="Gestión | Más Allá del Color", page_icon="🎨", layout="wide")

# --- Colores Institucionales ---
FERREINOX_DARK_BLUE = "#0D47A1"
st.markdown(f"""
<style>
    .main {{ background-color: #F0F2F6; }}
    .block-container {{ padding-top: 2rem; padding-bottom: 2rem; }}
    h1, h2, h3, h4 {{ color: {FERREINOX_DARK_BLUE}; }}
    .stButton>button {{
        border-radius: 8px; border: 2px solid {FERREINOX_DARK_BLUE}; background-color: #1565C0;
        color: white; font-weight: bold; transition: all 0.3s;
    }}
    .stButton>button:hover {{ background-color: {FERREINOX_DARK_BLUE}; }}
</style>
""", unsafe_allow_html=True)


# =================================================================================================
# 1. CONEXIONES Y CACHÉ
# =================================================================================================

@st.cache_resource
def connect_to_gsheets():
    """Conecta con Google Sheets usando los secretos de Streamlit."""
    try:
        creds_dict = st.secrets["google_credentials"].to_dict()
        scopes = ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive']
        creds = Credentials.from_service_account_info(creds_dict, scopes=scopes)
        gc = gspread.authorize(creds)
        return gc
    except Exception as e:
        st.error(f"Error conectando a Google Sheets: {e}")
        return None

@st.cache_resource
def connect_to_dropbox():
    """Conecta con Dropbox usando el refresh token de los secretos."""
    try:
        creds = st.secrets["dropbox_credentials"]
        dbx = dropbox.Dropbox(
            oauth2_refresh_token=creds["refresh_token"],
            app_key=creds["app_key"],
            app_secret=creds["app_secret"]
        )
        return dbx
    except Exception as e:
        st.error(f"Error conectando a Dropbox con refresh token: {e}")
        return None

@st.cache_data(ttl=600)
def load_client_data(_gc):
    """Carga los datos de los clientes desde Google Sheets a un DataFrame de Pandas."""
    if _gc is None: return pd.DataFrame()
    try:
        worksheet = _gc.open_by_key(st.secrets["google_sheet_id"]).sheet1
        records = worksheet.get_all_records()
        df = pd.DataFrame(records)
        required_cols = ['NIT / Cédula', 'Razón Social / Nombre Natural', 'Correo', 'Teléfono / Celular', 'Fecha_Nacimiento']
        for col in required_cols:
            if col not in df.columns:
                df[col] = ''
        return df
    except Exception as e:
        st.error(f"Error cargando datos de clientes desde Google Sheet: {e}")
        return pd.DataFrame()

# Función de normalización de texto
def normalizar_texto(texto):
    if not isinstance(texto, str): return texto
    try:
        texto_sin_tildes = ''.join(c for c in unicodedata.normalize('NFD', texto) if unicodedata.category(c) != 'Mn')
        return texto_sin_tildes.upper().replace('-', ' ').replace('_', ' ').strip().replace('  ', ' ')
    except (TypeError, AttributeError): return texto

@st.cache_data(ttl=300)
def load_sales_data(_dbx):
    """
    Descarga y carga el archivo de ventas desde Dropbox.
    Esta versión está corregida y alineada con tu script de Resumen Mensual.
    """
    if _dbx is None: return pd.DataFrame()
    try:
        file_path = '/data/ventas_detalle.csv'
        _, res = _dbx.files_download(path=file_path)
        contenido_csv = res.content.decode('latin1')

        column_names_ventas = [
            'anio', 'mes', 'fecha_venta', 'Serie', 'TipoDocumento',
            'codigo_vendedor', 'nomvendedor', 'id_cliente', 'nombre_cliente',
            'codigo_articulo', 'nombre_articulo', 'categoria_producto',
            'unidades_vendidas', 'costo_unitario', 'valor_venta', 'linea_producto',
            'marca_producto', 'super_categoria'
        ]

        df = pd.read_csv(io.StringIO(contenido_csv), sep='|', header=None,
                         names=column_names_ventas, engine='python', on_bad_lines='warn', quoting=3)

        # --- Procesamiento de columnas ---
        df['fecha_venta'] = pd.to_datetime(df['fecha_venta'], dayfirst=True, errors='coerce')
        df.dropna(subset=['fecha_venta'], inplace=True)
        df['fecha_venta'] = df['fecha_venta'].dt.tz_localize('America/Bogota')

        if 'nombre_cliente' in df.columns:
            df['nombre_cliente'] = df['nombre_cliente'].apply(normalizar_texto)
        
        if 'id_cliente' in df.columns:
            df['id_cliente'] = df['id_cliente'].astype(str)
        
        if 'valor_venta' in df.columns:
            df['valor_venta'] = pd.to_numeric(df['valor_venta'], errors='coerce')

        return df
    except dropbox.exceptions.ApiError as e:
        st.error(f"Error: No se encontró el archivo '{file_path}' en Dropbox. Detalles: {e}")
        return pd.DataFrame()
    except Exception as e:
        st.error(f"Error procesando el archivo de ventas: {e}. Asegúrate que el CSV tenga el formato y el separador correcto (|).")
        return pd.DataFrame()

# =================================================================================================
# 2. FUNCIONES AUXILIARES
# =================================================================================================

def send_email(recipient_email, subject, body):
    """Envía un correo electrónico a un destinatario."""
    if not recipient_email:
        st.warning("No se puede enviar el email: el destinatario no tiene un correo válido.")
        return False
    try:
        creds = st.secrets["email_credentials"]
        sender_email = creds["smtp_user"]
        sender_password = creds["smtp_password"]
        smtp_server = creds["smtp_server"]
        smtp_port = int(creds["smtp_port"])

        msg = MIMEMultipart()
        msg['From'] = f"Ferreinox S.A.S. BIC <{sender_email}>"
        msg['To'] = recipient_email
        msg['Subject'] = subject
        msg.attach(MIMEText(body, 'html'))

        context = smtplib.ssl.create_default_context()
        with smtplib.SMTP_SSL(smtp_server, smtp_port, context=context) as server:
            server.login(sender_email, sender_password)
            server.send_message(msg)
        return True
    except Exception as e:
        st.error(f"No se pudo enviar el email a {recipient_email}. Error: {e}")
        return False

def get_whatsapp_link(phone, message):
    """Genera un enlace de WhatsApp con un mensaje predefinido."""
    cleaned_phone = ''.join(filter(str.isdigit, str(phone)))
    if cleaned_phone:
        if not cleaned_phone.startswith('57'):
            cleaned_phone = '57' + cleaned_phone
        return f"https://wa.me/{cleaned_phone}?text={quote(message)}"
    return ""

# =================================================================================================
# 3. LÓGICA DE LA APLICACIÓN
# =================================================================================================

def check_password():
    """Verifica la contraseña de acceso al panel."""
    def password_entered():
        if st.session_state.get("password") == st.secrets["admin_password"]:
            st.session_state["password_correct"] = True
            if "password" in st.session_state:
                del st.session_state["password"]
        else:
            st.session_state["password_correct"] = False

    if "password_correct" not in st.session_state:
        st.text_input("Ingresa la contraseña para acceder al panel:", type="password", on_change=password_entered, key="password")
        return False
    elif not st.session_state["password_correct"]:
        st.error("😕 Contraseña incorrecta.")
        st.text_input("Ingresa la contraseña para acceder al panel:", type="password", on_change=password_entered, key="password")
        return False
    else:
        return True

# --- INICIO DEL PANEL DE GESTIÓN ---
if check_password():
    st.title("🎨 Panel de Gestión: Más Allá del Color")
    st.markdown("---")

    gc = connect_to_gsheets()
    dbx = connect_to_dropbox()
    
    with st.spinner("Cargando datos de clientes y ventas..."):
        client_df = load_client_data(gc)
        sales_df = load_sales_data(dbx)

    # --- MÓDULO DE SEGUIMIENTO POST-VENTA ---
    with st.container(border=True):
        st.header("📞 Seguimiento Post-Venta")

        if sales_df.empty or 'fecha_venta' not in sales_df.columns:
            st.warning("No se pudieron cargar los datos de ventas correctamente o el archivo está vacío.")
        else:
            bogota_tz = pytz.timezone('America/Bogota')
            current_time_bogota = datetime.now(bogota_tz)
            four_days_ago = current_time_bogota - timedelta(days=4)
            
            recent_sales = sales_df[sales_df['fecha_venta'] >= four_days_ago].copy()
            
            st.info(f"Se encontraron **{len(recent_sales)}** transacciones de venta en los últimos 4 días.")

            if not recent_sales.empty and not client_df.empty:
                
                client_df['nombre_norm'] = client_df['Razón Social / Nombre Natural'].apply(normalizar_texto)
                recent_sales['nombre_norm'] = recent_sales['nombre_cliente']

                merged_sales_clients = pd.merge(
                    recent_sales,
                    client_df[['nombre_norm', 'Razón Social / Nombre Natural', 'Correo', 'Teléfono / Celular']],
                    on='nombre_norm',
                    how='left'
                )

                merged_sales_clients['Correo'] = merged_sales_clients['Correo'].fillna('')
                merged_sales_clients['Teléfono / Celular'] = merged_sales_clients['Teléfono / Celular'].fillna('')
                merged_sales_clients['Razón Social / Nombre Natural'] = merged_sales_clients['Razón Social / Nombre Natural'].fillna(merged_sales_clients['nombre_cliente'])
                
                merged_sales_clients.sort_values(by='fecha_venta', ascending=False, inplace=True)
                merged_sales_clients.drop_duplicates(subset=['nombre_norm'], keep='first', inplace=True)

                st.success(f"De estas, **{len(merged_sales_clients)}** clientes únicos con compras recientes fueron identificados. Selecciónalos para contactar.")

                merged_sales_clients['Seleccionar'] = False
                cols_to_display = ['Seleccionar', 'Razón Social / Nombre Natural', 'fecha_venta', 'Correo', 'Teléfono / Celular']
                actual_cols_to_display = [col for col in cols_to_display if col in merged_sales_clients.columns]
                
                # ### INICIO DE LA SECCIÓN CORREGIDA ###
                # CORRECCIÓN: Se quitan 'Correo' y 'Teléfono / Celular' de la lista de deshabilitados.
                disabled_cols = [col for col in ['Razón Social / Nombre Natural', 'fecha_venta'] if col in merged_sales_clients.columns]

                edited_df = st.data_editor(
                    merged_sales_clients[actual_cols_to_display],
                    hide_index=True, key="sales_selector",
                    disabled=disabled_cols,
                    column_config={"fecha_venta": st.column_config.DateColumn("Fecha Última Compra", format="YYYY-MM-DD")}
                )
                # ### FIN DE LA SECCIÓN CORREGIDA ###
                
                selected_clients = edited_df[edited_df['Seleccionar']]

                if not selected_clients.empty:
                    st.markdown("---")
                    st.subheader("Clientes Seleccionados para Contactar:")
                    
                    for index, row in selected_clients.iterrows():
                        client_name = row.get('Razón Social / Nombre Natural', 'Cliente Desconocido')
                        email = row.get('Correo', '')
                        phone = row.get('Teléfono / Celular', '')
                        message = f"¡Hola, {client_name}! 👋 Soy de Ferreinox. Te escribo para saludarte y saber cómo te fue con el color y los productos que elegiste. ¡Esperamos que todo haya quedado espectacular! 🎨 Recuerda que en nosotros tienes un aliado. Con Pintuco, tu satisfacción es nuestra garantía."
                        
                        col1, col2, col3 = st.columns([2, 1, 1])
                        with col1: st.write(f"**{client_name}**")
                        with col2:
                            if email:
                                if st.button(f"📧 Enviar Email", key=f"email_sale_{index}", use_container_width=True):
                                    subject = f"✨ Un saludo especial desde Ferreinox y Pintuco ✨"
                                    if send_email(email, subject, message):
                                        st.toast(f"Email enviado a {client_name}!", icon="✅")
                            else:
                                st.info("Sin email 🚫")
                        with col3:
                            if phone:
                                st.link_button("📲 Abrir WhatsApp", get_whatsapp_link(phone, message), use_container_width=True)
                            else:
                                st.info("Sin teléfono 🚫")
                else:
                    st.info("Selecciona clientes en la tabla de arriba para ver las opciones de contacto.")
            else:
                 st.info("No hay ventas recientes o no se cargaron los datos de clientes para procesar.")

    st.markdown("<br>", unsafe_allow_html=True)

    # --- MÓDULO DE CUMPLEAÑOS ---
    with st.container(border=True):
        st.header("🎂 Cumpleaños del Día")

        if client_df.empty:
            st.warning("No se pudieron cargar los datos de clientes.")
        else:
            bogota_tz = pytz.timezone('America/Bogota')
            today = datetime.now(bogota_tz)
            
            if 'Fecha_Nacimiento' in client_df.columns:
                client_df['Fecha_Nacimiento'] = pd.to_datetime(client_df['Fecha_Nacimiento'], errors='coerce')
                
                birthday_clients = client_df[
                    (client_df['Fecha_Nacimiento'].dt.month == today.month) &
                    (client_df['Fecha_Nacimiento'].dt.day == today.day)
                ].copy()
            else:
                st.warning("La columna 'Fecha_Nacimiento' no se encontró en el DataFrame de clientes.")
                birthday_clients = pd.DataFrame()
            
            if birthday_clients.empty:
                st.info("No hay clientes cumpliendo años hoy.")
            else:
                st.success(f"¡Hoy es el cumpleaños de **{len(birthday_clients)}** cliente(s)! Selecciónalos para felicitar.")
                birthday_clients['Seleccionar'] = False
                cols_bday_display = ['Seleccionar', 'Razón Social / Nombre Natural', 'Correo', 'Teléfono / Celular']
                actual_cols_bday_display = [col for col in cols_bday_display if col in birthday_clients.columns]
                disabled_bday_cols = [col for col in ['Razón Social / Nombre Natural', 'Correo', 'Teléfono / Celular'] if col in birthday_clients.columns]

                edited_bday_df = st.data_editor(
                    birthday_clients[actual_cols_bday_display],
                    hide_index=True, key="bday_selector",
                    disabled=disabled_bday_cols
                )

                selected_bday_clients = edited_bday_df[edited_bday_df['Seleccionar']]

                if not selected_bday_clients.empty:
                    st.markdown("---")
                    st.subheader("Clientes Seleccionados para Felicitar:")
                    
                    for index, row in selected_bday_clients.iterrows():
                        client_name = row.get('Razón Social / Nombre Natural', 'Cliente Desconocido')
                        email = row.get('Correo', '')
                        phone = row.get('Teléfono / Celular', '')
                        message = f"¡Hola, {client_name}! 🎉 Todo el equipo de Ferreinox quiere desearte un ¡MUY FELIZ CUMPLEAÑOS! 🎈 Gracias por ser parte de nuestra familia. Esperamos que tu día esté lleno de alegría y, por supuesto, ¡mucho color! 🎨✨"
                        
                        col1, col2, col3 = st.columns([2, 1, 1])
                        with col1: st.write(f"**{client_name}**")
                        with col2:
                            if email:
                                if st.button(f"📧 Enviar Email", key=f"email_bday_{index}_{client_name[:5]}", use_container_width=True):
                                    subject = f"🥳 ¡{client_name}, Ferreinox te desea un Feliz Cumpleaños! 🥳"
                                    if send_email(email, subject, message):
                                        st.toast(f"Felicitación enviada a {client_name}!", icon="🎉")
                            else:
                                st.info("Sin email 🚫")
                        with col3:
                            if phone:
                                st.link_button("📲 Abrir WhatsApp", get_whatsapp_link(phone, message), use_container_width=True)
                            else:
                                st.info("Sin teléfono 🚫")
                else:
                    st.info("Selecciona clientes en la tabla de arriba para ver las opciones de contacto.")
