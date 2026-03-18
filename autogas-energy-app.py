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

# --- 2. CONTENIDO DE PAQUETES (Checklist) ---
PAQUETES = {
    "PAQUETE A": ["Cambio de Aceite", "Filtro de Aceite", "Limpieza de Filtro de Aire", "Revisión de Niveles", "Escaneo de Motor"],
    "PAQUETE B": ["Limpieza de Inyectores", "Cambio de Bujías", "Limpieza de Obturador", "Escaneo Completo", "Revisión de Bobinas"],
    "PAQUETE C": ["Mantenimiento Preventivo Gas", "Cambio de Filtro Fase Líquida", "Cambio de Filtro Fase Gaseosa", "Regulación de Mezcla", "Revisión de Estanqueidad"],
    "PAQUETE D": ["Mantenimiento General GNV/GLP", "Limpieza de Riel de Inyectores", "Escaneo Computarizado", "Verificación de Parámetros", "Limpieza de Sensores"],
    "PAQUETE E": ["Afinamiento Electrónico", "Mantenimiento de Frenos", "Limpieza de Sensores ABS", "Revisión de Tren Delantero", "Check de Seguridad"],
    "PAQUETE F": ["Servicio Correctivo Especializado", "Diagnóstico de Fallas", "Prueba de Sensores de Oxígeno", "Verificación de Compresión"]
}

# --- 3. DISEÑO VISUAL ---
st.set_page_config(page_title="AUTOGAS ENERGY", layout="centered")
st.markdown("""
    <style>
    .stApp { background-color: #0b0e11; color: #f0f0f0; }
    .main-card { background: rgba(255, 255, 255, 0.05); border-radius: 20px; padding: 25px; border: 1px solid rgba(255, 255, 255, 0.1); margin-bottom: 20px; }
    .stButton>button { width: 100%; border-radius: 12px; height: 3.5em; background: linear-gradient(90deg, #00c6ff 0%, #0072ff 100%) !important; color: white !important; font-weight: bold; border: none; }
    .prox-box { background: linear-gradient(135deg, #00c6ff 0%, #0072ff 100%); padding: 40px; border-radius: 25px; text-align: center; color: white; box-shadow: 0 10px 30px rgba(0,198,255,0.3); }
    h1, h2, h3 { color: #00c6ff !important; text-align: center; font-weight: 800; }
    .check-item { background: rgba(0, 198, 255, 0.1); padding: 8px 15px; border-radius: 8px; margin: 5px 0; border-left: 4px solid #00c6ff; }
    </style>
""", unsafe_allow_html=True)

# --- 4. LÓGICA DE ESTADO ---
if 'view' not in st.session_state: st.session_state.view = 'home'
if 'step_admin' not in st.session_state: st.session_state.step_admin = 1
if 'c_tab' not in st.session_state: st.session_state.c_tab = 'none'

def get_data():
    df = pd.DataFrame(db.get_all_records())
    df.columns = [c.lower().strip() for c in df.columns]
    return df

# --- 5. VISTA: HOME ---
if st.session_state.view == 'home':
    st.image("https://i.postimg.cc/mD3mzc9v/logo-autogas.png", width=230)
    st.markdown('<div class="main-card"><h1>CENTRO DE SERVICIOS</h1>', unsafe_allow_html=True)
    if st.button("👤 MODO CLIENTE"): st.session_state.view = 'cliente'; st.rerun()
    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("🛠️ MODO ADMINISTRADOR"): st.session_state.view = 'login'; st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

# --- 6. VISTA: LOGIN ---
elif st.session_state.view == 'login':
    st.markdown('<div class="main-card"><h3>ACCESO AUTORIZADO</h3>', unsafe_allow_html=True)
    u = st.text_input("Usuario")
    p = st.text_input("Clave", type="password")
    if st.button("ENTRAR"):
        if u == "percy" and p == "autogas2026": 
            st.session_state.view = 'admin'; st.rerun()
    if st.button("VOLVER"): st.session_state.view = 'home'; st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

