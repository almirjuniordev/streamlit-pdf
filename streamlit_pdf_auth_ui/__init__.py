from .utils import (get_db_connection, init_db, create_user_type, list_user_types, update_user_type, delete_user_type, 
                    get_user_type_by_id, register_new_usr, list_users, update_user, delete_user, 
                    check_usr_pass, check_valid_name, check_valid_email, check_unique_email, check_unique_usr, 
                    check_email_exists, check_current_passwd, generate_random_passwd, send_passwd_in_email, change_passwd)

from .widgets import __login__
from .solution import main_page
import streamlit as st

st.markdown('<style>div.block-container{padding-top:1rem;}</style>', unsafe_allow_html=True)
#st.set_option('deprecation.showfileUploaderEncoding', False)
#st.set_option('deprecation.showPyplotGlobalUse', False)
# Inicializar o banco de dados na primeira execução
init_db()
