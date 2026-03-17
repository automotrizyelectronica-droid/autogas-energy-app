import streamlit as st
import io
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload

# --- DATOS DE PRUEBA ---
ID_CARPETA = "1Vk6naUsEDgadg0GDcCrz0nY6MCXrI-1S"
# TU CORREO (Dueño de los 2TB)
TU_CORREO = "automotrizyelectronica@gmail.com" 

st.title("🧪 Prueba Técnica: Salto de Cuota 403")

def conectar_drive():
    try:
        creds = Credentials.from_service_account_info(
            st.secrets["google_credentials"], 
            scopes=["https://www.googleapis.com/auth/drive"]
        )
        return build('drive', 'v3', credentials=creds)
    except Exception as e:
        st.error(f"Error credenciales: {e}")
        return None

drive_service = conectar_drive()

archivo = st.file_uploader("Sube una foto para romper el error 403", type=['jpg', 'png', 'jpeg'])

if st.button("EJECUTAR PRUEBA DE SUBIDA"):
    if archivo and drive_service:
        try:
            with st.spinner("Subiendo y transfiriendo propiedad..."):
                # 1. Subida
                media = MediaIoBaseUpload(io.BytesIO(archivo.getvalue()), mimetype='image/jpeg')
                metadata = {'name': 'PRUEBA_FINAL.jpg', 'parents': [ID_CARPETA]}
                
                f = drive_service.files().create(
                    body=metadata,
                    media_body=media,
                    fields='id',
                    supportsAllDrives=True
                ).execute()
                
                f_id = f.get('id')

                # 2. TRASPASO DE PROPIEDAD (La clave para los 2TB)
                permiso = {
                    'type': 'user',
                    'role': 'owner',
                    'emailAddress': TU_CORREO
                }
                
                drive_service.permissions().create(
                    fileId=f_id,
                    body=permiso,
                    transferOwnership=True, # Obliga a Google a usar tus 2TB
                    supportsAllDrives=True
                ).execute()
                
                st.success(f"✅ ¡LOGRADO! Foto subida usando tus 2TB. ID: {f_id}")
                st.balloons()
                
        except Exception as e:
            st.error("❌ ERROR CRÍTICO")
            st.code(str(e))
    else:
        st.warning("Selecciona un archivo primero.")
