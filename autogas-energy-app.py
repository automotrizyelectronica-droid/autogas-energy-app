import streamlit as st
import pandas as pd
from datetime import datetime
from fpdf import FPDF
import io
import gspread
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload
import streamlit.components.v1 as components

# --- MARCA Y CONFIGURACIÓN ---
DATOS_TALLER = {
    "nombre": "AUTOGAS ENERGY",
    "direccion": "Av. Canto Grande 2916, San Juan de Lurigancho",
    "whatsapp": "927843738",
    "logo_url": "https://i.postimg.cc/mD3mzc9v/logo-autogas.png"
}
ID_CARPETA_FOTOS = "1Vk6naUsEDgadg0GDcCrz0nY6MCXrI-1S"

st.set_page_config(page_title=DATOS_TALLER["nombre"], layout="centered")
components.html("<script>window.onbeforeunload = function() { return '¿Salir?'; };</script>", height=0)

# --- SERVICIOS GOOGLE ---
def conectar():
    creds = Credentials.from_service_account_info(st.secrets["google_credentials"], 
            scopes=["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"])
    return gspread.authorize(creds), build('drive', 'v3', credentials=creds)

client, drive_service = conectar()
db_sheet = client.open("DB_Autogas_Energy").sheet1

def subir_foto(file_bytes, nombre):
    try:
        media = MediaIoBaseUpload(io.BytesIO(file_bytes), mimetype='image/jpeg')
        metadata = {'name': nombre, 'parents': [ID_CARPETA_FOTOS]}
        # supportsAllDrives=True es la instrucción clave para saltar el error 403
        f = drive_service.files().create(body=metadata, media_body=media, fields='id', supportsAllDrives=True).execute()
        return f.get('id')
    except Exception as e:
        return f"Err_{str(e)[:10]}"

# --- PDF ---
def generar_pdf(reg):
    pdf = FPDF(); pdf.add_page()
    pdf.set_fill_color(0, 51, 153); pdf.rect(0, 0, 210, 40, 'F')
    pdf.set_text_color(255, 255, 255); pdf.set_font('Arial', 'B', 16)
    pdf.set_xy(10, 10); pdf.cell(0, 10, DATOS_TALLER["nombre"], ln=True)
    pdf.set_font('Arial', '', 10); pdf.cell(0, 5, DATOS_TALLER["direccion"], ln=True)
    pdf.ln(20); pdf.set_text_color(0, 0, 0); pdf.set_font('Arial', 'B', 12)
    pdf.cell(0, 10, "REPORTE TECNICO", 1, 1, 'C')
    pdf.set_font('Arial', '', 10)
    pdf.cell(50, 8, f"PLACA: {reg['placa']}", 1); pdf.cell(50, 8, f"FECHA: {reg['fecha']}", 1, 1)
    pdf.multi_cell(0, 8, f"TRABAJOS: {reg['tareas']}", 1)
    return pdf.output(dest='S').encode('latin-1')

# --- LOGICA DE NAVEGACION ---
if 'view' not in st.session_state: st.session_state.view = 'inicio'
if 'step' not in st.session_state: st.session_state.step = 1

PAQUETES = {
    "A": ["Cambio aceite", "Filtro aire", "Filtro aceite", "Fugas gas", "Fugas refrig.", "Scan motor", "Siliconeo"],
    "B": ["Paquete A + Bujias"],
    "C": ["Paquete A + Filtro Gas"],
    "D": ["Limpieza Inyectores", "Obturador", "Sensores", "Filtros", "Fugas", "Scan"],
    "E": ["Full Inyectores Gas/Gaso", "Regulacion", "Sensores", "Filtros", "Scan"],
    "F": ["Reductor Gas", "Calibracion", "Bujias", "Fugas", "Scan"]
}

if st.session_state.view == 'inicio':
    st.image(DATOS_TALLER["logo_url"], width=200)
    if st.button("👤 CLIENTE", use_container_width=True): st.session_state.view = 'cliente'; st.rerun()
    if st.button("🛠️ ADMIN", use_container_width=True): st.session_state.view = 'login'; st.rerun()

elif st.session_state.view == 'login':
    u = st.text_input("Usuario"); p = st.text_input("Clave", type="password")
    if st.button("Ingresar"):
        if u == "percy" and p == "autogas2026": st.session_state.view = 'admin'; st.rerun()

elif st.session_state.view == 'admin':
    if st.session_state.step == 1:
        placa = st.text_input("PLACA").upper().strip()
        ma, mo, km = st.text_input("Marca"), st.text_input("Modelo"), st.number_input("KM", min_value=0)
        paq = st.selectbox("Paquete", list(PAQUETES.keys()))
        if st.button("SIGUIENTE"):
            st.session_state.datos = {"placa": placa, "ma": ma, "mo": mo, "km": km, "paq": paq}
            st.session_state.step = 2; st.rerun()
    else:
        d = st.session_state.datos
        tareas = [t for t in PAQUETES[d['paq']] if st.checkbox(t, value=True)]
        obs = st.text_area("Notas")
        fotos = st.file_uploader("Fotos", accept_multiple_files=True)
        if st.button("✅ GUARDAR"):
            with st.spinner("Guardando..."):
                ids = [subir_foto(f.getvalue(), f"{d['placa']}.jpg") for f in fotos] if fotos else []
                db_sheet.append_row([datetime.now().strftime("%d/%m/%Y"), d['placa'], d['ma'], d['mo'], "2024", d['km'], d['paq'], ", ".join(tareas), obs, ",".join(ids)])
                st.success("¡Guardado!"); st.session_state.view = 'inicio'; st.session_state.step = 1; st.rerun()

elif st.session_state.view == 'cliente':
    p_c = st.text_input("PLACA").upper().strip()
    if st.button("CONSULTAR"):
        df = pd.DataFrame(db_sheet.get_all_records())
        df.columns = [c.lower().strip() for c in df.columns]
        hist = df[df['placa'].astype(str).str.upper() == p_c].to_dict('records')
        if hist:
            prox = int(hist[-1]['km']) + 5000
            st.markdown(f"<div style='background-color:#d4edda; padding:30px; border-radius:15px; text-align:center; border:2px solid #155724;'><h2 style='color:#155724;'>¡Estimado Cliente!</h2><p>Mantenimiento a los:</p><h1 style='color:#155724; font-size:4em;'>{prox} KM</h1></div>", unsafe_allow_html=True)
            for r in reversed(hist):
                with st.expander(f"Servicio {r['fecha']}"):
                    st.download_button("Descargar PDF", generar_pdf(r), f"Rep_{r['placa']}.pdf", key=r['km'])
        else: st.warning("Sin registros.")
    if st.button("Volver"): st.session_state.view = 'inicio'; st.rerun()
