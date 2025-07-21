# -*- coding: utf-8 -*-
# =================================================================================================
# PANEL DE GESTIÓN "MÁS ALLÁ DEL COLOR" - FERREINOX S.A.S. BIC
# Versión 1.2 (Autenticación Dropbox con Refresh Token)
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
import io # Import the io module
import unicodedata # Necesario para normalizar texto, útil para comparar nombres de columnas

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
        # Asegúrate de que el sheet_id en secrets apunte al correcto para clientes
        worksheet = _gc.open_by_key(st.secrets["google_sheet_id"]).sheet1
        records = worksheet.get_all_records()
        df = pd.DataFrame(records)
        required_cols = ['NIT / Cédula', 'Razón Social / Nombre Natural', 'Correo', 'Teléfono / Celular', 'Fecha_Nacimiento']
        for col in required_cols:
            # Asegura que las columnas existan, inicializándolas vacías si no están presentes
            if col not in df.columns:
                df[col] = ''
        return df
    except Exception as e:
        st.error(f"Error cargando datos de clientes desde Google Sheet: {e}")
        return pd.DataFrame()

# Función de normalización de texto (copiada del script de Resumen Mensual)
def normalizar_texto(texto):
    if not isinstance(texto, str): return texto
    try:
        texto_sin_tildes = ''.join(c for c in unicodedata.normalize('NFD', texto) if unicodedata.category(c) != 'Mn')
        # Reemplazar doble espacio por uno simple, luego normalizar un solo espacio
        return texto_sin_tildes.upper().replace('-', ' ').replace('_', ' ').strip().replace('  ', ' ')
    except (TypeError, AttributeError): return texto

@st.cache_data(ttl=300)
def load_sales_data(_dbx):
    """
    Descarga y carga el archivo de ventas desde Dropbox,
    manejando los nombres de las columnas explícitamente y
    convirtiendo 'fecha_venta' a datetime con timezone.
    """
    if _dbx is None: return pd.DataFrame()
    try:
        file_path = '/data/ventas_detalle.csv'
        _, res = _dbx.files_download(path=file_path)
        contenido_csv = res.content.decode('latin1')

        # Definir los nombres de columna esperados para el archivo ventas_detalle.csv
        # ESTO ES CRÍTICO: DEBEN COINCIDIR CON EL ORDEN DE LAS COLUMNAS EN TU CSV DE VENTAS
        # He tomado como referencia las columnas de 'ventas' en el APP_CONFIG de tu segundo script
        column_names_ventas = [
            'anio', 'mes', 'fecha_venta', 'Serie', 'TipoDocumento', 'codigo_vendedor',
            'nomvendedor', 'id_cliente', 'nombre_cliente', 'codigo_articulo',
            'nombre_articulo', 'categoria_producto', 'linea_producto', 'marca_producto',
            'valor_venta', 'unidades_vendidas', 'costo_unitario', 'super_categoria'
        ]

        # Leer el CSV sin encabezado y asignar las columnas manualmente
        df = pd.read_csv(io.StringIO(contenido_csv), sep='|', header=None,
                         names=column_names_ventas, engine='python', on_bad_lines='warn')

        # Normalizar algunas columnas para asegurar consistencia
        if 'id_cliente' in df.columns:
            df['id_cliente'] = df['id_cliente'].astype(str)
        if 'nomvendedor' in df.columns:
            df['nomvendedor'] = df['nomvendedor'].apply(normalizar_texto)
        if 'TipoDocumento' in df.columns:
            df['TipoDocumento'] = df['TipoDocumento'].apply(normalizar_texto)
        
        # Convertir 'fecha_venta' a datetime y hacerla timezone-aware
        if 'fecha_venta' in df.columns:
            df['fecha_venta'] = pd.to_datetime(df['fecha_venta'], dayfirst=True, errors='coerce')
            # Localizar a la zona horaria de Bogotá (GMT-5)
            # Esto asignará el timezone a las fechas
            df['fecha_venta'] = df['fecha_venta'].dt.tz_localize('America/Bogota', errors='coerce')
        
        return df
    except dropbox.exceptions.ApiError as e:
        st.error(f"Error: No se encontró el archivo '{file_path}' en Dropbox. Detalles: {e}")
        return pd.DataFrame(columns=['id_cliente', 'fecha_venta', 'nombre_cliente']) # Retorna un DF vacío con cols mínimas
    except Exception as e:
        st.error(f"Error procesando el archivo de ventas: {e}. Asegúrate que el CSV tenga el formato y el separador correcto (|) y las columnas esperadas.")
        return pd.DataFrame(columns=['id_cliente', 'fecha_venta', 'nombre_cliente']) # Retorna un DF vacío con cols mínimas

