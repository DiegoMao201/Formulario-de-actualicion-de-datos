# CÓDIGO DE PRUEBA #1 - VERIFICANDO GOOGLE SHEETS
import streamlit as st
import gspread
from google.oauth2 import service_account

st.set_page_config(page_title="Prueba de Conexión", layout="centered")
st.title("🔬 Prueba de Conexión: Google Sheets")

try:
    st.info("Intentando leer los secretos...")
    creds_info = st.secrets["gcp_service_account"]
    GOOGLE_SHEET_ID = st.secrets.get("google_sheet_id")
    st.success("Secretos leídos correctamente.")

    st.info("Creando credenciales...")
    scopes = ['https://www.googleapis.com/auth/spreadsheets']
    creds = service_account.Credentials.from_service_account_info(creds_info, scopes=scopes)
    st.success("Credenciales creadas.")

    st.info(f"Autorizando gspread e intentando abrir la hoja con ID: {GOOGLE_SHEET_ID}")
    gc = gspread.authorize(creds)
    worksheet = gc.open_by_key(GOOGLE_SHEET_ID).sheet1

    st.balloons()
    st.success("✅ ¡CONEXIÓN CON GOOGLE SHEETS EXITOSA!")
    st.markdown(f"**Se pudo abrir la hoja de cálculo llamada '{worksheet.title}'.**")

except Exception as e:
    st.error(f"❌ ¡FALLÓ LA CONEXIÓN CON GOOGLE SHEETS!")
    st.error(f"El error `404 Not Found` probablemente viene de aquí. Revisa el ID de tu hoja y sus permisos.")
    st.error(f"Detalle técnico: {e}")
