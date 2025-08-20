import streamlit as st
from pdf2image import convert_from_bytes
import pytesseract
from PIL import Image
import io
import re
import os
import time

# Configuração do Tesseract para Docker (Linux)
# pytesseract.pytesseract.tesseract_cmd = r"C:/Program Files/Tesseract-OCR/tesseract.exe"  # Windows
# No Docker, o Tesseract está instalado no PATH do sistema

def run_ai_pdf():
    """Função principal do AI PDF Scanner"""
    # CONFIGURAÇÃO
    st.set_page_config(page_title="AI BOT Scanner", layout="wide")
    col1, col2 = st.columns([10, 2])
    with col1:
        st.title("📄 AI para PDFs Escaneados")
    with col2:
        # st.image("logo.png", width=280)  # Comentado pois não temos logo no Docker
        pass

    # Obter nome do usuário logado
    username = st.session_state.get('USERNAME', 'unknown_user')
    
    protocolo = st.text_input("Informe o número do protocolo!")
    
    # Armazenar arquivos processados na sessão
    if "processed_files" not in st.session_state:
        st.session_state["processed_files"] = []
    
    if "protocolo_atual" not in st.session_state:
        st.session_state["protocolo_atual"] = ""
    
    if "nome_pasta" not in st.session_state:
        st.session_state["nome_pasta"] = ""

    # Botão para criar diretório/nomear pasta
    if st.button("📁 Criar Nome da Pasta"):
        if protocolo:
            nome_pasta = f"protocolo_{protocolo}_{username}"
            st.session_state["nome_pasta"] = nome_pasta
            st.session_state["protocolo_atual"] = protocolo
            st.success(f"✅ Pasta criada: '{nome_pasta}'")
            st.info("Agora você pode fazer upload dos PDFs. Os arquivos serão organizados nesta pasta quando você fizer o download.")
        else:
            st.error("⚠️ Por favor, insira o número do protocolo antes de criar a pasta.")

    uploaded_files = st.file_uploader("Faça upload de PDFs escaneados", type=["pdf"], accept_multiple_files=True)

    # FUNÇÕES
    def preprocess_variants(image):
        """Retorna uma lista de variações da imagem pré-processada para OCR"""
        variants = []

        # Versão 1: Mais clara
        gray1 = image.convert("L")
        bin1 = gray1.point(lambda x: 0 if x < 180 else 255)
        variants.append(bin1)

        # Versão 2: Mais escura/adaptativa
        gray2 = image.convert("L")
        bin2 = gray2.point(lambda x: 0 if x < 160 else 255)
        variants.append(bin2)

        return variants

    def extract_card_number(text):
        pattern = r"(?:Nº|No|Número|Guia)\s*(?:Guia)?\s*(?:no|nº|número)?\s*Prestador[:\s]*([0-9]{6,})"
        match = re.search(pattern, text, re.IGNORECASE)
        return match.group(1) if match else None

    def reduzir_ou_dividir_pdf(pdf_bytes, max_mb=3):
        imagens = convert_from_bytes(pdf_bytes, dpi=300)
        partes = []
        tamanho_total = 0
        paginas_atual = []

        for i, imagem in enumerate(imagens):
            temp_buffer = io.BytesIO()
            imagem.save(temp_buffer, format="PDF")
            tamanho_pagina = len(temp_buffer.getvalue())

            if (tamanho_total + tamanho_pagina) > (max_mb * 1024 * 1024):
                if paginas_atual:
                    parte_buffer = io.BytesIO()
                    paginas_atual[0].save(parte_buffer, format='PDF', save_all=True, append_images=paginas_atual[1:])
                    partes.append(parte_buffer.getvalue())
                paginas_atual = [imagem]
                tamanho_total = tamanho_pagina
            else:
                paginas_atual.append(imagem)
                tamanho_total += tamanho_pagina

        if paginas_atual:
            parte_buffer = io.BytesIO()
            paginas_atual[0].save(parte_buffer, format='PDF', save_all=True, append_images=paginas_atual[1:])
            partes.append(parte_buffer.getvalue())

        return partes

    def preprocess_image(image):
        gray = image.convert("L")  # Grayscale
        # Binarização com threshold adaptativo
        return gray.point(lambda x: 0 if x < 160 else 255)

    # NOVA LÓGICA: OCR antes da compressão
    def encontrar_numero_guia(pdf_bytes):
        imagens = convert_from_bytes(pdf_bytes, dpi=300)
        for page_index, imagem in enumerate(imagens):
            angles = [0, 90, -90, 180]
            for angle in angles:
                rotated = imagem.rotate(angle, expand=True)

                for variant in preprocess_variants(rotated):
                    config = r'--oem 3 --psm 3'
                    text = pytesseract.image_to_string(variant, lang="por+eng", config=config)
                    numero = extract_card_number(text)
                    if numero:
                        return numero, len(imagens)
        return None, len(imagens)

    # PROCESSAMENTO PRINCIPAL
    if uploaded_files and st.session_state["nome_pasta"]:
        # Verificar se a pasta foi criada
        if not st.session_state["nome_pasta"]:
            st.error("⚠️ Crie o nome da pasta antes de processar os arquivos.")
            return
        
        start_time = time.time()
        sucesso = 0
        compactados = 0
        nao_encontrados = 0
        processed_files = []

        for uploaded_file in uploaded_files:
            st.divider()
            st.subheader(f"📄 Processando: {uploaded_file.name}")

            original_pdf_bytes = uploaded_file.read()
            tamanho_mb = len(original_pdf_bytes) / (1024 * 1024)

            # EXTRAIR NÚMERO ANTES DE VERIFICAR TAMANHO
            with st.spinner("🔍 Realizando a leitura do arquivo..."):
                numero_guia, total_paginas = encontrar_numero_guia(original_pdf_bytes)

            st.info(f"Total de páginas no PDF: {total_paginas}")

            if numero_guia:
                st.success(f"🔢 Número da guia encontrado: {numero_guia}")
            else:
                st.warning("⚠️ Número 'Nº Guia no Prestador:' não encontrado na primeira página.")
            
            # REDUZIR SE NECESSÁRIO
            if tamanho_mb > 3:
                st.warning(f"⚠️ Arquivo excede 3MB ({tamanho_mb:.2f} MB). Reduzindo e dividindo se necessário...")
                partes_pdf = reduzir_ou_dividir_pdf(original_pdf_bytes)
                compactados += 1
            else:
                partes_pdf = [original_pdf_bytes]

            # Processar e armazenar arquivos na sessão
            if numero_guia:
                for idx, parte in enumerate(partes_pdf):
                    sufixo_parte = f"_GUIA_DOC{idx+1}.pdf"
                    nome_arquivo = f"{numero_guia}{sufixo_parte}"
                    
                    processed_files.append({
                        'nome': nome_arquivo,
                        'dados': parte,
                        'tipo': 'com_guia',
                        'numero_guia': numero_guia
                    })
                st.success(f"✅ PDF processado: {numero_guia}_GUIA_DOC*.pdf")
                sucesso += 1
            else:
                for idx, parte in enumerate(partes_pdf):
                    sufixo_parte = f"_SEM_GUIA_DOC{idx+1}.pdf"
                    nome_arquivo = f"SEM_GUIA_{uploaded_file.name.replace('.pdf', '')}{sufixo_parte}"
                    
                    processed_files.append({
                        'nome': nome_arquivo,
                        'dados': parte,
                        'tipo': 'sem_guia',
                        'numero_guia': None
                    })

                st.info(f"📂 PDF sem número processado: {nome_arquivo}")
                nao_encontrados += 1

        # Armazenar arquivos processados na sessão
        st.session_state["processed_files"] = processed_files

        # RESUMO
        total = len(uploaded_files)
        st.divider()
        st.header("📊 Resumo do processamento")
        st.markdown(f"""
        - 📂 Arquivos processados: **{total}**
        - ✅ Arquivos com número da guia encontrado: **{sucesso}**
        - 📉 Arquivos compactados (reduzidos/divididos): **{compactados}**
        - ❌ Arquivos sem número da guia: **{nao_encontrados}**
        """)
        elapsed_time = time.time() - start_time
        minutes, seconds = divmod(int(elapsed_time), 60)
        st.info(f"🕒 Tempo total de execução: **{minutes} min {seconds} seg**")

    elif uploaded_files and not st.session_state["nome_pasta"]:
        st.error("⚠️ Crie o nome da pasta antes de processar os arquivos.")
    elif uploaded_files and not protocolo:
        st.error("⚠️ Informe o número do protocolo antes de criar a pasta.")

    # SEÇÃO DE DOWNLOAD DOS ARQUIVOS PROCESSADOS
    if st.session_state["processed_files"]:
        st.divider()
        st.header("💾 Download dos Arquivos Processados")
        st.info(f"📁 Pasta: {st.session_state['nome_pasta']}")
        
        # Botão para download de todos os arquivos
        if st.button("📦 Download de Todos os Arquivos (ZIP)"):
            import zipfile
            
            # Criar arquivo ZIP em memória
            zip_buffer = io.BytesIO()
            with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
                for file_info in st.session_state["processed_files"]:
                    zip_file.writestr(file_info['nome'], file_info['dados'])
            
            zip_buffer.seek(0)
            
            # Botão de download do ZIP
            st.download_button(
                label="💾 Download ZIP Completo",
                data=zip_buffer.getvalue(),
                file_name=f"{st.session_state['nome_pasta']}_processados.zip",
                mime="application/zip"
            )
        
        # Download individual de cada arquivo
        st.subheader("📄 Download Individual")
        for i, file_info in enumerate(st.session_state["processed_files"]):
            col1, col2 = st.columns([3, 1])
            with col1:
                st.write(f"**{file_info['nome']}**")
                if file_info['tipo'] == 'com_guia':
                    st.success(f"Guia: {file_info['numero_guia']}")
                else:
                    st.warning("Sem número de guia")
            
            with col2:
                st.download_button(
                    label="💾 Download",
                    data=file_info['dados'],
                    file_name=file_info['nome'],
                    mime="application/pdf",
                    key=f"download_{i}"
                )
        
        # Botão para limpar arquivos processados
        if st.button("🗑️ Limpar Arquivos Processados"):
            st.session_state["processed_files"] = []
            st.session_state["protocolo_atual"] = ""
            st.session_state["nome_pasta"] = ""
            st.rerun()

    # RODAPÉ
    footer_html = """
    <div style='text-align: center;'>
    <p>Developed by EDS Tecnologia da Informação - <small>v7 14/08/2025</small></p>
    </div>
    """
    st.markdown(footer_html, unsafe_allow_html=True)

# Executar a função principal
if __name__ == "__main__":
    run_ai_pdf()
