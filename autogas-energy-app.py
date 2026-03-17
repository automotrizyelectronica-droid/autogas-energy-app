import streamlit as st
import pandas as pd
from datetime import datetime
from fpdf import FPDF
import io
import tempfile
import os
from PIL import Image
import gspread
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload

# --- CONFIGURACIÓN DE MARCA ---
DATOS_TALLER = {
    "nombre": "AUTOGAS ENERGY",
    "direccion": "Av. Canto Grande 2916, San Juan de Lurigancho",
    "whatsapp": "927843738",
    "logo_url": "https://i.postimg.cc/mD3mzc9v/logo-autogas.png"
}

st.set_page_config(page_title=DATOS_TALLER["nombre"], layout="centered")

# --- CONEXIÓN CON GOOGLE (EL CEREBRO) ---
def conectar_google():
    scope = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive"
    ]
    # Usamos los Secrets que pegaste en Streamlit
    creds_dict = st.secrets["google_credentials"]
    creds = Credentials.from_service_account_info(creds_dict, scopes=scope)
    
    client = gspread.authorize(creds)
    drive_service = build('drive', 'v3', credentials=creds)
    
    # Abrir el Excel que creaste
    sheet = client.open("DB_Autogas_Energy").sheet1
    
    # Si el Excel está nuevo, creamos los encabezados
    if not sheet.get_all_values():
        sheet.append_row(["fecha", "placa", "marca", "modelo", "anio", "km", "paquete", "tareas", "notas", "links_fotos"])
        
    return sheet, drive_service

try:
    db_sheet, drive_service = conectar_google()
except Exception as e:
    st.error(f"Error de conexión: {e}. Revisa si compartiste el Excel con el bot.")
    st.stop()

# --- FUNCIONES DE DRIVE ---
def subir_foto_drive(file_bytes, nombre_archivo):
    # ID de la carpeta "Fotos_Autogas" (la sacas del link de la carpeta en Drive)
    # Si no la pones, se guardará en la raíz del Drive del bot
    file_metadata = {'name': nombre_archivo}
    media = MediaIoBaseUpload(io.BytesIO(file_bytes), mimetype='image/jpeg')
    file = drive_service.files().create(body=file_metadata, media_body=media, fields='id').execute()
    return file.get('id')

# --- CLASE PDF PROFESIONAL ---
class ReporteProfesional(FPDF):
    def header(self):
        self.set_fill_color(0, 51, 153)
        self.rect(0, 0, 210, 40, 'F')
        try: self.image(DATOS_TALLER["logo_url"], 12, 8, 30)
        except: pass
        self.set_text_color(255, 255, 255)
        self.set_font('Arial', 'B', 18)
        self.set_xy(50, 10)
        self.cell(0, 10, DATOS_TALLER["nombre"], ln=True)
        self.set_font('Arial', '', 9)
        self.set_x(50)
        self.cell(0, 5, DATOS_TALLER["direccion"], ln=True)
        self.ln(15)

def generar_pdf_pro(datos):
    pdf = ReporteProfesional()
    pdf.add_page()
    pdf.set_text_color(0, 0, 0)
    pdf.set_font('Arial', 'B', 14); pdf.set_fill_color(230, 230, 230)
    pdf.cell(0, 10, "REPORTE TECNICO DE MANTENIMIENTO", 0, 1, 'C', True); pdf.ln(5)
    
    pdf.set_font('Arial', 'B', 10)
    pdf.cell(45, 8, "PLACA:", 1, 0, 'L', True); pdf.cell(50, 8, str(datos['placa']), 1)
    pdf.cell(45, 8, "FECHA:", 1, 0, 'L', True); pdf.cell(50, 8, str(datos['fecha']), 1, 1)
    pdf.cell(45, 8, "VEHICULO:", 1, 0, 'L', True); pdf.cell(50, 8, f"{datos['marca']} {datos['modelo']}", 1)
    pdf.cell(45, 8, "KM:", 1, 0, 'L', True); pdf.cell(50, 8, f"{datos['km']} KM", 1, 1)
    
    pdf.ln(5); pdf.set_font('Arial', 'B', 11); pdf.cell(0, 8, f"TRABAJOS (PAQUETE {datos['paquete']})", 0, 1)
    pdf.set_font('Arial', '', 10)
    for t in datos['tareas'].split(", "):
        pdf.cell(10, 6, "-", 0); pdf.cell(0, 6, t, 0, 1)

    if datos['notas']:
        pdf.ln(5); pdf.set_font('Arial', 'B', 11); pdf.cell(0, 8, "OBSERVACIONES", 0, 1)
        pdf.multi_cell(0, 6, datos['notas'], 1)

    return pdf.output(dest='S').encode('latin-1')

