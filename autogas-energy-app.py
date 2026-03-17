import streamlit as st
import pandas as pd
from datetime import datetime
from fpdf import FPDF
import io
from PIL import Image
import gspread
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload

# --- CONFIGURACIÓN ---
DATOS_TALLER = {
    "nombre": "AUTOGAS ENERGY",
    "direccion": "Av. Canto Grande 2916, San Juan de Lurigancho",
    "logo_url": "https://i.postimg.cc/mD3mzc9v/logo-autogas.png"
}

st.set_page_config(page_title=DATOS_TALLER["nombre"])

# --- CONEXIÓN ---
@st.cache_resource
def conectar_google():
    try:
        scope = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
        creds = Credentials.from_service_account_info(st.secrets["google_credentials"], scopes=scope)
        client = gspread.authorize(creds)
        drive_service = build('drive', 'v3', credentials=creds)
        sheet = client.open("DB_Autogas_Energy").sheet1
        return sheet, drive_service
    except Exception as e:
        st.error(f"Error de conexión: {e}")
        return None, None

db_sheet, drive_service = conectar_google()

def subir_foto_drive(file_bytes, nombre):
    try:
        # Usamos el ID de tus Secrets corregido
        f_id = st.secrets["GOOGLE_DRIVE_FOLDER_ID"]
        media = MediaIoBaseUpload(io.BytesIO(file_bytes), mimetype='image/jpeg', resumable=True)
        file_metadata = {'name': nombre, 'parents': [f_id]}
        file = drive_service.files().create(body=file_metadata, media_body=media, fields='id').execute()
        return file.get('id')
    except Exception as e:
        return f"Error_{str(e)[:10]}"

# --- PAQUETES ---
PAQUETES = {
    "A": ["Cambio de aceite", "Filtro aire", "Filtro aceite", "Fugas gas", "Scanneo", "Siliconeo"],
    "B": ["Paquete A + Bujias"],
    "C": ["Paquete A + Filtro Gas"],
    "D": ["Mantenimiento Completo", "Inyectores", "Obturador", "Sensores", "Bujias"],
    "E": ["Full Gas", "Limpieza Inyectores Gas/Gaso", "Regulacion", "Scanneo"],
    "F": ["Reductor Gas", "Regulacion", "Bujias", "Scanneo"]
}

# --- NAVEGACIÓN ---
if 'view' not in st.session_state: st.session_state.view = 'inicio'

if st.session_state.view == 'inicio':
    st.image(DATOS_TALLER["logo_url"], width=200)
    col1, col2 = st.columns(2)
    if col1.button("👤 CLIENTE"): st.session_state.view = 'cliente'; st.rerun()
    if col2.button("🛠️ ADMIN"): st.session_state.view = 'login'; st.rerun()

elif st.session_state.view == 'login':
    u = st.text_input("Usuario")
    p = st.text_input("Clave", type="password")
    if st.button("Entrar"):
        if u == "percy" and p == "autogas2026":
            st.session_state.view = 'admin'
            st.rerun()

elif st.session_state.view == 'admin':
    st.subheader("Registrar Servicio")
    placa = st.text_input("PLACA").upper().strip()
    km = st.number_input("KM", min_value=0)
    paq = st.selectbox("Paquete", list(PAQUETES.keys()))
    fotos = st.file_uploader("Fotos", accept_multiple_files=True)
    
    if st.button("GUARDAR"):
        with st.spinner("Subiendo..."):
            ids = []
            if fotos:
                for f in fotos:
                    res = subir_foto_drive(f.read(), f"{placa}_{f.name}")
                    ids.append(res)
            
            db_sheet.append_row([
                datetime.now().strftime("%d/%m/%Y"), 
                placa, "Marca", "Modelo", "2024", km, paq, 
                ", ".join(PAQUETES[paq]), "Nota", ",".join(ids)
            ])
            st.success("¡Hecho!")
            st.session_state.view = 'inicio'; st.rerun()

elif st.session_state.view == 'cliente':
    placa_c = st.text_input("TU PLACA").upper().strip()
    if st.button("VER MANTENIMIENTO"):
        df = pd.DataFrame(db_sheet.get_all_records())
        df.columns = [c.lower().strip() for c in df.columns]
        hist = df[df['placa'].astype(str).str.upper() == placa_c]
        
        if not hist.empty:
            ultimo_km = int(hist.iloc[-1]['km'])
            prox = ultimo_km + 5000
            st.markdown(f"""
            <div style="background-color:#d4edda; padding:30px; border-radius:15px; text-align:center; border:2px solid #155724;">
                <h2 style="color:#155724;">¡Estimado Cliente!</h2>
                <p>Su próximo mantenimiento preventivo es a los:</p>
                <h1 style="color:#155724; font-size:4em;">{prox} KM</h1>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.error("No se encontró la placa.")
    if st.button("Volver"): st.session_state.view = 'inicio'; st.rerun()
