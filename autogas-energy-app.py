import streamlit as st
import pandas as pd
from datetime import datetime
import gspread
from google.oauth2.service_account import Credentials
import cloudinary
import cloudinary.uploader

# --- 1. CONFIGURACIÓN ---
cloudinary.config(
  cloud_name = st.secrets["CLOUDINARY_CLOUD_NAME"],
  api_key = st.secrets["CLOUDINARY_API_KEY"],
  api_secret = st.secrets["CLOUDINARY_API_SECRET"],
  secure = True
)

@st.cache_resource
def init_google():
    creds = Credentials.from_service_account_info(st.secrets["google_credentials"], 
            scopes=["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"])
    return gspread.authorize(creds).open("DB_Autogas_Energy").sheet1

db = init_google()

# --- 2. PAQUETES ---
PAQUETES = {
    "PAQUETE A": ["Cambio de Aceite", "Filtro de Aire", "Revisión de Niveles"],
    "PAQUETE B": ["Limpieza de Inyectores", "Cambio de Bujías", "Escaneo Computarizado"],
    "PAQUETE C": ["Mantenimiento GLP/GNV", "Cambio de Filtros Gas", "Calibración"],
    "PAQUETE D": ["Afinamiento Electrónico", "Limpieza de Mariposa", "Prueba de Sensores"],
    "PAQUETE E": ["Mantenimiento Preventivo Full", "Suspensión", "Frenos"],
    "PAQUETE F": ["Servicio Especial Autogas", "Diagnóstico Avanzado"]
}

# --- 3. ESTADO DE NAVEGACIÓN ---
if 'view' not in st.session_state: st.session_state.view = 'home'
if 'step_admin' not in st.session_state: st.session_state.step_admin = 1

# --- 4. VISTA: HOME (MENÚ PRINCIPAL) ---
if st.session_state.view == 'home':
    st.image("https://i.postimg.cc/mD3mzc9v/logo-autogas.png", width=250)
    st.title("AUTOGAS ENERGY")
    if st.button("👤 MODO CLIENTE"): 
        st.session_state.view = 'cliente'
        st.rerun()
    st.write("---")
    if st.button("🛠️ MODO ADMINISTRADOR"): 
        st.session_state.view = 'login'
        st.rerun()

# --- 5. VISTA: LOGIN ---
elif st.session_state.view == 'login':
    st.subheader("Acceso Administrativo")
    u = st.text_input("Usuario")
    p = st.text_input("Clave", type="password")
    if st.button("INGRESAR"):
        if u == "percy" and p == "autogas2026":
            st.session_state.view = 'admin'
            st.rerun()
    if st.button("VOLVER"): 
        st.session_state.view = 'home'
        st.rerun()

