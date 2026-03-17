import streamlit as st
import io
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload

# --- CONFIGURACIÓN MÍNIMA ---
# ID de tu carpeta "Fotos_Autogas"
ID_CARPETA = "1Vk6naUsEDgadg0GDcCrz0nY6MCXrI-1S"

st.title("🧪 Prueba de Subida Directa")

def conectar_drive():
    try:
        creds = Credentials.from_service_account_info(
            st.secrets["google_credentials"], 
            scopes=["https://www.googleapis.com/auth/drive"]
        )
        return build('drive', 'v3', credentials=creds)
    except Exception as e:
        st.error(f"Error de credenciales: {e}")
        return None

drive_service = conectar_drive()

# --- INTERFAZ DE PRUEBA ---
archivo = st.file_uploader("Selecciona una foto pequeña para probar", type=['jpg', 'png', 'jpeg'])

if st.button("SUBIR AHORA"):
    if archivo is not None and drive_service is not None:
        try:
            with st.spinner("Subiendo..."):
                media = MediaIoBaseUpload(io.BytesIO(archivo.getvalue()), mimetype='image/jpeg')
                metadata = {
                    'name': 'PRUEBA_RAPIDA.jpg',
                    'parents': [ID_CARPETA]
                }
                
                # Intentamos la subida más básica posible
                f = drive_service.files().create(
                    body=metadata,
                    media_body=media,
                    fields='id',
                    supportsAllDrives=True
                ).execute()
                
                st.success(f"✅ ¡FUNCIONÓ! ID del archivo: {f.get('id')}")
                st.balloons()
                
        except Exception as e:
            st.error("❌ FALLÓ LA SUBIDA")
            st.code(str(e)) # Aquí veremos el error completo sin recortes
    else:
        st.warning("Primero selecciona un archivo.")
