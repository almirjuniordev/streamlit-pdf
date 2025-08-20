import warnings
import streamlit as st
from streamlit_pdf_auth_ui.utils import init_db
from streamlit_pdf_auth_ui.widgets import __login__
from streamlit_pdf_auth_ui.solution import start_scheduler

# Configurar persistência do session_state
st.set_page_config(
    page_title="PDF Management System",
    page_icon="📄",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Suprimir avisos de uma categoria específica
#st.set_option('deprecation.showfileUploaderEncoding', False)
#st.set_option('deprecation.showPyplotGlobalUse', False)
init_db()

# Inicializa a interface de login
auth_token = "YOUR_AUTH_TOKEN"
company_name = "PDF Management System"
width = 500
height = 500

login_ui = __login__(
    auth_token=auth_token,
    company_name=company_name,
    width=width,
    height=height
)

LOGGED_IN = login_ui.build_login_ui()

start_scheduler()

# if LOGGED_IN:
#     st.title("Welcome to the PDF Dashboard")
#     st.write("You are logged in!")
