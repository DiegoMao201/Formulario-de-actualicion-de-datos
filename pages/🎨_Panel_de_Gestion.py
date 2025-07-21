# -*- coding: utf-8 -*-
# =================================================================================================
# PANEL DE GESTIÓN "MÁS ALLÁ DEL COLOR" - FERREINOX S.A.S. BIC
# Versión 1.1 (Corrección de Acceso a Secretos)
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
    """Conecta con Dropbox usando el token de acceso de los secretos."""
    try:
        dbx = dropbox.Dropbox(st.secrets["dropbox_access_token"])
        return dbx
    except Exception as e:
        st.error(f"Error conectando a Dropbox: {e}")
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
            if col not in df.columns: df[col] = ''
        return df
    except Exception as e:
        st.error(f"Error cargando datos de clientes desde Google Sheet: {e}")
        return pd.DataFrame()

@st.cache_data(ttl=300)
def load_sales_data(_dbx):
    """Descarga y carga el archivo de ventas desde Dropbox."""
    if _dbx is None: return pd.DataFrame()
    try:
        file_path = '/data/detalle_ventas.csv'
        _, res = _dbx.files_download(path=file_path)
        df = pd.read_csv(res.content)
        return df
    except dropbox.exceptions.ApiError as e:
        st.error(f"Error: No se encontró el archivo '{file_path}' en Dropbox. Detalles: {e}")
        return pd.DataFrame()
    except Exception as e:
        st.error(f"Error procesando el archivo de ventas: {e}")
        return pd.DataFrame()

# =================================================================================================
# 2. FUNCIONES AUXILIARES
# =================================================================================================

def send_email(recipient_email, subject, body):
    """Función genérica para enviar correos electrónicos."""
    try:
        creds = st.secrets["email_credentials"]
        sender_email, sender_password, smtp_server, smtp_port = creds.smtp_user, creds.smtp_password, creds.smtp_server, int(creds.smtp_port)
        msg = MIMEMultipart()
        msg['From'], msg['To'], msg['Subject'] = sender_email, recipient_email, subject
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
    """Genera un link 'click-to-chat' de WhatsApp."""
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
    """Muestra un prompt de contraseña y retorna True si es correcta."""
    def password_entered():
        if st.session_state["password"] == st.secrets["admin_password"]:
            st.session_state["password_correct"] = True
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

