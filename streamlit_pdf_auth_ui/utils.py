import re
import psycopg2
import secrets
import uuid
from argon2 import PasswordHasher
import requests
import yaml
import os
import streamlit as st

def get_db_connection(with_database=True):
    connection_params = {
        'host': os.getenv('POSTGRES_HOST', 'postgres'),
        'user': os.getenv('POSTGRES_USER', 'postgres'),
        'password': os.getenv('POSTGRES_PASSWORD', 'postgres'),
        'port': 5432
    }
    if with_database:
        connection_params['database'] = os.getenv('POSTGRES_DB', 'auth_db')
    return psycopg2.connect(**connection_params)

def init_db():
    # Conecta ao banco de dados específico (PostgreSQL cria o banco automaticamente)
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        # Criação das tabelas
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_types (
                id VARCHAR(36) PRIMARY KEY,
                type_name VARCHAR(255) UNIQUE NOT NULL
            );
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id VARCHAR(36) PRIMARY KEY,
                username VARCHAR(255) UNIQUE NOT NULL,
                email VARCHAR(255) UNIQUE NOT NULL,
                password TEXT NOT NULL,
                user_type_id VARCHAR(36),
                FOREIGN KEY (user_type_id) REFERENCES user_types(id)
            );
        ''')
        conn.commit()

        # Carrega os dados dos usuários do arquivo YAML
        with open('users_config.yml', 'r') as file:
            config = yaml.safe_load(file)
            users = config['users']

        # Insere os tipos de usuário no banco de dados
        user_types = set(user_info['type'] for user_info in users.values())
        type_id_map = {}
        for user_type in user_types:
            type_id = str(uuid.uuid4())
            type_id_map[user_type] = type_id
            try:
                cursor.execute(
                    'INSERT INTO user_types (id, type_name) VALUES (%s, %s)',
                    (type_id, user_type)
                )
                conn.commit()
            except psycopg2.IntegrityError:
                cursor.execute(
                    'SELECT id FROM user_types WHERE type_name = %s',
                    (user_type,)
                )
                existing_type = cursor.fetchone()
                type_id_map[user_type] = existing_type[0]
                conn.rollback()  # Rola para trás a transação em caso de erro

        # Insere os usuários no banco de dados
        for user_info in users.values():
            try:
                hashed_password = PasswordHasher().hash(user_info['password'])
                cursor.execute(
                    'INSERT INTO users (id, username, email, password, user_type_id) VALUES (%s, %s, %s, %s, %s)',
                    (str(uuid.uuid4()), user_info['username'], user_info['email'], hashed_password, type_id_map[user_info['type']])
                )
                conn.commit()
            except psycopg2.IntegrityError:
                print(f"Usuário {user_info['username']} já existe.")
                conn.rollback()  # Rola para trás a transação em caso de erro

    except psycopg2.Error as err:
        print(f"Error: {err}")
        conn.rollback()
    finally:
        cursor.close()
        conn.close()

# Funções CRUD para user_types
def create_user_type(type_name: str):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute('INSERT INTO user_types (id, type_name) VALUES (%s, %s)', (str(uuid.uuid4()), type_name))
        conn.commit()
    except psycopg2.IntegrityError:
        print(f"User type {type_name} already exists.")
        conn.rollback()
    finally:
        cursor.close()
        conn.close()

def list_user_types():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM user_types')
    user_types = cursor.fetchall()
    cursor.close()
    conn.close()
    # Converter para formato de dicionário
    return [{'id': row[0], 'type_name': row[1]} for row in user_types]

def update_user_type(type_id: str, new_type_name: str):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute('UPDATE user_types SET type_name = %s WHERE id = %s', (new_type_name, type_id))
        conn.commit()
    except psycopg2.Error as err:
        print(f"Error: {err}")
        conn.rollback()
    finally:
        cursor.close()
        conn.close()

def delete_user_type(type_id: str):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute('DELETE FROM user_types WHERE id = %s', (type_id,))
        conn.commit()
    except psycopg2.Error as err:
        print(f"Error: {err}")
        conn.rollback()
    finally:
        cursor.close()
        conn.close()

def get_user_type_by_id(type_id: str):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM user_types WHERE id = %s', (type_id,))
    user_type = cursor.fetchone()
    cursor.close()
    conn.close()
    if user_type:
        return {'id': user_type[0], 'type_name': user_type[1]}
    return None

# Funções CRUD para usuários
def register_new_usr(email_sign_up: str, username_sign_up: str, password_sign_up: str, user_type_id: str):
    conn = get_db_connection()
    cursor = conn.cursor()
    new_user_id = str(uuid.uuid4())
    ph = PasswordHasher()
    hashed_password = ph.hash(password_sign_up)
    try:
        cursor.execute('INSERT INTO users (id, username, email, password, user_type_id) VALUES (%s, %s, %s, %s, %s)',
                       (new_user_id, username_sign_up, email_sign_up, hashed_password, user_type_id))
        conn.commit()
    except psycopg2.IntegrityError:
        print(f"Usuário {username_sign_up} já existe.")
        conn.rollback()
    finally:
        cursor.close()
        conn.close()

def list_users():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM users')
    users = cursor.fetchall()
    cursor.close()
    conn.close()
    # Converter para formato de dicionário
    return [{'id': row[0], 'username': row[1], 'email': row[2], 'password': row[3], 'user_type_id': row[4]} for row in users]

def update_user(user_id: str, new_username: str, new_email: str, new_user_type: str):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute('UPDATE users SET username = %s, email = %s, user_type_id = %s WHERE id = %s', (new_username, new_email, new_user_type, user_id))
        conn.commit()
    except psycopg2.Error as err:
        print(f"Error: {err}")
        conn.rollback()
    finally:
        cursor.close()
        conn.close()

def delete_user(user_id: str):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute('DELETE FROM users WHERE id = %s', (user_id,))
        conn.commit()
    except psycopg2.Error as err:
        print(f"Error: {err}")
        conn.rollback()
    finally:
        cursor.close()
        conn.close()

# Funções auxiliares
@st.cache_data(ttl=None, show_spinner=True)
def check_usr_pass(username: str, password: str):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT u.password, ut.type_name 
        FROM users u
        JOIN user_types ut ON u.user_type_id = ut.id
        WHERE u.username = %s
    ''', (username,))
    user = cursor.fetchone()
    cursor.close()
    conn.close()
    if user:
        ph = PasswordHasher()
        try:
            if ph.verify(user[0], password):  # user[0] é o password
                return True, user[1]  # user[1] é o type_name
        except:
            pass
    return False, None

