import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime
from fpdf import FPDF
import io
from PIL import Image

# --- CONFIGURACIÓN DE MARCA ---
DATOS_TALLER = {
    "nombre": "AUTOGAS ENERGY",
    "direccion": "Av. Canto Grande 2916, San Juan de Lurigancho",
    "whatsapp": "927843738",
    "facebook": "MasterGas & Mecánica",
    "logo_url": "https://i.postimg.cc/mD3mzc9v/logo-autogas.png"
}

st.set_page_config(page_title=DATOS_TALLER["nombre"], layout="centered")

# --- BASE DE DATOS ---
def init_db():
    conn = sqlite3.connect('autogas_energy_v8.db', check_same_thread=False)
    c = conn.cursor()
    c.execute('CREATE TABLE IF NOT EXISTS vehiculos (placa TEXT PRIMARY KEY, marca TEXT, modelo TEXT, anio TEXT)')
    c.execute('''CREATE TABLE IF NOT EXISTS historial 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, fecha TEXT, placa TEXT, 
                  km_tablero INTEGER, paquete TEXT, tareas TEXT, notas TEXT)''')
    conn.commit()
    return conn

conn = init_db()

# --- CLASE PDF PROFESIONAL ---
class ReporteProfesional(FPDF):
    def header(self):
        self.set_fill_color(0, 71, 171) # Azul Corporativo
        self.rect(0, 0, 210, 35, 'F')
        self.set_text_color(255, 255, 255)
        self.set_font('Arial', 'B', 20)
        self.cell(0, 10, DATOS_TALLER["nombre"], ln=True, align='C')
        self.set_font('Arial', '', 10)
        self.cell(0, 5, DATOS_TALLER["direccion"], ln=True, align='C')
        self.cell(0, 5, f"WhatsApp: {DATOS_TALLER['whatsapp']}", ln=True, align='C')
        self.ln(10)

def generar_pdf_pro(datos_h, datos_v):
    pdf = ReporteProfesional()
    pdf.add_page()
    pdf.set_text_color(0, 0, 0)
    
    # Datos Vehículo
    pdf.set_font('Arial', 'B', 12)
    pdf.cell(0, 10, "INFORME TÉCNICO DE MANTENIMIENTO", 0, 1, 'C')
    pdf.ln(5)
    
    pdf.set_font('Arial', 'B', 10)
    pdf.set_fill_color(240, 240, 240)
    pdf.cell(45, 8, "Placa:", 1, 0, 'L', True); pdf.cell(50, 8, str(datos_h['placa']), 1)
    pdf.cell(45, 8, "Fecha:", 1, 0, 'L', True); pdf.cell(50, 8, str(datos_h['fecha']), 1, 1)
    
    pdf.cell(45, 8, "Marca/Modelo:", 1, 0, 'L', True); pdf.cell(50, 8, f"{datos_v[1]} {datos_v[2]}", 1)
    pdf.cell(45, 8, "KM:", 1, 0, 'L', True); pdf.cell(50, 8, f"{datos_h['km_tablero']}", 1, 1)
    pdf.ln(10)

    # Tareas
    pdf.set_font('Arial', 'B', 11)
    pdf.cell(0, 8, f"Trabajos Realizados - Paquete {datos_h['paquete']}", 0, 1)
    pdf.set_font('Arial', '', 10)
    for t in datos_h['tareas'].split(", "):
        pdf.cell(10, 6, ">>", 0); pdf.cell(0, 6, t, 0, 1)
    
    return pdf.output(dest='S').encode('latin-1')

# --- TAREAS ---
PAQUETES = {
    "A": ["Cambio de aceite", "Filtro aire", "Filtro aceite", "Fugas gas", "Fugas refrig/aceite", "Scanner", "Siliconeo"],
    "B": ["Cambio de aceite", "Filtro aire", "Filtro aceite", "Fugas gas", "Fugas refrig", "Bujias", "Scanner", "Siliconeo"],
    "C": ["Cambio de aceite", "Filtro aire", "Filtro aceite", "Filtro de gas", "Fugas gas", "Fugas refrig", "Scanner", "Siliconeo"],
    "D": ["C. Aceite/Filtros", "Filtro gas", "Filtro gasolina", "Inyectores gasolina", "Orings/Filtros", "Obturador", "Bujias", "Sensores", "Fugas", "Scanner", "Siliconeo"],
    "E": ["C. Aceite/Filtros", "Filtro gas", "Inyectores gas", "Filtro gasolina", "Inyectores gasolina", "Obturador", "Bujias", "Sensores", "Fugas", "Scanner", "Regulacion gas", "Siliconeo"],
    "F": ["C. Aceite/Filtros", "Bujias", "Limpieza reductor", "Fugas", "Scanner", "Regulacion gas", "Siliconeo"]
}

# --- LÓGICA DE NAVEGACIÓN ---
if 'view' not in st.session_state: st.session_state.view = 'inicio'
if 'placa_cliente' not in st.session_state: st.session_state.placa_cliente = ""

# --- VISTA: INICIO ---
if st.session_state.view == 'inicio':
    st.image(DATOS_TALLER["logo_url"], width=200)
    st.title(DATOS_TALLER["nombre"])
    col1, col2 = st.columns(2)
    if col1.button("👤 ÁREA CLIENTE", use_container_width=True):
        st.session_state.view = 'cliente_placa'
        st.rerun()
    if col2.button("🛠️ ADMINISTRACIÓN", use_container_width=True):
        st.session_state.view = 'login'
        st.rerun()

