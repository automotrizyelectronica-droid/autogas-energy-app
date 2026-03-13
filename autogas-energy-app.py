import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime
from fpdf import FPDF
import io

# --- CONFIGURACIÓN DE MARCA ---
DATOS_TALLER = {
    "nombre": "AUTOGAS ENERGY",
    "direccion": "Av. Canto Grande 2916, San Juan de Lurigancho",
    "whatsapp": "927843738",
    "logo_url": "https://i.postimg.cc/mD3mzc9v/logo-autogas.png"
}

st.set_page_config(page_title=DATOS_TALLER["nombre"], layout="centered")

# --- BASE DE DATOS ---
def init_db():
    conn = sqlite3.connect('autogas_pro_v7.db', check_same_thread=False)
    c = conn.cursor()
    c.execute('CREATE TABLE IF NOT EXISTS vehiculos (placa TEXT PRIMARY KEY, marca TEXT, modelo TEXT, anio TEXT)')
    c.execute('''CREATE TABLE IF NOT EXISTS historial 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, fecha TEXT, placa TEXT, 
                  km_tablero INTEGER, paquete TEXT, tareas TEXT, notas TEXT)''')
    conn.commit()
    return conn

conn = init_db()

# --- CLASE PARA PDF PROFESIONAL ---
class ReportePDF(FPDF):
    def header(self):
        # Logo y Datos del Taller
        try:
            self.image(DATOS_TALLER["logo_url"], 10, 8, 33)
        except:
            self.set_font('Arial', 'B', 15)
            self.cell(40, 10, 'AUTOGAS')
        
        self.set_font('Arial', 'B', 12)
        self.cell(80)
        self.cell(0, 5, DATOS_TALLER["nombre"], ln=True, align='R')
        self.set_font('Arial', '', 9)
        self.cell(0, 5, DATOS_TALLER["direccion"], ln=True, align='R')
        self.cell(0, 5, f"WhatsApp: {DATOS_TALLER['whatsapp']}", ln=True, align='R')
        self.ln(20)

def generar_pdf_formato(datos_h, datos_v):
    pdf = ReportePDF()
    pdf.add_page()
    
    # Título del Informe
    pdf.set_fill_color(230, 230, 230)
    pdf.set_font('Arial', 'B', 14)
    pdf.cell(0, 10, f"INFORME DE MANTENIMIENTO - PAQUETE {datos_h['paquete']}", 0, 1, 'C', True)
    pdf.ln(5)
    
    # Cuadro Datos del Vehículo
    pdf.set_font('Arial', 'B', 11)
    pdf.cell(0, 7, "DATOS DEL VEHÍCULO", 0, 1, 'L')
    pdf.set_font('Arial', '', 10)
    pdf.cell(95, 7, f"Placa: {datos_h['placa']}", 1)
    pdf.cell(95, 7, f"Fecha: {datos_h['fecha']}", 1, 1)
    pdf.cell(95, 7, f"Marca/Modelo: {datos_v[1]} {datos_v[2]}", 1)
    pdf.cell(95, 7, f"Kilometraje: {datos_h['km_tablero']} KM", 1, 1)
    pdf.ln(5)
    
    # Checklist de Tareas
    pdf.set_font('Arial', 'B', 11)
    pdf.cell(0, 7, "TRABAJOS REALIZADOS", 0, 1, 'L')
    pdf.set_font('Arial', '', 9)
    tareas = datos_h['tareas'].split(", ")
    for t in tareas:
        pdf.cell(10, 6, " [X] ", 0)
        pdf.cell(0, 6, t, 0, 1)
    
    # Observaciones
    if datos_h['notas']:
        pdf.ln(5)
        pdf.set_font('Arial', 'B', 11)
        pdf.cell(0, 7, "OBSERVACIONES TÉCNICAS", 0, 1, 'L')
        pdf.set_font('Arial', 'I', 10)
        pdf.multi_cell(0, 6, datos_h['notas'])
    
    return pdf.output(dest='S').encode('latin-1')

# --- LOS 6 PAQUETES ---
PAQUETES = {
    "A": ["Cambio de aceite", "Cambio de filtro de aire", "Cambio de filtro de aceite", "Inspeccion de fugas de gas", "Inspeccion de fugas de refrigerate y aceite", "Scanneo de motor", "siliconeo de motor"],
    "B": ["Cambio de aceite", "Cambio de filtro de aire", "Cambio de filtro de aceite", "Inspeccion de fugas de gas", "Inspeccion de fugas de refrigerate y aceite", "Cambio o inspeccion de bujias", "Scanneo de motor", "siliconeo de motor"],
    "C": ["Cambio de aceite", "Cambio de filtro de aire", "Cambio de filtro de aceite", "Cambio de filtro de gas", "Inspeccion de fugas de gas", "Inspeccion de fugas de refrigerate y aceite", "Scanneo de motor", "siliconeo de motor"],
    "D": ["Cambio de aceite", "Cambio de filtro de aire", "Cambio de filtro de aceite", "Cambio de filtro de gas", "Cambio de filtro de gasolina (externo)", "Limpieza de inyectores gasolina", "Cambio de oring y filtro de inyector", "Limpieza de obturador", "Cambio o inpeccion de bujias", "Limpieza de sensores (maf-map-cmp-ckp-vvt-o2)", "Inspeccion de fugas de gas", "Inspeccion de fugas de refrigerate y aceite", "Scanneo de motor", "siliconeo de motor"],
    "E": ["Cambio de aceite", "Cambio de filtro de aire", "Cambio de filtro de aceite", "Cambio de filtro de gas", "Limpieza de inyectores de gas", "Cambio de filtro de gasolina (externo)", "Limpieza de inyectores gasolina", "Cambio de oring y filtro de inyector", "Limpieza de obturador", "Cambio o inpeccion de bujias", "Limpieza de sensores", "Inspeccion de fugas de gas", "Inspeccion de fugas de refrigerate y aceite", "Scanneo de motor", "Regulacion / Calibracion de gas", "siliconeo de motor"],
    "F": ["Cambio de aceite", "Cambio de filtro de aire", "Cambio de filtro de aceite", "Cambio o inpeccion de bujias", "Limpieza de reductor de gas", "Inspeccion de fugas de gas", "Inspeccion de fugas de refrigerate y aceite", "Scanneo de motor", "Regulacion / Calibracion de gas", "siliconeo de motor"]
}

