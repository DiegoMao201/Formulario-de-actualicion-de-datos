# -*- coding: utf-8 -*-
# =========================================================================================
# APLICACIÓN DE VINCULACIÓN - VERSIÓN DE DIAGNÓSTICO FINAL
# Este script prueba las conexiones a Drive y Sheets de forma independiente al arrancar.
# =========================================================================================

import streamlit as st
import gspread
from google.oauth2 import service_account
from googleapiclient.discovery import build

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="Diagnóstico de Conexiones", page_icon="ախ")

st.title("ախ Diagnóstico de Conexiones de APIs de Google")
st.markdown("---")

# --- FUNCIÓN DE VERIFICACIÓN ---
def check_google_connections():
    """
    Intenta conectarse a Sheets y Drive por separado para aislar el error.
    La aplicación se detendrá en el primer error que encuentre.
    """
    try:
        # --- Lectura de Secretos ---
        st.info("Paso 1: Leyendo los secretos desde Streamlit Cloud...")
        creds_info = st.secrets["gcp_service_account"]
        DRIVE_FOLDER_ID = st.secrets.get("drive_folder_id")
        GOOGLE_SHEET_ID = st.secrets.get("google_sheet_id")
        st.success("✅ Secretos leídos correctamente.")
        
        # --- Creación de Credenciales ---
        st.info("Paso 2: Creando credenciales de autenticación...")
        scopes = ['https://www.googleapis.com/auth/drive', 'https://www.googleapis.com/auth/spreadsheets']
        creds = service_account.Credentials.from_service_account_info(creds_info, scopes=scopes)
        st.success("✅ Credenciales creadas.")

    except Exception as e:
        st.error("❌ ERROR FATAL: No se pudieron leer los secretos o crear las credenciales.")
        st.error("Verifica que la sección [gcp_service_account] exista y sea correcta en tus secretos.")
        st.error(f"Detalle técnico: {e}")
        st.stop()

    # --- Prueba de Conexión a Google Sheets ---
    try:
        st.info(f"Paso 3: Intentando conectar con Google Sheets (ID: {GOOGLE_SHEET_ID})...")
        gc = gspread.authorize(creds)
        worksheet = gc.open_by_key(GOOGLE_SHEET_ID).sheet1
        st.success(f"✅ Conexión con Google Sheets ('{worksheet.title}') verificada.")
    except Exception as e:
        st.error("❌ FALLO en la conexión con Google Sheets.")
        st.error(f"El ID '{GOOGLE_SHEET_ID}' no se encontró o el robot no tiene permisos de 'Editor'.")
        st.error(f"Detalle técnico: {e}")
        st.stop()

    # --- Prueba de Conexión a Google Drive ---
    try:
        st.info(f"Paso 4: Intentando conectar con la carpeta de Google Drive (ID: {DRIVE_FOLDER_ID})...")
        drive_service = build('drive', 'v3', credentials=creds)
        folder_metadata = drive_service.files().get(fileId=DRIVE_FOLDER_ID, supportsAllDrives=True, fields='name').execute()
        st.success(f"✅ Conexión con Google Drive (Carpeta '{folder_metadata.get('name')}') verificada.")
    except Exception as e:
        st.error("❌ FALLO en la conexión con Google Drive.")
        st.error(f"El ID '{DRIVE_FOLDER_ID}' no se encontró o el robot no tiene permisos de 'Editor' o 'Gestor de contenido'.")
        st.error(f"Detalle técnico: {e}")
        st.stop()
        
    # --- Si todo sale bien ---
    st.balloons()
    st.header("¡Todas las conexiones funcionan perfectamente!")
    st.info("Ahora puedes reemplazar este código de diagnóstico por el código completo de la aplicación.")


# --- Ejecutar la verificación al iniciar la app ---
check_google_connections()
