import streamlit as st
import pandas as pd
from datetime import datetime
import gspread
from google.oauth2.service_account import Credentials
import cloudinary
import cloudinary.uploader

# --- CONFIGURACIÓN DE NUBE (CLOUDINARY) ---
cloudinary.config(
  cloud_name = st.secrets["CLOUDINARY_CLOUD_NAME"],
  api_key = st.secrets["CLOUDINARY_API_KEY"],
  api_secret = st.secrets["CLOUDINARY_API_SECRET"],
  secure = True
)

# --- ESTILO VISUAL (MANTENIENDO EL COLOR AZUL PRO) ---
st.set_page_config(page_title="AUTOGAS ENERGY", layout="centered")
st.markdown("""
    <style>
    .stApp { background-color: #0e1117; color: white; }
    .stButton>button { width: 100%; border-radius: 10px; height: 3em; background: #00c6ff; color: white; font-weight: bold; }
    .card { background: #1c252e; padding: 20px; border-radius: 15px; border: 1px solid #333; margin-bottom: 15px; }
    h1, h2, h3 { color: #00c6ff !important; }
    </style>
""", unsafe_allow_html=True)

# --- CONEXIÓN GOOGLE SHEETS ---
@st.cache_resource
def init_google():
    creds = Credentials.from_service_account_info(st.secrets["google_credentials"], 
            scopes=["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"])
    return gspread.authorize(creds).open("DB_Autogas_Energy").sheet1

db = init_google()

# --- DEFINICIÓN DE PAQUETES (Check-list) ---
PAQUETES = {
    "PAQUETE A": ["Cambio de Aceite", "Filtro de Aire", "Revisión de Niveles"],
    "PAQUETE B": ["Limpieza de Inyectores", "Cambio de Bujías", "Escaneo Computarizado"],
    "PAQUETE C": ["Mantenimiento GLP/GNV", "Cambio de Filtros Gas", "Calibración"],
}

# --- ESTADO DE NAVEGACIÓN ---
if 'view' not in st.session_state: st.session_state.view = 'home'
if 'step_admin' not in st.session_state: st.session_state.step_admin = 1

# --- VISTA: HOME ---
if st.session_state.view == 'home':
    st.image("https://i.postimg.cc/mD3mzc9v/logo-autogas.png", width=200)
    st.title("SISTEMA AUTOGAS ENERGY")
    if st.button("👤 MODO CLIENTE"): st.session_state.view = 'cliente'; st.rerun()
    if st.button("🛠️ MODO ADMINISTRADOR"): st.session_state.view = 'login'; st.rerun()

# --- VISTA: LOGIN ---
elif st.session_state.view == 'login':
    u = st.text_input("Usuario")
    p = st.text_input("Clave", type="password")
    if st.button("ENTRAR"):
        if u == "percy" and p == "autogas2026":
            st.session_state.view = 'admin'; st.rerun()
    if st.button("VOLVER"): st.session_state.view = 'home'; st.rerun()

