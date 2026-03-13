import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime
from fpdf import FPDF
import io
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
    conn = sqlite3.connect('autogas_pro_final.db', check_same_thread=False)
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
        # Fondo decorativo en la cabecera
        self.set_fill_color(0, 71, 171) # Azul oscuro
        self.rect(0, 0, 210, 40, 'F')
        
        # Logo (Si falla la URL, pone texto)
        try:
            self.image(DATOS_TALLER["logo_url"], 10, 5, 30)
        except:
            pass
            
        self.set_text_color(255, 255, 255)
        self.set_font('Arial', 'B', 18)
        self.cell(40)
        self.cell(0, 10, DATOS_TALLER["nombre"], ln=True, align='L')
        
        self.set_font('Arial', '', 9)
        self.cell(40)
        self.cell(0, 5, DATOS_TALLER["direccion"], ln=True, align='L')
        self.cell(40)
        self.cell(0, 5, f"WhatsApp: {DATOS_TALLER['whatsapp']} | Facebook: {DATOS_TALLER['facebook']}", ln=True, align='L')
        self.ln(15)

    def footer(self):
        self.set_y(-15)
        self.set_font('Arial', 'I', 8)
        self.set_text_color(150)
        self.cell(0, 10, f'AUTOGAS ENERGY - Especialistas en Sistemas de Gas - Página {self.page_no()}', 0, 0, 'C')

def generar_pdf_pro(datos_h, datos_v, fotos_lista):
    pdf = ReporteProfesional()
    pdf.add_page()
    pdf.set_text_color(0, 0, 0)
    
    # TÍTULO PRINCIPAL
    pdf.set_font('Arial', 'B', 14)
    pdf.set_fill_color(240, 240, 240)
    pdf.cell(0, 10, f"INFORME TÉCNICO: MANTENIMIENTO PREVENTIVO", 0, 1, 'C', True)
    pdf.ln(5)

    # BLOQUE: INFORMACIÓN DEL VEHÍCULO (Estilo Launch)
    pdf.set_font('Arial', 'B', 11)
    pdf.cell(0, 8, "1. INFORMACION DEL VEHICULO", 0, 1)
    pdf.set_font('Arial', '', 10)
    
    col_width = 47
    pdf.cell(col_width, 8, "Placa:", 1, 0, 'L', True)
    pdf.cell(col_width, 8, str(datos_h['placa']), 1)
    pdf.cell(col_width, 8, "Fecha:", 1, 0, 'L', True)
    pdf.cell(col_width, 8, str(datos_h['fecha']), 1, 1)
    
    pdf.cell(col_width, 8, "Marca/Modelo:", 1, 0, 'L', True)
    pdf.cell(col_width, 8, f"{datos_v[1]} {datos_v[2]}", 1)
    pdf.cell(col_width, 8, "Kilometraje:", 1, 0, 'L', True)
    pdf.cell(col_width, 8, f"{datos_h['km_tablero']} KM", 1, 1)
    pdf.ln(5)

    # BLOQUE: TAREAS (CHECKLIST)
    pdf.set_font('Arial', 'B', 11)
    pdf.cell(0, 8, f"2. TRABAJOS REALIZADOS (PAQUETE {datos_h['paquete']})", 0, 1)
    pdf.set_font('Arial', '', 9)
    
    tareas = datos_h['tareas'].split(", ")
    for t in tareas:
        pdf.cell(10, 6, " [X] ", 0)
        pdf.cell(0, 6, t, 0, 1)
    
    # BLOQUE: OBSERVACIONES
    if datos_h['notas']:
        pdf.ln(5)
        pdf.set_font('Arial', 'B', 11)
        pdf.cell(0, 8, "3. OBSERVACIONES Y RECOMENDACIONES", 0, 1)
        pdf.set_font('Arial', 'I', 10)
        pdf.multi_cell(0, 6, datos_h['notas'], 1)

    # BLOQUE: FOTOS (EVIDENCIA)
    if fotos_lista:
        pdf.add_page()
        pdf.set_font('Arial', 'B', 11)
        pdf.cell(0, 10, "4. EVIDENCIA FOTOGRAFICA", 0, 1)
        
        # Colocamos las fotos de 2 en 2
        y_start = pdf.get_y()
        x_pos = [10, 110]
        idx = 0
        for foto in fotos_lista:
            img = Image.open(foto)
            img_byte_arr = io.BytesIO()
            img.save(img_byte_arr, format='JPEG')
            
            curr_x = x_pos[idx % 2]
            if idx > 0 and idx % 2 == 0:
                pdf.ln(60)
            
            pdf.image(img_byte_arr, curr_x, pdf.get_y(), 90)
            idx += 1

    return pdf.output(dest='S').encode('latin-1')

