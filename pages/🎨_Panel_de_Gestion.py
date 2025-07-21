# -*- coding: utf-8 -*-
import streamlit as st
import pandas as pd
# Aquí importaremos las otras librerías que necesitemos (dropbox, gspread, etc.)

st.set_page_config(page_title="Gestión | Más Allá del Color", page_icon="🎨", layout="wide")

# --- FUNCIÓN DE SEGURIDAD ---
def check_password():
    """Returns `True` if the user had the correct password."""
    def password_entered():
        if st.session_state["password"] == st.secrets["admin_password"]:
            st.session_state["password_correct"] = True
            del st.session_state["password"]
        else:
            st.session_state["password_correct"] = False

    if "password_correct" not in st.session_state:
        st.text_input(
            "Ingresa la contraseña para acceder al panel:", type="password", on_change=password_entered, key="password"
        )
        return False
    elif not st.session_state["password_correct"]:
        st.error("😕 Contraseña incorrecta. Intenta de nuevo.")
        st.text_input(
            "Ingresa la contraseña para acceder al panel:", type="password", on_change=password_entered, key="password"
        )
        return False
    else:
        return True

# --- INICIO DE LA APP ---
if check_password():
    st.title("🎨 Panel de Gestión: Más Allá del Color")
    st.markdown("---")

    # --- MÓDULO DE SEGUIMIENTO POST-VENTA (FASE 2) ---
    st.header("📞 Seguimiento Post-Venta")
    if st.button("Buscar clientes de los últimos 4 días"):
        # Aquí irá la lógica para:
        # 1. Conectar a Dropbox
        # 2. Leer detalle_ventas.csv
        # 3. Filtrar por fecha
        # 4. Mostrar en una tabla seleccionable (st.data_editor)
        st.info("Funcionalidad en construcción...")


    st.markdown("---")


    # --- MÓDULO DE CUMPLEAÑOS (FASE 3) ---
    st.header("🎂 Cumpleaños del Día")
    if st.button("Buscar cumpleañeros de hoy"):
        # Aquí irá la lógica para:
        # 1. Conectar a Google Sheets
        # 2. Leer la base de datos de clientes
        # 3. Filtrar por fecha de nacimiento (día y mes de hoy)
        # 4. Mostrar en una tabla para felicitar
        st.info("Funcionalidad en construcción...")
