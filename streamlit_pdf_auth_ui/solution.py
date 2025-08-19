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
    """Página principal para upload e processamento de PDFs"""
    st.markdown("""
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css" rel="stylesheet" integrity="sha384-QWTKZyjpPEjISv5WaRU9OFeRpok6YctnYmDr5pNlyT2bRjXh0JMhjY6hW+ALEwIH" crossorigin="anonymous">
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.3/font/bootstrap-icons.min.css">
    """, unsafe_allow_html=True)

    st.markdown("""
    <style>
        .block-container {
            max-width: 80rem;
        }
        .upload-area {
            border: 2px dashed #ccc;
            border-radius: 10px;
            padding: 20px;
            text-align: center;
            margin: 10px 0;
        }
        .upload-area:hover {
            border-color: #007bff;
        }
    </style>
    """, unsafe_allow_html=True)

    st.title('📄 Sistema de Gerenciamento de PDFs')
    st.subheader("Upload, Processamento e Análise de Documentos PDF")

    # Criar diretório para arquivos
    save_directory = 'uploaded_pdfs'
    os.makedirs(save_directory, exist_ok=True)

    # Container principal
    container = st.container(border=True)
    
    with container:
        st.markdown("### 📤 Upload de PDF")
        
        # Upload de arquivo
        uploaded_file = st.file_uploader(
            "Selecione um arquivo PDF para processar",
            type=['pdf'],
            help="Arquivos suportados: PDF"
        )

        if uploaded_file is not None:
            # Gerar nome único para o arquivo
            timestamp = datetime.now().strftime('%Y%m%d%H%M%S%f')
            file_name = f'pdf_{timestamp}.pdf'
            file_path = os.path.join(save_directory, file_name)

            # Salvar arquivo
            with open(file_path, 'wb') as f:
                f.write(uploaded_file.getbuffer())

            # Informações do arquivo
            file_size = len(uploaded_file.getbuffer()) / 1024  # KB
            st.success(f"✅ Arquivo carregado com sucesso!")
            st.info(f"📁 Nome: {uploaded_file.name}")
            st.info(f"📏 Tamanho: {file_size:.2f} KB")

            # Processar PDF
            with st.spinner("Processando PDF..."):
                pdf_info = process_pdf(file_path)

            if 'error' not in pdf_info:
                # Exibir informações do PDF
                st.markdown("### 📊 Informações do PDF")
                
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.metric("📄 Páginas", pdf_info['num_pages'])
                
                with col2:
                    st.metric("📏 Tamanho", f"{file_size:.2f} KB")
                
                with col3:
                    st.metric("📅 Criado", pdf_info['metadata'].get('creationDate', 'N/A'))

                # Abas para diferentes funcionalidades
                tab1, tab2, tab3, tab4 = st.tabs(["📋 Metadados", "📝 Texto", "🖼️ Imagens", "💾 Download"])

                with tab1:
                    st.markdown("#### Metadados do PDF")
                    if pdf_info['metadata']:
                        metadata_df = pd.DataFrame(list(pdf_info['metadata'].items()), columns=['Campo', 'Valor'])
                        st.dataframe(metadata_df, use_container_width=True)
                    else:
                        st.info("Nenhum metadado encontrado no PDF.")

                with tab2:
                    st.markdown("#### Extração de Texto")
                    
                    if st.button("🔍 Extrair Texto Completo"):
                        with st.spinner("Extraindo texto..."):
                            full_text = extract_text_from_pdf(file_path)
                            
                        if full_text and not full_text.startswith("Erro"):
                            st.text_area("Texto Extraído", full_text, height=400)
                            
                            # Botão para download do texto
                            text_bytes = full_text.encode('utf-8')
                            st.download_button(
                                label="💾 Download Texto (.txt)",
                                data=text_bytes,
                                file_name=f"{uploaded_file.name.replace('.pdf', '')}_texto.txt",
                                mime="text/plain"
                            )
                        else:
                            st.error("Não foi possível extrair texto do PDF.")
                    
                    # Preview do texto
                    st.markdown("#### Preview do Texto")
                    st.text_area("Primeiras 500 caracteres", pdf_info['text_preview'], height=200, disabled=True)

                with tab3:
                    st.markdown("#### Extração de Imagens")
                    
                    if st.button("🖼️ Extrair Imagens"):
                        with st.spinner("Extraindo imagens..."):
                            images = extract_images_from_pdf(file_path)
                        
                        if images:
                            st.success(f"✅ {len(images)} imagem(s) encontrada(s)")
                            
                            for i, img_data in enumerate(images):
                                with st.expander(f"Imagem {i+1} - Página {img_data['page']}"):
                                    st.image(img_data['image'], caption=f"Página {img_data['page']}")
                                    
                                    # Converter imagem para bytes para download
                                    img_byte_arr = io.BytesIO()
                                    img_data['image'].save(img_byte_arr, format='PNG')
                                    img_byte_arr = img_byte_arr.getvalue()
                                    
                                    st.download_button(
                                        label=f"💾 Download Imagem {i+1}",
                                        data=img_byte_arr,
                                        file_name=f"{uploaded_file.name.replace('.pdf', '')}_img_{i+1}.png",
                                        mime="image/png"
                                    )
                        else:
                            st.info("Nenhuma imagem encontrada no PDF.")

                with tab4:
                    st.markdown("#### Download do Arquivo Original")
                    
                    # Ler arquivo para download
                    with open(file_path, 'rb') as f:
                        file_bytes = f.read()
                    
                    st.download_button(
                        label="💾 Download PDF Original",
                        data=file_bytes,
                        file_name=uploaded_file.name,
                        mime="application/pdf"
                    )

            else:
                st.error(f"❌ Erro ao processar PDF: {pdf_info['error']}")

            # Limpar arquivo após processamento
            try:
                if os.path.exists(file_path):
                    os.remove(file_path)
            except Exception as e:
                st.warning(f"⚠️ Não foi possível limpar o arquivo temporário: {e}")

        else:
            st.info("📤 Faça upload de um arquivo PDF para começar.")

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
