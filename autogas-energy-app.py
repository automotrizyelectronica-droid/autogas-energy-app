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

# --- ESTILO VISUAL PROFESIONAL (MODO OSCURO PREMIUM) ---
st.set_page_config(page_title="AUTOGAS ENERGY", layout="centered")

st.markdown("""
    <style>
    .stApp {
        background: linear-gradient(135deg, #0b0e11 0%, #1c252e 100%);
        color: #e0e0e0;
    }
    .main-card {
        background: rgba(255, 255, 255, 0.04);
        backdrop-filter: blur(12px);
        border-radius: 25px;
        padding: 2.5rem;
        border: 1px solid rgba(255, 255, 255, 0.1);
        box-shadow: 0 15px 35px rgba(0,0,0,0.4);
    }
    .stButton>button {
        width: 100%;
        border-radius: 15px;
        height: 3.8em;
        background: linear-gradient(90deg, #00c6ff 0%, #0072ff 100%) !important;
        color: white !important;
        font-weight: bold;
        font-size: 1.1rem;
        border: none;
        box-shadow: 0 4px 15px rgba(0, 198, 255, 0.3);
    }
    .stButton>button:hover {
        transform: scale(1.02);
        box-shadow: 0 8px 25px rgba(0, 198, 255, 0.5);
    }
    h1 { color: #00c6ff !important; text-align: center; font-weight: 800; }
    </style>
""", unsafe_allow_html=True)

# --- CONEXIÓN GOOGLE SHEETS ---
@st.cache_resource
def init_google():
    creds = Credentials.from_service_account_info(st.secrets["google_credentials"], 
            scopes=["https://www.googleapis.com/auth/spreadsheets"])
    return gspread.authorize(creds).open("DB_Autogas_Energy").sheet1

db = init_google()

# --- LÓGICA DE NAVEGACIÓN ---
if 'view' not in st.session_state: st.session_state.view = 'home'
if 'step' not in st.session_state: st.session_state.step = 1

# --- FUNCIONES ---
def upload_cloudinary(file, placa):
    res = cloudinary.uploader.upload(file, 
        folder=f"Autogas_{placa}",
        public_id=f"{placa}_{datetime.now().strftime('%H%M%S')}")
    return res['secure_url']

# --- VISTAS ---
if st.session_state.view == 'home':
    st.image("https://i.postimg.cc/mD3mzc9v/logo-autogas.png", width=250)
    st.markdown('<div class="main-card">', unsafe_allow_html=True)
    st.markdown("<h1>GESTIÓN AUTOMOTRIZ VIP</h1>", unsafe_allow_html=True)
    if st.button("👤 CONSULTAR MI VEHÍCULO"): 
        st.session_state.view = 'cliente'; st.rerun()
    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("🛠️ ACCESO ADMINISTRADOR"): 
        st.session_state.view = 'login'; st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

elif st.session_state.view == 'login':
    st.markdown('<div class="main-card">', unsafe_allow_html=True)
    st.markdown("### 🔑 PANEL DE CONTROL")
    u = st.text_input("Usuario")
    p = st.text_input("Contraseña", type="password")
    if st.button("DESBLOQUEAR"):
        if u == "percy" and p == "autogas2026":
            st.session_state.view = 'admin'; st.rerun()
    if st.button("⬅️ VOLVER"): st.session_state.view = 'home'; st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

elif st.session_state.view == 'admin':
    st.markdown('<div class="main-card">', unsafe_allow_html=True)
    if st.session_state.step == 1:
        st.subheader("Paso 1: Identificación")
        placa = st.text_input("N° DE PLACA").upper().strip()
        km = st.number_input("Kilometraje Actual", min_value=0)
        paq = st.selectbox("Paquete de Servicio", ["A", "B", "C", "D", "E", "F"])
        if st.button("SIGUIENTE ➡️"):
            st.session_state.datos = {"placa": placa, "km": km, "paq": paq}
            st.session_state.step = 2; st.rerun()
    else:
        d = st.session_state.datos
        st.subheader(f"Paso 2: Registro Fotográfico - {d['placa']}")
        obs = st.text_area("Observaciones del Técnico")
        fotos = st.file_uploader("Subir Evidencias (Fotos)", accept_multiple_files=True)
        if st.button("✅ GUARDAR REGISTRO FINAL"):
            with st.spinner("Sincronizando con la nube..."):
                urls = [upload_cloudinary(f.getvalue(), d['placa']) for f in fotos] if fotos else []
                db.append_row([datetime.now().strftime("%d/%m/%Y"), d['placa'], "", "", "2024", d['km'], d['paq'], "Mantenimiento Preventivo", obs, ",".join(urls)])
                st.success("¡Datos guardados con éxito!"); st.session_state.view = 'home'; st.session_state.step = 1; st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

elif st.session_state.view == 'cliente':
    st.markdown('<div class="main-card">', unsafe_allow_html=True)
    p_c = st.text_input("ESCRIBE TU PLACA").upper()
    if st.button("VER MI HISTORIAL"):
        df = pd.DataFrame(db.get_all_records())
        df.columns = [c.lower().strip() for c in df.columns]
        hist = df[df['placa'].astype(str).str.upper() == p_c].to_dict('records')
        if hist:
            prox = int(hist[-1]['km']) + 5000
            st.markdown(f"""
                <div style="background: rgba(0, 198, 255, 0.1); padding:25px; border-radius:20px; border-left: 8px solid #00c6ff; text-align:center;">
                    <h2 style="color:#00c6ff; margin:0;">PRÓXIMO SERVICIO</h2>
                    <h1 style="font-size:60px; margin:10px;">{prox} KM</h1>
                    <p style="color: #aaa;">Basado en su último registro del {hist[-1]['fecha']}</p>
                </div>
            """, unsafe_allow_html=True)
            st.markdown("### 📋 SERVICIOS ANTERIORES")
            for r in reversed(hist):
                with st.expander(f"Mantenimiento del {r['fecha']}"):
                    if r.get('links_fotos'):
                        for url in str(r['links_fotos']).split(","):
                            st.image(url, caption="Evidencia Técnica", use_container_width=True)
        else: st.warning("No se encontraron registros para esta placa.")
    if st.button("⬅️ VOLVER"): st.session_state.view = 'home'; st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)
