import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime
from fpdf import FPDF
import base64

# --- CONFIGURACIÓN DE MARCA ---
DATOS_TALLER = {
    "nombre": "AUTOGAS ENERGY",
    "direccion": "Av. Canto Grande 2916, San Juan de Lurigancho",
    "whatsapp": "927843738",
    "facebook": "MasterGas & Mecánica",
    "tecnico": "Percy Cristóbal"
}

st.set_page_config(page_title=DATOS_TALLER["nombre"], layout="centered", page_icon="⛽")

# --- BASE DE DATOS ---
def init_db():
    conn = sqlite3.connect('autogas_energy_v2.db', check_same_thread=False)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS historial 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, fecha TEXT, placa TEXT, 
                  km_tablero INTEGER, paquete TEXT, km_proximo INTEGER, notas TEXT)''')
    conn.commit()
    return conn

conn = init_db()

# --- LÓGICA DE PAQUETES (TU EXCEL) ---
PAQUETES_TAREAS = {
    "A": ["Cambio de aceite", "Filtro de aire", "Filtro de aceite", "Inspección fugas gas", "Inspección fugas refrigerante/aceite", "Scanner motor", "Siliconeo motor"],
    "B": ["Cambio de aceite", "Filtro de aire", "Filtro de aceite", "Inspección fugas gas", "Inspección fugas refrigerante/aceite", "Inspección bujías", "Scanner motor", "Siliconeo motor"],
    "C": ["Cambio de aceite", "Filtro de aire", "Filtro de aceite", "Filtro de gas", "Inspección fugas gas", "Inspección fugas refrigerante/aceite", "Scanner motor", "Siliconeo motor"],
    "D": ["Cambio de aceite", "Filtro de aire", "Filtro de aceite", "Filtro de gas", "Filtro gasolina externo", "Limpieza inyectores gasolina", "Orings y filtros inyectores", "Limpieza obturador", "Scanner motor"],
    "E": ["Cambio de aceite", "Filtro de aire", "Filtro de aceite", "Filtro de gas", "Limpieza inyectores gas", "Filtro gasolina externo", "Limpieza inyectores gasolina", "Orings y filtros inyectores", "Bujías", "Scanner motor"],
    "F": ["Cambio de aceite", "Filtro de aire", "Filtro de aceite", "Bujías", "Limpieza reductor gas", "Inspección fugas gas", "Inspección fugas refrigerante/aceite", "Scanner motor", "Regulación/Calibración gas"]
}

def sugerir_paquete(km):
    if km in [5000, 25000, 35000, 55000, 65000, 85000, 95000]: return "A"
    if km in [10000, 20000, 40000, 50000, 70000, 80000]: return "B"
    if km in [30000, 90000]: return "C"
    if km == 60000: return "D"
    if km == 100000: return "E"
    return "A"

# --- GENERACIÓN DE PDF ---
def crear_pdf(datos):
    pdf = FPDF()
    pdf.add_page()
    
    # Encabezado estilo Launch
    pdf.set_font('Arial', 'B', 16)
    pdf.cell(0, 10, DATOS_TALLER["nombre"], ln=True, align='C')
    pdf.set_font('Arial', '', 10)
    pdf.cell(0, 5, DATOS_TALLER["direccion"], ln=True, align='C')
    pdf.cell(0, 5, f"WhatsApp: {DATOS_TALLER['whatsapp']} | FB: {DATOS_TALLER['facebook']}", ln=True, align='C')
    pdf.ln(10)
    
    # Cuadro Info Vehículo
    pdf.set_fill_color(230, 230, 230)
    pdf.set_font('Arial', 'B', 12)
    pdf.cell(0, 10, "INFORME DE MANTENIMIENTO", 1, ln=True, align='C', fill=True)
    
    pdf.set_font('Arial', '', 11)
    pdf.cell(95, 10, f"Placa: {datos['placa']}", 1)
    pdf.cell(95, 10, f"Fecha: {datos['fecha']}", 1, ln=True)
    pdf.cell(95, 10, f"KM Tablero: {datos['km_tablero']}", 1)
    pdf.cell(95, 10, f"KM Proximo: {datos['km_proximo']}", 1, ln=True)
    pdf.ln(5)
    
    # Tareas Realizadas
    pdf.set_font('Arial', 'B', 12)
    pdf.cell(0, 10, f"Paquete Aplicado: Tipo {datos['paquete']}", ln=True)
    pdf.set_font('Arial', '', 10)
    for tarea in PAQUETES_TAREAS[datos['paquete']]:
        pdf.cell(0, 7, f"- {tarea}", ln=True)
    
    pdf.ln(5)
    pdf.set_font('Arial', 'B', 11)
    pdf.cell(0, 10, "Observaciones / Otros:", ln=True)
    pdf.set_font('Arial', 'I', 10)
    pdf.multi_cell(0, 7, datos['notas'])
    
    pdf.ln(10)
    pdf.set_font('Arial', 'B', 10)
    pdf.cell(0, 10, f"Técnico Responsable: {DATOS_TALLER['tecnico']}", ln=True, align='R')
    
    return pdf.output(dest='S').encode('latin-1')

# --- INTERFAZ ---
if 'view' not in st.session_state: st.session_state.view = 'inicio'

if st.session_state.view == 'inicio':
    st.markdown(f"<h1 style='text-align: center; color: #E63946;'>{DATOS_TALLER['nombre']}</h1>", unsafe_allow_html=True)
    st.info(f"📍 {DATOS_TALLER['direccion']}")
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("👤 CONSULTA CLIENTE"): st.session_state.view = 'cliente'; st.rerun()
    with col2:
        if st.button("🛠️ ADMINISTRACIÓN"): st.session_state.view = 'login'; st.rerun()

elif st.session_state.view == 'cliente':
    if st.button("⬅️ Volver"): st.session_state.view = 'inicio'; st.rerun()
    st.title("🔎 Historial de mi Vehículo")
    placa_in = st.text_input("Ingrese su Placa").upper()
    if placa_in:
        df = pd.read_sql_query(f"SELECT * FROM historial WHERE placa='{placa_in}' ORDER BY id DESC", conn)
        if not df.empty:
            ultimo = df.iloc[0]
            st.success(f"### Próximo Mantenimiento: {ultimo['km_proximo']} km")
            for _, row in df.iterrows():
                with st.expander(f"Fecha: {row['fecha']} | {row['km_tablero']} km"):
                    st.write(f"**Tipo:** {row['paquete']}")
                    st.write(f"**Notas:** {row['notas']}")
                    pdf_bytes = crear_pdf(row)
                    st.download_button("📥 Descargar Reporte PDF", pdf_bytes, f"Reporte_{row['placa']}_{row['fecha']}.pdf", "application/pdf")
        else: st.error("No hay registros.")

elif st.session_state.view == 'login':
    if st.button("⬅️ Volver"): st.session_state.view = 'inicio'; st.rerun()
    u = st.text_input("Usuario")
    p = st.text_input("Contraseña", type="password")
    if st.button("Entrar"):
        if u == "percy" and p == "autogas2026": st.session_state.view = 'admin'; st.rerun()
        else: st.error("Incorrecto")

elif st.session_state.view == 'admin':
    st.title("🛠️ Registro de Servicio")
    if st.button("🚪 Cerrar Sesión"): st.session_state.view = 'inicio'; st.rerun()
    
    with st.form("reg"):
        placa = st.text_input("Placa").upper()
        km_tab = st.number_input("KM Tablero", min_value=0)
        sug = sugerir_paquete(km_tab)
        paq = st.selectbox("Paquete", ["A", "B", "C", "D", "E", "F"], index=["A", "B", "C", "D", "E", "F"].index(sug))
        notas = st.text_area("Observaciones (Frenos, etc.)")
        if st.form_submit_button("Guardar"):
            f = datetime.now().strftime("%d/%m/%Y")
            prox = km_tab + 5000
            c = conn.cursor()
            c.execute("INSERT INTO historial (fecha, placa, km_tablero, paquete, km_proximo, notas) VALUES (?,?,?,?,?,?)",
                      (f, placa, km_tab, paq, prox, notas))
            conn.commit()
            st.success(f"Guardado. Próximo: {prox} km")
