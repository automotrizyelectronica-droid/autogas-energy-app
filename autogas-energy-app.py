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

# --- CONFIGURACIÓN DE MARCA ---
DATOS_TALLER = {
    "nombre": "AUTOGAS ENERGY",
    "direccion": "Av. Canto Grande 2916, San Juan de Lurigancho",
    "whatsapp": "927843738",
    "logo_url": "https://i.postimg.cc/mD3mzc9v/logo-autogas.png"
}

st.set_page_config(page_title=DATOS_TALLER["nombre"], layout="centered")
components.html("<script>window.onbeforeunload = function() { return '¿Salir?'; };</script>", height=0)

# --- CONEXIÓN GOOGLE ---
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
        media = MediaIoBaseUpload(io.BytesIO(file_bytes), mimetype='image/jpeg', resumable=True)
        # Sube a la raíz por ahora para asegurar que no falle
        file = drive_service.files().create(body={'name': nombre}, media_body=media, fields='id').execute()
        return file.get('id')
    except: return "error"

# --- PDF PROFESIONAL ---
class ReporteProfesional(FPDF):
    def header(self):
        self.set_fill_color(0, 51, 153); self.rect(0, 0, 210, 40, 'F')
        try: self.image(DATOS_TALLER["logo_url"], 12, 8, 30)
        except: pass
        self.set_text_color(255, 255, 255); self.set_font('Arial', 'B', 18)
        self.set_xy(50, 10); self.cell(0, 10, DATOS_TALLER["nombre"], ln=True)
        self.ln(15)

def generar_pdf_pro(reg):
    pdf = ReporteProfesional(); pdf.add_page(); pdf.set_text_color(0, 0, 0)
    pdf.set_font('Arial', 'B', 14); pdf.set_fill_color(230, 230, 230)
    pdf.cell(0, 10, "REPORTE TECNICO", 0, 1, 'C', True); pdf.ln(5)
    pdf.set_font('Arial', 'B', 10)
    pdf.cell(45, 8, "PLACA:", 1, 0, 'L', True); pdf.cell(50, 8, str(reg.get('placa', '')), 1)
    pdf.cell(45, 8, "FECHA:", 1, 0, 'L', True); pdf.cell(50, 8, str(reg.get('fecha', '')), 1, 1)
    pdf.ln(10)
    pdf.multi_cell(0, 6, f"Trabajos realizados: {reg.get('tareas', '')}")
    return pdf.output(dest='S').encode('latin-1')

PAQUETES = {
    "A": ["Cambio de aceite", "Filtros", "Inspeccion general"],
    "B": ["Paquete A + Bujias"],
    "C": ["Paquete A + Filtro Gas"],
    "D": ["Mantenimiento Completo Sistema"],
    "E": ["Mantenimiento Full + Inyectores"],
    "F": ["Revision Reductor + Calibracion"]
}

# --- NAVEGACIÓN ---
if 'view' not in st.session_state: st.session_state.view = 'inicio'
if 'admin_step' not in st.session_state: st.session_state.admin_step = 1

if st.session_state.view == 'inicio':
    st.image(DATOS_TALLER["logo_url"], width=200); st.title(DATOS_TALLER["nombre"])
    col1, col2 = st.columns(2)
    if col1.button("👤 ÁREA CLIENTE", use_container_width=True): st.session_state.view = 'cliente_placa'; st.rerun()
    if col2.button("🛠️ ADMIN", use_container_width=True): st.session_state.view = 'login'; st.rerun()

elif st.session_state.view == 'login':
    u = st.text_input("Usuario"); p = st.text_input("Contraseña", type="password")
    if st.button("INGRESAR"):
        if u == "percy" and p == "autogas2026": st.session_state.view = 'admin_panel'; st.rerun()

elif st.session_state.view == 'admin_panel':
    if st.session_state.admin_step == 1:
        placa = st.text_input("PLACA").upper()
        ma, mo, an = st.text_input("Marca"), st.text_input("Modelo"), st.text_input("Año")
        km = st.number_input("KM", min_value=0)
        pa = st.selectbox("Paquete", list(PAQUETES.keys()))
        if st.button("SIGUIENTE ➡️"):
            st.session_state.temp = {"placa": placa, "marca": ma, "modelo": mo, "anio": an, "km": km, "paquete": pa}
            st.session_state.admin_step = 2; st.rerun()
    elif st.session_state.admin_step == 2:
        d = st.session_state.temp
        tareas_ok = [t for t in PAQUETES[d['paquete']] if st.checkbox(t, value=True)]
        notas = st.text_area("Notas")
        fotos = st.file_uploader("Fotos", accept_multiple_files=True)
        if st.button("✅ GUARDAR"):
            ids = [subir_foto_drive(f.getvalue(), f"{d['placa']}.jpg") for f in fotos] if fotos else []
            db_sheet.append_row([datetime.now().strftime("%d/%m/%Y"), d['placa'], d['marca'], d['modelo'], d['anio'], d['km'], d['paquete'], ", ".join(tareas_ok), notas, ",".join(ids)])
            st.success("Guardado!"); st.session_state.view = 'inicio'; st.session_state.admin_step = 1; st.rerun()

elif st.session_state.view == 'cliente_placa':
    p_c = st.text_input("PLACA").upper()
    if st.button("CONSULTAR"):
        st.session_state.placa_cliente = p_c; st.session_state.view = 'cliente_menu'; st.rerun()

elif st.session_state.view == 'cliente_menu':
    st.title(f"Placa: {st.session_state.placa_cliente}")
    # Lectura corregida:
    try:
        data = db_sheet.get_all_records()
        hist = [r for r in data if str(r.get('placa')).upper() == st.session_state.placa_cliente]
    except: hist = []
    
    if st.button("📅 PRÓXIMO MANTENIMIENTO"):
        if hist: st.success(f"Toca a los {int(hist[-1]['km'])+5000} KM")
        else: st.warning("No hay datos.")
    
    if st.button("📋 HISTORIAL"):
        for r in reversed(hist):
            with st.expander(f"Servicio {r['fecha']}"):
                st.download_button("Descargar PDF", data=generar_pdf_pro(r), file_name="Rep.pdf", key=f"{r['fecha']}{r['km']}")
    if st.button("⬅️ VOLVER"): st.session_state.view = 'inicio'; st.rerun()