# --- VISTA: CLIENTE (INGRESO PLACA) ---
elif st.session_state.view == 'cliente_placa':
    if st.button("⬅️ REGRESAR"): st.session_state.view = 'inicio'; st.rerun()
    st.subheader("Ingrese su placa para consultar")
    p_c = st.text_input("PLACA").upper()
    if st.button("CONSULTAR"):
        if p_c:
            st.session_state.placa_cliente = p_c
            st.session_state.view = 'cliente_menu'
            st.rerun()
        else: st.error("Ingrese una placa")

# --- VISTA: CLIENTE (MENÚ 3 BOTONES) ---
elif st.session_state.view == 'cliente_menu':
    st.title(f"🚗 Vehículo: {st.session_state.placa_cliente}")
    if st.button("⬅️ REGRESAR"): st.session_state.view = 'cliente_placa'; st.rerun()
    
    # 1. PRÓXIMO MANTENIMIENTO
    if st.button("📅 PRÓXIMO MANTENIMIENTO PREVENTIVO", use_container_width=True):
        df = pd.read_sql_query(f"SELECT km_tablero FROM historial WHERE placa='{st.session_state.placa_cliente}' ORDER BY id DESC LIMIT 1", conn)
        if not df.empty:
            prox = int(df.iloc[0]['km_tablero']) + 5000
            st.markdown(f"<div style='background-color:#d4edda; padding:20px; border-radius:10px; text-align:center;'><h2>¡Estimado Cliente!</h2><p style='font-size:1.2em;'>Su próximo mantenimiento preventivo en <b>AUTOGAS ENERGY</b> le toca a los:</p><h1 style='color:#155724;'>{prox} KM</h1></div>", unsafe_allow_html=True)
        else: st.warning("No hay registros para esta placa.")

    # 2. MANTENIMIENTO ACTUAL (HISTORIAL)
    if st.button("📋 MANTENIMIENTO ACTUAL (HISTORIAL)", use_container_width=True):
        df = pd.read_sql_query(f"SELECT * FROM historial WHERE placa='{st.session_state.placa_cliente}' ORDER BY id DESC", conn)
        c = conn.cursor()
        c.execute("SELECT * FROM vehiculos WHERE placa=?", (st.session_state.placa_cliente,))
        v_data = c.fetchone()
        
        if not df.empty and v_data:
            for _, row in df.iterrows():
                with st.expander(f"📄 Servicio: {row['fecha']} - {row['km_tablero']} KM"):
                    pdf_bin = generar_pdf_pro(row, v_data)
                    st.download_button(f"📥 Descargar PDF {row['fecha']}", data=pdf_bin, file_name=f"Informe_{row['placa']}.pdf", key=row['id'])
        else: st.warning("No hay historial disponible.")

    # 3. DIAGNÓSTICO
    if st.button("🔍 HISTORIAL DE DIAGNÓSTICO", use_container_width=True):
        st.info("Próximamente informes de fallas.")

# --- VISTA: LOGIN ADMIN ---
elif st.session_state.view == 'login':
    if st.button("⬅️ REGRESAR"): st.session_state.view = 'inicio'; st.rerun()
    u = st.text_input("Usuario")
    p = st.text_input("Contraseña", type="password")
    if st.button("INGRESAR"):
        if u == "percy" and p == "autogas2026":
            st.session_state.view = 'admin_panel'
            st.session_state.admin_step = 1
            st.rerun()

# --- VISTA: ADMIN PANEL ---
elif st.session_state.view == 'admin_panel':
    if st.session_state.admin_step == 1:
        placa = st.text_input("PLACA").upper()
        if placa:
            c = conn.cursor()
            c.execute("SELECT * FROM vehiculos WHERE placa=?", (placa,))
            v = c.fetchone()
            ma = st.text_input("Marca", value=v[1] if v else "")
            mo = st.text_input("Modelo", value=v[2] if v else "")
            an = st.text_input("Año", value=v[3] if v else "")
            km = st.number_input("Kilometraje Actual", min_value=0)
            pa = st.selectbox("Paquete", ["A", "B", "C", "D", "E", "F"])
            if st.button("SIGUIENTE ➡️"):
                st.session_state.temp = {"placa": placa, "marca": ma, "modelo": mo, "anio": an, "km": km, "paquete": pa, "nuevo": v is None}
                st.session_state.admin_step = 2; st.rerun()
    
    elif st.session_state.admin_step == 2:
        d = st.session_state.temp
        st.subheader(f"Hoja de Trabajo: {d['placa']}")
        tareas_ok = [t for t in PAQUETES[d['paquete']] if st.checkbox(t, value=True)]
        notas = st.text_area("Observaciones")
        if st.button("✅ GUARDAR"):
            c = conn.cursor()
            if d['nuevo']: c.execute("INSERT INTO vehiculos VALUES (?,?,?,?)", (d['placa'], d['marca'], d['modelo'], d['anio']))
            f = datetime.now().strftime("%d/%m/%Y")
            c.execute("INSERT INTO historial (fecha, placa, km_tablero, paquete, tareas, notas) VALUES (?,?,?,?,?,?)",
                      (f, d['placa'], d['km'], d['paquete'], ", ".join(tareas_ok), notas))
            conn.commit()
            st.session_state.view = 'inicio'; st.rerun()
