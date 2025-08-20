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

    protocolo = st.text_input("Informe o número do protocolo!")
    if "caminho_completo" not in st.session_state:
        st.session_state["caminho_completo"] = ""

    # Caminho base adaptado para Docker
    caminho_base = '/app/processed_pdfs/' 

    if st.button("Criar diretório"):
        if protocolo:
            caminho_completo = os.path.join(caminho_base, protocolo)
            st.session_state["caminho_completo"] = caminho_completo
            if os.path.exists(caminho_completo):
                st.warning(f"O diretório '{caminho_completo}' já existe.")
            else:
                os.makedirs(caminho_completo)
                st.success(f"Diretório '{caminho_completo}' criado com sucesso.")
        else:
            st.error("Por favor, insira um nome de diretório.")

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

    #def preprocess_image(image):
    #    gray = image.convert("L")
    #    return gray.point(lambda x: 0 if x < 180 else 255)

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
    if uploaded_files and st.session_state["caminho_completo"]:
        start_time = time.time()
        sucesso = 0
        compactados = 0
        nao_encontrados = 0

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

            if numero_guia:
                for idx, parte in enumerate(partes_pdf):
                    sufixo_parte = f"_GUIA_DOC{idx+1}.pdf"
                    caminho_parte = os.path.join(st.session_state["caminho_completo"], f"{numero_guia}{sufixo_parte}")
                    with open(caminho_parte, "wb") as f:
                        f.write(parte)
                st.success(f"✅ PDF salvo com nome base: {numero_guia}_GUIA_DOC*.pdf")
                sucesso += 1
            else:
                sub_dir_sem_numero = os.path.join(st.session_state["caminho_completo"], "SEM_NUMERO")
                if not os.path.exists(sub_dir_sem_numero):
                    os.makedirs(sub_dir_sem_numero)

                for idx, parte in enumerate(partes_pdf):
                    sufixo_parte = f"_SEM_GUIA_DOC{idx+1}.pdf"
                    caminho_parte = os.path.join(sub_dir_sem_numero, sufixo_parte)
                    with open(caminho_parte, "wb") as f:
                        f.write(parte)

                st.info(f"📂 PDF sem número foi salvo em: {sub_dir_sem_numero}")
                nao_encontrados += 1

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
        st.error("Pressione CTRL + F5 no teclado para processar outra remessa.")

    else:
        if uploaded_files and not st.session_state["caminho_completo"]:
            st.error("⚠️ Crie o diretório antes de fazer upload dos arquivos.")

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
