import json
import os
import pandas as pd
import streamlit as st
import yaml
from yaml.loader import SafeLoader
from .solution import main_page
from streamlit_option_menu import option_menu
from datetime import datetime, timedelta
from st_keyup import st_keyup
from .utils import (check_usr_pass, check_valid_name, check_valid_email, 
                    check_unique_email, check_unique_usr, delete_user, 
                    list_users, register_new_usr, check_email_exists, 
                    generate_random_passwd, send_passwd_in_email, 
                    change_passwd, create_user_type, 
                    list_user_types, update_user, update_user_type, 
                    delete_user_type)
import extra_streamlit_components as stx
from PIL import Image
import base64

class __login__:
    def __init__(self, auth_token: str, company_name: str, width, height, logout_button_name: str = 'Logout', hide_menu_bool: bool = False, hide_footer_bool: bool = False, lottie_url: str = "https://assets8.lottiefiles.com/packages/lf20_ktwnwv5m.json"):
        self.auth_token = auth_token
        self.company_name = company_name
        self.width = width
        self.height = height
        self.logout_button_name = logout_button_name
        self.hide_menu_bool = hide_menu_bool
        self.hide_footer_bool = hide_footer_bool

        # Initialize cookies
        self.cookie_manager = stx.CookieManager()

    def set_cookie(self, key, value, days_expire=30):
        expire_date = datetime.utcnow() + timedelta(days=days_expire)
        self.cookie_manager.set(key, value, expires_at=expire_date)

    def get_cookie(self, key):
        cookies = self.cookie_manager.get_all()
        return cookies.get(key)

    def delete_cookie(self, key):
        self.cookie_manager.delete(key)

    def get_image_base64(self, image_path):
        with open(image_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode()

    def admin_create_user_widget(self):
        user_types = list_user_types()
        user_type_names = [ut['type_name'] for ut in user_types]
        
        with st.form("Create User Form"):
            username = st.text_input("New User Username")
            email = st.text_input("New User Email")
            password = st.text_input("New User Password", type='password')
            selected_user_type = st.selectbox("User Type", user_type_names)
            create_user_button = st.form_submit_button("Create User")

            if create_user_button:
                if check_valid_email(email) and check_unique_email(email) and check_valid_name(username) and check_unique_usr(username):
                    user_type_id = next((ut['id'] for ut in user_types if ut['type_name'] == selected_user_type), None)
                    register_new_usr(email, username, password, user_type_id)
                    st.success(f"User {username} created successfully as {selected_user_type}.")
                else:
                    st.error("Failed to create user. Please check the input fields.")

    def admin_user_type_crud(self):
        st.header("User Type Management")
        options = ["Create", "Read", "Update", "Delete"]
        choice = st.selectbox("Action", options)

        if choice == "Create":
            with st.form("Create User Type"):
                type_name = st.text_input("User Type Name")
                create_button = st.form_submit_button("Create")
                if create_button:
                    create_user_type(type_name)
                    st.success(f"User type '{type_name}' created successfully.")

        elif choice == "Read":
            user_types = list_user_types()
            if user_types:
                # Converte a lista de dicionários para um DataFrame
                df_user_types = pd.DataFrame(user_types)
                df_user_types.reset_index(drop=True, inplace=True)  # Remove o índice numérico

                # Campo de busca
                search_query = st_keyup("Search by type name", key="search_user_type")

                if search_query:
                    df_user_types = df_user_types[df_user_types['type_name'].str.contains(search_query, case=False, na=False)]

                st.table(df_user_types)
            else:
                st.write("No user types found.")

        elif choice == "Update":
            user_types = list_user_types()
            user_type_mapping = {ut['type_name']: ut['id'] for ut in user_types}
            selected_user_type = st.selectbox("Select User Type", list(user_type_mapping.keys()))
            new_type_name = st.text_input("New User Type Name")
            update_button = st.button("Update")
            if update_button:
                user_type_id = user_type_mapping[selected_user_type]
                update_user_type(user_type_id, new_type_name)
                st.success(f"User type updated to '{new_type_name}'.")

        elif choice == "Delete":
            user_types = list_user_types()
            user_type_mapping = {ut['type_name']: ut['id'] for ut in user_types}
            selected_user_type = st.selectbox("Select User Type", list(user_type_mapping.keys()))
            delete_button = st.button("Delete")
            if delete_button:
                user_type_id = user_type_mapping[selected_user_type]
                delete_user_type(user_type_id)
                st.success("User type deleted successfully.")

    def admin_user_crud(self):
        st.header("User Management")
        options = ["Create", "Read", "Update", "Delete"]
        choice = st.selectbox("Action", options)

        if choice == "Create":
            self.admin_create_user_widget()

        elif choice == "Read":
            users = list_users()
            if users:
                user_types = list_user_types()
                type_id_to_name = {ut['id']: ut['type_name'] for ut in user_types}
                
                # Remova o campo password e substitua user_type_id por type_name
                for user in users:
                    user['type_name'] = type_id_to_name.get(user.pop('user_type_id'), 'Unknown')
                    user.pop('password', None)
                
                # Converte a lista de dicionários para um DataFrame
                df_users = pd.DataFrame(users)
                df_users.reset_index(drop=True, inplace=True)  # Remove o índice numérico

                # Campo de busca
                search_query = st_keyup("Search by username", key="search_user")

                if search_query:
                    df_users = df_users[df_users['username'].str.contains(search_query, case=False, na=False)]

                st.table(df_users)
            else:
                st.write("No users found.")

        elif choice == "Update":
            users = list_users()
            user_mapping = {u['username']: u['id'] for u in users}
            selected_username = st.selectbox("Select User", list(user_mapping.keys()))
            new_username = st.text_input("New Username")
            new_email = st.text_input("New Email")
            user_types = list_user_types()
            new_user_type = st.selectbox("New User Type", [ut['type_name'] for ut in user_types])
            update_button = st.button("Update")
            if update_button:
                user_id = user_mapping[selected_username]
                user_type_id = next((ut['id'] for ut in user_types if ut['type_name'] == new_user_type), None)
                update_user(user_id, new_username, new_email, user_type_id)
                st.success("User updated successfully.")

        elif choice == "Delete":
            users = list_users()
            user_mapping = {u['username']: u['id'] for u in users}
            selected_username = st.selectbox("Select User", list(user_mapping.keys()))
            delete_button = st.button("Delete")
            if delete_button:
                user_id = user_mapping[selected_username]
                delete_user(user_id)
                st.success("User deleted successfully.")

    def login_widget(self) -> None:
        # Mostrar a imagem apenas se o usuário não estiver logado
        if not st.session_state.get('LOGGED_IN', False):
            # Centralizar a imagem no topo da página com CSS embutido
            st.markdown(
                f"""
                <style>
                
                .centered-image {{
                    display: block;
                    margin-left: auto;
                    margin-right: auto;
                    width: 35%;  /* Ajuste a largura conforme necessário */
                }}
                
                </style>
                <div style="text-align: center; margin: 20px 0;">
                    <h1>📄 PDF Management System</h1>
                    <p>Sistema de Gerenciamento e Processamento de PDFs</p>
                </div>
                """,
                unsafe_allow_html=True
            )

        config_path = os.path.join(os.path.dirname(__file__), '../config.yml')
        # Configuração do Streamlit Authenticator
        with open(config_path) as file:
            config = yaml.load(file, Loader=SafeLoader)

        if not st.session_state.get('LOGGED_IN', False):
            del_login = st.empty()
            with del_login.form("Login Form"):
                username = st.text_input("Username", placeholder='Your unique username')
                password = st.text_input("Password", placeholder='Your password', type='password')
                login_submit_button = st.form_submit_button(label='Login')

                if login_submit_button:
                    authenticated, user_type = check_usr_pass(username, password)
                    if not authenticated:
                        st.error("Invalid Username or Password!")
                    else:
                        st.session_state['LOGGED_IN'] = True
                        st.session_state['USER_TYPE'] = user_type
                        st.session_state['USERNAME'] = username
                        st.session_state['SELECTED_MENU'] = 'PDF Upload'  # Definindo menu padrão
                        expiration_date = (datetime.utcnow() + timedelta(days=30)).strftime("%Y-%m-%dT%H:%M:%S GMT")

                        # Cria o dicionário de dados da sessão
                        session_data = {
                            'user_id': username,
                            'expires': expiration_date
                        }

                        # Salva na sessão persistente
                        st.session_state['persistent_session'] = session_data

                        # Serializa o dicionário para uma string JSON (para cookie)
                        cookie_data_json = json.dumps(session_data)

                        # Define o cookie também
                        self.set_cookie('__streamlit_login_signup_ui_username__', cookie_data_json, days_expire=30)
                        st.rerun()

        if st.session_state.get('LOGGED_IN', False):
            # Exibe informações do usuário logado
            username = st.session_state.get('USERNAME', 'Unknown')
            user_type = st.session_state.get('USER_TYPE', 'Unknown')
            
            with st.sidebar:
                st.markdown(f"**👤 Usuário:** {username}")
                st.markdown(f"**🔑 Tipo:** {user_type}")
                st.markdown("---")
            
            self.nav_sidebar()  # Adicionando chamada ao método nav_sidebar para garantir que o menu de navegação seja renderizado
            if st.session_state.get('USER_TYPE') == 'admin':
                self.render_admin_interface()
            else:
                self.render_basic_interface()

    def render_admin_interface(self):
        st.write("Admin Interface")
        selected_option = st.session_state.get('SELECTED_MENU')
        if selected_option == 'User Management':
            self.admin_user_crud()
        elif selected_option == 'User Type Management':
            self.admin_user_type_crud()
        elif selected_option == 'PDF Upload':
            main_page()

    def render_basic_interface(self):
        # Ocultar menu do Streamlit para usuários não-admin
        self.hide_menu_for_non_admin()
        
        selected_option = st.session_state.get('SELECTED_MENU')
        if selected_option == 'PDF Upload':
            main_page()



    def admin_nav_sidebar(self):
        main_page_sidebar = st.sidebar.empty()
        with main_page_sidebar:
            selected_option = option_menu(
                menu_title='Admin Navigation',
                menu_icon='gear',
                options=['PDF Upload', 'User Management', 'User Type Management'],
                icons=['file-earmark-pdf', 'person-plus', 'list'],
                default_index=0,
                orientation="vertical",
                styles={
                    "container": {"padding": "5px"},
                    "nav-link": {"font-size": "14px", "text-align": "left", "margin": "0px"}
                })
        st.session_state['SELECTED_MENU'] = selected_option
        return main_page_sidebar, selected_option

    def nav_sidebar(self):
        if st.session_state.get('USER_TYPE') == 'admin':
            self.admin_nav_sidebar()
        else:
            with st.sidebar:
                selected_option = option_menu(
                    menu_title='Menu',
                    options=['PDF Upload'],
                    icons=['upload'],
                    default_index=0,
                    orientation="vertical",
                    styles={
                        "container": {"padding": "5px"},
                        "nav-link": {"font-size": "14px", "text-align": "left", "margin": "0px"}
                    }
                )
                st.session_state['SELECTED_MENU'] = selected_option

    def sign_up_widget(self) -> None:
        with st.form("Sign Up Form"):
            name_sign_up = st.text_input("Name *", placeholder="Type your name")
            email_sign_up = st.text_input("Email *", placeholder="Type your email")
            user_name_sign_up = st.text_input("Username *", placeholder="Type your username")
            password_sign_up = st.text_input("Password *", placeholder="Type your password", type="password")
            confirm_password_sign_up = st.text_input("Confirm Password *", placeholder="Confirm your password", type="password")

            submit_sign_up = st.form_submit_button(label='Create Account')

            if submit_sign_up:
                user_types = list_user_types()
                user_type_id = next((ut['id'] for ut in user_types if ut['type_name'] == 'basic'), None)
                if not check_valid_email(email_sign_up):
                    st.error("Email address is invalid.")
                elif not check_unique_email(email_sign_up):
                    st.error("Email address already exists. Please use a different email address.")
                elif not check_valid_name(user_name_sign_up):
                    st.error("Username is invalid. Please try again with a different username.")
                elif not check_unique_usr(user_name_sign_up):
                    st.error("Username already exists. Please try again with a different username.")
                elif password_sign_up != confirm_password_sign_up:
                    st.error("Passwords do not match. Please try again.")
                else:
                    register_new_usr(email_sign_up, user_name_sign_up, password_sign_up, user_type_id)
                    st.success("You have successfully created an account. Please login to use the application.")

    def forgot_password_widget(self):
        with st.form("Forgot Password Form"):
            email_forgot_passwd = st.text_input("Email", placeholder="Type your email")
            submit_forgot_passwd = st.form_submit_button(label='Reset Password')

            if submit_forgot_passwd:
                email_exists, username = check_email_exists(email_forgot_passwd)
                if email_exists:
                    passwd = generate_random_passwd()
                    change_passwd(email_forgot_passwd, passwd)
                    send_passwd_in_email(self.auth_token, username, email_forgot_passwd, self.company_name, passwd)
                    st.success("Your password has been reset. Please check your email for the new password.")
                else:
                    st.error("Email address does not exist. Please try again with a different email address.")

    def logout_widget(self) -> None:
        if st.session_state['LOGGED_IN']:
            st.sidebar.button(self.logout_button_name, key="logout", on_click=self.logout)
    
    def logout(self):
        st.session_state['LOGGED_IN'] = False
        st.session_state['USER_TYPE'] = None
        st.session_state['USERNAME'] = None
        st.session_state['SELECTED_MENU'] = None
        
        # Remove a sessão persistente
        if 'persistent_session' in st.session_state:
            del st.session_state['persistent_session']
        
        # Remove o cookie
        self.delete_cookie('__streamlit_login_signup_ui_username__')
        st.rerun()

    def hide_menu(self) -> None:
        st.markdown(""" <style>
        #MainMenu {visibility: hidden;}
        </style> """, unsafe_allow_html=True)

    def hide_menu_for_non_admin(self) -> None:
        """Oculta o menu principal do Streamlit para usuários não-admin"""
        if st.session_state.get('USER_TYPE') != 'admin':
            st.markdown(""" <style>
            /* Ocultar menu principal do Streamlit */
            #MainMenu {visibility: hidden !important;}
            
            /* Ocultar header com menu de três pontos */
            header {visibility: hidden !important;}
            
            /* Ocultar footer */
            footer {visibility: hidden !important;}
            
            /* Ocultar botão de menu hambúrguer */
            .css-1d391kg {display: none !important;}
            
            /* Ocultar menu de deploy e configurações */
            .css-1d391kg, .css-1d391kg * {display: none !important;}
            </style> """, unsafe_allow_html=True)

    def hide_footer(self) -> None:
        st.markdown(""" <style>
        footer {visibility: hidden;}
        </style> """, unsafe_allow_html=True)

    def check_cookie_session(self):
        """Verifica se existe uma sessão válida nos cookies"""
        try:
            cookie_data = self.get_cookie('__streamlit_login_signup_ui_username__')
            if cookie_data:
                # Verifica se cookie_data já é um dicionário
                if isinstance(cookie_data, dict):
                    cookie_info = cookie_data
                else:
                    cookie_info = json.loads(cookie_data)
                
                expiration_date = datetime.strptime(cookie_info['expires'], "%Y-%m-%dT%H:%M:%S GMT")
                
                # Verifica se o cookie não expirou
                if expiration_date > datetime.utcnow():
                    return True, cookie_info['user_id']
                else:
                    # Cookie expirado, remove
                    self.delete_cookie('__streamlit_login_signup_ui_username__')
        except (json.JSONDecodeError, KeyError, ValueError) as e:
            # Cookie inválido, remove
            self.delete_cookie('__streamlit_login_signup_ui_username__')
        
        return False, None

    def check_persistent_session(self):
        """Verifica se existe uma sessão persistente no session_state"""
        try:
            if 'persistent_session' in st.session_state:
                session_data = st.session_state['persistent_session']
                expiration_date = datetime.strptime(session_data['expires'], "%Y-%m-%dT%H:%M:%S GMT")
                
                # Verifica se a sessão não expirou
                if expiration_date > datetime.utcnow():
                    return True, session_data['user_id']
                else:
                    # Sessão expirada, remove
                    del st.session_state['persistent_session']
        except (KeyError, ValueError) as e:
            # Sessão inválida, remove
            if 'persistent_session' in st.session_state:
                del st.session_state['persistent_session']
        
        return False, None

    def build_login_ui(self):
        if 'LOGGED_IN' not in st.session_state:
            st.session_state['LOGGED_IN'] = False
        if 'LOGOUT_BUTTON_HIT' not in st.session_state:
            st.session_state['LOGOUT_BUTTON_HIT'] = False

        # Verifica se há uma sessão válida nos cookies ou session_state
        if not st.session_state['LOGGED_IN']:
            # Primeiro tenta verificar a sessão persistente
            session_valid, username = self.check_persistent_session()
            if not session_valid:
                # Se não há sessão persistente, tenta verificar cookies
                session_valid, username = self.check_cookie_session()
            
            if session_valid and username:
                # Recupera informações do usuário do banco
                authenticated, user_type = check_usr_pass(username, "")
                if authenticated:
                    st.session_state['LOGGED_IN'] = True
                    st.session_state['USER_TYPE'] = user_type
                    st.session_state['USERNAME'] = username
                    st.session_state['SELECTED_MENU'] = 'PDF Upload'

        self.login_widget()
        self.logout_widget()

        if st.session_state['LOGGED_IN']:
            st.sidebar.empty()

        if self.hide_menu_bool:
            self.hide_menu()

        if self.hide_footer_bool:
            self.hide_footer()

        return st.session_state['LOGGED_IN']
