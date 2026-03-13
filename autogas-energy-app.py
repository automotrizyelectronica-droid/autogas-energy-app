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
    "facebook": "MasterGas & Mecánica",
    "logo_url": "https://i.postimg.cc/mD3mzc9v/logo-autogas.png"
}

st.set_page_config(page_title=DATOS_TALLER["nombre"], layout="centered")

# --- BASE DE DATOS ---
def init_db():
    conn = sqlite3.connect('autogas_energy_v6.db', check_same_thread=False)
    c = conn.cursor()
    c.execute('CREATE TABLE IF NOT EXISTS vehiculos (placa TEXT PRIMARY KEY, marca TEXT, modelo TEXT, anio TEXT)')
    c.execute('''CREATE TABLE IF NOT EXISTS historial 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, fecha TEXT, placa TEXT, 
                  km_tablero INTEGER, paquete TEXT, tareas TEXT, notas TEXT)''')
    conn.commit()
    return conn

conn = init_db()

# --- DATOS DE LOS PAQUETES (TEXTO EXACTO) ---
PAQUETES = {
    "A": ["Cambio de aceite", "Cambio de filtro de aire", "Cambio de filtro de aceite", "Inspeccion de fugas de gas", "Inspeccion de fugas de refrigerate y aceite", "Scanneo de motor", "siliconeo de motor"],
    "B": ["Cambio de aceite", "Cambio de filtro de aire", "Cambio de filtro de aceite", "Inspeccion de fugas de gas", "Inspeccion de fugas de refrigerate y aceite", "Cambio o inspeccion de bujias", "Scanneo de motor", "siliconeo de motor"],
    "C": ["Cambio de aceite", "Cambio de filtro de aire", "Cambio de filtro de aceite", "Cambio de filtro de gas", "Inspeccion de fugas de gas", "Inspeccion de fugas de refrigerate y aceite", "Scanneo de motor", "siliconeo de motor"],
    "D": ["Cambio de aceite", "Cambio de filtro de aire", "Cambio de filtro de aceite", "Cambio de filtro de gas", "Cambio de filtro de gasolina (externo)", "Limpieza de inyectores gasolina", "Cambio de oring y filtro de inyector", "Limpieza de obturador", "Cambio o inpeccion de bujias", "Limpieza de sensores (maf-map-cmp-ckp-vvt-o2)", "Inspeccion de fugas de gas", "Inspeccion de fugas de refrigerate y aceite", "Scanneo de motor", "siliconeo de motor"],
    "E": ["Cambio de aceite", "Cambio de filtro de aire", "Cambio de filtro de aceite", "Cambio de filtro de gas", "Limpieza de inyectores de gas", "Cambio de filtro de gasolina (externo)", "Limpieza de inyectores gasolina", "Cambio de oring y filtro de inyector", "Limpieza de obturador", "Cambio o inpeccion de bujias", "Limpieza de sensores (maf-map-cmp-ckp-vvt-o2)", "Inspeccion de fugas de gas", "Inspeccion de fugas de refrigerate y aceite", "Scanneo de motor", "Regulacion / Calibracion de gas", "siliconeo de motor"],
    "F": ["Cambio de aceite", "Cambio de filtro de aire", "Cambio de filtro de aceite", "Cambio o inpeccion de bujias", "Limpieza de reductor de gas", "Inspeccion de fugas de gas", "Inspeccion de fugas de refrigerate y aceite", "Scanneo de motor", "Regulacion / Calibracion de gas", "siliconeo de motor"]
}

# --- CONTROL DE ESTADOS ---
if 'view' not in st.session_state: st.session_state.view = 'inicio'
if 'admin_step' not in st.session_state: st.session_state.admin_step = 1
if 'temp_reg' not in st.session_state: st.session_state.temp_reg = {}

# --- VISTA: INICIO ---
if st.session_state.view == 'inicio':
    st.image(DATOS_TALLER["logo_url"], width=200)
    st.title(DATOS_TALLER["nombre"])
    st.write(f"📍 {DATOS_TALLER['direccion']}")
    col1, col2 = st.columns(2)
    if col1.button("👤 ÁREA CLIENTE", use_container_width=True): st.session_state.view = 'cliente_placa'; st.rerun()
    if col2.button("🛠️ ADMINISTRACIÓN", use_container_width=True): st.session_state.view = 'login'; st.rerun()

# --- VISTA: LOGIN ---
elif st.session_state.view == 'login':
    if st.button("⬅️ REGRESAR"): st.session_state.view = 'inicio'; st.rerun()
    u = st.text_input("Usuario")
    p = st.text_input("Contraseña", type="password")
    if st.button("INGRESAR"):
        if u == "percy" and p == "autogas2026": st.session_state.view = 'admin_panel'; st.session_state.admin_step = 1; st.rerun()
        else: st.error("Acceso denegado")

