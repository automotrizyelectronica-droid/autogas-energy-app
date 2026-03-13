import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime
from fpdf import FPDF

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
    conn = sqlite3.connect('autogas_energy_v3.db', check_same_thread=False)
    c = conn.cursor()
    # Tabla de historial
    c.execute('''CREATE TABLE IF NOT EXISTS historial 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, fecha TEXT, placa TEXT, 
                  km_tablero INTEGER, paquete TEXT, km_proximo INTEGER, notas TEXT, tareas_check TEXT)''')
    conn.commit()
    return conn

conn = init_db()

# --- DICCIONARIO DE TAREAS (TU EXCEL) ---
PAQUETES = {
    "A": ["Cambio de aceite", "Filtro de aire", "Filtro de aceite", "Inspección fugas gas", "Inspección fugas refrigerante/aceite", "Scanner motor", "Siliconeo motor"],
    "B": ["Cambio de aceite", "Filtro de aire", "Filtro de aceite", "Inspección fugas gas", "Inspección fugas refrigerante/aceite", "Cambio o inspección de bujías", "Scanner motor", "Siliconeo motor"],
    "C": ["Cambio de aceite", "Filtro de aire", "Filtro de aceite", "Cambio de filtro de gas", "Inspección fugas gas", "Inspección fugas refrigerante/aceite", "Scanner motor", "Siliconeo motor"],
    "D": ["Cambio de aceite", "Filtro de aire", "Filtro de aceite", "Cambio de filtro de gas", "Cambio de filtro gasolina (externo)", "Limpieza inyectores gasolina", "Cambio oring y filtro inyector", "Limpieza de obturador", "Scanner motor"],
    "E": ["Cambio de aceite", "Filtro de aire", "Filtro de aceite", "Cambio de filtro de gas", "Limpieza inyectores de gas", "Cambio de filtro gasolina (externo)", "Limpieza inyectores gasolina", "Cambio oring y filtro inyector", "Limpieza de obturador", "Cambio o inspección de bujías", "Limpieza sensores (MAF/MAP/etc)", "Scanner motor"],
    "F": ["Cambio de aceite", "Filtro de aire", "Filtro de aceite", "Cambio o inspección de bujías", "Limpieza de reductor de gas", "Inspección fugas de gas", "Inspección fugas refrigerante/aceite", "Scanner motor", "Regulación/Calibración de gas", "Siliconeo motor"]
}

def sugerir_paquete(km):
    if km in [5000, 25000, 35000, 55000, 65000, 85000, 95000]: return "A"
    if km in [10000, 20000, 40000, 50000, 70000, 80000]: return "B"
    if km in [30000, 90000]: return "C"
    if km == 60000: return "D"
    if km == 100000: return "E"
    return "A"

# --- INTERFAZ ---
if 'view' not in st.session_state: st.session_state.view = 'inicio'

if st.session_state.view == 'inicio':
    st.markdown(f"<h1 style='text-align: center; color: #0047AB;'>{DATOS_TALLER['nombre']}</h1>", unsafe_allow_html=True)
    st.info(f"📍 {DATOS_TALLER['direccion']}")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("👤 CONSULTA CLIENTE"): st.session_state.view = 'cliente'; st.rerun()
    with col2:
        if st.button("🛠️ ADMINISTRACIÓN"): st.session_state.view = 'login'; st.rerun()

elif st.session_state.view == 'login':
    if st.button("⬅️ Volver"): st.session_state.view = 'inicio'; st.rerun()
    u = st.text_input("Usuario")
    p = st.text_input("Contraseña", type="password")
    if st.button("Ingresar"):
        if u == "percy" and p == "autogas2026": st.session_state.view = 'admin'; st.rerun()
        else: st.error("Acceso incorrecto")

elif st.session_state.view == 'admin':
    st.title("⚙️ Registro de Servicio")
    if st.button("🚪 Salir"): st.session_state.view = 'inicio'; st.rerun()
    
    placa_input = st.text_input("Escriba la Placa").upper()
    
    # BUSCAR DATOS PREVIOS SI EXISTE LA PLACA
    datos_previos = pd.read_sql_query(f"SELECT * FROM historial WHERE placa='{placa_input}' ORDER BY id DESC LIMIT 1", conn)
    
    if not datos_previos.empty:
        st.success(f"Vehículo recurrente detectado. Último KM: {datos_previos.iloc[0]['km_tablero']} km")
        km_defecto = int(datos_previos.iloc[0]['km_tablero']) + 5000
    else:
        km_defecto = 0

    with st.form("registro_form"):
        km_real = st.number_input("Kilometraje actual (Tablero)", value=km_defecto)
        sug = sugerir_paquete(km_real)
        paq_final = st.selectbox("Paquete a realizar", ["A", "B", "C", "D", "E", "F"], index=["A", "B", "C", "D", "E", "F"].index(sug))
        
        st.write("---")
        st.subheader(f"Checklist de Tareas - Paquete {paq_final}")
        
        # Generar Checkboxes dinámicos
        tareas_seleccionadas = []
        for tarea in PAQUETES[paq_final]:
            if st.checkbox(tarea, value=True):
                tareas_seleccionadas.append(tarea)
        
        st.write("---")
        notas = st.text_area("Notas / Observaciones (Frenos, detalles adicionales, etc.)")
        
        if st.form_submit_button("Guardar Registro"):
            if placa_input == "":
                st.error("Por favor ingrese una placa")
            else:
                f = datetime.now().strftime("%d/%m/%Y")
                prox = km_real + 5000
                tareas_str = ", ".join(tareas_seleccionadas)
                c = conn.cursor()
                c.execute("INSERT INTO historial (fecha, placa, km_tablero, paquete, km_proximo, notas, tareas_check) VALUES (?,?,?,?,?,?,?)",
                          (f, placa_input, km_real, paq_final, prox, notas, tareas_str))
                conn.commit()
                st.success(f"✅ Guardado. Próxima visita sugerida: {prox} km")

elif st.session_state.view == 'cliente':
    if st.button("⬅️ Volver"): st.session_state.view = 'inicio'; st.rerun()
    st.title("🔎 Mi Historial - AUTOGAS ENERGY")
    placa_buscada = st.text_input("Ingrese su Placa").upper()
    if placa_buscada:
        df = pd.read_sql_query(f"SELECT * FROM historial WHERE placa='{placa_buscada}' ORDER BY id DESC", conn)
        if not df.empty:
            st.success(f"### Próximo Mantenimiento: {df.iloc[0]['km_proximo']} km")
            for _, row in df.iterrows():
                with st.expander(f"Fecha: {row['fecha']} | Paquete {row['paquete']}"):
                    st.write(f"**Kilometraje:** {row['km_tablero']} km")
                    st.write(f"**Tareas realizadas:** {row['tareas_check']}")
                    st.write(f"**Observaciones:** {row['notas']}")
        else:
            st.warning("No hay registros para esta placa.")
