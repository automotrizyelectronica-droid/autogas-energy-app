import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime
from fpdf import FPDF
import io
import os
import tempfile
from PIL import Image

# --- CONFIGURACIÓN DE MARCA ---
DATOS_TALLER = {
    "nombre": "AUTOGAS ENERGY",
    "direccion": "Av. Canto Grande 2916, San Juan de Lurigancho",
    "whatsapp": "927843738",
    "facebook": "MasterGas & Mecánica",
    "logo_url": "https://i.postimg.cc/mD3mzc9v/logo-autogas.png"
}

st.set_page_config(page_title=DATOS_TALLER["nombre"], layout="centered")

# --- BASE DE DATOS ---
def init_db():
    conn = sqlite3.connect('autogas_final_v13.db', check_same_thread=False)
    c = conn.cursor()
    c.execute('CREATE TABLE IF NOT EXISTS vehiculos (placa TEXT PRIMARY KEY, marca TEXT, modelo TEXT, anio TEXT)')
    c.execute('''CREATE TABLE IF NOT EXISTS historial 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, fecha TEXT, placa TEXT, 
                  km_tablero INTEGER, paquete TEXT, tareas TEXT, notas TEXT, fotos_blob BLOB)''')
    conn.commit()
    return conn

conn = init_db()

# --- CLASE PDF PROFESIONAL ---
class ReporteProfesional(FPDF):
    def header(self):
        # Cabecera azul elegante
        self.set_fill_color(0, 51, 153)
        self.rect(0, 0, 210, 40, 'F')
        
        # Logo
        try:
            # Usamos un logo temporal para el PDF
            self.image(DATOS_TALLER["logo_url"], 12, 8, 30)
        except:
            pass
            
        self.set_text_color(255, 255, 255)
        self.set_font('Arial', 'B', 18)
        self.set_xy(50, 10)
        self.cell(0, 10, DATOS_TALLER["nombre"], ln=True)
        self.set_font('Arial', '', 9)
        self.set_x(50)
        self.cell(0, 5, DATOS_TALLER["direccion"], ln=True)
        self.set_x(50)
        self.cell(0, 5, f"WhatsApp: {DATOS_TALLER['whatsapp']} | FB: {DATOS_TALLER['facebook']}", ln=True)
        self.ln(15)

    def footer(self):
        self.set_y(-15)
        self.set_font('Arial', 'I', 8)
        self.set_text_color(128)
        self.cell(0, 10, f'Informe generado por AUTOGAS ENERGY - Pagina {self.page_no()}', 0, 0, 'C')

def generar_pdf_pro(row_h, v_data):
    pdf = ReporteProfesional()
    pdf.add_page()
    pdf.set_text_color(0, 0, 0)
    
    # Título
    pdf.set_font('Arial', 'B', 14)
    pdf.set_fill_color(230, 230, 230)
    pdf.cell(0, 10, f"REPORTE TECNICO DE MANTENIMIENTO", 0, 1, 'C', True)
    pdf.ln(5)

    # Info Vehículo
    pdf.set_font('Arial', 'B', 10)
    pdf.cell(45, 8, "PLACA:", 1, 0, 'L', True); pdf.cell(50, 8, str(row_h['placa']), 1)
    pdf.cell(45, 8, "FECHA:", 1, 0, 'L', True); pdf.cell(50, 8, str(row_h['fecha']), 1, 1)
    pdf.cell(45, 8, "VEHICULO:", 1, 0, 'L', True); pdf.cell(50, 8, f"{v_data[1]} {v_data[2]}", 1)
    pdf.cell(45, 8, "KILOMETRAJE:", 1, 0, 'L', True); pdf.cell(50, 8, f"{row_h['km_tablero']} KM", 1, 1)
    pdf.ln(5)

    # Tareas
    pdf.set_font('Arial', 'B', 11)
    pdf.cell(0, 8, f"DETALLE DE TRABAJOS (PAQUETE {row_h['paquete']})", 0, 1)
    pdf.set_font('Arial', '', 10)
    for t in row_h['tareas'].split(", "):
        pdf.cell(10, 6, chr(149), 0); pdf.cell(0, 6, t, 0, 1) # chr(149) es un punto de lista

    # Notas
    if row_h['notas']:
        pdf.ln(5)
        pdf.set_font('Arial', 'B', 11)
        pdf.cell(0, 8, "OBSERVACIONES DEL TECNICO", 0, 1)
        pdf.set_font('Arial', 'I', 10)
        pdf.multi_cell(0, 6, row_h['notas'], 1)

    # FOTOS PROFESIONALES
    if row_h['fotos_blob']:
        pdf.add_page()
        pdf.set_font('Arial', 'B', 12)
        pdf.cell(0, 10, "EVIDENCIA FOTOGRAFICA DEL SERVICIO", 0, 1, 'C')
        pdf.ln(5)
        
        fotos = row_h['fotos_blob'].split(b"---SEP---")
        for f_data in fotos:
            if f_data:
                # Crear archivo temporal para que fpdf lo lea correctamente
                with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as tmp:
                    tmp.write(f_data)
                    tmp_path = tmp.name
                
                # Insertar imagen y luego borrar temporal
                pdf.image(tmp_path, x=25, w=160)
                os.remove(tmp_path)
                pdf.ln(10)

    return pdf.output(dest='S').encode('latin-1')

