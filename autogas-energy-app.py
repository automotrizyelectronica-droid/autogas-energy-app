# --- CONEXIÓN GOOGLE SHEETS (VERSIÓN ANTIFALLOS) ---
@st.cache_resource
def init_google():
    try:
        creds = Credentials.from_service_account_info(
            st.secrets["google_credentials"], 
            scopes=[
                "https://www.googleapis.com/auth/spreadsheets",
                "https://www.googleapis.com/auth/drive"
            ]
        )
        client = gspread.authorize(creds)
        
        # Intentar abrir el archivo directamente por su nombre
        # ASEGÚRATE QUE EL EXCEL SE LLAME EXACTAMENTE: DB_Autogas_Energy
        return client.open("DB_Autogas_Energy").sheet1
    except Exception as e:
        st.error(f"Error de Conexión Google: {str(e)}")
        return None

db = init_google()