def check_valid_name(name_sign_up: str) -> bool:
    return bool(re.search(r'^[A-Za-z_][A-Za-z0-9_]*', name_sign_up))

def check_valid_email(email_sign_up: str) -> bool:
    regex = re.compile(r'([A-Za-z0-9]+[.-_])*[A-Za-z0-9]+@[A-Za-z0-9-]+(\.[A-Z|a-z]{2,})+')
    return bool(re.fullmatch(regex, email_sign_up))

@st.cache_data(ttl=None, show_spinner=True)
def check_unique_email(email_sign_up: str) -> bool:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT id FROM users WHERE email = %s', (email_sign_up,))
    user = cursor.fetchone()
    cursor.close()
    conn.close()
    return user is None

@st.cache_data(ttl=None, show_spinner=True)
def check_unique_usr(username_sign_up: str) -> bool:
    if not non_empty_str_check(username_sign_up):
        return False

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT id FROM users WHERE username = %s', (username_sign_up,))
    user = cursor.fetchone()
    cursor.close()
    conn.close()
    return user is None

@st.cache_data(ttl=None, show_spinner=True)
def check_email_exists(email_forgot_passwd: str):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT username FROM users WHERE email = %s', (email_forgot_passwd,))
    user = cursor.fetchone()
    cursor.close()
    conn.close()
    if user:
        return True, user[0]  # user[0] é o username
    return False, None

def check_current_passwd(email_reset_passwd: str, current_passwd: str) -> bool:
    conn = get_db_connection()
    ph = PasswordHasher()
    cursor = conn.cursor()
    cursor.execute('SELECT password FROM users WHERE email = %s', (email_reset_passwd,))
    user = cursor.fetchone()
    cursor.close()
    conn.close()
    if user:
        try:
            return ph.verify(user[0], current_passwd)  # user[0] é o password
        except:
            pass
    return False

def non_empty_str_check(username_sign_up: str) -> bool:
    return bool(username_sign_up and not username_sign_up.isspace())

@st.cache_data(ttl=None, show_spinner=True)
def generate_random_passwd() -> str:
    password_length = 10
    return secrets.token_urlsafe(password_length)

def send_passwd_in_email(auth_token: str, username_forgot_passwd: str, email_forgot_passwd: str, company_name: str, random_password: str) -> None:
    client = Courier(auth_token=auth_token)
    resp = client.send_message(
        message={
            "to": {
                "email": email_forgot_passwd
            },
            "content": {
                "title": f"{company_name}: Login Password!",
                "body": f"Hello {username_forgot_passwd},\n\nYour new temporary password is: {random_password}\n\nPlease reset your password as soon as possible for security reasons."
            },
            "data": {
                "info": "Please reset your password as soon as possible for security reasons."
            }
        }
    )

def change_passwd(email_: str, random_password: str) -> None:
    conn = get_db_connection()
    ph = PasswordHasher()
    hashed_password = ph.hash(random_password)
    cursor = conn.cursor()
    try:
        cursor.execute('UPDATE users SET password = %s WHERE email = %s', (hashed_password, email_))
        conn.commit()
    except psycopg2.Error as err:
        print(f"Error: {err}")
        conn.rollback()
    finally:
        cursor.close()
        conn.close()
