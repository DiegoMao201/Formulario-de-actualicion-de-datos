# CÓDIGO DE PRUEBA #2 - IGNORANDO st.secrets PARA EL ID
import streamlit as st
import gspread
from google.oauth2 import service_account

st.set_page_config(page_title="Prueba de Conexión Final", layout="centered")
st.title("🔬 Prueba de Conexión Final (ID Hardcodeado)")

try:
    st.info("Intentando leer los secretos de la cuenta de servicio...")
    creds_info = st.secrets["gcp_service_account"]
    st.success("Secretos de la cuenta de servicio leídos correctamente.")

    # ========================== MODIFICACIÓN CLAVE ==========================
    # Comentamos la línea que lee de los secretos y ponemos el ID directamente.
    # GOOGLE_SHEET_ID_FROM_SECRETS = st.secrets.get("google_sheet_id")
    GOOGLE_SHEET_ID_HARDCODED = "1Rwv-sk9EcETAsAkyiQlEejGwjhGRqX0gnRplnyCgu5E"
    st.info(f"ID de la hoja de cálculo para la prueba: {GOOGLE_SHEET_ID_HARDCODED}")
    # ========================================================================

    st.info("Creando credenciales...")
    scopes = ['https://www.googleapis.com/auth/spreadsheets']
    creds = service_account.Credentials.from_service_account_info(creds_info, scopes=scopes)
    st.success("Credenciales creadas.")

    st.info(f"Autorizando gspread e intentando abrir la hoja...")
    gc = gspread.authorize(creds)
    worksheet = gc.open_by_key(GOOGLE_SHEET_ID_HARDCODED).sheet1
    
    st.balloons()
    st.success("✅ ¡CONEXIÓN CON GOOGLE SHEETS EXITOSA!")
    st.markdown(f"**Se pudo abrir la hoja de cálculo llamada '{worksheet.title}'.**")
    st.markdown("---")
    st.warning("¡EXCELENTE! Esto prueba que tus permisos y el ID de la hoja son CORRECTOS. El problema está únicamente en cómo Streamlit Cloud está guardando tus secretos.")

except Exception as e:
    st.error(f"❌ ¡FALLÓ LA CONEXIÓN INCLUSO CON EL ID HARDCODEADO!")
    st.error(f"Si ves esto, el problema SÍ está en los permisos de la hoja o el robot no es el correcto. Verifica que compartiste la hoja como Editor con el correo: {st.secrets.gcp_service_account.get('client_email')}")
    st.error(f"Detalle técnico: {e}")