# --- PAQUETES --- (Tus datos exactos)
PAQUETES = {
    "A": ["Cambio de aceite", "Cambio de filtro de aire", "Cambio de filtro de aceite", "Inspeccion de fugas de gas", "Inspeccion de fugas de refrigerate y aceite", "Scanneo de motor", "siliconeo de motor"],
    "B": ["Cambio de aceite", "Cambio de filtro de aire", "Cambio de filtro de aceite", "Inspeccion de fugas de gas", "Inspeccion de fugas de refrigerate y aceite", "Cambio o inspeccion de bujias", "Scanneo de motor", "siliconeo de motor"],
    "C": ["Cambio de aceite", "Cambio de filtro de aire", "Cambio de filtro de aceite", "Cambio de filtro de gas", "Inspeccion de fugas de gas", "Inspeccion de fugas de refrigerate y aceite", "Scanneo de motor", "siliconeo de motor"],
    "D": ["Cambio de aceite", "Cambio de filtro de aire", "Cambio de filtro de aceite", "Cambio de filtro de gas", "Cambio de filtro de gasolina (externo)", "Limpieza de inyectores gasolina", "Cambio de oring y filtro de inyector", "Limpieza de obturador", "Cambio o inpeccion de bujias", "Limpieza de sensores (maf-map-cmp-ckp-vvt-o2)", "Inspeccion de fugas de gas", "Inspeccion de fugas de refrigerate y aceite", "Scanneo de motor", "siliconeo de motor"],
    "E": ["Cambio de aceite", "Cambio de filtro de aire", "Cambio de filtro de aceite", "Cambio de filtro de gas", "Limpieza de inyectores de gas", "Cambio de filtro de gasolina (externo)", "Limpieza de inyectores gasolina", "Cambio de oring y filtro de inyector", "Limpieza de obturador", "Cambio o inpeccion de bujias", "Limpieza de sensores", "Inspeccion de fugas de gas", "Inspeccion de fugas de refrigerate y aceite", "Scanneo de motor", "Regulacion / Calibracion de gas", "siliconeo de motor"],
    "F": ["Cambio de aceite", "Cambio de filtro de aire", "Cambio de filtro de aceite", "Cambio o inpeccion de bujias", "Limpieza de reductor de gas", "Inspeccion de fugas de gas", "Inspeccion de fugas de refrigerate y aceite", "Scanneo de motor", "Regulacion / Calibracion de gas", "siliconeo de motor"]
}

# --- NAVEGACIÓN ---
if 'view' not in st.session_state: st.session_state.view = 'inicio'
if 'admin_step' not in st.session_state: st.session_state.admin_step = 1

