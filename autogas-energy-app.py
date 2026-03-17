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
        file = drive_service.files().create(body={'name': nombre}, media_body=media, fields='id').execute()
        return file.get('id')
    except: return "sin_foto"

# --- PDF PROFESIONAL ---
class ReporteProfesional(FPDF):
    def header(self):
        self.set_fill_color(0, 51, 153); self.rect(0, 0, 210, 40, 'F')
        try: self.image(DATOS_TALLER["logo_url"], 12, 8, 30)
        except: pass
        self.set_text_color(255, 255, 255); self.set_font('Arial', 'B', 18)
        self.set_xy(50, 10); self.cell(0, 10, DATOS_TALLER["nombre"], ln=True)
        self.set_font('Arial', '', 9); self.set_x(50); self.cell(0, 5, DATOS_TALLER["direccion"], ln=True)
        self.ln(15)

def generar_pdf_pro(reg):
    pdf = ReporteProfesional(); pdf.add_page(); pdf.set_text_color(0, 0, 0)
    pdf.set_font('Arial', 'B', 14); pdf.set_fill_color(230, 230, 230)
    pdf.cell(0, 10, "REPORTE TECNICO DE MANTENIMIENTO", 0, 1, 'C', True); pdf.ln(5)
    pdf.set_font('Arial', 'B', 10)
    pdf.cell(45, 8, "PLACA:", 1, 0, 'L', True); pdf.cell(50, 8, str(reg.get('placa', '')), 1)
    pdf.cell(45, 8, "FECHA:", 1, 0, 'L', True); pdf.cell(50, 8, str(reg.get('fecha', '')), 1, 1)
    pdf.cell(45, 8, "VEHICULO:", 1, 0, 'L', True); pdf.cell(50, 8, f"{reg.get('marca', '')} {reg.get('modelo', '')}", 1)
    pdf.cell(45, 8, "KM:", 1, 0, 'L', True); pdf.cell(50, 8, f"{reg.get('km', '')} KM", 1, 1)
    pdf.ln(5); pdf.set_font('Arial', 'B', 11); pdf.cell(0, 8, f"TRABAJOS (PAQUETE {reg.get('paquete', '')})", 0, 1)
    pdf.set_font('Arial', '', 10)
    for t in str(reg.get('tareas', '')).split(", "):
        pdf.cell(10, 6, "-", 0); pdf.cell(0, 6, t, 0, 1)
    if reg.get('notas'):
        pdf.ln(5); pdf.set_font('Arial', 'B', 11); pdf.cell(0, 8, "OBSERVACIONES", 0, 1)
        pdf.multi_cell(0, 6, str(reg.get('notas', '')), 1)
    return pdf.output(dest='S').encode('latin-1')

