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
    "logo_url": "https://i.postimg.cc/mD3mzc9v/logo-autogas.png" # Tu logo
}

st.set_page_config(page_title=DATOS_TALLER["nombre"], layout="centered")

# --- BASE DE DATOS ---
def init_db():
    conn = sqlite3.connect('autogas_energy_final.db', check_same_thread=False)
    c = conn.cursor()
    c.execute('CREATE TABLE IF NOT EXISTS vehiculos (placa TEXT PRIMARY KEY, marca TEXT, modelo TEXT, anio TEXT)')
    c.execute('''CREATE TABLE IF NOT EXISTS historial 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, fecha TEXT, placa TEXT, 
                  km_tablero INTEGER, paquete TEXT, tareas TEXT, notas TEXT, pdf_data BLOB)''')
    conn.commit()
    return conn

conn = init_db()

# --- TAREAS POR PAQUETE (Tus datos de texto) ---
PAQUETES = {
    "A": ["Cambio de aceite", "Filtro de aire", "Filtro de aceite", "Inspección fugas gas", "Fugas refrig/aceite", "Scanner motor", "Siliconeo motor"],
    "B": ["Cambio de aceite", "Filtro de aire", "Filtro de aceite", "Inspección fugas gas", "Fugas refrig/aceite", "Bujías", "Scanner motor", "Siliconeo motor"],
    "C": ["Cambio de aceite", "Filtro de aire", "Filtro de aceite", "Filtro de gas", "Inspección fugas gas", "Fugas refrig/aceite", "Scanner motor", "Siliconeo motor"],
    "D": ["C. Aceite/Aire/Aceite", "Filtro gas", "Filtro gasolina", "Inyectores gasolina", "Orings/Filtros inyector", "Obturador", "Bujías", "Sensores (MAF/MAP/etc)", "Fugas", "Scanner", "Siliconeo"],
    "E": ["C. Aceite/Aire/Aceite/Gas", "Inyectores Gas", "Filtro gasolina", "Inyectores gasolina", "Orings", "Obturador", "Bujías", "Sensores", "Fugas", "Scanner", "Regulación Gas", "Siliconeo"],
    "F": ["C. Aceite/Aire/Aceite", "Bujías", "Limpieza Reductor Gas", "Fugas", "Scanner", "Regulación Gas", "Siliconeo"]
}

# --- NAVEGACIÓN ---
if 'view' not in st.session_state: st.session_state.view = 'inicio'
if 'temp_admin' not in st.session_state: st.session_state.temp_admin = {}

# --- VISTA: INICIO ---
if st.session_state.view == 'inicio':
    st.image(DATOS_TALLER["logo_url"], width=200)
    st.title(DATOS_TALLER["nombre"])
    col1, col2 = st.columns(2)
    if col1.button("👤 ÁREA CLIENTE", use_container_width=True): st.session_state.view = 'cliente_placa'; st.rerun()
    if col2.button("🛠️ ADMINISTRACIÓN", use_container_width=True): st.session_state.view = 'login'; st.rerun()

# --- VISTA: LOGIN ---
elif st.session_state.view == 'login':
    if st.button("⬅️ REGRESAR"): st.session_state.view = 'inicio'; st.rerun()
    u = st.text_input("Usuario")
    p = st.text_input("Contraseña", type="password")
    if st.button("INGRESAR"):
        if u == "percy" and p == "autogas2026": st.session_state.view = 'admin_paso1'; st.rerun()
        else: st.error("Clave incorrecta")

# --- ADMIN PASO 1: VEHICULO ---
elif st.session_state.view == 'admin_paso1':
    st.subheader("Paso 1: Identificación y Servicio")
    placa = st.text_input("PLACA").upper()
    if placa:
        c = conn.cursor()
        c.execute("SELECT * FROM vehiculos WHERE placa=?", (placa,))
        v = c.fetchone()
        
        marca = st.text_input("Marca", value=v[1] if v else "")
        modelo = st.text_input("Modelo", value=v[2] if v else "")
        anio = st.text_input("Año", value=v[3] if v else "")
        km = st.number_input("Kilometraje Actual", min_value=0)
        paquete = st.selectbox("Paquete", ["A", "B", "C", "D", "E", "F"])
        
        if st.button("INGRESAR"):
            st.session_state.temp_admin = {"placa": placa, "marca": marca, "modelo": modelo, "anio": anio, "km": km, "paquete": paquete, "nuevo": v is None}
            st.session_state.view = 'admin_paso2'; st.rerun()

# --- ADMIN PASO 2: FORMATO DE LLENADO ---
elif st.session_state.view == 'admin_paso2':
    d = st.session_state.temp_admin
    st.title(f"Hoja de Trabajo: Paquete {d['paquete']}")
    st.write(f"🚗 {d['placa']} | {d['marca']} {d['modelo']}")
    
    st.write("### Checklist de Tareas")
    tareas_ok = []
    for t in PAQUETES[d['paquete']]:
        if st.checkbox(t, value=True): tareas_ok.append(t)
    
    notas = st.text_area("Observaciones (Frenos, etc.)")
    st.file_uploader("Subir Fotos", accept_multiple_files=True)
    
    if st.button("✅ GUARDAR Y FINALIZAR"):
        c = conn.cursor()
        if d['nuevo']: c.execute("INSERT INTO vehiculos VALUES (?,?,?,?)", (d['placa'], d['marca'], d['modelo'], d['anio']))
        fecha = datetime.now().strftime("%d/%m/%Y")
        c.execute("INSERT INTO historial (fecha, placa, km_tablero, paquete, tareas, notas) VALUES (?,?,?,?,?,?)",
                  (fecha, d['placa'], d['km'], d['paquete'], ", ".join(tareas_ok), notas))
        conn.commit()
        st.success("Guardado exitosamente")
        st.session_state.view = 'inicio'; st.rerun()

# --- VISTA CLIENTE: 3 BOTONES ---
elif st.session_state.view == 'cliente_placa':
    if st.button("⬅️ REGRESAR"): st.session_state.view = 'inicio'; st.rerun()
    placa = st.text_input("INGRESE SU PLACA").upper()
    if placa:
        st.session_state.placa_cliente = placa
        st.session_state.view = 'cliente_menu'; st.rerun()

elif st.session_state.view == 'cliente_menu':
    st.title(f"🚗 Placa: {st.session_state.placa_cliente}")
    if st.button("⬅️ REGRESAR"): st.session_state.view = 'cliente_placa'; st.rerun()
    
    if st.button("📅 PRÓXIMO MANTENIMIENTO PREVENTIVO", use_container_width=True):
        df = pd.read_sql_query(f"SELECT * FROM historial WHERE placa='{st.session_state.placa_cliente}' ORDER BY id DESC LIMIT 1", conn)
        if not df.empty:
            st.info(f"Su próximo mantenimiento es a los **{int(df.iloc[0]['km_tablero']) + 5000} km**.")
        else: st.warning("No hay registros.")

    if st.button("📋 MANTENIMIENTO ACTUAL (HISTORIAL)", use_container_width=True):
        df = pd.read_sql_query(f"SELECT * FROM historial WHERE placa='{st.session_state.placa_cliente}' ORDER BY id DESC", conn)
        for _, row in df.iterrows():
            st.button(f"📄 KM: {row['km_tablero']} - Fecha: {row['fecha']}", key=row['id'])

    if st.button("🔍 HISTORIAL DE DIAGNÓSTICO", use_container_width=True):
        st.write("Sección en desarrollo.")