# --- LOS 6 PAQUETES ---
PAQUETES = {
    "A": ["Cambio de aceite", "Cambio de filtro de aire", "Cambio de filtro de aceite", "Inspeccion de fugas de gas", "Inspeccion de fugas de refrigerate y aceite", "Scanneo de motor", "siliconeo de motor"],
    "B": ["Cambio de aceite", "Cambio de filtro de aire", "Cambio de filtro de aceite", "Inspeccion de fugas de gas", "Inspeccion de fugas de refrigerate y aceite", "Cambio o inspeccion de bujias", "Scanneo de motor", "siliconeo de motor"],
    "C": ["Cambio de aceite", "Cambio de filtro de aire", "Cambio de filtro de aceite", "Cambio de filtro de gas", "Inspeccion de fugas de gas", "Inspeccion de fugas de refrigerate y aceite", "Scanneo de motor", "siliconeo de motor"],
    "D": ["C. Aceite/Aire/Aceite", "Filtro de gas", "Filtro gasolina externo", "Inyectores gasolina", "Orings y filtros", "Obturador", "Bujias", "Sensores (maf-map-etc)", "Fugas", "Scanner", "Siliconeo"],
    "E": ["C. Aceite/Aire/Aceite", "Filtro gas", "Inyectores gas", "Filtro gasolina", "Inyectores gasolina", "Obturador", "Bujias", "Sensores", "Fugas", "Scanner", "Regulacion gas", "Siliconeo"],
    "F": ["C. Aceite/Aire/Aceite", "Bujias", "Limpieza reductor gas", "Fugas", "Scanner", "Regulacion gas", "Siliconeo"]
}

# --- INTERFAZ ---
if 'view' not in st.session_state: st.session_state.view = 'inicio'
if 'admin_step' not in st.session_state: st.session_state.admin_step = 1

if st.session_state.view == 'inicio':
    st.image(DATOS_TALLER["logo_url"], width=200)
    st.title(DATOS_TALLER["nombre"])
    col1, col2 = st.columns(2)
    if col1.button("👤 CLIENTE", use_container_width=True): st.session_state.view = 'cliente_placa'; st.rerun()
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
            ma = st.text_input("Marca", value=v[1] if v else "")
            mo = st.text_input("Modelo", value=v[2] if v else "")
            an = st.text_input("Año", value=v[3] if v else "")
            km = st.number_input("Kilometraje", min_value=0)
            pa = st.selectbox("Paquete", ["A", "B", "C", "D", "E", "F"])
            if st.button("INGRESAR"):
                st.session_state.temp = {"placa": placa, "marca": ma, "modelo": mo, "anio": an, "km": km, "paquete": pa, "nuevo": v is None}
                st.session_state.admin_step = 2; st.rerun()
    
    elif st.session_state.admin_step == 2:
        d = st.session_state.temp
        st.subheader(f"Hoja de Trabajo: {d['placa']}")
        tareas_ok = [t for t in PAQUETES[d['paquete']] if st.checkbox(t, value=True)]
        notas = st.text_area("Observaciones")
        fotos_subidas = st.file_uploader("Subir fotos", accept_multiple_files=True, type=['png', 'jpg', 'jpeg'])
        
        if st.button("✅ GUARDAR Y FINALIZAR"):
            c = conn.cursor()
            if d['nuevo']: c.execute("INSERT INTO vehiculos VALUES (?,?,?,?)", (d['placa'], d['marca'], d['modelo'], d['anio']))
            f_hoy = datetime.now().strftime("%d/%m/%Y")
            c.execute("INSERT INTO historial (fecha, placa, km_tablero, paquete, tareas, notas) VALUES (?,?,?,?,?,?)",
                      (f_hoy, d['placa'], d['km'], d['paquete'], ", ".join(tareas_ok), notas))
            conn.commit()
            st.session_state.view = 'inicio'; st.rerun()

elif st.session_state.view == 'cliente_menu':
    st.title(f"🚗 Placa: {st.session_state.placa_cliente}")
    # ... (Botón de próximo mantenimiento se mantiene igual) ...
    
    if st.button("📋 MANTENIMIENTO ACTUAL", use_container_width=True):
        df = pd.read_sql_query(f"SELECT * FROM historial WHERE placa='{st.session_state.placa_cliente}' ORDER BY id DESC", conn)
        c = conn.cursor()
        c.execute("SELECT * FROM vehiculos WHERE placa=?", (st.session_state.placa_cliente,))
        v_data = c.fetchone()
        
        for _, row in df.iterrows():
            with st.expander(f"📄 KM: {row['km_tablero']} - Fecha: {row['fecha']}"):
                # Aquí se genera el PDF Profesional al momento de descargar
                # Nota: Las fotos se pasan aquí si se guardaron en la sesión
                pdf_bin = generar_pdf_pro(row, v_data, []) 
                st.download_button("📥 Imprimir Informe PDF Profesional", data=pdf_bin, file_name=f"Informe_{row['placa']}.pdf")