# --- 6. VISTA: ADMINISTRADOR (FLUJO POR PASOS) ---
elif st.session_state.view == 'admin':
    st.header("🛠️ Registro de Servicio")
    
    # PASO 1: PLACA
    if st.session_state.step_admin == 1:
        placa = st.text_input("INGRESE PLACA").upper().strip()
        if st.button("SIGUIENTE"):
            df = pd.DataFrame(db.get_all_records())
            df.columns = [c.lower().strip() for c in df.columns]
            st.session_state.form = {"placa": placa}
            
            match = df[df['placa'].astype(str) == placa] if 'placa' in df.columns else pd.DataFrame()
            if not match.empty:
                last = match.iloc[-1]
                st.session_state.form.update({"marca": last.get('marca',''), "modelo": last.get('modelo',''), "año": last.get('año','')})
                st.session_state.step_admin = 2
            else:
                st.session_state.step_admin = 1.5
            st.rerun()

    # PASO 1.5: DATOS AUTO NUEVO
    elif st.session_state.step_admin == 1.5:
        st.info("Vehículo Nuevo. Complete los datos:")
        st.session_state.form["marca"] = st.text_input("Marca")
        st.session_state.form["modelo"] = st.text_input("Modelo")
        st.session_state.form["año"] = st.text_input("Año")
        if st.button("REGISTRAR VEHÍCULO"):
            st.session_state.step_admin = 2
            st.rerun()

    # PASO 2: PAQUETE Y KM
    elif st.session_state.step_admin == 2:
        st.subheader(f"Placa: {st.session_state.form['placa']}")
        st.session_state.form["paquete"] = st.selectbox("Seleccione Paquete", list(PAQUETES.keys()))
        st.session_state.form["km"] = st.number_input("Kilometraje Actual", min_value=0)
        if st.button("SIGUIENTE ➡️"):
            st.session_state.step_admin = 3
            st.rerun()

    # PASO 3: CHECKLIST Y FOTOS
    elif st.session_state.step_admin == 3:
        paq_sel = st.session_state.form["paquete"]
        st.subheader(f"Check-list: {paq_sel}")
        for item in PAQUETES[paq_sel]:
            st.checkbox(item, value=True)
        
        st.session_state.form["obs"] = st.text_area("Cuadro de Observaciones")
        fotos = st.file_uploader("Subir Evidencia Fotográfica", accept_multiple_files=True)
        
        if st.button("✅ GUARDAR TODO"):
            with st.spinner("Subiendo a la nube..."):
                urls = [cloudinary.uploader.upload(f.getvalue(), folder=f"Taller_{st.session_state.form['placa']}")['secure_url'] for f in fotos] if fotos else []
                f = st.session_state.form
                db.append_row([datetime.now().strftime("%d/%m/%Y"), f['placa'], f['marca'], f['modelo'], f['año'], f['km'], f['paquete'], "Terminado", f['obs'], ",".join(urls)])
                st.success("¡Registro Exitoso!")
                st.session_state.view = 'home'
                st.session_state.step_admin = 1
                st.rerun()

# --- 7. VISTA: CLIENTE (3 OPCIONES) ---
elif st.session_state.view == 'cliente':
    placa_c = st.text_input("INGRESE SU PLACA").upper().strip()
    if placa_c:
        df = pd.DataFrame(db.get_all_records())
        df.columns = [c.lower().strip() for c in df.columns]
        hist = df[df['placa'].astype(str) == placa_c].to_dict('records')
        
        if hist:
            st.write("---")
            c1, c2, c3 = st.columns(3)
            if c1.button("Próximo Mantenimiento"): st.session_state.c_view = 'prox'
            if c2.button("Mantenimiento Actual"): st.session_state.c_view = 'actual'
            if c3.button("Historial Diagnóstico"): st.session_state.c_view = 'diag'

            mode = st.session_state.get('c_view', 'prox')
            
            if mode == 'prox':
                prox_km = int(hist[-1]['km']) + 5000
                st.markdown(f"""
                    <div style="background:#00c6ff; padding:50px; border-radius:20px; text-align:center; color:white;">
                        <h2>PRÓXIMO MANTENIMIENTO</h2>
                        <h1 style="font-size:75px; color:white !important;">{prox_km} KM</h1>
                    </div>
                """, unsafe_allow_html=True)

            elif mode == 'actual':
                last = hist[-1]
                st.subheader(f"Servicio Actual: {last['fecha']}")
                st.write(f"**KM:** {last['km']} | **Paquete:** {last['paquete']}")
                st.write(f"**Observaciones:** {last.get('notas', last.get('observaciones', ''))}")
                for url in str(last.get('links_fotos', '')).split(","):
                    if "http" in url: st.image(url)

            elif mode == 'diag':
                st.subheader("Historial Completo")
                for r in reversed(hist):
                    with st.expander(f"📅 {r['fecha']} - {r['km']} KM"):
                        st.write(f"Trabajo: {r['paquete']}")
                        for url in str(r.get('links_fotos', '')).split(","):
                            if "http" in url: st.image(url)
        else:
            st.warning("No se encontró la placa.")
            
    if st.button("VOLVER AL INICIO"):
        st.session_state.view = 'home'
        st.rerun()
