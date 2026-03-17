import streamlit as st
import pandas as pd
from datetime import datetime
from fpdf import FPDF
import io
import gspread
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload

# --- CONSTANTES FIJAS ---
ID_CARPETA = "1Vk6naUsEDgadg0GDcCrz0nY6MCXrI-1S"
NOMBRE_EXCEL = "DB_Autogas_Energy"

# --- CONEXIÓN ---
def iniciar_servicios():
    creds = Credentials.from_service_account_info(st.secrets["google_credentials"], 
            scopes=["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"])
    return gspread.authorize(creds), build('drive', 'v3', credentials=creds)

client, drive_service = iniciar_servicios()

def subir_a_drive(file_bytes, nombre_archivo):
    try:
        media = MediaIoBaseUpload(io.BytesIO(file_bytes), mimetype='image/jpeg')
        metadata = {'name': nombre_archivo, 'parents': [ID_CARPETA]}
        # El parámetro 'supportsAllDrives' es vital para evitar el error de cuota
        file = drive_service.files().create(body=metadata, media_body=media, fields='id', supportsAllDrives=True).execute()
        return file.get('id')
    except Exception as e:
        return f"Error_API: {str(e)[:20]}"

# --- INTERFAZ ---
st.title("AUTOGAS ENERGY - Panel de Control")

menu = st.sidebar.selectbox("Seleccione Acción", ["Registrar Servicio", "Consultar Cliente"])

if menu == "Registrar Servicio":
    with st.form("registro"):
        placa = st.text_input("PLACA").upper().strip()
        km = st.number_input("Kilometraje Actual", min_value=0)
        paquete = st.selectbox("Paquete", ["A", "B", "C", "D", "E", "F"])
        notas = st.text_area("Observaciones")
        fotos = st.file_uploader("Subir Fotos", accept_multiple_files=True)
        
        if st.form_submit_button("GUARDAR EN BASE DE DATOS"):
            if not placa:
                st.error("La placa es obligatoria")
            else:
                with st.spinner("Procesando..."):
                    ids_fotos = []
                    if fotos:
                        for f in fotos:
                            f_id = subir_a_drive(f.read(), f"{placa}_{datetime.now().strftime('%H%M%S')}.jpg")
                            ids_fotos.append(f_id)
                    
                    # Guardado en Excel (A=Fecha, B=Placa, C=KM, D=Paquete, E=Notas, F=Fotos)
                    sheet = client.open(NOMBRE_EXCEL).sheet1
                    nueva_fila = [datetime.now().strftime("%d/%m/%Y"), placa, km, paquete, notas, ",".join(ids_fotos)]
                    sheet.append_row(nueva_fila)
                    st.success(f"Servicio de {placa} registrado correctamente.")

elif menu == "Consultar Cliente":
    placa_c = st.text_input("Ingrese Placa del Cliente").upper().strip()
    if st.button("Buscar Historial"):
        sheet = client.open(NOMBRE_EXCEL).sheet1
        data = pd.DataFrame(sheet.get_all_records())
        # Limpieza de columnas para evitar errores de nombres
        data.columns = [c.lower().strip() for c in data.columns]
        
        historial = data[data['placa'].astype(str).str.upper() == placa_c]
        
        if not historial.empty:
            ultimo = historial.iloc[-1]
            prox = int(ultimo['km']) + 5000
            st.markdown(f"""
            <div style="background-color:#d4edda; padding:30px; border-radius:15px; text-align:center; border:2px solid #155724;">
                <h2 style="color:#155724;">¡Estimado Cliente!</h2>
                <p>Su próximo mantenimiento preventivo es a los:</p>
                <h1 style="color:#155724; font-size:4em;">{prox} KM</h1>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.warning("No hay registros para esa placa.")