PAQUETES = {
    "A": ["Cambio de aceite", "Cambio de filtro de aire", "Cambio de filtro de aceite", "Inspeccion de fugas de gas", "Inspeccion de fugas de refrigerate y aceite", "Scanneo de motor", "siliconeo de motor"],
    "B": ["Cambio de aceite", "Cambio de filtro de aire", "Cambio de filtro de aceite", "Inspeccion de fugas de gas", "Inspeccion de fugas de refrigerate y aceite", "Cambio o inspeccion de bujias", "Scanneo de motor", "siliconeo de motor"],
    "C": ["Cambio de aceite", "Cambio de filtro de aire", "Cambio de filtro de aceite", "Cambio de filtro de gas", "Inspeccion de fugas de gas", "Inspeccion de fugas de refrigerate y aceite", "Scanneo de motor", "siliconeo de motor"],
    "D": ["Cambio de aceite", "Cambio de filtro de aire", "Cambio de filtro de aceite", "Cambio de filtro de gas", "Cambio de filtro de gasolina (externo)", "Limpieza de inyectores gasolina", "Cambio de oring y filtro de inyector", "Limpieza de obturador", "Cambio o inpeccion de bujias", "Limpieza de sensores (maf-map-cmp-ckp-vvt-o2)", "Inspeccion de fugas de gas", "Inspeccion de fugas de refrigerate y aceite", "Scanneo de motor", "siliconeo de motor"],
    "E": ["Cambio de aceite", "Cambio de filtro de aire", "Cambio de filtro de aceite", "Cambio de filtro de gas", "Limpieza de inyectores de gas", "Cambio de filtro de gasolina (externo)", "Limpieza de inyectores gasolina", "Cambio de oring y filtro de inyector", "Limpieza de obturador", "Cambio o inpeccion de bujias", "Limpieza de sensores", "Inspeccion de fugas de gas", "Inspeccion de fugas de refrigerate y aceite", "Scanneo de motor", "Regulacion / Calibracion de gas", "siliconeo de motor"],
    "F": ["Cambio de aceite", "Cambio de filtro de aire", "Cambio de filtro de aceite", "Cambio o inpeccion de bujias", "Limpieza de reductor de gas", "Inspeccion de fugas de gas", "Inspeccion de fugas de refrigerate y aceite", "Scanneo de motor", "Regulacion / Calibracion de gas", "siliconeo de motor"]
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
        if u == "percy" and p == "autogas2026": st.session_state.view = 'admin_panel'; st.session_state.admin_step = 1; st.rerun()

elif st.session_state.view == 'admin_panel':
    if st.session_state.admin_step == 1:
        placa = st.text_input("PLACA").upper()
        ma = st.text_input("Marca")
        mo = st.text_input("Modelo")
        an = st.text_input("Año")
        km = st.number_input("KM Actual", min_value=0)
        pa = st.selectbox("Paquete", ["A","B","C","D","E","F"])
        if st.button("SIGUIENTE ➡️"):
            if not placa: st.error("Ingresa la placa"); st.stop()
            st.session_state.temp = {"placa": placa, "marca": ma, "modelo": mo, "anio": an, "km": km, "paquete": pa}
            st.session_state.admin_step = 2; st.rerun()

    elif st.session_state.admin_step == 2:
        d = st.session_state.temp; st.subheader(f"Hoja de Trabajo: {d['placa']}")
        tareas_ok = [t for t in PAQUETES[d['paquete']] if st.checkbox(t, value=True)]
        notas = st.text_area("Observaciones")
        fotos = st.file_uploader("Fotos", accept_multiple_files=True, type=['jpg','png','jpeg'])
        if st.button("✅ GUARDAR"):
            with st.spinner("Guardando..."):
                ids = []
                if fotos:
                    for f in fotos:
                        f_id = subir_foto_drive(f.getvalue(), f"{d['placa']}_{datetime.now().strftime('%H%M%S')}.jpg")
                        ids.append(f_id)
                # GUARDADO DIRECTO SIN BUSQUEDAS PREVIAS
                fila = [datetime.now().strftime("%d/%m/%Y"), d['placa'], d['marca'], d['modelo'], d['anio'], d['km'], d['paquete'], ", ".join(tareas_ok), notas, ",".join(ids)]
                if not db_sheet.get_all_values(): # Si está vacío, poner cabeceras
                    db_sheet.append_row(["fecha", "placa", "marca", "modelo", "anio", "km", "paquete", "tareas", "notas", "links_fotos"])
                db_sheet.append_row(fila)
                st.success("¡Registro Exitoso!"); st.session_state.view = 'inicio'; st.session_state.admin_step = 1; st.rerun()

elif st.session_state.view == 'cliente_placa':
    p_c = st.text_input("INGRESE SU PLACA").upper()
    if st.button("CONSULTAR"):
        if p_c: st.session_state.placa_cliente = p_c; st.session_state.view = 'cliente_menu'; st.rerun()

elif st.session_state.view == 'cliente_menu':
    st.title(f"🚗 Placa: {st.session_state.placa_cliente}")
    df_raw = pd.DataFrame(db_sheet.get_all_records())
    if not df_raw.empty:
        # Forzamos los nombres de columnas a minúsculas por seguridad
        df_raw.columns = [c.lower() for c in df_raw.columns]
        hist = df_raw[df_raw['placa'].astype(str).str.upper() == st.session_state.placa_cliente].to_dict('records')
    else: hist = []

    if st.button("📅 PRÓXIMO MANTENIMIENTO"):
        if hist:
            prox = int(hist[-1].get('km', 0)) + 5000
            st.success(f"Su próximo mantenimiento es a los {prox} KM")
        else: st.warning("No hay datos.")
    
    if st.button("📋 HISTORIAL"):
        if not hist: st.warning("Sin registros.")
        for r in reversed(hist):
            with st.expander(f"Servicio {r.get('fecha')}"):
                st.download_button("Descargar PDF", data=generar_pdf_pro(r), file_name="Reporte.pdf", key=f"{r.get('fecha')}{r.get('km')}")
    if st.button("⬅️ VOLVER"): st.session_state.view = 'inicio'; st.rerun()
