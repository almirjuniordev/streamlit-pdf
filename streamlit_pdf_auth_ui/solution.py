from datetime import datetime
import time
import os
import shutil
import threading
import schedule
import streamlit as st
import pandas as pd
import PyPDF2
import pdfplumber
try:
    import fitz  # PyMuPDF
except ImportError:
    from pymupdf import fitz  # PyMuPDF
from PIL import Image
import io

def process_pdf(file_path):
    """Processa um arquivo PDF e extrai informações básicas"""
    try:
        # Abrir o PDF com PyMuPDF para informações gerais
        doc = fitz.open(file_path)
        
        # Informações básicas
        num_pages = len(doc)
        metadata = doc.metadata
        
        # Extrair texto das primeiras páginas (limitado para performance)
        text_content = ""
        for page_num in range(min(3, num_pages)):  # Primeiras 3 páginas
            page = doc.load_page(page_num)
            text_content += page.get_text()
        
        doc.close()
        
        return {
            'num_pages': num_pages,
            'metadata': metadata,
            'text_preview': text_content[:500] + "..." if len(text_content) > 500 else text_content
        }
    except Exception as e:
        return {
            'error': str(e),
            'num_pages': 0,
            'metadata': {},
            'text_preview': ""
        }

def extract_text_from_pdf(file_path):
    """Extrai texto completo do PDF"""
    try:
        text = ""
        with pdfplumber.open(file_path) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"
        return text
    except Exception as e:
        return f"Erro ao extrair texto: {str(e)}"

def extract_images_from_pdf(file_path):
    """Extrai imagens do PDF"""
    try:
        images = []
        doc = fitz.open(file_path)
        
        for page_num in range(len(doc)):
            page = doc.load_page(page_num)
            image_list = page.get_images()
            
            for img_index, img in enumerate(image_list):
                xref = img[0]
                base_image = doc.extract_image(xref)
                image_bytes = base_image["image"]
                
                # Converter para PIL Image
                image = Image.open(io.BytesIO(image_bytes))
                images.append({
                    'page': page_num + 1,
                    'image': image,
                    'index': img_index
                })
        
        doc.close()
        return images
    except Exception as e:
        return []

def main_page():
    """Página principal para upload e processamento de PDFs com AI"""
    # Importar e executar a função do AI PDF
    from .ai_pdf import run_ai_pdf
    run_ai_pdf()

# Função para limpar a pasta uploaded_pdfs
def clean_uploaded_files():
    folder = 'uploaded_pdfs'
    if os.path.exists(folder):
        for filename in os.listdir(folder):
            file_path = os.path.join(folder, filename)
            try:
                if os.path.isfile(file_path) or os.path.islink(file_path):
                    os.unlink(file_path)
                elif os.path.isdir(file_path):
                    shutil.rmtree(file_path)
            except Exception as e:
                print(f'Failed to delete {file_path}. Reason: {e}')

# Configurar a tarefa agendada para limpar os arquivos diariamente à meia-noite
def schedule_daily_clean():
    schedule.every().day.at("00:00").do(clean_uploaded_files)

    while True:
        schedule.run_pending()
        time.sleep(1)

# Iniciar o agendamento em um thread separado
def start_scheduler():
    scheduler_thread = threading.Thread(target=schedule_daily_clean)
    scheduler_thread.daemon = True
    scheduler_thread.start()