# --- INICIO DEL PANEL DE GESTIÓN (protegido por contraseña)---
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

        if sales_df.empty:
            st.warning("No se pudieron cargar los datos de ventas. Revisa la conexión con Dropbox y el archivo.")
        else:
            sales_df['fecha_venta'] = pd.to_datetime(sales_df['fecha_venta'], dayfirst=True, errors='coerce')
            four_days_ago = datetime.now() - timedelta(days=4)
            recent_sales = sales_df[sales_df['fecha_venta'] >= four_days_ago].copy()
            
            st.info(f"Se encontraron {len(recent_sales)} ventas en los últimos 4 días. Selecciónalas para contactar.")

            if not recent_sales.empty:
                recent_sales['Seleccionar'] = False
                cols_to_display = ['Seleccionar', 'nombre_cliente', 'id_cliente', 'fecha_venta']
                edited_df = st.data_editor(
                    recent_sales[cols_to_display],
                    hide_index=True, key="sales_selector",
                    disabled=['nombre_cliente', 'id_cliente', 'fecha_venta'],
                    column_config={"fecha_venta": st.column_config.DateColumn(format="YYYY-MM-DD")}
                )
                
                selected_clients = edited_df[edited_df['Seleccionar']]

                if not selected_clients.empty:
                    st.markdown("---")
                    st.subheader("Clientes Seleccionados para Contactar:")
                    
                    for index, row in selected_clients.iterrows():
                        client_id = row['id_cliente']
                        client_name = row['nombre_cliente']
                        
                        contact_info = client_df[client_df['NIT / Cédula'].astype(str) == str(client_id)]
                        
                        if not contact_info.empty:
                            email = contact_info.iloc[0]['Correo']
                            phone = contact_info.iloc[0]['Teléfono / Celular']
                            message = f"¡Hola, {client_name}! 👋 Soy de Ferreinox. Te escribo para saludarte y saber cómo te fue con el color y los productos que elegiste. ¡Esperamos que todo haya quedado espectacular! 🎨 Recuerda que en nosotros tienes un aliado. Con Pintuco, tu satisfacción es nuestra garantía."
                            
                            col1, col2, col3 = st.columns([2, 1, 1])
                            with col1: st.write(f"**{client_name}**")
                            with col2:
                                if st.button(f"📧 Enviar Email", key=f"email_sale_{client_id}", use_container_width=True):
                                    subject = f"✨ Un saludo especial desde Ferreinox y Pintuco ✨"
                                    if send_email(email, subject, message):
                                        st.toast(f"Email enviado a {client_name}!", icon="✅")
                            with col3:
                                st.link_button("📲 Abrir WhatsApp", get_whatsapp_link(phone, message), use_container_width=True)
                        else:
                            st.warning(f"No se encontró info de contacto para {client_name} (ID: {client_id}).")

    st.markdown("<br>", unsafe_allow_html=True)

    # --- MÓDULO DE CUMPLEAÑOS ---
    with st.container(border=True):
        st.header("🎂 Cumpleaños del Día")

        if client_df.empty:
            st.warning("No se pudieron cargar los datos de clientes.")
        else:
            today = datetime.now(pytz.timezone('America/Bogota'))
            client_df['Fecha_Nacimiento'] = pd.to_datetime(client_df['Fecha_Nacimiento'], errors='coerce')
            
            birthday_clients = client_df[
                (client_df['Fecha_Nacimiento'].dt.month == today.month) &
                (client_df['Fecha_Nacimiento'].dt.day == today.day)
            ].copy()
            
            if birthday_clients.empty:
                st.info("No hay clientes cumpliendo años hoy.")
            else:
                st.success(f"¡Hoy es el cumpleaños de {len(birthday_clients)} cliente(s)! Selecciónalos para felicitar.")
                birthday_clients['Seleccionar'] = False
                cols_bday_display = ['Seleccionar', 'Razón Social / Nombre Natural', 'Correo', 'Teléfono / Celular']
                edited_bday_df = st.data_editor(
                    birthday_clients[cols_bday_display],
                    hide_index=True, key="bday_selector",
                    disabled=['Razón Social / Nombre Natural', 'Correo', 'Teléfono / Celular']
                )

                selected_bday_clients = edited_bday_df[edited_bday_df['Seleccionar']]

                if not selected_bday_clients.empty:
                    st.markdown("---")
                    st.subheader("Clientes Seleccionados para Felicitar:")
                    
                    for index, row in selected_bday_clients.iterrows():
                        client_name = row['Razón Social / Nombre Natural']
                        email = row['Correo']
                        phone = row['Teléfono / Celular']
                        message = f"¡Hola, {client_name}! 🎉 Todo el equipo de Ferreinox quiere desearte un ¡MUY FELIZ CUMPLEAÑOS! 🎈 Gracias por ser parte de nuestra familia. Esperamos que tu día esté lleno de alegría y, por supuesto, ¡mucho color! 🎨✨"
                        
                        col1, col2, col3 = st.columns([2, 1, 1])
                        with col1: st.write(f"**{client_name}**")
                        with col2:
                            if st.button(f"📧 Enviar Email", key=f"email_bday_{email}", use_container_width=True):
                                subject = f"🥳 ¡{client_name}, Ferreinox te desea un Feliz Cumpleaños! 🥳"
                                if send_email(email, subject, message):
                                    st.toast(f"Felicitación enviada a {client_name}!", icon="🎉")
                        with col3:
                            st.link_button("📲 Abrir WhatsApp", get_whatsapp_link(phone, message), use_container_width=True)