# =================================================================================================
# 2. FUNCIONES AUXILIARES
# =================================================================================================

def send_email(recipient_email, subject, body):
    """Envía un correo electrónico a un destinatario."""
    if not recipient_email: # Verificar si el email es una cadena vacía o None
        st.warning("No se puede enviar el email: el destinatario no tiene un correo válido.")
        return False
    try:
        creds = st.secrets["email_credentials"]
        sender_email = creds.smtp_user
        sender_password = creds.smtp_password
        smtp_server = creds.smtp_server
        smtp_port = int(creds.smtp_port)

        msg = MIMEMultipart()
        msg['From'] = sender_email
        msg['To'] = recipient_email
        msg['Subject'] = subject
        msg.attach(MIMEText(body, 'html')) # Envía el cuerpo como HTML

        context = smtplib.ssl.create_default_context() # Contexto SSL para seguridad
        with smtplib.SMTP_SSL(smtp_server, smtp_port, context=context) as server:
            server.login(sender_email, sender_password)
            server.send_message(msg)
        return True
    except Exception as e:
        st.error(f"No se pudo enviar el email a {recipient_email}. Error: {e}")
        return False

def get_whatsapp_link(phone, message):
    """Genera un enlace de WhatsApp con un mensaje predefinido."""
    # Limpia el número de teléfono, quitando todo lo que no sea dígito
    cleaned_phone = ''.join(filter(str.isdigit, str(phone)))
    if cleaned_phone:
        # Si el número no empieza con '57' (código de Colombia), lo añade
        if not cleaned_phone.startswith('57'):
            cleaned_phone = '57' + cleaned_phone
        return f"https://wa.me/{cleaned_phone}?text={quote(message)}"
    return "" # Retorna cadena vacía si el teléfono no es válido

# =================================================================================================
# 3. LÓGICA DE LA APLICACIÓN
# =================================================================================================

def check_password():
    """Verifica la contraseña de acceso al panel."""
    def password_entered():
        """Función callback para verificar la contraseña."""
        if st.session_state.get("password") == st.secrets["admin_password"]:
            st.session_state["password_correct"] = True
            # Eliminar la contraseña de la sesión para seguridad
            if "password" in st.session_state:
                del st.session_state["password"]
        else:
            st.session_state["password_correct"] = False

    if "password_correct" not in st.session_state:
        # Primera vez que se carga la página o contraseña no introducida
        st.text_input("Ingresa la contraseña para acceder al panel:", type="password", on_change=password_entered, key="password")
        return False
    elif not st.session_state["password_correct"]:
        # Contraseña incorrecta, mostrar error y pedir de nuevo
        st.error("😕 Contraseña incorrecta.")
        st.text_input("Ingresa la contraseña para acceder al panel:", type="password", on_change=password_entered, key="password")
        return False
    else:
        return True