# --- PAQUETES ---
PAQUETES = {
    "A": ["Cambio de aceite", "Cambio de filtro de aire", "Cambio de filtro de aceite", "Inspeccion de fugas de gas", "Scanneo de motor", "siliconeo de motor"],
    "B": ["Cambio de aceite", "Cambio de filtro de aire", "Cambio de filtro de aceite", "Inspeccion de fugas de gas", "Cambio o inspeccion de bujias", "Scanneo de motor", "siliconeo de motor"],
    "C": ["Cambio de aceite", "Cambio de filtro de aire", "Cambio de filtro de aceite", "Cambio de filtro de gas", "Inspeccion de fugas de gas", "Scanneo de motor", "siliconeo de motor"],
    "D": ["Cambio de aceite", "Cambio de filtro de aire", "Cambio de filtro de aceite", "Cambio de filtro de gas", "Limpieza de inyectores gasolina", "Limpieza de obturador", "Cambio o inpeccion de bujias", "Limpieza de sensores", "Scanneo de motor", "siliconeo de motor"],
    "E": ["Cambio de aceite", "Cambio de filtro de aire", "Cambio de filtro de aceite", "Cambio de filtro de gas", "Limpieza de inyectores de gas", "Limpieza de inyectores gasolina", "Limpieza de obturador", "Cambio o inpeccion de bujias", "Limpieza de sensores", "Regulacion / Calibracion de gas", "siliconeo de motor"],
    "F": ["Cambio de aceite", "Cambio de filtro de aire", "Cambio de filtro de aceite", "Cambio o inpeccion de bujias", "Limpieza de reductor de gas", "Regulacion / Calibracion de gas", "siliconeo de motor"]
}

# --- NAVEGACIÓN ---
if 'view' not in st.session_state: st.session_state.view = 'inicio'

if st.session_state.view == 'inicio':
    st.image(DATOS_TALLER["logo_url"], width=200)
    st.title(DATOS_TALLER["nombre"])
    col1, col2 = st.columns(2)
    if col1.button("👤 ÁREA CLIENTE", use_container_width=True): st.session_state.view = 'cliente_placa'; st.rerun()
    if col2.button("🛠️ ADMIN", use_container_width=True): st.session_state.view = 'login'; st.rerun()

elif st.session_state.view == 'login':
    u = st.text_input("Usuario")
    p = st.text_input("Contraseña", type="password")
    if st.button("INGRESAR"):
        if u == "percy" and p == "autogas2026": st.session_state.view = 'admin_panel'; st.rerun()

elif st.session_state.view == 'admin_panel':
    st.subheader("🛠️ Registro de Mantenimiento")
    placa = st.text_input("PLACA").upper()
    ma = st.text_input("Marca")
    mo = st.text_input("Modelo")
    an = st.text_input("Año")
    km = st.number_input("Kilometraje Actual", min_value=0)
    pa = st.selectbox("Seleccionar Paquete", ["A", "B", "C", "D", "E", "F"])
    tareas_ok = [t for t in PAQUETES[pa] if st.checkbox(t, value=True)]
    notas = st.text_area("Observaciones")
    fotos = st.file_uploader("Subir Fotos", accept_multiple_files=True, type=['jpg', 'png', 'jpeg'])

    if st.button("✅ GUARDAR MANTENIMIENTO"):
        with st.spinner("Guardando en la nube..."):
            links_ids = []
            if fotos:
                for f in fotos:
                    f_id = subir_foto_drive(f.getvalue(), f"{placa}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jpg")
                    links_ids.append(f_id)
            
            # Guardamos la fila en Google Sheets
            nueva_fila = [
                datetime.now().strftime("%d/%m/%Y"),
                placa, ma, mo, an, km, pa, ", ".join(tareas_ok), notas, ",".join(links_ids)
            ]
            db_sheet.append_row(nueva_fila)
            st.success("¡Datos guardados para siempre!")
            st.session_state.view = 'inicio'; st.rerun()

elif st.session_state.view == 'cliente_placa':
    p_c = st.text_input("INGRESE SU PLACA").upper()
    if st.button("VER MI HISTORIAL"):
        st.session_state.placa_cliente = p_c; st.session_state.view = 'cliente_menu'; st.rerun()

elif st.session_state.view == 'cliente_menu':
    st.title(f"🚗 Vehículo: {st.session_state.placa_cliente}")
    # Buscamos en Google Sheets todos los registros de esa placa
    all_data = db_sheet.get_all_records()
    historial = [r for r in all_data if str(r['placa']).upper() == st.session_state.placa_cliente]
    
    if not historial:
        st.warning("No se encontraron registros para esta placa.")
    else:
        for reg in reversed(historial):
            with st.expander(f"📄 Servicio: {reg['fecha']} - {reg['km']} KM"):
                pdf_bin = generar_pdf_pro(reg)
                st.download_button(f"📥 Descargar Reporte PDF", data=pdf_bin, file_name=f"Informe_{reg['placa']}.pdf", key=f"btn_{reg['km']}")

    if st.button("⬅️ VOLVER"): st.session_state.view = 'inicio'; st.rerun()
