import streamlit as st
import pandas as pd
from datetime import datetime
import gspread
from google.oauth2.service_account import Credentials
import cloudinary
import cloudinary.uploader

# --- 1. CONFIGURACIÓN DE NUBE ---
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

# --- 2. DISEÑO VISUAL PREMIUM (CSS CUSTOM) ---
st.set_page_config(page_title="AUTOGAS ENERGY", layout="centered")

st.markdown("""
    <style>
    .stApp { background-color: #0b0e11; color: #e0e0e0; }
    .main-card { background: rgba(255, 255, 255, 0.03); border-radius: 20px; padding: 2rem; border: 1px solid rgba(255, 255, 255, 0.1); margin-bottom: 20px; }
    .stButton>button { width: 100%; border-radius: 12px; height: 3.5em; background: linear-gradient(90deg, #00c6ff 0%, #0072ff 100%) !important; color: white !important; font-weight: bold; border: none; }
    .prox-box { background: linear-gradient(135deg, #00c6ff 0%, #0072ff 100%); padding: 30px; border-radius: 20px; text-align: center; color: white; box-shadow: 0 10px 25px rgba(0, 198, 255, 0.3); }
    h1, h2, h3 { color: #00c6ff !important; text-align: center; }
    .stCheckbox { background: rgba(255,255,255,0.05); padding: 10px; border-radius: 8px; margin-bottom: 5px; }
    </style>
""", unsafe_allow_html=True)

# --- 3. LOGICA DE NAVEGACIÓN ---
if 'view' not in st.session_state: st.session_state.view = 'home'
if 'step_admin' not in st.session_state: st.session_state.step_admin = 1
if 'c_tab' not in st.session_state: st.session_state.c_tab = 'none'

# --- 4. VISTA: HOME ---
if st.session_state.view == 'home':
    st.image("https://i.postimg.cc/mD3mzc9v/logo-autogas.png", width=250)
    st.markdown('<div class="main-card"><h1>BIENVENIDO</h1>', unsafe_allow_html=True)
    if st.button("👤 ÁREA DEL CLIENTE"): st.session_state.view = 'cliente'; st.rerun()
    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("🛠️ ACCESO TÉCNICO"): st.session_state.view = 'login'; st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

# --- 5. VISTA: LOGIN ---
elif st.session_state.view == 'login':
    st.markdown('<div class="main-card"><h3>ACCESO PANEL ADM</h3>', unsafe_allow_html=True)
    u = st.text_input("Usuario")
    p = st.text_input("Clave", type="password")
    if st.button("DESBLOQUEAR"):
        if u == "percy" and p == "autogas2026": st.session_state.view = 'admin'; st.rerun()
    if st.button("⬅️ VOLVER"): st.session_state.view = 'home'; st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

# --- 6. VISTA: ADMINISTRADOR (FLUJO POR PASOS) ---
elif st.session_state.view == 'admin':
    st.markdown(f'<div class="main-card"><h2>REGISTRO PASO {st.session_state.step_admin}</h2>', unsafe_allow_html=True)
    
    if st.session_state.step_admin == 1:
        placa = st.text_input("INGRESE PLACA").upper().strip()
        if st.button("VALIDAR PLACA ➡️"):
            df = pd.DataFrame(db.get_all_records())
            df.columns = [c.lower().strip() for c in df.columns]
            st.session_state.form = {"placa": placa}
            match = df[df['placa'].astype(str) == placa] if 'placa' in df.columns else pd.DataFrame()
            if not match.empty:
                last = match.iloc[-1]
                st.session_state.form.update({"marca": last.get('marca',''), "modelo": last.get('modelo',''), "año": last.get('año','')})
                st.session_state.step_admin = 2
            else: st.session_state.step_admin = 1.5
            st.rerun()

    elif st.session_state.step_admin == 1.5:
        st.write("Vehículo nuevo. Ingrese datos básicos:")
        st.session_state.form["marca"] = st.text_input("Marca")
        st.session_state.form["modelo"] = st.text_input("Modelo")
        st.session_state.form["año"] = st.text_input("Año")
        if st.button("CONTINUAR"): st.session_state.step_admin = 2; st.rerun()

    elif st.session_state.step_admin == 2:
        st.write(f"Auto: {st.session_state.form['placa']} - {st.session_state.form['marca']}")
        st.session_state.form["paquete"] = st.selectbox("Seleccione Paquete", ["A", "B", "C", "D", "E", "F"])
        st.session_state.form["km"] = st.number_input("KM Actual", min_value=0)
        if st.button("IR A CHECKLIST ➡️"): st.session_state.step_admin = 3; st.rerun()

    elif st.session_state.step_admin == 3:
        st.write(f"Check-list: Paquete {st.session_state.form['paquete']}")
        st.checkbox("Inspección de Motor", value=True)
        st.checkbox("Limpieza General", value=True)
        st.session_state.form["obs"] = st.text_area("Observaciones Técnicas")
        fotos = st.file_uploader("Subir Fotos del Trabajo", accept_multiple_files=True)
        if st.button("✅ FINALIZAR Y GUARDAR"):
            with st.spinner("Subiendo evidencias..."):
                urls = [cloudinary.uploader.upload(f.getvalue(), folder=f"Taller_{st.session_state.form['placa']}")['secure_url'] for f in fotos] if fotos else []
                f = st.session_state.form
                db.append_row([datetime.now().strftime("%d/%m/%Y"), f['placa'], f['marca'], f['modelo'], f['año'], f['km'], f['paquete'], "Completado", f['obs'], ",".join(urls)])
                st.success("¡Registro Exitoso!"); st.session_state.view = 'home'; st.session_state.step_admin = 1; st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

# --- 7. VISTA: CLIENTE (3 OPCIONES REQUERIDAS) ---
elif st.session_state.view == 'cliente':
    st.markdown('<div class="main-card">', unsafe_allow_html=True)
    placa_c = st.text_input("INGRESE SU PLACA").upper().strip()
    
    if placa_c:
        df = pd.DataFrame(db.get_all_records())
        df.columns = [c.lower().strip() for c in df.columns]
        hist = df[df['placa'].astype(str) == placa_c].to_dict('records')
        
        if hist:
            st.write("---")
            col1, col2, col3 = st.columns(3)
            if col1.button("MANTENIMIENTO\nPREVENTIVO"): st.session_state.c_tab = 'prox'
            if col2.button("MANTENIMIENTO\nACTUAL"): st.session_state.c_tab = 'actual'
            if col3.button("HISTORIAL DE\nDIAGNÓSTICOS"): st.session_state.c_tab = 'hist'
            
            st.write("<br>", unsafe_allow_html=True)
            
            # 1. PRÓXIMO MANTENIMIENTO PREVENTIVO
            if st.session_state.c_tab == 'prox':
                prox_km = int(hist[-1]['km']) + 5000
                st.markdown(f"""
                    <div class="prox-box">
                        <h2 style="color:white !important; margin:0;">PRÓXIMO SERVICIO EN:</h2>
                        <h1 style="color:white !important; font-size:90px; margin:10px;">{prox_km} KM</h1>
                        <p style="font-weight:bold;">Taller Autorizado: AUTOGAS ENERGY</p>
                    </div>
                """, unsafe_allow_html=True)
            
            # 2. MANTENIMIENTO ACTUAL
            elif st.session_state.c_tab == 'actual':
                last = hist[-1]
                st.markdown(f"### Detalle del Servicio: {last['fecha']}")
                st.info(f"📍
