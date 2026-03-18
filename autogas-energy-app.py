import streamlit as st
import pandas as pd
from datetime import datetime
import gspread
from google.oauth2.service_account import Credentials
import cloudinary
import cloudinary.uploader

# --- 1. CONFIGURACIÓN DE NUBE (CLOUDINARY) ---
try:
    cloudinary.config(
      cloud_name = st.secrets["CLOUDINARY_CLOUD_NAME"],
      api_key = st.secrets["CLOUDINARY_API_KEY"],
      api_secret = st.secrets["CLOUDINARY_API_SECRET"],
      secure = True
    )
except Exception as e:
    st.error("Error en llaves de Cloudinary. Revisa tus Secrets.")

# --- 2. ESTILO VISUAL PREMIUM (MODO OSCURO) ---
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
        margin-bottom: 20px;
    }
    .stButton>button {
        width: 100%;
        border-radius: 15px;
        height: 3.8em;
        background: linear-gradient(90deg, #00c6ff 0%, #0072ff 100%) !important;
        color: white !important;
        font-weight: bold;
        border: none;
    }
    h1 { color: #00c6ff !important; text-align: center; font-weight: 800; }
    </style>
""", unsafe_allow_html=True)

# --- 3. CONEXIÓN GOOGLE SHEETS ---
@st.cache_resource
def init_google():
    try:
        # Cargamos credenciales desde el bloque [google_credentials] de tus Secrets
        info = st.secrets["google_credentials"]
        creds = Credentials.from_service_account_info(info, 
                scopes=["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"])
        client = gspread.authorize(creds)
        # Busca el nombre exacto de tu archivo
        return client.open("DB_Autogas_Energy").sheet1
    except Exception as e:
        st.error(f"Error conectando al Excel: {e}")
        return None

db = init_google()

# --- 4. ESTADO DE LA APP ---
if 'view' not in st.session_state: st.session_state.view = 'home'
if 'step' not in st.session_state: st.session_state.step = 1

# --- 5. VISTAS ---
if st.session_state.view == 'home':
    st.image("https://i.postimg.cc/mD3mzc9v/logo-autogas.png", width=220)
    st.markdown('<div class="main-card">', unsafe_allow_html=True)
    st.markdown("<h1>AUTOGAS ENERGY PRO</h1>", unsafe_allow_html=True)
    if st.button("👤 ÁREA DEL CLIENTE"): st.session_state.view = 'cliente'; st.rerun()
    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("🛠️ PANEL ADMINISTRADOR"): st.session_state.view = 'login'; st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

elif st.session_state.view == 'login':
    st.markdown('<div class="main-card">', unsafe_allow_html=True)
    st.subheader("Acceso Técnico")
    u = st.text_input("Usuario")
    p = st.text_input("Clave", type="password")
    if st.button("INGRESAR"):
        if u == "percy" and p == "autogas2026":
            st.session_state.view = 'admin'; st.rerun()
    if st.button("VOLVER"): st.session_state.view = 'home'; st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

elif st.session_state.view == 'admin':
    st.markdown('<div class="main-card">', unsafe_allow_html=True)
    if st.session_state.step == 1:
        placa = st.text_input("PLACA").upper().strip()
        km = st.number_input("Kilometraje", min_value=0)
        paq = st.selectbox("Paquete", ["A", "B", "C", "D", "E", "F"])
        if st.button("SIGUIENTE ➡️"):
            st.session_state.temp = {"placa": placa, "km": km, "paq": paq}
            st.session_state.step = 2; st.rerun()
    else:
        d = st.session_state.temp
        obs = st.text_area("Observaciones")
        fotos = st.file_uploader("Subir Fotos", accept_multiple_files=True)
        if st.button("✅ GUARDAR TODO"):
            with st.spinner("Subiendo evidencias..."):
                urls = []
                for f in fotos:
                    res = cloudinary.uploader.upload(f.getvalue(), folder=f"Autogas_{d['placa']}")
                    urls.append(res['secure_url'])
                
                db.append_row([datetime.now().strftime("%d/%m/%Y"), d['placa'], "", "", "2024", d['km'], d['paq'], "Mantenimiento", obs, ",".join(urls)])
                st.success("¡Guardado!"); st.session_state.view = 'home'; st.session_state.step = 1; st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

elif st.session_state.view == 'cliente':
    st.markdown('<div class="main-card">', unsafe_allow_html=True)
    p_c = st.text_input("INGRESE SU PLACA").upper()
    if st.button("CONSULTAR"):
        df = pd.DataFrame(db.get_all_records())
        df.columns = [c.lower().strip() for c in df.columns]
        hist = df[df['placa'].astype(str).str.upper() == p_c].to_dict('records')
        if hist:
            prox = int(hist[-1]['km']) + 5000
            st.success(f"Próximo mantenimiento: {prox} KM")
            for r in reversed(hist):
                with st.expander(f"Servicio {r['fecha']}"):
                    if r.get('links_fotos'):
                        for url in str(r['links_fotos']).split(","):
                            st.image(url, use_container_width=True)
        else: st.warning("No hay registros.")
    if st.button("VOLVER"): st.session_state.view = 'home'; st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)
