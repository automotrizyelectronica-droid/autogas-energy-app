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

# --- 2. DISEÑO VISUAL ---
st.set_page_config(page_title="AUTOGAS ENERGY", layout="centered")
st.markdown("""
    <style>
    .stApp { background-color: #0b0e11; color: #e0e0e0; }
    .main-card { background: rgba(255, 255, 255, 0.03); border-radius: 20px; padding: 2rem; border: 1px solid rgba(255, 255, 255, 0.1); margin-bottom: 20px; }
    .stButton>button { width: 100%; border-radius: 12px; height: 3.5em; background: linear-gradient(90deg, #00c6ff 0%, #0072ff 100%) !important; color: white !important; font-weight: bold; border: none; }
    .prox-box { background: linear-gradient(135deg, #00c6ff 0%, #0072ff 100%); padding: 30px; border-radius: 20px; text-align: center; color: white; }
    h1, h2, h3 { color: #00c6ff !important; text-align: center; }
    </style>
""", unsafe_allow_html=True)

# --- 3. ESTADO ---
if 'view' not in st.session_state: st.session_state.view = 'home'
if 'step_admin' not in st.session_state: st.session_state.step_admin = 1
if 'c_tab' not in st.session_state: st.session_state.c_tab = 'none'

# --- 4. VISTA: HOME ---
if st.session_state.view == 'home':
    st.image("https://i.postimg.cc/mD3mzc9v/logo-autogas.png", width=250)
    st.markdown('<div class="main-card"><h1>AUTOGAS ENERGY</h1>', unsafe_allow_html=True)
    if st.button("👤 MODO CLIENTE"): 
        st.session_state.view = 'cliente'
        st.rerun()
    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("🛠️ MODO ADMINISTRADOR"): 
        st.session_state.view = 'login'
        st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

# --- 5. VISTA: LOGIN ---
elif st.session_state.view == 'login':
    st.markdown('<div class="main-card"><h3>ACCESO TÉCNICO</h3>', unsafe_allow_html=True)
    u = st.text_input("Usuario")
    p = st.text_input("Clave", type="password")
    if st.button("INGRESAR"):
        if u == "percy" and p == "autogas2026": 
            st.session_state.view = 'admin'
            st.rerun()
    if st.button("VOLVER"): 
        st.session_state.view = 'home'
        st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

# --- 6. VISTA: ADMINISTRADOR ---
elif st.session_state.view == 'admin':
    st.markdown(f'<div class="main-card"><h2>PASO {st.session_state.step_admin}</h2>', unsafe_allow_html=True)
    
    if st.session_state.step_admin == 1:
        placa = st.text_input("PLACA").upper().strip()
        if st.button("SIGUIENTE"):
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
        st.session_state.form["marca"] = st.text_input("Marca")
        st.session_state.form["modelo"] = st.text_input("Modelo")
        st.session_state.form["año"] = st.text_input("Año")
        if st.button("CONTINUAR"): 
            st.session_state.step_admin = 2
            st.rerun()

    elif st.session_state.step_admin == 2:
        st.session_state.form["paquete"] = st.selectbox("Paquete", ["A", "B", "C", "D", "E", "F"])
        st.session_state.form["km"] = st.number_input("KM Actual", min_value=0)
        if st.button("VER CHECKLIST ➡️"): 
            st.session_state.step_admin = 3
            st.rerun()

    elif st.session_state.step_admin == 3:
        st.session_state.form["obs"] = st.text_area("Observaciones")
        fotos = st.file_uploader("Fotos", accept_multiple_files=True)
        if st.button("✅ GUARDAR"):
            with st.spinner("Subiendo..."):
                urls = [cloudinary.uploader.upload(f.getvalue(), folder=f"Taller_{st.session_state.form['placa']}")['secure_url'] for f in fotos] if fotos else []
                f = st.session_state.form
                db.append_row([datetime.now().strftime("%d/%m/%Y"), f['placa'], f['marca'], f['modelo'], f['año'], f['km'], f['paquete'], "Completado", f['obs'], ",".join(urls)])
                st.session_state.view = 'home'
                st.session_state.step_admin = 1
                st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

# --- 7. VISTA: CLIENTE (LAS 3 OPCIONES) ---
elif st.session_state.view == 'cliente':
    st.markdown('<div class="main-card">', unsafe_allow_html=True)
    placa_c = st.text_input("INGRESE PLACA").upper().strip()
    
    if placa_c:
        df = pd.DataFrame(db.get_all_records())
        df.columns = [c.lower().strip() for c in df.columns]
        hist = df[df['placa'].astype(str) == placa_c].to_dict('records')
        
        if hist:
            c1, c2, c3 = st.columns(3)
            if c1.button("MANTENIMIENTO PREVENTIVO"): st.session_state.c_tab = 'prox'
            if c2.button("MANTENIMIENTO ACTUAL"): st.session_state.c_tab = 'actual'
            if c3.button("HISTORIAL DE DIAGNÓSTICOS"): st.session_state.c_tab = 'hist'
            
            if st.session_state.c_tab == 'prox':
                prox = int(hist[-1]['km']) + 5000
                st.markdown(f'<div class="prox-box"><h2>PRÓXIMO SERVICIO EN</h2><h1 style="color:white !important; font-size:80px;">{prox} KM</h1></div>', unsafe_allow_html=True)
            
            elif st.session_state.c_tab == 'actual':
                last = hist[-1]
                st.info(f"Fecha: {last['fecha']} | KM: {last['km']}")
                st.write(f"Paquete: {last['paquete']}")
                for url in str(last.get('links_fotos','')).split(","):
                    if "http" in url: st.image(url)

            elif st.session_state.c_tab == 'hist':
                for r in reversed(hist):
                    with st.expander(f"{r['fecha']} - {r['km']} KM"):
                        for url in str(r.get('links_fotos','')).split(","):
                            if "http" in url: st.image(url)
        else: st.warning("No hay registros.")

    if st.button("⬅️ VOLVER"): 
        st.session_state.view = 'home'
        st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)
