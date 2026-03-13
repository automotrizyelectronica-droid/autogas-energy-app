
import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime

# --- CONFIGURACIÓN DE MARCA ---
DATOS_TALLER = {
    "nombre": "AUTOGAS ENERGY",
    "direccion": "Av. Canto Grande 2916, San Juan de Lurigancho",
    "whatsapp": "927843738",
    "tecnico": "Percy Cristóbal"
}

st.set_page_config(page_title=DATOS_TALLER["nombre"], layout="centered")

# --- BASE DE DATOS ---
def init_db():
    conn = sqlite3.connect('autogas_profesional.db', check_same_thread=False)
    c = conn.cursor()
    # Tabla de Vehículos
    c.execute('''CREATE TABLE IF NOT EXISTS vehiculos 
                 (placa TEXT PRIMARY KEY, marca TEXT, modelo TEXT, anio TEXT)''')
    # Tabla de Historial
    c.execute('''CREATE TABLE IF NOT EXISTS historial 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, fecha TEXT, placa TEXT, 
                  km_tablero INTEGER, paquete TEXT, notas TEXT, fotos TEXT)''')
    conn.commit()
    return conn

conn = init_db()

# --- LÓGICA DE PAQUETES (TU EXCEL) ---
PAQUETES = {
    "A": ["Cambio de aceite", "Filtro de aire", "Filtro de aceite", "Inspección fugas gas", "Scanner motor", "Siliconeo motor"],
    "B": ["Cambio de aceite", "Filtro de aire", "Filtro de aceite", "Inspección bujías", "Scanner motor", "Siliconeo motor"],
    "C": ["Cambio de aceite", "Filtro de aire", "Filtro de aceite", "Filtro de gas", "Inspección fugas gas", "Scanner motor"],
    "D": ["Cambio de aceite", "Filtro de aire", "Filtro de aceite", "Filtro de gas", "Filtro gasolina", "Limpieza inyectores", "Limpieza obturador"],
    "E": ["Mantenimiento Integral Gas/Gasolina", "Limpieza inyectores", "Bujías", "Filtros completos", "Scanner", "Limpieza sensores"],
    "F": ["Mantenimiento Reductor Gas", "Cambio de aceite", "Bujías", "Regulación/Calibración gas", "Scanner motor"]
}

# --- NAVEGACIÓN ---
if 'view' not in st.session_state: st.session_state.view = 'inicio'
if 'datos_temp' not in st.session_state: st.session_state.datos_temp = {}

# --- VISTA: INICIO ---
if st.session_state.view == 'inicio':
    st.title(f"🚗 {DATOS_TALLER['nombre']}")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("👤 CLIENTE"): st.session_state.view = 'cliente'; st.rerun()
    with col2:
        if st.button("🛠️ ADMIN"): st.session_state.view = 'login'; st.rerun()

# --- VISTA: LOGIN ---
elif st.session_state.view == 'login':
    if st.button("⬅️"): st.session_state.view = 'inicio'; st.rerun()
    u = st.text_input("Usuario")
    p = st.text_input("Contraseña", type="password")
    if st.button("Entrar"):
        if u == "percy" and p == "autogas2026": st.session_state.view = 'paso1'; st.rerun()
        else: st.error("Error")

# --- PASO 1: DATOS DEL VEHÍCULO Y KM ---
elif st.session_state.view == 'paso1':
    st.title("🛠️ Identificación del Vehículo")
    placa = st.text_input("PLACA").upper()
    
    if placa:
        c = conn.cursor()
        c.execute("SELECT * FROM vehiculos WHERE placa=?", (placa,))
        v = c.fetchone()
        
        with st.form("datos_carro"):
            col1, col2 = st.columns(2)
            marca = col1.text_input("Marca", value=v[1] if v else "")
            modelo = col2.text_input("Modelo", value=v[2] if v else "")
            km = st.number_input("Kilometraje Actual", min_value=0)
            paquete = st.selectbox("Seleccione Paquete", ["A", "B", "C", "D", "E", "F"])
            
            if st.form_submit_button("Siguiente ➡️"):
                st.session_state.datos_temp = {
                    "placa": placa, "marca": marca, "modelo": modelo, 
                    "km": km, "paquete": paquete, "nuevo": v is None
                }
                st.session_state.view = 'paso2'; st.rerun()

# --- PASO 2: FORMATO / CHECKLIST ---
elif st.session_state.view == 'paso2':
    d = st.session_state.datos_temp
    st.title(f"📋 Formato de Trabajo: {d['paquete']}")
    st.subheader(f"Vehículo: {d['placa']} ({d['marca']} {d['modelo']})")
    
    st.write("### Checklist de Tareas")
    tareas_finales = []
    for t in PAQUETES[d['paquete']]:
        if st.checkbox(t, value=True, key=t):
            tareas_finales.append(t)
            
    notas = st.text_area("Observaciones (Ej: Estado de frenos, fugas detectadas...)")
    fotos = st.file_uploader("Adjuntar Fotos de Evidencia", accept_multiple_files=True)
    
    if st.button("✅ GUARDAR TODO Y GENERAR"):
        c = conn.cursor()
        # Guardar vehículo si es nuevo
        if d['nuevo']:
            c.execute("INSERT INTO vehiculos VALUES (?,?,?,'')", (d['placa'], d['marca'], d['modelo']))
        # Guardar historial
        f = datetime.now().strftime("%d/%m/%Y")
        c.execute("INSERT INTO historial (fecha, placa, km_tablero, paquete, notas) VALUES (?,?,?,?,?)",
                  (f, d['placa'], d['km'], d['paquete'], notas))
        conn.commit()
        st.success("¡Registro guardado en la base de datos!")
        if st.button("Volver al Inicio"): st.session_state.view = 'inicio'; st.rerun()

# --- VISTA: CLIENTE ---
elif st.session_state.view == 'cliente':
    if st.button("⬅️"): st.session_state.view = 'inicio'; st.rerun()
    st.title("🔎 Consulta de Historial")
    p = st.text_input("Ingrese Placa").upper()
    if p:
        df = pd.read_sql_query(f"SELECT * FROM historial WHERE placa='{p}' ORDER BY id DESC", conn)
        if not df.empty:
            st.info(f"Próximo Mantenimiento: {int(df.iloc[0]['km_tablero']) + 5000} km")
            st.dataframe(df[['fecha', 'km_tablero', 'paquete', 'notas']])
        else: st.warning("No hay datos.")
