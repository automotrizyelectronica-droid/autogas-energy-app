import streamlit as st
import pandas as pd
from datetime import datetime
import cloudinary
import cloudinary.uploader
from supabase import create_client, Client

# --- 1. CONFIGURACIÓN DE CREDENCIALES ---
# Configura tus secretos en Streamlit Cloud (st.secrets) o ponlos aquí temporalmente
SUPABASE_URL = "https://cemyzwxswjgkeeoaayfm.supabase.co"
SUPABASE_KEY = "sb_publishable_XO9ULfAj6gIQg-AWRL0zqg_oIZQm36V"

# Inicializar cliente de Supabase
@st.cache_resource
def init_supabase() -> Client:
    return create_client(SUPABASE_URL, SUPABASE_KEY)

supabase = init_supabase()

# Configurar Cloudinary (asegúrate de tener esto configurado con tus datos)
cloudinary.config(
  cloud_name = st.secrets.get("CLOUDINARY_CLOUD_NAME", "tu_cloud_name"),
  api_key = st.secrets.get("CLOUDINARY_API_KEY", "tu_api_key"),
  api_secret = st.secrets.get("CLOUDINARY_API_SECRET", "tu_api_secret")
)

# --- 2. FUNCIONES DE BASE DE DATOS (PRO) ---
def get_data():
    try:
        response = supabase.table("servicios").select("*").execute()
        return pd.DataFrame(response.data) if response.data else pd.DataFrame(columns=['placa', 'marca', 'modelo', 'anio', 'km', 'paquete', 'estado', 'observaciones'])
    except Exception as e:
        st.error(f"Error al leer la base de datos: {e}")
        return pd.DataFrame()

# --- 3. DICCIONARIO DE PAQUETES ---
PAQUETES = {
    "Mantenimiento Preventivo GLP/GNV": ["Cambio de filtros", "Calibración de riel", "Inspección de mangueras", "Diagnóstico por scanner"],
    "Mantenimiento Mayor": ["Cambio de filtros", "Revisión de tanque", "Prueba de hermeticidad", "Mantenimiento de inyectores", "Escaneo completo"]
}

# --- 4. VISTA: ADMINISTRADOR (FLUJO PRO) ---
if 'view' not in st.session_state:
    st.session_state.view = 'admin'
if 'step_admin' not in st.session_state:
    st.session_state.step_admin = 1
if 'form' not in st.session_state:
    st.session_state.form = {}

st.markdown(f'<div class="main-card"><h2>REGISTRO TÉCNICO - PASO {st.session_state.step_admin}</h2>', unsafe_allow_html=True)

if st.session_state.step_admin == 1:
    placa = st.text_input("PLACA DEL VEHÍCULO").upper().strip()
    if st.button("CONTINUAR ➡️"):
        df = get_data()
        st.session_state.form = {"placa": placa}
        
        # Verificar si la placa ya existe
        if not df.empty and 'placa' in df.columns:
            match = df[df['placa'].astype(str) == placa]
        else:
            match = pd.DataFrame()
            
        if not match.empty:
            last = match.iloc[-1]
            st.session_state.form.update({
                "marca": last.get('marca',''), 
                "modelo": last.get('modelo',''), 
                "anio": last.get('anio','')
            })
            st.session_state.step_admin = 2
        else: 
            st.session_state.step_admin = 1.5
        st.rerun()

elif st.session_state.step_admin == 1.5:
    st.write("Vehículo no registrado. Complete los datos:")
    st.session_state.form["marca"] = st.text_input("Marca")
    st.session_state.form["modelo"] = st.text_input("Modelo")
    st.session_state.form["anio"] = st.text_input("Año")
    if st.button("REGISTRAR Y SEGUIR"): 
        st.session_state.step_admin = 2
        st.rerun()

elif st.session_state.step_admin == 2:
    st.write(f"**Auto:** {st.session_state.form['placa']} | {st.session_state.form['marca']}")
    st.session_state.form["paquete"] = st.selectbox("Seleccione el Paquete Realizado", list(PAQUETES.keys()))
    st.session_state.form["km"] = st.number_input("Kilometraje Actual", min_value=0, step=100)
    if st.button("IR A DETALLES Y FOTOS ➡️"): 
        st.session_state.step_admin = 3
        st.rerun()

elif st.session_state.step_admin == 3:
    paq_sel = st.session_state.form["paquete"]
    st.subheader(f"📋 Checklist: {paq_sel}")
    
    for item in PAQUETES[paq_sel]:
        st.checkbox(item, value=True, key=f"check_{item}")
        
    st.write("---")
    st.session_state.form["obs"] = st.text_area("Cuadro de Observaciones del Técnico")
    fotos = st.file_uploader("Subir fotos (Seleccionar de galería)", type=["jpg", "png", "jpeg"], accept_multiple_files=True)
    
    if st.button("✅ FINALIZAR Y GUARDAR"):
        with st.spinner("Guardando en la base de datos profesional..."):
            try:
                f = st.session_state.form
                
                # 1. Insertar el servicio principal en Supabase
                service_data = {
                    "placa": f['placa'],
                    "marca": f.get('marca', ''),
                    "modelo": f.get('modelo', ''),
                    "anio": str(f.get('anio', '')),
                    "km": int(f.get('km', 0)),
                    "paquete": f['paquete'],
                    "estado": "Completado",
                    "observaciones": f.get('obs', '')
                }
                
                res_service = supabase.table("servicios").insert(service_data).execute()
                
                if res_service.data:
                    # Obtener el ID del servicio recién creado
                    servicio_id = res_service.data[0]['id']
                    
                    # 2. Subir fotos a Cloudinary y registrar los links en la tabla 'fotos' de Supabase
                    if fotos:
                        for foto in fotos:
                            upload_res = cloudinary.uploader.upload(foto, folder=f"Autogas_{f['placa']}")
                            secure_url = upload_res['secure_url']
                            
                            # Guardar la relación en la base de datos
                            supabase.table("fotos").insert({
                                "servicio_id": servicio_id,
                                "url_foto": secure_url
                            }).execute()
                    
                    st.success("¡Servicio y evidencias guardadas con éxito en Supabase!")
                    st.session_state.step_admin = 1
                    st.session_state.form = {}
                    st.rerun()
                else:
                    st.error("No se pudo registrar el servicio en la base de datos.")
                    
            except Exception as e:
                st.error(f"Error técnico al guardar: {e}")
                
st.markdown('</div>', unsafe_allow_html=True)