# --- INICIO DEL PANEL DE GESTIÓN ---
if check_password():
    st.title("🎨 Panel de Gestión: Más Allá del Color")
    st.markdown("---")

    # Establece las conexiones y carga los datos una sola vez por ejecución
    gc = connect_to_gsheets()
    dbx = connect_to_dropbox()
    
    with st.spinner("Cargando datos de clientes y ventas..."):
        client_df = load_client_data(gc)
        sales_df = load_sales_data(dbx)

    # --- PRE-PROCESAMIENTO DE DATOS PARA COMBINAR ---
    # Asegurar que las columnas clave para la combinación sean de tipo string para evitar errores
    # Añadimos una verificación para asegurarnos de que la columna exista antes de intentar convertirla
    if not sales_df.empty and 'id_cliente' in sales_df.columns:
        sales_df['id_cliente'] = sales_df['id_cliente'].astype(str)
    else:
        st.warning("La columna 'id_cliente' no se encontró en el archivo de ventas o el DataFrame está vacío. Se procederá con un DataFrame de ventas limitado.")
        sales_df = pd.DataFrame(columns=['id_cliente', 'fecha_venta', 'nombre_cliente']) # Asegura un DF mínimo

    if not client_df.empty:
        if 'NIT / Cédula' in client_df.columns:
            client_df['NIT / Cédula'] = client_df['NIT / Cédula'].astype(str)
        # Asegurarse de que las columnas de contacto y nombre no sean nulas en client_df ANTES de usarlas
        client_df['Correo'] = client_df['Correo'].fillna('')
        client_df['Teléfono / Celular'] = client_df['Teléfono / Celular'].fillna('')
        client_df['Razón Social / Nombre Natural'] = client_df['Razón Social / Nombre Natural'].fillna('')


    # --- MÓDULO DE SEGUIMIENTO POST-VENTA ---
    with st.container(border=True):
        st.header("📞 Seguimiento Post-Venta")

        # Verificar si sales_df está vacío o le faltan columnas críticas
        if sales_df.empty or 'fecha_venta' not in sales_df.columns or 'id_cliente' not in sales_df.columns:
            st.warning("No se pudieron cargar los datos de ventas correctamente o faltan columnas esenciales ('fecha_venta', 'id_cliente'). Revisa la conexión con Dropbox y el archivo.")
        else:
            # La columna 'fecha_venta' ya es timezone-aware desde load_sales_data
            # 'four_days_ago' también es timezone-aware. ¡Ahora la comparación funcionará!
            bogota_tz = pytz.timezone('America/Bogota')
            current_time_bogota = datetime.now(bogota_tz)
            four_days_ago = current_time_bogota - timedelta(days=4)
            recent_sales = sales_df[sales_df['fecha_venta'] >= four_days_ago].copy()
            
            st.info(f"Se encontraron **{len(recent_sales)}** ventas en los últimos 4 días. Selecciónalas para contactar.")

            if not recent_sales.empty:
                # Combina la información de ventas con la de clientes para obtener los datos de contacto
                # Se usa 'left' para mantener todas las ventas recientes y añadir info de cliente si existe.
                merged_sales_clients = pd.merge(
                    recent_sales,
                    client_df[['NIT / Cédula', 'Razón Social / Nombre Natural', 'Correo', 'Teléfono / Celular']],
                    left_on='id_cliente',
                    right_on='NIT / Cédula',
                    how='left'
                )

                # Rellena los valores NaN en las columnas de contacto que provienen de la unión
                # Es fundamental que estos sean strings vacíos para las comprobaciones posteriores.
                merged_sales_clients['Correo'] = merged_sales_clients['Correo'].fillna('')
                merged_sales_clients['Teléfono / Celular'] = merged_sales_clients['Teléfono / Celular'].fillna('')
                # Si 'Razón Social / Nombre Natural' se volvió NaN por la unión (porque no estaba en Sheets),
                # usa 'nombre_cliente' de sales_df como respaldo.
                # Asegúrate que 'nombre_cliente' exista en merged_sales_clients antes de usarlo.
                if 'nombre_cliente' in merged_sales_clients.columns:
                    merged_sales_clients['Razón Social / Nombre Natural'] = merged_sales_clients['Razón Social / Nombre Natural'].fillna(merged_sales_clients['nombre_cliente'])
                else:
                    merged_sales_clients['Razón Social / Nombre Natural'] = merged_sales_clients['Razón Social / Nombre Natural'].fillna('Cliente Desconocido')


                merged_sales_clients['Seleccionar'] = False
                # Columnas a mostrar en el editor de datos, ahora incluyendo las de contacto mapeadas
                cols_to_display = ['Seleccionar', 'Razón Social / Nombre Natural', 'id_cliente', 'fecha_venta', 'Correo', 'Teléfono / Celular']
                # Filtra las columnas que realmente existen en el DataFrame
                actual_cols_to_display = [col for col in cols_to_display if col in merged_sales_clients.columns]

                # Asegúrate de que las columnas deshabilitadas existan
                disabled_cols = [col for col in ['Razón Social / Nombre Natural', 'id_cliente', 'fecha_venta', 'Correo', 'Teléfono / Celular'] if col in merged_sales_clients.columns]

                edited_df = st.data_editor(
                    merged_sales_clients[actual_cols_to_display],
                    hide_index=True, key="sales_selector",
                    # Deshabilitar todas las columnas excepto 'Seleccionar'
                    disabled=disabled_cols,
                    column_config={"fecha_venta": st.column_config.DateColumn(format="YYYY-MM-DD")}
                )
                
                selected_clients = edited_df[edited_df['Seleccionar']]

                if not selected_clients.empty:
                    st.markdown("---")
                    st.subheader("Clientes Seleccionados para Contactar:")
                    
                    for index, row in selected_clients.iterrows():
                        client_id = row.get('id_cliente', 'N/A') # Usar .get para evitar errores si la columna no existe
                        # Ya usamos 'Razón Social / Nombre Natural' como la fuente principal
                        client_name = row.get('Razón Social / Nombre Natural', 'Cliente Desconocido')
                        email = row.get('Correo', '')
                        phone = row.get('Teléfono / Celular', '')
                        message = f"¡Hola, {client_name}! 👋 Soy de Ferreinox. Te escribo para saludarte y saber cómo te fue con el color y los productos que elegiste. ¡Esperamos que todo haya quedado espectacular! 🎨 Recuerda que en nosotros tienes un aliado. Con Pintuco, tu satisfacción es nuestra garantía."
                        
                        col1, col2, col3 = st.columns([2, 1, 1])
                        with col1: st.write(f"**{client_name}** (ID: {client_id})")
                        with col2:
                            if email: # Solo muestra el botón si hay un email registrado
                                if st.button(f"📧 Enviar Email", key=f"email_sale_{client_id}", use_container_width=True):
                                    subject = f"✨ Un saludo especial desde Ferreinox y Pintuco ✨"
                                    if send_email(email, subject, message):
                                        st.toast(f"Email enviado a {client_name}!", icon="✅")
                            else:
                                st.info("Sin email 🚫") # Mensaje si no hay email
                        with col3:
                            if phone: # Solo muestra el botón si hay un teléfono registrado
                                st.link_button("📲 Abrir WhatsApp", get_whatsapp_link(phone, message), use_container_width=True)
                            else:
                                st.info("Sin teléfono 🚫") # Mensaje si no hay teléfono
            else:
                st.info("Selecciona clientes en la tabla de arriba para ver las opciones de contacto.")


    st.markdown("<br>", unsafe_allow_html=True)

    # --- MÓDULO DE CUMPLEAÑOS ---
    with st.container(border=True):
        st.header("🎂 Cumpleaños del Día")

        if client_df.empty:
            st.warning("No se pudieron cargar los datos de clientes.")
        else:
            # Configura la zona horaria para la fecha actual
            bogota_tz = pytz.timezone('America/Bogota')
            today = datetime.now(bogota_tz)
            
            # Convierte la columna de fecha de nacimiento a formato datetime
            if 'Fecha_Nacimiento' in client_df.columns:
                client_df['Fecha_Nacimiento'] = pd.to_datetime(client_df['Fecha_Nacimiento'], errors='coerce')
                
                # Opcional: Si quieres que Fecha_Nacimiento sea timezone-aware para futuras comparaciones,
                # aunque para día y mes no es estrictamente necesario, puede ayudar a la consistencia.
                # client_df['Fecha_Nacimiento'] = client_df['Fecha_Nacimiento'].dt.tz_localize('America/Bogota', errors='coerce')
                
                # Filtra los clientes que cumplen años hoy
                birthday_clients = client_df[
                    (client_df['Fecha_Nacimiento'].dt.month == today.month) &
                    (client_df['Fecha_Nacimiento'].dt.day == today.day)
                ].copy() # .copy() para evitar SettingWithCopyWarning
            else:
                st.warning("La columna 'Fecha_Nacimiento' no se encontró en el DataFrame de clientes. No se mostrarán cumpleaños.")
                birthday_clients = pd.DataFrame() # No hay fecha de nacimiento, no hay cumpleaños para mostrar
            
            if birthday_clients.empty:
                st.info("No hay clientes cumpliendo años hoy.")
            else:
                st.success(f"¡Hoy es el cumpleaños de **{len(birthday_clients)}** cliente(s)! Selecciónalos para felicitar.")
                birthday_clients['Seleccionar'] = False
                cols_bday_display = ['Seleccionar', 'Razón Social / Nombre Natural', 'Correo', 'Teléfono / Celular']
                # Filtra las columnas que realmente existen
                actual_cols_bday_display = [col for col in cols_bday_display if col in birthday_clients.columns]
                disabled_bday_cols = [col for col in ['Razón Social / Nombre Natural', 'Correo', 'Teléfono / Celular'] if col in birthday_clients.columns]

                edited_bday_df = st.data_editor(
                    birthday_clients[actual_cols_bday_display],
                    hide_index=True, key="bday_selector",
                    disabled=disabled_bday_cols # Campos no editables
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
                            if email: # Solo muestra el botón si hay un email
                                # Usar un key único que incluya el índice o un id único para el botón
                                if st.button(f"📧 Enviar Email", key=f"email_bday_{index}_{client_name[:5]}", use_container_width=True): 
                                    subject = f"🥳 ¡{client_name}, Ferreinox te desea un Feliz Cumpleaños! 🥳"
                                    if send_email(email, subject, message):
                                        st.toast(f"Felicitación enviada a {client_name}!", icon="🎉")
                            else:
                                st.info("Sin email 🚫")
                        with col3:
                            if phone: # Solo muestra el botón si hay un teléfono
                                st.link_button("📲 Abrir WhatsApp", get_whatsapp_link(phone, message), use_container_width=True)
                            else:
                                st.info("Sin teléfono 🚫")
                else:
                    st.info("Selecciona clientes en la tabla de arriba para ver las opciones de contacto.")
