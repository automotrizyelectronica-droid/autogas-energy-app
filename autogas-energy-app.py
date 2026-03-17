import streamlit as st
import pandas as pd
from datetime import datetime
from fpdf import FPDF
import io
import gspread
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload
import streamlit.components.v1 as components

# --- CONFIGURACIÓN DE IDENTIDAD ---
DATOS_TALLER = {
    "nombre": "AUTOGAS ENERGY",
    "direccion": "Av. Canto Grande 2916, San Juan de Lurigancho",
    "whatsapp": "927843738",
    "logo_url": "https://i.postimg.cc/mD3mzc9v/logo-autogas.png"
}
ID_CARPETA_FOTOS = "1Vk6naUsEDgadg0GDcCrz0nY6MCXrI-1S"
# El dueño de los 2TB
MI_CORREO_PERSONAL = "automotrizyelectronica@gmail.com" 

st.set_page_config(page_title=DATOS_TALLER["nombre"], layout="centered")
components.html("<script>window.onbeforeunload = function() { return '¿Salir?'; };</script>", height=0)

# --- CONEXIÓN CON GOOGLE ---
def conectar_servicios():
    creds = Credentials.from_service_account_info(
        st.secrets["google_credentials"], 
        scopes=["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
    )
    return gspread.authorize(creds), build('drive', 'v3', credentials=creds)

client, drive_service = conectar_servicios()
db_sheet = client.open("DB_Autogas_Energy").sheet1

def subir_y_transferir_foto(file_bytes, nombre):
    try:
        # 1. Preparar la subida
        media = MediaIoBaseUpload(io.BytesIO(file_bytes), mimetype='image/jpeg')
        metadata = {'name': nombre, 'parents': [ID_CARPETA_FOTOS]}
        
        # 2. Crear el archivo en Drive
        archivo = drive_service.files().create(
            body=metadata, 
            media_body=media, 
            fields='id', 
            supportsAllDrives=True
        ).execute()
        
        id_archivo = archivo.get('id')
        
        # 3. TRANSFERENCIA DE PROPIEDAD (Aquí se soluciona el Error 403)
        permiso = {
            'type': 'user',
            'role': 'owner',
            'emailAddress': MI_CORREO_PERSONAL
        }
        
        drive_service.permissions().create(
            fileId=id_archivo,
            body=permiso,
            transferOwnership=True,
            supportsAllDrives=True
        ).execute()
        
        return id_archivo
    except Exception as e:
        # Si falla, devolvemos el error abreviado para el Excel
        return f"Error_Subida: {str(e)[:20]}"

# --- GENERACIÓN DE PDF ---
def generar_pdf_reporte(reg):
    pdf = FPDF(); pdf.add_page()
    # Encabezado azul
    pdf.set_fill_color(0, 51, 153); pdf.rect(0, 0, 210, 40, 'F')
    pdf.set_text_color(255, 255, 255); pdf.set_font('Arial', 'B', 16)
    pdf.set_xy(10, 10); pdf.cell(0, 10, DATOS_TALLER["nombre"], ln=True)
    pdf.set_font('Arial', '', 10); pdf.cell(0, 5, DATOS_TALLER["direccion"], ln=True)
    
    pdf.ln(20); pdf.set_text_color(0, 0, 0); pdf.set_font('Arial', 'B', 12)
    pdf.cell(0, 10, "REPORTE TÉCNICO DE MANTENIMIENTO", 1, 1, 'C')
    
    pdf.set_font('Arial', '', 10)
    pdf.cell(95, 8, f"PLACA: {reg.get('placa', '---')}", 1)
    pdf.cell(95, 8, f"FECHA: {reg.get('fecha', '---')}", 1, 1)
    pdf.cell(95, 8, f"KM: {reg.get('km', '---')}", 1)
    pdf.cell(95, 8, f"PAQUETE: {reg.get('paquete', '---')}", 1, 1)
    
    pdf.ln(5); pdf.set_font('Arial', 'B', 10); pdf.cell(0, 8, "TRABAJOS REALIZADOS:", 0, 1)
    pdf.set_font('Arial', '', 10)
    pdf.multi_cell(0, 6, str(reg.get('tareas', 'No especificado')), 1)
    
    return pdf.output(dest='S').encode('latin-1')

# --- LÓGICA DE INTERFAZ Y NAVEGACIÓN ---
if 'view' not in st.session_state: st.session_state.view = 'inicio'
if 'admin_step' not in st.session_state: st.session_state.admin_step = 1

PAQUETES = {
    "A": ["Cambio aceite", "Filtro aire", "Filtro aceite", "Fugas gas", "Scan motor", "Siliconeo"],
    "B": ["Paquete A", "Bujías"],
    "C": ["Paquete A", "Filtro Gas"],
    "D": ["Limpieza Inyectores", "Obturador", "Sensores", "Filtros", "Fugas", "Scan"],
    "E": ["Full Inyectores Gas/Gaso", "Regulación", "Sensores", "Filtros", "Scan motor"],
    "F": ["Reductor Gas", "Calibración", "Bujías", "Fugas", "Scan motor"]
}

if st.session_state.view == 'inicio':
    st.image(DATOS_TALLER["logo_url"], width=200); st.title(DATOS_TALLER["nombre"])
    if st.button("👤 ÁREA CLIENTE (CONSULTAR)", use_container_width=True): st.session_state.view = 'cliente'; st.rerun()
    if st.button("🛠️ ADMINISTRACIÓN TALLER", use_container_width=True): st.session_state.view = 'login'; st.rerun()

elif st.session_state.view == 'login':
    st.subheader("Acceso Administrativo")
    user = st.text_input("Usuario"); clave = st.text_input("Contraseña", type="password")
    if st.button("Entrar"):
        if user == "percy" and clave == "autogas2026": st.session_state.view = 'admin'; st.rerun()
        else: st.error("Credenciales incorrectas")

elif st.session_state.view == 'admin':
    if st.session_state.admin_step == 1:
        st.subheader("Paso 1: Datos del Vehículo")
        placa = st.text_input("PLACA").upper().strip()
        km = st.number_input("Kilometraje Actual", min_value=0)
        paq = st.selectbox("Seleccione Paquete", list(PAQUETES.keys()))
        if st.button("SIGUIENTE ➡️"):
            st.session_state.temp_data = {"placa": placa, "km": km, "paq": paq}
            st.session_state.admin_step = 2; st.rerun()
    else:
        st.subheader(f"Paso 2: Detalle de Servicio - {st.session_state.temp_data['placa']}")
        d = st.session_state.temp_data
        tareas_sel = [t for t in PAQUETES[d['paq']] if st.checkbox(t, value=True)]
        obs = st.text_area("Observaciones Adicionales")
        archivos = st.file_uploader("Subir Evidencias (Fotos)", accept_multiple_files=True)
        
        if st.button("✅ FINALIZAR Y GUARDAR"):
            with st.spinner("Subiendo fotos y guardando registro..."):
                ids_fotos = []
                if archivos:
                    for i, f in enumerate(archivos):
                        nombre_img = f"{d['placa']}_{datetime.now().strftime('%H%M%S')}_{i}.jpg"
                        res_id = subir_y_transferir_foto(f.getvalue(), nombre_img)
                        ids_fotos.append(res_id)
                
                # Guardar en Google Sheets
                fila = [
                    datetime.now().strftime("%d/%m/%Y"), 
                    d['placa'], "", "", "2024", d['km'], 
                    d['paq'], ", ".join(tareas_sel), obs, ",".join(ids_fotos)
                ]
                db_sheet.append_row(fila)
                st.success("¡Registro completado con éxito!")
                st.session_state.view = 'inicio'; st.session_state.admin_step = 1; st.rerun()

elif st.session_state.view == 'cliente':
    st.subheader("Consulta de Mantenimiento")
    p_cliente = st.text_input("INGRESE SU NÚMERO DE PLACA").upper().strip()
    if st.button("BUSCAR"):
        df = pd.DataFrame(db_sheet.get_all_records())
        df.columns = [c.lower().strip() for c in df.columns]
        registros = df[df['placa'].astype(str).str.upper() == p_cliente].to_dict('records')
        
        if registros:
            # Cuadro verde de próximo servicio
            prox_km = int(registros[-1]['km']) + 5000
            st.markdown(f"""
                <div style='background-color:#d4edda; padding:30px; border-radius:15px; text-align:center; border:2px solid #155724;'>
                    <h2 style='color:#155724;'>¡Estimado Cliente!</h2>
                    <p style='font-size:1.2em;'>Su próximo mantenimiento preventivo en <b>AUTOGAS ENERGY</b> le toca a los:</p>
                    <h1 style='color:#155724; font-size:4.5em;'>{prox_km} KM</h1>
                </div>
            """, unsafe_allow_html=True)
            
            st.write("### Historial de Servicios")
            for r in reversed(registros):
                with st.expander(f"Fecha: {r['fecha']} - {r['km']} KM"):
                    st.download_button(
                        "Descargar Informe PDF", 
                        generar_pdf_reporte(r), 
                        f"Reporte_{r['placa']}_{r['fecha']}.pdf", 
                        key=f"btn_{r['km']}_{r['fecha']}"
                    )
        else:
            st.warning("No se encontraron registros para esta placa.")
    if st.button("⬅️ Volver"): st.session_state.view = 'inicio'; st.rerun()