# --- VISTA: ADMIN (PASOS) ---
elif st.session_state.view == 'admin_panel':
    if st.session_state.admin_step == 1:
        st.subheader("Paso 1: Identificación y Selección")
        placa = st.text_input("PLACA").upper()
        if placa:
            c = conn.cursor()
            c.execute("SELECT * FROM vehiculos WHERE placa=?", (placa,))
            v = c.fetchone()
            marca = st.text_input("Marca", value=v[1] if v else "")
            modelo = st.text_input("Modelo", value=v[2] if v else "")
            anio = st.text_input("Año", value=v[3] if v else "")
            km = st.number_input("Kilometraje Actual", min_value=0)
            paquete = st.selectbox("Seleccione Paquete", ["A", "B", "C", "D", "E", "F"])
            if st.button("INGRESAR"):
                st.session_state.temp_reg = {"placa": placa, "marca": marca, "modelo": modelo, "anio": anio, "km": km, "paquete": paquete, "nuevo": v is None}
                st.session_state.admin_step = 2; st.rerun()

    elif st.session_state.admin_step == 2:
        d = st.session_state.temp_reg
        st.title(f"Hoja de Trabajo: {d['placa']}")
        st.write(f"Vehículo: {d['marca']} {d['modelo']} | Paquete: {d['paquete']}")
        
        st.write("---")
        st.subheader("Checklist de Tareas")
        tareas_finales = []
        for t in PAQUETES[d['paquete']]:
            if st.checkbox(t, value=True): tareas_finales.append(t)
            
        notas = st.text_area("Cuadro de Observaciones (Frenos, etc.)")
        fotos = st.file_uploader("Adjuntar Fotos de Evidencia", accept_multiple_files=True)
        
        if st.button("✅ GUARDAR Y FINALIZAR"):
            c = conn.cursor()
            if d['nuevo']: c.execute("INSERT INTO vehiculos VALUES (?,?,?,?)", (d['placa'], d['marca'], d['modelo'], d['anio']))
            f = datetime.now().strftime("%d/%m/%Y")
            c.execute("INSERT INTO historial (fecha, placa, km_tablero, paquete, tareas, notas) VALUES (?,?,?,?,?,?)",
                      (f, d['placa'], d['km'], d['paquete'], ", ".join(tareas_finales), notas))
            conn.commit()
            st.success("Guardado correctamente")
            st.session_state.view = 'inicio'; st.rerun()

# --- VISTA: CLIENTE (3 BOTONES) ---
elif st.session_state.view == 'cliente_placa':
    if st.button("⬅️ REGRESAR"): st.session_state.view = 'inicio'; st.rerun()
    placa_c = st.text_input("INGRESE SU PLACA").upper()
    if placa_c:
        st.session_state.placa_cliente = placa_c
        st.session_state.view = 'cliente_menu'; st.rerun()

elif st.session_state.view == 'cliente_menu':
    st.title(f"🚗 Vehículo: {st.session_state.placa_cliente}")
    if st.button("⬅️ REGRESAR AL INICIO"): st.session_state.view = 'inicio'; st.rerun()
    
    if st.button("📅 PRÓXIMO MANTENIMIENTO PREVENTIVO", use_container_width=True):
        df = pd.read_sql_query(f"SELECT km_tablero FROM historial WHERE placa='{st.session_state.placa_cliente}' ORDER BY id DESC LIMIT 1", conn)
        if not df.empty:
            prox_km = int(df.iloc[0]['km_tablero']) + 5000
            st.markdown(f"<div style='background-color:#d4edda; padding:20px; border-radius:10px; text-align:center;'><h2>¡Estimado Cliente!</h2><p style='font-size:1.5em;'>Su próximo mantenimiento preventivo en <b>AUTOGAS ENERGY</b> le toca a los:</p><h1 style='font-size:3.5em;'>{prox_km} KM</h1></div>", unsafe_allow_html=True)
        else: st.warning("Sin registros.")

    if st.button("📋 MANTENIMIENTO ACTUAL (HISTORIAL)", use_container_width=True):
        df = pd.read_sql_query(f"SELECT * FROM historial WHERE placa='{st.session_state.placa_cliente}' ORDER BY id DESC", conn)
        for _, row in df.iterrows():
            with st.expander(f"📄 KM: {row['km_tablero']} - Fecha: {row['fecha']}"):
                st.write(f"**Trabajos:** {row['tareas']}")
                st.write(f"**Observaciones:** {row['notas']}")
                st.button("Descargar PDF (Próximamente)", key=row['id'])

    if st.button("🔍 HISTORIAL DE DIAGNÓSTICO", use_container_width=True):
        st.info("Sección reservada para informes de fallas.")