# --- VISTA: ADMINISTRADOR (FLUJO POR PASOS) ---
elif st.session_state.view == 'admin':
    st.header("🛠️ Registro de Servicio")
    
    # PASO 1: VALIDAR PLACA
    if st.session_state.step_admin == 1:
        placa = st.text_input("INGRESE PLACA").upper().strip()
        if st.button("SIGUIENTE"):
            all_data = pd.DataFrame(db.get_all_records())
            # Buscar si existe la placa
            match = all_data[all_data['PLACA'].astype(str).str.upper() == placa] if not all_data.empty else pd.DataFrame()
            
            st.session_state.form = {"placa": placa}
            if not match.empty:
                last = match.iloc[-1]
                st.session_state.form.update({"marca": last['MARCA'], "modelo": last['MODELO'], "año": last['AÑO']})
                st.session_state.step_admin = 2 # Salta a elegir paquete
            else:
                st.session_state.step_admin = 1.5 # Datos de auto nuevo
            st.rerun()

    # PASO 1.5: DATOS AUTO NUEVO
    elif st.session_state.step_admin == 1.5:
        st.subheader("Nuevo Vehículo detectado")
        st.session_state.form["marca"] = st.text_input("Marca")
        st.session_state.form["modelo"] = st.text_input("Modelo")
        st.session_state.form["año"] = st.text_input("Año")
        if st.button("REGISTRAR AUTO"):
            st.session_state.step_admin = 2; st.rerun()

    # PASO 2: PAQUETE Y KM
    elif st.session_state.step_admin == 2:
        st.subheader(f"Vehículo: {st.session_state.form['placa']}")
        st.session_state.form["paquete"] = st.selectbox("Seleccione Paquete", list(PAQUETES.keys()))
        st.session_state.form["km"] = st.number_input("Kilometraje Actual", min_value=0)
        if st.button("SIGUIENTE ➡️"):
            st.session_state.step_admin = 3; st.rerun()

    # PASO 3: CHECKLIST Y FOTOS
    elif st.session_state.step_admin == 3:
        paq_sel = st.session_state.form["paquete"]
        st.subheader(f"Contenido {paq_sel}")
        for item in PAQUETES[paq_sel]:
            st.checkbox(item, value=True) # Check-list visual
        
        st.session_state.form["obs"] = st.text_area("Observaciones Generales")
        fotos = st.file_uploader("Evidencia Fotográfica", accept_multiple_files=True)
        
        if st.button("✅ GUARDAR REGISTRO"):
            with st.spinner("Subiendo a Cloudinary..."):
                urls = [cloudinary.uploader.upload(f.getvalue(), folder=f"Taller_{st.session_state.form['placa']}")['secure_url'] for f in fotos] if fotos else []
                f = st.session_state.form
                db.append_row([datetime.now().strftime("%d/%m/%Y"), f['placa'], f['marca'], f['modelo'], f['año'], f['km'], f['paquete'], "Completado", f['obs'], ",".join(urls)])
                st.success("¡Guardado correctamente!"); st.session_state.view = 'home'; st.session_state.step_admin = 1; st.rerun()

# --- VISTA: CLIENTE (LAS 3 OPCIONES) ---
elif st.session_state.view == 'cliente':
    placa_c = st.text_input("INGRESE SU PLACA").upper().strip()
    if placa_c:
        df = pd.DataFrame(db.get_all_records())
        hist = df[df['PLACA'].astype(str).str.upper() == placa_c].to_dict('records')
        
        if hist:
            col1, col2, col3 = st.columns(3)
            with col1:
                if st.button("Próximo Mantenimiento"): st.session_state.c_view = 'prox'
            with col2:
                if st.button("Mantenimiento Actual"): st.session_state.c_view = 'hist'
            with col3:
                if st.button("Diagnóstico"): st.session_state.c_view = 'diag'

            # SUB-VISTAS CLIENTE
            c_mode = st.session_state.get('c_view', 'prox')
            
            if c_mode == 'prox':
                prox_km = int(hist[-1]['KM']) + 5000
                st.markdown(f"""
                    <div style="background:#00c6ff; padding:40px; border-radius:20px; text-align:center; color:white;">
                        <h2>TU PRÓXIMO MANTENIMIENTO EN</h2>
                        <h1 style="font-size:70px; color:white !important;">{prox_km} KM</h1>
                        <p>Visítanos en Autogas Energy para mantener tu garantía.</p>
                    </div>
                """, unsafe_allow_html=True)

            elif c_mode == 'hist':
                st.subheader("Historial de Trabajos")
                for r in reversed(hist):
                    with st.expander(f"📅 {r['FECHA']} - {r['KM']} KM"):
                        st.write(f"**Trabajo:** {r['PAQUETE']}")
                        st.write(f"**Notas:** {r['NOTAS']}")
                        for url in str(r['LINKS_FOTOS']).split(","):
                            if "http" in url: st.image(url)
                        st.button(f"Descargar Reporte {r['FECHA']}", key=r['FECHA'])

        else: st.warning("Placa no encontrada.")
    if st.button("VOLVER"): st.session_state.view = 'home'; st.rerun()
