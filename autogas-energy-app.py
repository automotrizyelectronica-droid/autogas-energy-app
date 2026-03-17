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

# ID DE TU CARPETA (Verificado)
ID_CARPETA_FOTOS = "1Vk6naUsEDgadg0GDcCrz0nY6MCXrI-1S"

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
        # CORRECCIÓN TÉCNICA: Se añade supportsAllDrives para evitar el error 403 de cuota
        file_metadata = {'name': nombre, 'parents': [ID_CARPETA_FOTOS]}
        file = drive_service.files().create(
            body=file_metadata, 
            media_body=media, 
            fields='id',
            supportsAllDrives=True 
        ).execute()
        return file.get('id')
    except Exception as e:
        return f"Error_API: {str(e)[:15]}"

# --- PDF ---
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
    pdf.cell(45, 8, "PLACA:", 1, 0, 'L', True); pdf.cell(50, 8, str(reg.get('placa', '')).upper(), 1)
    pdf.cell(45, 8, "FECHA:", 1, 0, 'L', True); pdf.cell(50, 8, str(reg.get('fecha', '')), 1, 1)
    pdf.cell(45, 8, "VEHICULO:", 1, 0, 'L', True); pdf.cell(50, 8, f"{reg.get('marca', '')} {reg.get('modelo', '')}", 1)
    pdf.cell(45, 8, "KM:", 1, 0, 'L', True); pdf.cell(50, 8, f"{reg.get('km', '')} KM", 1, 1)
    pdf.ln(5); pdf.set_font('Arial', 'B', 11); pdf.cell(0, 8, "DETALLE DE TRABAJOS", 0, 1)
    pdf.set_font('Arial', '', 10)
    for t in str(reg.get('tareas', '')).split(", "):
        pdf.cell(10, 6, "-", 0); pdf.cell(0, 6, t, 0, 1)
    return pdf.output(dest='S').encode('latin-1')

PAQUETES = {
    "A": ["Cambio de aceite", "Cambio de filtro de aire", "Cambio de filtro de aceite", "Inspeccion de fugas de gas", "Inspeccion de fugas de refrigerate y aceite", "Scanneo de motor", "siliconeo de motor"],
    "B": ["Cambio de aceite", "Cambio de filtro de aire", "Cambio de filtro de aceite", "Inspeccion de fugas de gas", "Inspeccion de fugas de refrigerate y aceite", "Cambio o inspeccion de bujias", "Scanneo de motor", "siliconeo de motor"],
    "C": ["Cambio de aceite", "Cambio de filtro de aire", "Cambio de filtro de aceite", "Cambio de filtro de gas", "Inspeccion de fugas de gas", "Inspeccion de fugas de refrigerate y aceite", "Scanneo de motor", "siliconeo de motor"],
    "D": ["Cambio de aceite", "Cambio de filtro de aire", "Cambio de filtro de aceite", "Cambio de filtro de gas", "Filtro gasolina ext.", "Limpieza inyectores gasolina", "Limpieza obturador", "Bujias", "Sensores", "Fugas gas", "Scanneo"],
    "E": ["Mantenimiento Full Gas", "Inyectores Gas/Gasolina", "Obturador", "Sensores", "Regulacion/Calibracion", "Filtros", "Scanneo"],
    "F": ["Reductor Gas", "Regulacion Gas", "Bujias", "Inspeccion fugas", "Scanneo motor"]
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
        placa = st.text_input("PLACA").upper().strip()
        ma, mo, an = st.text_input("Marca"), st.text_input("Modelo"), st.text_input("Año")
        km = st.number_input("KM Actual", min_value=0); pa = st.selectbox("Paquete", list(PAQUETES.keys()))
        if st.button("SIGUIENTE ➡️"):
            st.session_state.temp = {"placa": placa, "marca": ma, "modelo": mo, "anio": an, "km": km, "paquete": pa}
            st.session_state.admin_step = 2; st.rerun()
    elif st.session_state.admin_step == 2:
        d = st.session_state.temp; st.subheader(f"Servicio: {d['placa']}")
        tareas_ok = [t for t in PAQUETES[d['paquete']] if st.checkbox(t, value=True)]
        notas = st.text_area("Observaciones")
        fotos = st.file_uploader("Subir Fotos", accept_multiple_files=True)
        if st.button("✅ GUARDAR"):
            with st.spinner("Guardando..."):
                ids = [subir_foto_drive(f.getvalue(), f"{d['placa']}.jpg") for f in fotos] if fotos else []
                db_sheet.append_row([datetime.now().strftime("%d/%m/%Y"), d['placa'], d['marca'], d['modelo'], d['anio'], d['km'], d['paquete'], ", ".join(tareas_ok), notas, ",".join(ids)])
                st.success("¡Guardado!"); st.session_state.view = 'inicio'; st.session_state.admin_step = 1; st.rerun()

elif st.session_state.view == 'cliente_placa':
    p_c = st.text_input("INGRESE SU PLACA").upper()
    if st.button("CONSULTAR"):
        st.session_state.placa_cliente = p_c; st.session_state.view = 'cliente_menu'; st.rerun()

elif st.session_state.view == 'cliente_menu':
    st.title(f"🚗 Placa: {st.session_state.placa_cliente}")
    df_raw = pd.DataFrame(db_sheet.get_all_records())
    if not df_raw.empty:
        df_raw.columns = [c.lower().strip() for c in df_raw.columns]
        hist = df_raw[df_raw['placa'].astype(str).str.upper().str.strip() == st.session_state.placa_cliente.strip()].to_dict('records')
    else: hist = []
    
    if st.button("📅 PRÓXIMO MANTENIMIENTO PREVENTIVO", use_container_width=True):
        if hist:
            prox = int(hist[-1].get('km', 0)) + 5000
            st.markdown(f"<div style='background-color:#d4edda; padding:30px; border-radius:15px; text-align:center; border: 2px solid #155724;'><h2>¡Estimado Cliente!</h2><p style='font-size:1.3em;'>Su próximo mantenimiento preventivo en <b>AUTOGAS ENERGY</b> le toca a los:</p><h1 style='color:#155724; font-size:4em;'>{prox} KM</h1></div>", unsafe_allow_html=True)
        else: st.warning("Sin historial registrado.")

    if st.button("📋 MANTENIMIENTO ACTUAL (HISTORIAL)", use_container_width=True):
        for r in reversed(hist):
            with st.expander(f"Servicio {r.get('fecha')} - {r.get('km')} KM"):
                st.download_button("Descargar PDF", data=generar_pdf_pro(r), file_name=f"Informe.pdf", key=f"btn_{r.get('km')}")
    if st.button("⬅️ VOLVER"): st.session_state.view = 'inicio'; st.rerun()