if st.session_state.view == 'inicio':
    st.image(DATOS_TALLER["logo_url"], width=200)
    st.title(DATOS_TALLER["nombre"])
    col1, col2 = st.columns(2)
    if col1.button("👤 ÁREA CLIENTE", use_container_width=True): st.session_state.view = 'cliente_placa'; st.rerun()
    if col2.button("🛠️ ADMIN", use_container_width=True): st.session_state.view = 'login'; st.rerun()

elif st.session_state.view == 'login':
    if st.button("⬅️ REGRESAR"): st.session_state.view = 'inicio'; st.rerun()
    u = st.text_input("Usuario")
    p = st.text_input("Contraseña", type="password")
    if st.button("INGRESAR"):
        if u == "percy" and p == "autogas2026": st.session_state.view = 'admin_panel'; st.session_state.admin_step = 1; st.rerun()

elif st.session_state.view == 'admin_panel':
    if st.session_state.admin_step == 1:
        placa = st.text_input("PLACA").upper()
        if placa:
            c = conn.cursor()
            c.execute("SELECT * FROM vehiculos WHERE placa=?", (placa,))
            v = c.fetchone()
            ma, mo, an = st.text_input("Marca", value=v[1] if v else ""), st.text_input("Modelo", value=v[2] if v else ""), st.text_input("Año", value=v[3] if v else "")
            km = st.number_input("Kilometraje Actual", min_value=0)
            pa = st.selectbox("Paquete", ["A", "B", "C", "D", "E", "F"])
            if st.button("SIGUIENTE ➡️"):
                st.session_state.temp = {"placa": placa, "marca": ma, "modelo": mo, "anio": an, "km": km, "paquete": pa, "nuevo": v is None}
                st.session_state.admin_step = 2; st.rerun()
    
    elif st.session_state.admin_step == 2:
        d = st.session_state.temp
        st.subheader(f"Hoja de Trabajo: {d['placa']}")
        tareas_ok = [t for t in PAQUETES[d['paquete']] if st.checkbox(t, value=True)]
        notas = st.text_area("Cuadro de Observaciones")
        fotos = st.file_uploader("Adjuntar fotos", accept_multiple_files=True, type=['jpg', 'png', 'jpeg'])
        
        if st.button("✅ GUARDAR Y FINALIZAR"):
            blobs = []
            if fotos:
                for f in fotos:
                    # Redimensionar para que no pesen tanto
                    img = Image.open(f)
                    img.thumbnail((800, 800))
                    output = io.BytesIO()
                    img.save(output, format='JPEG', quality=70)
                    blobs.append(output.getvalue())
            
            f_blob = b"---SEP---".join(blobs)
            c = conn.cursor()
            if d['nuevo']: c.execute("INSERT INTO vehiculos VALUES (?,?,?,?)", (d['placa'], d['marca'], d['modelo'], d['anio']))
            f_hoy = datetime.now().strftime("%d/%m/%Y")
            c.execute("INSERT INTO historial (fecha, placa, km_tablero, paquete, tareas, notas, fotos_blob) VALUES (?,?,?,?,?,?,?)",
                      (f_hoy, d['placa'], d['km'], d['paquete'], ", ".join(tareas_ok), notas, f_blob))
            conn.commit()
            st.session_state.view = 'inicio'; st.rerun()

elif st.session_state.view == 'cliente_menu':
    st.title(f"🚗 Placa: {st.session_state.placa_cliente}")
    # ... (Botón Próximo Mantenimiento se mantiene igual) ...
    
    if st.button("📋 MANTENIMIENTO ACTUAL", use_container_width=True):
        df = pd.read_sql_query(f"SELECT * FROM historial WHERE placa='{st.session_state.placa_cliente}' ORDER BY id DESC", conn)
        c = conn.cursor()
        c.execute("SELECT * FROM vehiculos WHERE placa=?", (st.session_state.placa_cliente,))
        v_data = c.fetchone()
        
        for _, row in df.iterrows():
            with st.expander(f"📄 Servicio: {row['fecha']} - {row['km_tablero']} KM"):
                pdf_bin = generar_pdf_pro(row, v_data)
                st.download_button(f"📥 Imprimir Reporte Profesional", data=pdf_bin, file_name=f"Reporte_{row['placa']}.pdf", key=f"btn_{row['id']}")