# --- CONTROL DE FLUJO ---
if 'view' not in st.session_state: st.session_state.view = 'inicio'
if 'admin_step' not in st.session_state: st.session_state.admin_step = 1

# --- VISTAS ---
if st.session_state.view == 'inicio':
    st.image(DATOS_TALLER["logo_url"], width=200)
    st.title(DATOS_TALLER["nombre"])
    col1, col2 = st.columns(2)
    if col1.button("👤 ÁREA CLIENTE", use_container_width=True): st.session_state.view = 'cliente_placa'; st.rerun()
    if col2.button("🛠️ ADMINISTRACIÓN", use_container_width=True): st.session_state.view = 'login'; st.rerun()

elif st.session_state.view == 'login':
    if st.button("⬅️ REGRESAR"): st.session_state.view = 'inicio'; st.rerun()
    u = st.text_input("Usuario")
    p = st.text_input("Contraseña", type="password")
    if st.button("INGRESAR"):
        if u == "percy" and p == "autogas2026": st.session_state.view = 'admin_panel'; st.session_state.admin_step = 1; st.rerun()
        else: st.error("Error")

elif st.session_state.view == 'admin_panel':
    if st.session_state.admin_step == 1:
        st.subheader("Paso 1: Identificación")
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
            if st.button("INGRESAR"):
                st.session_state.temp = {"placa": placa, "marca": ma, "modelo": mo, "anio": an, "km": km, "paquete": pa, "nuevo": v is None}
                st.session_state.admin_step = 2; st.rerun()
    
    elif st.session_state.admin_step == 2:
        d = st.session_state.temp
        st.title(f"Hoja de Trabajo: {d['placa']}")
        tareas_ok = []
        for t in PAQUETES[d['paquete']]:
            if st.checkbox(t, value=True): tareas_ok.append(t)
        notitas = st.text_area("Observaciones")
        st.file_uploader("Subir Fotos", accept_multiple_files=True)
        if st.button("✅ GUARDAR Y FINALIZAR"):
            c = conn.cursor()
            if d['nuevo']: c.execute("INSERT INTO vehiculos VALUES (?,?,?,?)", (d['placa'], d['marca'], d['modelo'], d['anio']))
            f = datetime.now().strftime("%d/%m/%Y")
            c.execute("INSERT INTO historial (fecha, placa, km_tablero, paquete, tareas, notas) VALUES (?,?,?,?,?,?)",
                      (f, d['placa'], d['km'], d['paquete'], ", ".join(tareas_ok), notitas))
            conn.commit()
            st.session_state.view = 'inicio'; st.rerun()

elif st.session_state.view == 'cliente_placa':
    if st.button("⬅️ REGRESAR"): st.session_state.view = 'inicio'; st.rerun()
    p_c = st.text_input("INGRESE SU PLACA").upper()
    if p_c: st.session_state.placa_cliente = p_c; st.session_state.view = 'cliente_menu'; st.rerun()

elif st.session_state.view == 'cliente_menu':
    st.title(f"🚗 Placa: {st.session_state.placa_cliente}")
    if st.button("⬅️ REGRESAR AL INICIO"): st.session_state.view = 'inicio'; st.rerun()
    
    # 1. PRÓXIMO MANTENIMIENTO (DISEÑO INTOCABLE)
    if st.button("📅 PRÓXIMO MANTENIMIENTO PREVENTIVO", use_container_width=True):
        df = pd.read_sql_query(f"SELECT km_tablero FROM historial WHERE placa='{st.session_state.placa_cliente}' ORDER BY id DESC LIMIT 1", conn)
        if not df.empty:
            prox = int(df.iloc[0]['km_tablero']) + 5000
            st.markdown(f"<div style='background-color:#d4edda; padding:20px; border-radius:10px; text-align:center;'><h2>¡Estimado Cliente!</h2><p style='font-size:1.5em;'>Su próximo mantenimiento preventivo en <b>AUTOGAS ENERGY</b> le toca a los:</p><h1 style='font-size:3.5em;'>{prox} KM</h1></div>", unsafe_allow_html=True)

    # 2. MANTENIMIENTO ACTUAL (CON PDF PROFESIONAL)
    if st.button("📋 MANTENIMIENTO ACTUAL (HISTORIAL)", use_container_width=True):
        df = pd.read_sql_query(f"SELECT * FROM historial WHERE placa='{st.session_state.placa_cliente}' ORDER BY id DESC", conn)
        c = conn.cursor()
        c.execute("SELECT * FROM vehiculos WHERE placa=?", (st.session_state.placa_cliente,))
        v_data = c.fetchone()
        
        for _, row in df.iterrows():
            with st.expander(f"📄 KM: {row['km_tablero']} - Fecha: {row['fecha']}"):
                pdf_bin = generar_pdf_formato(row, v_data)
                st.download_button(label="📥 Descargar Reporte PDF Profesional", 
                                   data=pdf_bin, 
                                   file_name=f"Reporte_{row['placa']}_{row['fecha']}.pdf", 
                                   mime="application/pdf")
