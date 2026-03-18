import streamlit as st
import pandas as pd
from datetime import datetime
import gspread
from google.oauth2.service_account import Credentials
import cloudinary
import cloudinary.uploader

# --- CONFIGURACIÓN (NO TOCAR) ---
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

# --- DEFINICIÓN DE PAQUETES ---
PAQUETES = {
    "PAQUETE A": ["Cambio de Aceite", "Filtro de Aire", "Revisión de Niveles"],
    "PAQUETE B": ["Limpieza de Inyectores", "Cambio de Bujías", "Escaneo Computarizado"],
    "PAQUETE C": ["Mantenimiento GLP/GNV", "Cambio de Filtros Gas", "Calibración"],
}

if 'view' not in st.session_state: st.session_state.view = 'home'
if 'step_admin' not in st.session_state: st.session_state.step_admin = 1

# --- VISTA: ADMINISTRADOR (FLUJO SOLICITADO) ---
if st.session_state.view == 'admin':
    st.header("🛠️ Registro de Servicio")
    
    if st.session_state.step_admin == 1:
        placa = st.text_input("INGRESE PLACA").upper().strip()
        if st.button("SIGUIENTE"):
            # Leemos datos y forzamos minúsculas para evitar el KeyError
            df = pd.DataFrame(db.get_all_records())
            df.columns = [c.lower().strip() for c in df.columns]
            
            st.session_state.form = {"placa": placa}
            match = df[df['placa'].astype(str) == placa] if 'placa' in df.columns else pd.DataFrame()
            
            if not match.empty:
                last = match.iloc[-1]
                st.session_state.form.update({"marca": last.get('marca',''), "modelo": last.get('modelo',''), "año": last.get('año','')})
                st.session_state.step_admin = 2 # Salta a Paquete/KM
            else:
                st.session_state.step_admin = 1.5 # Datos auto nuevo
            st.rerun()

    elif st.session_state.step_admin == 1.5:
        st.subheader("Datos de Vehículo Nuevo")
        st.session_state.form["marca"] = st.text_input("Marca")
        st.session_state.form["modelo"] = st.text_input("Modelo")
        st.session_state.form["año"] = st.text_input("Año")
        if st.button("REGISTRAR AUTO"): st.session_state.step_admin = 2; st.rerun()

    elif st.session_state.step_admin == 2:
        st.subheader(f"Vehículo: {st.session_state.form['placa']}")
        st.session_state.form["paquete"] = st.selectbox("Seleccione Paquete", list(PAQUETES.keys()))
        st.session_state.form["km"] = st.number_input("Kilometraje Actual", min_value=0)
        if st.button("SIGUIENTE ➡️"): st.session_state.step_admin = 3; st.rerun()

    elif st.session_state.step_admin == 3:
        paq_sel = st.session_state.form["paquete"]
        st.subheader(f"Check-list: {paq_sel}")
        for item in PAQUETES[paq_sel]: st.checkbox(item, value=True)
        st.session_state.form["obs"] = st.text_area("Cuadro de Observaciones")
        fotos = st.file_uploader("Subir Fotos", accept_multiple_files=True)
        if st.button("✅ GUARDAR REGISTRO"):
            with st.spinner("Subiendo..."):
                urls = [cloudinary.uploader.upload(f.getvalue(), folder=f"Taller_{st.session_state.form['placa']}")['secure_url'] for f in fotos] if fotos else []
                f = st.session_state.form
                db.append_row([datetime.now().strftime("%d/%m/%Y"), f['placa'], f['marca'], f['modelo'], f['año'], f['km'], f['paquete'], "Completado", f['obs'], ",".join(urls)])
                st.success("¡Guardado!"); st.session_state.view = 'home'; st.session_state.step_admin = 1; st.rerun()

# --- VISTA: CLIENTE (3 OPCIONES) ---
elif st.session_state.view == 'cliente':
    placa_c = st.text_input("INGRESE PLACA").upper().strip()
    if placa_c:
        df = pd.DataFrame(db.get_all_records())
        df.columns = [c.lower().strip() for c in df.columns]
        hist = df[df['placa'].astype(str) == placa_c].to_dict('records')
        
        if hist:
            c1, c2, c3 = st.columns(3)
            if c1.button("Mantenimiento Preventivo"): st.session_state.c_view = 'prox'
            if c2.button("Mantenimiento Actual"): st.session_state.c_view = 'actual'
            if c3.button("Historial Diagnóstico"): st.session_state.c_view = 'diag'

            mode = st.session_state.get('c_view', 'prox')
            if mode == 'prox':
                prox_km = int(hist[-1]['km']) + 5000
                st.markdown(f'<div style="background:#00c6ff; padding:50px; border-radius:20px; text-align:center;"><h2>PRÓXIMO MANTENIMIENTO</h2><h1 style="font-size:80px; color:white;">{prox_km} KM</h1></div>', unsafe_allow_html=True)
            elif mode == 'actual':
                last = hist[-1]
                st.subheader(f"Servicio: {last['fecha']} / {last['km']} KM")
                st.write(f"**Trabajo:** {last['paquete']}")
                st.write(f"**Observaciones:** {last.get('notas','')}")
                for url in str(last.get('links_fotos','')).split(","):
                    if "http" in url: st.image(url)
            elif mode == 'diag':
                for r in reversed(hist):
                    with st.expander(f"{r['fecha']} - {r['km']} KM"):
                        st.write(f"Paquete: {r['paquete']}")
                        for url in str(r.get('links_fotos','')).split(","):
                            if "http" in url: st.image(url)