# --- 7. VISTA: ADMINISTRADOR ---
elif st.session_state.view == 'admin':
    st.markdown(f'<div class="main-card"><h2>REGISTRO TÉCNICO - PASO {st.session_state.step_admin}</h2>', unsafe_allow_html=True)
    
    if st.session_state.step_admin == 1:
        placa = st.text_input("PLACA DEL VEHÍCULO").upper().strip()
        if st.button("CONTINUAR ➡️"):
            df = get_data()
            st.session_state.form = {"placa": placa}
            match = df[df['placa'].astype(str) == placa] if 'placa' in df.columns else pd.DataFrame()
            if not match.empty:
                last = match.iloc[-1]
                st.session_state.form.update({"marca": last.get('marca',''), "modelo": last.get('modelo',''), "año": last.get('año','')})
                st.session_state.step_admin = 2
            else: st.session_state.step_admin = 1.5
            st.rerun()

    elif st.session_state.step_admin == 1.5:
        st.write("Vehículo no registrado. Complete los datos:")
        st.session_state.form["marca"] = st.text_input("Marca")
        st.session_state.form["modelo"] = st.text_input("Modelo")
        st.session_state.form["año"] = st.text_input("Año")
        if st.button("REGISTRAR Y SEGUIR"): st.session_state.step_admin = 2; st.rerun()

    elif st.session_state.step_admin == 2:
        st.write(f"**Auto:** {st.session_state.form['placa']} | {st.session_state.form['marca']}")
        st.session_state.form["paquete"] = st.selectbox("Seleccione el Paquete Realizado", list(PAQUETES.keys()))
        st.session_state.form["km"] = st.number_input("Kilometraje Actual", min_value=0)
        if st.button("IR A DETALLES Y FOTOS ➡️"): st.session_state.step_admin = 3; st.rerun()

    elif st.session_state.step_admin == 3:
        paq_sel = st.session_state.form["paquete"]
        st.subheader(f"📋 Checklist: {paq_sel}")
        for item in PAQUETES[paq_sel]:
            st.checkbox(item, value=True, key=f"check_{item}")
        
        st.write("---")
        st.session_state.form["obs"] = st.text_area("Cuadro de Observaciones del Técnico")
        fotos = st.file_uploader("Evidencia Fotográfica (Cámara/Galería)", accept_multiple_files=True)
        
        if st.button("✅ FINALIZAR Y GUARDAR TODO"):
            with st.spinner("Subiendo datos y fotos..."):
                urls = [cloudinary.uploader.upload(f.getvalue(), folder=f"Autogas_{st.session_state.form['placa']}")['secure_url'] for f in fotos] if fotos else []
                f = st.session_state.form
                db.append_row([datetime.now().strftime("%d/%m/%Y"), f['placa'], f['marca'], f['modelo'], f['año'], f['km'], f['paquete'], "Completado", f['obs'], ",".join(urls)])
                st.success("¡Servicio Guardado con Éxito!"); st.session_state.view = 'home'; st.session_state.step_admin = 1; st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

# --- 8. VISTA: CLIENTE ---
elif st.session_state.view == 'cliente':
    st.markdown('<div class="main-card">', unsafe_allow_html=True)
    placa_c = st.text_input("INGRESE SU PLACA PARA CONSULTAR").upper().strip()
    
    if placa_c:
        df = get_data()
        hist = df[df['placa'].astype(str) == placa_c].to_dict('records')
        
        if hist:
            st.write("---")
            c1, c2, c3 = st.columns(3)
            if c1.button("PRÓXIMO\nMANTENIMIENTO"): st.session_state.c_tab = 'prox'
            if c2.button("MANTENIMIENTO\nACTUAL"): st.session_state.c_tab = 'actual'
            if c3.button("HISTORIAL DE\nDIAGNÓSTICOS"): st.session_state.c_tab = 'hist'
            
            # --- OPCIÓN 1: PREVENTIVO ---
            if st.session_state.c_tab == 'prox':
                prox_km = int(hist[-1]['km']) + 5000
                st.markdown(f"""
                    <div class="prox-box">
                        <h2 style="color:white !important;">PRÓXIMO MANTENIMIENTO</h2>
                        <p style="font-size:18px;">Su próximo mantenimiento en el taller <b>AUTOGAS ENERGY</b> es a los:</p>
                        <h1 style="color:white !important; font-size:80px;">{prox_km} KM</h1>
                    </div>
                """, unsafe_allow_html=True)
            
            # --- OPCIÓN 2: MANTENIMIENTO ACTUAL / DETALLE ---
            elif st.session_state.c_tab in ['actual', 'hist']:
                if st.session_state.c_tab == 'actual':
                    st.subheader("Mantenimiento Reciente")
                    servicios = [hist[-1]]
                else:
                    st.subheader("Historial de Diagnósticos")
                    servicios = reversed(hist)

                for r in servicios:
                    with st.expander(f"📅 {r['fecha']} | 📍 {r['km']} KM"):
                        st.markdown(f"### Trabajo Realizado: **{r['paquete']}**")
                        st.write("**Servicios incluidos:**")
                        for item in PAQUETES.get(r['paquete'], ["Servicio General"]):
                            st.markdown(f'<div class="check-item">✅ {item}</div>', unsafe_allow_html=True)
                        
                        st.markdown("---")
                        st.write(f"**Observaciones:** {r.get('notas', r.get('observaciones', 'Sin observaciones'))}")
                        
                        links = str(r.get('links_fotos','')).split(",")
                        if links and links[0] != "":
                            st.write("**Evidencia Visual:**")
                            for url in links:
                                if "http" in url: st.image(url, use_container_width=True)
                        
                        st.download_button("📥 Descargar Reporte de Servicio", data=str(r), file_name=f"Servicio_{r['placa']}_{r['fecha']}.txt")
        else: st.warning("No se encontró historial para esta placa.")

    if st.button("⬅️ VOLVER AL INICIO"): st.session_state.view = 'home'; st.session_state.c_tab = 'none'; st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)
