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

# --- ESTILO VISUAL PREMIUM (GLASSMORPHISM) ---
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
        font-size: 1.1rem;
        border: none;
        transition: 0.3s ease;
    }
    .stButton>button:hover {
        transform: scale(1.02);
        box-shadow: 0 8px 25px rgba(0, 198, 255, 0.5);
    }
    h1 { color: #00c6ff !important; text-align: center; font-weight: 800; letter-spacing: 1px; }
    h3 { color: #00c6ff !important; }
    .stExpander { background: rgba(255,255,255,0.05) !important; border-radius: 15px !important; border: none !important; }
    </style>
""", unsafe_allow_html=True)

# --- CONEXIÓN GOOGLE SHEETS ---
@st.cache_resource
def init_google():
    # Usamos la estructura que tienes en tus Secrets
    creds = Credentials.from_service_account_info(st.secrets["google_credentials"], 
            scopes=["https://www.googleapis.com/auth/spreadsheets"])
    return gspread.authorize(creds).open("DB_Autogas_Energy").sheet1

db = init_google()

# --- ESTADO DE NAVEGACIÓN ---
if 'view' not in st.session_state: st.session_state.view = 'home'
if 'step' not in st.session_state: st.session_state.step = 1

# --- MOTOR DE SUBIDA ---
def upload_to_cloud(file, placa):
    try:
        res = cloudinary.uploader.upload(file, 
            folder=f"Autogas_{placa}",
            public_id=f"{placa}_{datetime.now().strftime('%H%M%S')}")
        return res['secure_url']
    except Exception as e:
        return f"Err: {str(e)[:10]}"

# --- INTERFAZ ---
if st.session_state.view == 'home':
    st.markdown("<br>", unsafe_allow_html=True)
    st.image("https://i.postimg.cc/mD3mzc9v/logo-autogas.png", width=250)
    st.markdown('<div class="main-card">', unsafe_allow_html=True)
    st.markdown("<h1>AUTOGAS ENERGY VIP</h1>", unsafe_allow_html=True)
    st.write("<p style='text-align:center; color:#aaa;'>Tecnología y Precisión Automotriz</p>", unsafe_allow_html=True)
    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("👤 CONSULTAR MI VEHÍCULO"): 
        st.session_state.view = 'cliente'; st.rerun()
    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("🛠️ PANEL DE CONTROL (ADMIN)"): 
        st.session_state.view = 'login'; st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

elif st.session_state.view == 'login':
    st.markdown('<div class="main-card">', unsafe_allow_html=True)
    st.markdown("### 🔐 ACCESO TÉCNICO")
    u = st.text_input("Usuario")
    p = st.text_input("Contraseña", type="password")
    if st.button("INGRESAR"):
        if u == "percy" and p == "autogas2026":
            st.session_state.view = 'admin'; st.rerun()
        else: st.error("Acceso denegado")
    if st.button("⬅️ CANCELAR"): st.session_state.view = 'home'; st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

elif st.session_state.view == 'admin':
    st.markdown('<div class="main-card">', unsafe_allow_html=True)
    if st.session_state.step == 1:
        st.subheader("📝 Nuevo Registro")
        placa = st.text_input("PLACA DEL VEHÍCULO").upper().strip()
        km = st.number_input("Kilometraje Actual", min_value=0)
        paq = st.selectbox("Paquete de Servicio", ["A", "B", "C", "D", "E", "F"])
        if st.button("CONTINUAR ➡️"):
            if placa:
                st.session_state.datos = {"placa": placa, "km": km, "paq": paq}
                st.session_state.step = 2; st.rerun()
            else: st.warning("Ingrese la placa primero")
    else:
        d = st.session_state.datos
        st.subheader(f"📸 Evidencias: {d['placa']}")
        obs = st.text_area("Observaciones del Servicio")
        fotos = st.file_uploader("Subir Fotos del Trabajo", accept_multiple_files=True)
        if st.button("✅ FINALIZAR Y GUARDAR"):
            with st.spinner("Sincronizando con la nube profesional..."):
                urls = [upload_to_cloud(f.getvalue(), d['placa']) for f in fotos] if fotos else []
                # Formato Excel: Fecha, Placa, Marca, Modelo, Año, KM, Paquete, Tareas, Notas, Fotos
                db.append_row([datetime.now().strftime("%d/%m/%Y"), d['placa'], "", "", "2024", d['km'], d['paq'], "Servicio Premium", obs, ",".join(urls)])
                st.success("¡Datos guardados exitosamente!"); st.session_state.view = 'home'; st.session_state.step = 1; st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

elif st.session_state.view == 'cliente':
    st.markdown('<div class="glass-card">', unsafe_allow_html=True)
    p_c = st.text_input("INGRESE SU PLACA").upper().strip()
    if st.button("CONSULTAR HISTORIAL"):
        df = pd.DataFrame(db.get_all_records())
        df.columns = [c.lower().strip() for c in df.columns]
        hist = df[df['placa'].astype(str).str.upper() == p_c].to_dict('records')
        if hist:
            prox = int(hist[-1]['km']) + 5000
            st.markdown(f"""
                <div style="background: rgba(0, 198, 255, 0.1); padding:25px; border-radius:20px; border-left: 8px solid #00c6ff; text-align:center;">
                    <h2 style="color:#00c6ff; margin:0; font-size:1.2rem;">PRÓXIMO SERVICIO</h2>
                    <h1 style="font-size:55px; margin:10px;">{prox} KM</h1>
                    <p style="color: #aaa; margin:0;">Taller: Autogas Energy</p>
                </div>
            """, unsafe_allow_html=True)
            st.markdown("<br>### 📋 SERVICIOS REALIZADOS", unsafe_allow_html=True)
            for r in reversed(hist):
                with st.expander(f"📅 Fecha: {r['fecha']} | {r['km']} KM"):
                    st.write(f"**Servicio:** Paquete {r['paquete']}")
                    st.write(f"**Notas:** {r['notas']}")
                    if r.get('links_fotos'):
                        st.write("**Evidencia Visual:**")
                        cols = st.columns(2)
                        for i, url in enumerate(str(r['links_fotos']).split(",")):
                            if "http" in url: cols[i%2].image(url, use_container_width=True)
        else: st.warning("No se encontraron registros.")
    if st.button("⬅️ VOLVER"): st.session_state.view = 'home'; st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)
